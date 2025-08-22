import base64
import json
import imaplib
import smtplib
import ssl
import time
from datetime import datetime, timedelta
from email.message import EmailMessage
from email.header import decode_header, make_header
from email.parser import BytesParser
from email import policy
from email.utils import getaddresses, formataddr, formatdate
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..core.security import decrypt_secret
from ..db.models.email import Email, Attachment
from ..db.models.user import User


def _make_smtp(user: User):
    settings = get_settings()
    context = ssl.create_default_context()
    password = decrypt_secret(user.encrypted_password)
    if settings.SMTP_USE_SSL:
        server = smtplib.SMTP_SSL(host=user.smtp_host, port=user.smtp_port, timeout=settings.SMTP_TIMEOUT_SECONDS, context=context)
    else:
        server = smtplib.SMTP(host=user.smtp_host, port=user.smtp_port, timeout=settings.SMTP_TIMEOUT_SECONDS)
        server.starttls(context=context)
    server.login(user.email, password)
    return server


def _parse_imap_list_response(response_line: str) -> tuple[list[str], str, str]:
    r"""
    Parse IMAP LIST response according to RFC 3501 and RFC 6154.
    Returns: (flags, delimiter, folder_name)
    
    Example inputs:
    - (\HasNoChildren \Sent) "/" "Sent Messages"  
    - (\HasNoChildren) "/" INBOX
    - (\Noselect \HasChildren) "/" "[Gmail]"
    """
    import re
    
    # Match pattern: (flags) "delimiter" "folder_name" or (flags) delimiter folder_name
    pattern = r'\(([^)]*)\)\s+"?([^"]*)"?\s+"?([^"]*)"?$'
    match = re.match(pattern, response_line.strip())
    
    if match:
        flags_str, delimiter, folder_name = match.groups()
        flags = [f.strip() for f in flags_str.split() if f.strip()]
        return flags, delimiter.strip('"'), folder_name.strip('"')
    
    # Fallback parsing for non-standard responses
    parts = response_line.split()
    if len(parts) >= 3:
        flags_part = ' '.join(parts[:-2])
        flags = [f.strip('()\\') for f in flags_part.split() if f.strip('()')]
        delimiter = parts[-2].strip('"')
        folder_name = parts[-1].strip('"')
        return flags, delimiter, folder_name
    
    return [], "", ""


def _make_imap(user: User, timeout_seconds: Optional[int] = None):
    """Create a fresh IMAP connection."""
    settings = get_settings()
    password = decrypt_secret(user.encrypted_password)
    timeout = timeout_seconds or settings.IMAP_TIMEOUT_SECONDS
    
    try:
        if settings.IMAP_USE_SSL:
            imap = imaplib.IMAP4_SSL(host=user.imap_host, port=user.imap_port, timeout=timeout)
        else:
            imap = imaplib.IMAP4(host=user.imap_host, port=user.imap_port, timeout=timeout)
            imap.starttls(ssl_context=ssl.create_default_context())
        
        imap.login(user.email, password)
        return imap
    except imaplib.IMAP4.error as e:
        raise ValueError(f"IMAP authentication failed: {e}")
    except Exception as e:
        raise ValueError(f"IMAP connection failed: {e}")


def _serialize_addresses(addrs: List[str]) -> str:
    return json.dumps(addrs) if addrs else "[]"


def _deserialize_addresses(s: Optional[str]) -> List[str]:
    if not s:
        return []
    try:
        return json.loads(s)
    except Exception:
        return []


# Drafts

def save_draft(db: Session, user: User, subject: Optional[str], body: Optional[str], to: List[str], cc: List[str], bcc: List[str], attachments: List[Tuple[str, Optional[str], bytes]]) -> Email:
    email = Email(
        user_id=user.id,
        folder="Drafts",
        subject=subject,
        body=body,
        from_address=user.email,
        to_addresses=_serialize_addresses(to),
        cc_addresses=_serialize_addresses(cc),
        bcc_addresses=_serialize_addresses(bcc),
        is_read=True,
    )
    db.add(email)
    db.flush()

    for filename, content_type, content in attachments:
        att = Attachment(email_id=email.id, filename=filename, content_type=content_type, blob=content)
        db.add(att)
    db.flush()
    return email


# Send email

def send_email(db: Session, user: User, subject: Optional[str], body: Optional[str], to: List[str], cc: List[str], bcc: List[str], attachments: List[Tuple[str, Optional[str], bytes]], draft_id: Optional[int] = None) -> Email:
    msg = EmailMessage()
    msg["From"] = user.email
    msg["To"] = ", ".join(to)
    if cc:
        msg["Cc"] = ", ".join(cc)
    msg["Subject"] = subject or ""
    # Ensure Date header exists so IMAP stores a proper date
    if "Date" not in msg:
        msg["Date"] = formatdate(localtime=True)
    msg.set_content(body or "")

    for filename, content_type, content in attachments:
        # Ensure we have a valid content type
        if not content_type or "/" not in content_type:
            # Try to guess content type from filename extension
            if filename.lower().endswith('.pdf'):
                content_type = "application/pdf"
            elif filename.lower().endswith(('.jpg', '.jpeg')):
                content_type = "image/jpeg"
            elif filename.lower().endswith('.png'):
                content_type = "image/png"
            elif filename.lower().endswith('.txt'):
                content_type = "text/plain"
            elif filename.lower().endswith('.doc'):
                content_type = "application/msword"
            elif filename.lower().endswith('.docx'):
                content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            else:
                content_type = "application/octet-stream"
        
        maintype, subtype = content_type.split("/", 1)
        print(f"DEBUG: Adding attachment {filename} with type {maintype}/{subtype}, size: {len(content)} bytes")
        msg.add_attachment(content, maintype=maintype, subtype=subtype, filename=filename)

    # Send via SMTP
    server = _make_smtp(user)
    try:
        recipients = list({*to, *cc, *bcc})
        print(f"DEBUG: Sending email from {user.email} to {recipients}")
        print(f"DEBUG: Email has {len(list(msg.walk()))} parts")
        for i, part in enumerate(msg.walk()):
            print(f"DEBUG: Part {i}: {part.get_content_type()}, filename: {part.get_filename()}")
        
        # Get message size before sending
        raw_msg = msg.as_bytes()
        print(f"DEBUG: Raw message size: {len(raw_msg)} bytes")
        
        server.send_message(msg, from_addr=user.email, to_addrs=recipients)
        print(f"DEBUG: Email sent successfully via SMTP")
    finally:
        try:
            server.quit()
        except Exception:
            pass

    # Try to append the exact sent message to the IMAP "Sent" folder (with common aliases)
    append_success = False
    max_retries = 2
    
    for attempt in range(max_retries):
        try:
            print(f"DEBUG: IMAP append attempt {attempt + 1}/{max_retries}")
            # Use longer timeout for append operations (60 seconds)
            imap = _make_imap(user, timeout_seconds=60)
            try:
                # Ensure proper CRLF line endings (critical for Yahoo and other strict servers)
                raw = msg.as_bytes().replace(b'\n', b'\r\n').replace(b'\r\r\n', b'\r\n')
                # Mark as Seen in Sent folder and use proper timestamp
                flags = r"(\Seen)"
                timestamp = imaplib.Time2Internaldate(time.time())
                sent_mailboxes = [
                    "Sent",
                    "Sent Items", 
                    "Sent Mail",
                    "[Gmail]/Sent Mail",
                    "[Gmail]/Sent",
                    "INBOX.Sent",
                    "INBOX/Sent",
                ]
                
                # First, let's see what mailboxes exist and try to find the Sent folder (only on first attempt)
                actual_sent_folder = None
                if attempt == 0:
                    try:
                        # Try to use RFC 6154 special-use extension to find the Sent folder
                        try:
                            # RFC 6154: LIST-EXTENDED with SPECIAL-USE return option
                            status, special_use = imap.list('(SPECIAL-USE)', '*')
                            if status == "OK" and special_use:
                                print(f"DEBUG: RFC 6154 Special-use mailboxes found:")
                                for mb in special_use:
                                    mb_str = mb.decode() if isinstance(mb, bytes) else str(mb)
                                    print(f"  {mb_str}")
                                    
                                    # Parse the IMAP LIST response properly
                                    flags, delimiter, folder_name = _parse_imap_list_response(mb_str)
                                    
                                    # Look for \Sent attribute in the flags
                                    if '\\Sent' in flags or 'Sent' in flags:
                                        actual_sent_folder = folder_name
                                        print(f"DEBUG: Found RFC 6154 \\Sent folder: '{actual_sent_folder}' (flags: {flags})")
                                        break
                            else:
                                print(f"DEBUG: RFC 6154 LIST (SPECIAL-USE) returned: {status}")
                                
                        except Exception as e:
                            print(f"DEBUG: RFC 6154 special-use not supported or failed: {e}")
                            
                            # Fallback: Try alternative RFC 6154 syntax
                            try:
                                # Some servers might support XLIST (Gmail's predecessor to RFC 6154)
                                status, xlist_result = imap.xlist('', '*')
                                if status == "OK" and xlist_result:
                                    print(f"DEBUG: Trying XLIST (Gmail extension):")
                                    for mb in xlist_result:
                                        mb_str = mb.decode() if isinstance(mb, bytes) else str(mb)
                                        print(f"  {mb_str}")
                                        
                                        # Parse the XLIST response
                                        flags, delimiter, folder_name = _parse_imap_list_response(mb_str)
                                        
                                        if '\\Sent' in flags or 'Sent' in flags:
                                            actual_sent_folder = folder_name
                                            print(f"DEBUG: Found XLIST \\Sent folder: '{actual_sent_folder}' (flags: {flags})")
                                            break
                            except Exception as xlist_e:
                                print(f"DEBUG: XLIST also not supported: {xlist_e}")
                        
                        # List all mailboxes for debugging and look for special-use attributes
                        status, mailbox_list = imap.list()
                        if status == "OK":
                            print(f"DEBUG: Available mailboxes for {user.email}:")
                            for mb in mailbox_list:
                                mb_str = mb.decode() if isinstance(mb, bytes) else str(mb)
                                print(f"  {mb_str}")
                                
                                # Parse each mailbox to find special-use attributes
                                if not actual_sent_folder:
                                    flags, delimiter, folder_name = _parse_imap_list_response(mb_str)
                                    if '\\Sent' in flags:
                                        actual_sent_folder = folder_name
                                        print(f"DEBUG: Found \\Sent folder in regular LIST: '{actual_sent_folder}' (flags: {flags})")
                    except Exception as e:
                        print(f"DEBUG: Could not list mailboxes: {e}")
                
                # If we found the actual Sent folder via RFC 6154, try it first
                if actual_sent_folder:
                    # Remove duplicates and prioritize the RFC 6154 folder
                    sent_mailboxes = [actual_sent_folder] + [mb for mb in sent_mailboxes if mb != actual_sent_folder]
                    print(f"DEBUG: Prioritized folder order: {sent_mailboxes[:3]}...")  # Show first 3
                
                for mbox in sent_mailboxes:
                    print(f"DEBUG: Trying to append to mailbox: {mbox}")
                    try:
                        # Try with proper timestamp and flags (recommended approach)
                        status, response = imap.append(mbox, flags, timestamp, raw)
                        print(f"DEBUG: Append with flags and timestamp - Status: {status}, Response: {response}")
                        if status != "OK":
                            # Fallback: try without flags
                            status, response = imap.append(mbox, None, timestamp, raw)
                            print(f"DEBUG: Append without flags but with timestamp - Status: {status}, Response: {response}")
                        if status != "OK":
                            # Last resort: try without timestamp and flags
                            status, response = imap.append(mbox, None, None, raw)
                            print(f"DEBUG: Append minimal - Status: {status}, Response: {response}")
                        if status == "OK":
                            print(f"DEBUG: Successfully appended to {mbox}")
                            append_success = True
                            # Some servers need an expunge to make it visible immediately
                            try:
                                imap.expunge()
                            except Exception as e:
                                print(f"DEBUG: Expunge failed: {e}")
                            break
                    except Exception as e:
                        print(f"DEBUG: Failed to append to {mbox}: {e}")
                        # If we get a timeout, break out of the loop to avoid more timeouts
                        if "timed out" in str(e).lower():
                            print(f"DEBUG: Timeout detected, stopping further attempts on this connection")
                            break
                        # Some servers require the mailbox to exist first
                        try:
                            print(f"DEBUG: Trying to create mailbox: {mbox}")
                            create_status, create_response = imap.create(mbox)
                            print(f"DEBUG: Create mailbox - Status: {create_status}, Response: {create_response}")
                            if create_status == "OK":
                                # Try with proper timestamp and flags first
                                status, response = imap.append(mbox, flags, timestamp, raw)
                                print(f"DEBUG: Append after create (with flags and timestamp) - Status: {status}, Response: {response}")
                                if status != "OK":
                                    status, response = imap.append(mbox, None, timestamp, raw)
                                    print(f"DEBUG: Append after create (timestamp only) - Status: {status}, Response: {response}")
                                if status != "OK":
                                    status, response = imap.append(mbox, None, None, raw)
                                    print(f"DEBUG: Append after create (minimal) - Status: {status}, Response: {response}")
                                if status == "OK":
                                    print(f"DEBUG: Successfully appended to newly created {mbox}")
                                    append_success = True
                                    try:
                                        imap.expunge()
                                    except Exception as e:
                                        print(f"DEBUG: Expunge failed: {e}")
                                    break
                        except Exception as create_e:
                            print(f"DEBUG: Failed to create/append to {mbox}: {create_e}")
                            # If we get a timeout, break out of the loop
                            if "timed out" in str(create_e).lower():
                                print(f"DEBUG: Timeout during create, stopping further attempts")
                                break
                            continue
                
                if append_success:
                    break  # Success, no need to retry
                    
            finally:
                try:
                    imap.logout()
                except Exception as e:
                    print(f"DEBUG: IMAP logout failed: {e}")
                    
        except Exception as e:
            print(f"DEBUG: IMAP connection/operation failed on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                print(f"DEBUG: Retrying in 2 seconds...")
                time.sleep(2)
            continue
        
        if append_success:
            break
    
    if not append_success:
        print(f"DEBUG: Failed to append email to any IMAP Sent folder for {user.email} after {max_retries} attempts")

    # Persist a local copy in DB as before
    sent_email = Email(
        user_id=user.id,
        folder="Sent",
        subject=subject,
        body=body,
        from_address=user.email,
        to_addresses=_serialize_addresses(to),
        cc_addresses=_serialize_addresses(cc),
        bcc_addresses=_serialize_addresses(bcc),
        is_read=True,
    )
    db.add(sent_email)
    db.flush()

    for filename, content_type, content in attachments:
        att = Attachment(email_id=sent_email.id, filename=filename, content_type=content_type, blob=content)
        db.add(att)

    if draft_id:
        # Optionally, move draft to Sent/Trash; here we delete or mark as trash
        draft = db.get(Email, draft_id)
        if draft and draft.user_id == user.id:
            draft.folder = "Trash"
    db.flush()
    return sent_email


# IMAP debugging utility
def poll_for_new_emails(user: User, folder: str = "INBOX", timeout_seconds: int = 30) -> dict:
    """
    Poll for new emails using IMAP with comprehensive refresh strategy.
    Returns information about new emails found.
    """
    print(f"DEBUG: Starting email poll for {user.email} in folder {folder}")
    
    try:
        imap = _make_imap(user, timeout_seconds=timeout_seconds)
        try:
            # Select the folder
            status, select_response = imap.select(folder, readonly=True)
            if status != "OK":
                return {"success": False, "error": f"Failed to select folder {folder}"}
            
            print(f"DEBUG: Selected {folder}, response: {select_response}")
            
            # Comprehensive refresh strategy
            refresh_commands = []
            
            # 1. NOOP to get server updates
            try:
                imap.noop()
                refresh_commands.append("NOOP: OK")
            except Exception as e:
                refresh_commands.append(f"NOOP: FAILED - {e}")
            
            # 2. CHECK for mailbox checkpoint
            try:
                imap.check()
                refresh_commands.append("CHECK: OK")
            except Exception as e:
                refresh_commands.append(f"CHECK: FAILED - {e}")
            
            # 3. Re-select folder for fresh state
            try:
                imap.close()
                status, _ = imap.select(folder, readonly=True)
                if status == "OK":
                    refresh_commands.append("RE-SELECT: OK")
                else:
                    refresh_commands.append(f"RE-SELECT: FAILED - {status}")
            except Exception as e:
                refresh_commands.append(f"RE-SELECT: FAILED - {e}")
                # Fallback to original selection
                imap.select(folder, readonly=True)
            
            # Search for all emails
            status, all_data = imap.search(None, "ALL")
            total_count = 0
            if status == "OK" and all_data and all_data[0]:
                total_count = len(all_data[0].split())
            
            # Search for unseen emails
            status, unseen_data = imap.search(None, "UNSEEN")
            unseen_count = 0
            unseen_uids = []
            if status == "OK" and unseen_data and unseen_data[0]:
                unseen_uids = unseen_data[0].split()
                unseen_count = len(unseen_uids)
            
            # Search for recent emails
            status, recent_data = imap.search(None, "RECENT")
            recent_count = 0
            recent_uids = []
            if status == "OK" and recent_data and recent_data[0]:
                recent_uids = recent_data[0].split()
                recent_count = len(recent_uids)
            
            # Get details of recent emails
            new_emails = []
            for uid in recent_uids[:5]:  # Limit to 5 most recent
                try:
                    status, msg_data = imap.fetch(uid, "(BODY.PEEK[HEADER.FIELDS (SUBJECT FROM DATE)] FLAGS)")
                    if status == "OK" and msg_data:
                        raw_bytes = b""
                        flags_info = ""
                        for part in msg_data:
                            if isinstance(part, tuple):
                                raw_bytes += part[1]
                            else:
                                flags_info = str(part)
                        
                        # Parse basic headers
                        try:
                            msg = BytesParser(policy=policy.default).parsebytes(raw_bytes)
                            subject = str(make_header(decode_header(msg.get('Subject', '')))) if msg.get('Subject') else "No Subject"
                            from_addr = msg.get('From', 'Unknown Sender')
                            date = msg.get('Date', 'Unknown Date')
                            is_read = "\\Seen" in flags_info
                            
                            new_emails.append({
                                "uid": uid.decode() if isinstance(uid, bytes) else str(uid),
                                "subject": subject,
                                "from": from_addr,
                                "date": date,
                                "is_read": is_read
                            })
                        except Exception as e:
                            print(f"DEBUG: Failed to parse email UID {uid}: {e}")
                except Exception as e:
                    print(f"DEBUG: Failed to fetch email UID {uid}: {e}")
            
            return {
                "success": True,
                "folder": folder,
                "total_emails": total_count,
                "unseen_emails": unseen_count,
                "recent_emails": recent_count,
                "new_emails": new_emails,
                "refresh_commands": refresh_commands,
                "unseen_uids": [uid.decode() if isinstance(uid, bytes) else str(uid) for uid in unseen_uids],
                "recent_uids": [uid.decode() if isinstance(uid, bytes) else str(uid) for uid in recent_uids]
            }
            
        finally:
            # AGGRESSIVE CONNECTION CLEANUP - NO REUSE EVER
            try:
                print(f"DEBUG: Aggressively closing IMAP connection (poll_for_new_emails)")
                imap.close()  # Close selected folder
            except Exception as e:
                print(f"DEBUG: IMAP close failed: {e}")
            
            try:
                imap.logout()  # Logout and close connection
                print(f"DEBUG: IMAP logout successful (poll_for_new_emails)")
            except Exception as e:
                print(f"DEBUG: IMAP logout failed: {e}")
            
            try:
                # Force socket closure if possible
                if hasattr(imap, 'sock') and imap.sock:
                    imap.sock.close()
                    print(f"DEBUG: IMAP socket forcefully closed (poll_for_new_emails)")
            except Exception as e:
                print(f"DEBUG: IMAP socket close failed: {e}")
            
            # Explicitly delete the connection object
            try:
                del imap
                print(f"DEBUG: IMAP connection object deleted (poll_for_new_emails)")
            except Exception as e:
                print(f"DEBUG: IMAP object deletion failed: {e}")
                
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "folder": folder
        }


def imap_idle_monitor(user: User, folder: str = "INBOX", timeout_seconds: int = 300) -> dict:
    """
    Use IMAP IDLE to monitor for new emails in real-time.
    This is more efficient than polling but not all servers support it.
    """
    print(f"DEBUG: Starting IMAP IDLE monitor for {user.email} in folder {folder}")
    
    try:
        imap = _make_imap(user, timeout_seconds=timeout_seconds)
        try:
            # Check if server supports IDLE
            if 'IDLE' not in imap.capabilities:
                return {
                    "success": False,
                    "error": "Server does not support IMAP IDLE",
                    "capabilities": list(imap.capabilities)
                }
            
            # Select the folder
            status, select_response = imap.select(folder, readonly=True)
            if status != "OK":
                return {"success": False, "error": f"Failed to select folder {folder}"}
            
            print(f"DEBUG: Starting IDLE command for {folder}")
            
            # Start IDLE
            tag = imap._new_tag()
            imap.send(f'{tag} IDLE\r\n'.encode())
            
            # Wait for server response
            response = imap.readline()
            if b'+ idling' not in response.lower() and b'+ waiting' not in response.lower():
                return {
                    "success": False,
                    "error": f"IDLE command failed: {response.decode()}"
                }
            
            print(f"DEBUG: IDLE started successfully, waiting for updates...")
            
            # Monitor for updates
            updates = []
            start_time = time.time()
            
            while time.time() - start_time < timeout_seconds:
                try:
                    # Set a short timeout for readline to check for updates
                    imap.sock.settimeout(1.0)
                    response = imap.readline()
                    
                    if response:
                        response_str = response.decode().strip()
                        print(f"DEBUG: IDLE response: {response_str}")
                        updates.append(response_str)
                        
                        # Check for new message notifications
                        if 'EXISTS' in response_str or 'RECENT' in response_str:
                            print(f"DEBUG: New email detected: {response_str}")
                            break
                            
                except Exception as e:
                    if "timed out" not in str(e).lower():
                        print(f"DEBUG: IDLE monitoring error: {e}")
                    continue
            
            # End IDLE
            try:
                imap.send(b'DONE\r\n')
                response = imap.readline()
                print(f"DEBUG: IDLE ended: {response.decode()}")
            except Exception as e:
                print(f"DEBUG: Failed to end IDLE: {e}")
            
            # Check for new emails after IDLE
            status, all_data = imap.search(None, "ALL")
            total_count = len(all_data[0].split()) if status == "OK" and all_data and all_data[0] else 0
            
            status, unseen_data = imap.search(None, "UNSEEN")
            unseen_count = len(unseen_data[0].split()) if status == "OK" and unseen_data and unseen_data[0] else 0
            
            return {
                "success": True,
                "folder": folder,
                "idle_duration": time.time() - start_time,
                "updates_received": updates,
                "total_emails": total_count,
                "unseen_emails": unseen_count,
                "new_emails_detected": any('EXISTS' in update or 'RECENT' in update for update in updates)
            }
            
        finally:
            # AGGRESSIVE CONNECTION CLEANUP - NO REUSE EVER
            try:
                print(f"DEBUG: Aggressively closing IMAP connection (imap_idle_monitor)")
                imap.close()  # Close selected folder
            except Exception as e:
                print(f"DEBUG: IMAP close failed: {e}")
            
            try:
                imap.logout()  # Logout and close connection
                print(f"DEBUG: IMAP logout successful (imap_idle_monitor)")
            except Exception as e:
                print(f"DEBUG: IMAP logout failed: {e}")
            
            try:
                # Force socket closure if possible
                if hasattr(imap, 'sock') and imap.sock:
                    imap.sock.close()
                    print(f"DEBUG: IMAP socket forcefully closed (imap_idle_monitor)")
            except Exception as e:
                print(f"DEBUG: IMAP socket close failed: {e}")
            
            # Explicitly delete the connection object
            try:
                del imap
                print(f"DEBUG: IMAP connection object deleted (imap_idle_monitor)")
            except Exception as e:
                print(f"DEBUG: IMAP object deletion failed: {e}")
                
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "folder": folder
        }


def debug_imap_connection(user: User) -> dict:
    """Debug IMAP connection and return server info."""
    try:
        imap = _make_imap(user, timeout_seconds=30)
        try:
            # Get server capabilities
            capabilities = imap.capabilities
            
            # List all mailboxes
            status, mailboxes = imap.list()
            mailbox_list = []
            if status == "OK":
                for mb in mailboxes:
                    mb_str = mb.decode() if isinstance(mb, bytes) else str(mb)
                    mailbox_list.append(mb_str)
            
            # Select INBOX and get status
            status, select_response = imap.select("INBOX", readonly=True)
            inbox_status = {
                "status": status,
                "response": select_response[0].decode() if select_response and select_response[0] else None
            }
            
            # Search for recent emails
            status, recent_data = imap.search(None, "RECENT")
            recent_count = 0
            if status == "OK" and recent_data and recent_data[0]:
                recent_count = len(recent_data[0].split())
            
            # Search for all emails
            status, all_data = imap.search(None, "ALL")
            total_count = 0
            if status == "OK" and all_data and all_data[0]:
                total_count = len(all_data[0].split())
            
            return {
                "success": True,
                "capabilities": list(capabilities),
                "mailboxes": mailbox_list,
                "inbox_status": inbox_status,
                "recent_emails": recent_count,
                "total_emails": total_count,
                "server_info": {
                    "host": user.imap_host,
                    "port": user.imap_port,
                    "ssl": get_settings().IMAP_USE_SSL
                }
            }
        finally:
            # AGGRESSIVE CONNECTION CLEANUP - NO REUSE EVER
            try:
                print(f"DEBUG: Aggressively closing IMAP connection (debug_imap_connection)")
                imap.close()  # Close selected folder
            except Exception as e:
                print(f"DEBUG: IMAP close failed: {e}")
            
            try:
                imap.logout()  # Logout and close connection
                print(f"DEBUG: IMAP logout successful (debug_imap_connection)")
            except Exception as e:
                print(f"DEBUG: IMAP logout failed: {e}")
            
            try:
                # Force socket closure if possible
                if hasattr(imap, 'sock') and imap.sock:
                    imap.sock.close()
                    print(f"DEBUG: IMAP socket forcefully closed (debug_imap_connection)")
            except Exception as e:
                print(f"DEBUG: IMAP socket close failed: {e}")
            
            # Explicitly delete the connection object
            try:
                del imap
                print(f"DEBUG: IMAP connection object deleted (debug_imap_connection)")
            except Exception as e:
                print(f"DEBUG: IMAP object deletion failed: {e}")
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "server_info": {
                "host": user.imap_host,
                "port": user.imap_port,
                "ssl": get_settings().IMAP_USE_SSL
            }
        }


# Mailbox listing via IMAP (no caching for real-time data)

def list_mailbox(user: User, folder: str, page: int, size: int):
    """Return (total, items) for a mailbox using IMAP. Optimized for speed."""
    print(f"DEBUG: Fetching emails for {user.email} in {folder} (page {page}, size {size})")
    
    # Use shorter timeout for faster response
    timeout_seconds = 15
    imap = _make_imap(user, timeout_seconds=timeout_seconds)
    try:
        # Select folder with alternative names fallback
        # Map common folder names to actual IMAP folder names
        folder_map = {
            "INBOX": "INBOX",
            "Sent": "INBOX.Sent", 
            "Trash": "INBOX.Trash",
            "Archive": "INBOX.Archive",
            "Spam": "INBOX.spam",
            "Drafts": "INBOX.Drafts"
        }
        
        # Use the correct folder name
        actual_folder = folder_map.get(folder, folder)
        
        try:
            status, select_response = imap.select(actual_folder, readonly=True)
            if status == "OK":
                print(f"DEBUG: Selected {actual_folder}")
            else:
                print(f"DEBUG: Failed to select {actual_folder}: {status}")
                return {"total": 0, "items": []}
        except Exception as e:
            print(f"DEBUG: Exception selecting {actual_folder}: {e}")
            return {"total": 0, "items": []}
        
        # Simple search for all emails - no aggressive refresh
        try:
            status, data = imap.search(None, "ALL")
            if status != "OK" or not data or not data[0]:
                print(f"DEBUG: No emails found in {folder}")
                return {"total": 0, "items": []}
            
            all_uids = data[0].split()
            total = len(all_uids)
            print(f"DEBUG: Found {total} emails in {folder}")
            
        except Exception as e:
            print(f"DEBUG: Search failed: {e}")
            return {"total": 0, "items": []}
        
        # Sort by UID descending (newest first)
        try:
            all_uids.sort(key=lambda x: int(x), reverse=True)
        except Exception as e:
            print(f"DEBUG: UID sorting failed: {e}")
            all_uids = list(reversed(all_uids))
        
        # Get page slice
        start = (page - 1) * size
        end = start + size
        page_uids = all_uids[start:end]
        
        items = []
        print(f"DEBUG: Processing {len(page_uids)} emails for page {page}")
        
        for uid in page_uids:
            try:
                # Fetch headers and flags efficiently
                status, msg_data = imap.fetch(uid, "(BODY.PEEK[HEADER] FLAGS)")
                if status != "OK" or not msg_data:
                    print(f"DEBUG: Failed to fetch email UID {uid}")
                    continue
                
                raw_bytes = b""
                flags_info = ""
                for part in msg_data:
                    if isinstance(part, tuple):
                        raw_bytes += part[1]
                    else:
                        flags_info = str(part)
                
                # Parse flags to determine read status
                is_read = "\\Seen" in flags_info
                
                # Parse headers
                try:
                    msg = BytesParser(policy=policy.default).parsebytes(raw_bytes)
                    
                    # Decode Subject
                    dh = decode_header(msg.get('Subject', ''))
                    subject = str(make_header(dh)) if dh else None

                    # Decode From and To
                    from_parsed = getaddresses([msg.get('From', '')])
                    from_addr = formataddr(from_parsed[0]) if from_parsed else None

                    to_parsed = getaddresses([msg.get('To', '')])
                    to_addrs = [formataddr(t) for t in to_parsed] if to_parsed else []
                    
                except Exception as e:
                    print(f"DEBUG: Header parsing failed for UID {uid}: {e}")
                    # Fallback parsing
                    header_text = raw_bytes.decode(errors="ignore")
                    subject = header_text.split("\nSubject:", 1)[-1].split("\n", 1)[0].strip() if "Subject:" in header_text else None
                    from_addr = header_text.split("\nFrom:", 1)[-1].split("\n", 1)[0].strip() if "From:" in header_text else None
                    to_addrs = [p.strip() for p in (header_text.split("\nTo:", 1)[-1].split("\n", 1)[0] if "To:" in header_text else "").split(",") if p.strip()]

                # Convert UID to int
                try:
                    item_id = int(uid)
                except Exception:
                    item_id = int.from_bytes(uid, "big")
                
                email_item = {
                    "id": item_id,
                    "folder": folder,
                    "subject": subject,
                    "from_address": from_addr,
                    "to_addresses": to_addrs,
                    "is_read": is_read,
                }
                items.append(email_item)
                
            except Exception as e:
                print(f"DEBUG: Error processing UID {uid}: {e}")
                continue
        
        payload = {"total": total, "items": items}
        print(f"DEBUG: Completed fetch - Total: {total}, Items: {len(items)}")
        return payload
        
    finally:
        # Clean connection cleanup
        try:
            imap.close()
        except Exception as e:
            print(f"DEBUG: IMAP close failed: {e}")
        
        try:
            imap.logout()
        except Exception as e:
            print(f"DEBUG: IMAP logout failed: {e}")


def get_email_imap(user: User, folder: str, seq_num: int):
    """Fetch a single email detail from IMAP by sequence number in the folder."""
    imap = _make_imap(user)
    try:
        # Map common folder names to actual IMAP folder names
        folder_map = {
            "INBOX": "INBOX",
            "Sent": "INBOX.Sent", 
            "Trash": "INBOX.Trash",
            "Archive": "INBOX.Archive",
            "Spam": "INBOX.spam",
            "Drafts": "INBOX.Drafts"
        }
        
        # Use the correct folder name
        actual_folder = folder_map.get(folder, folder)
        
        status, _ = imap.select(actual_folder, readonly=True)
        if status != "OK":
            return None
        status, msg_data = imap.fetch(str(seq_num), "(BODY.PEEK[] FLAGS)")
        if status != "OK" or not msg_data:
            return None

        raw_bytes = b""
        flags_blob = b"".join(part[0] if isinstance(part, tuple) else b"" for part in msg_data)
        for part in msg_data:
            if isinstance(part, tuple):
                raw_bytes += part[1]
        try:
            msg = BytesParser(policy=policy.default).parsebytes(raw_bytes)
        except Exception:
            return None

        # Decode headers
        dh = decode_header(msg.get('Subject', ''))
        subject = str(make_header(dh)) if dh else None
        from_parsed = getaddresses([msg.get('From', '')])
        from_addr = formataddr(from_parsed[0]) if from_parsed else None
        to_parsed = getaddresses([msg.get('To', '')])
        to_addrs = [formataddr(t) for t in to_parsed] if to_parsed else []
        cc_parsed = getaddresses([msg.get('Cc', '')])
        cc_addrs = [formataddr(t) for t in cc_parsed] if cc_parsed else []
        bcc_parsed = getaddresses([msg.get('Bcc', '')])
        bcc_addrs = [formataddr(t) for t in bcc_parsed] if bcc_parsed else []

        # Body and attachments
        text_body = None
        html_body = None
        attachments: list[str] = []
        if msg.is_multipart():
            for part in msg.walk():
                disp = (part.get_content_disposition() or '').lower()
                ctype = part.get_content_type()
                if disp == 'attachment':
                    filename = part.get_filename()
                    if filename:
                        try:
                            filename = str(make_header(decode_header(filename)))
                        except Exception:
                            pass
                        attachments.append(filename)
                elif ctype == 'text/plain' and text_body is None:
                    try:
                        text_body = part.get_content()
                    except Exception:
                        try:
                            text_body = part.get_payload(decode=True).decode(errors='ignore')
                        except Exception:
                            pass
                elif ctype == 'text/html' and html_body is None:
                    try:
                        html_body = part.get_content()
                    except Exception:
                        try:
                            html_body = part.get_payload(decode=True).decode(errors='ignore')
                        except Exception:
                            pass
        else:
            ctype = msg.get_content_type()
            if ctype == 'text/plain':
                try:
                    text_body = msg.get_content()
                except Exception:
                    try:
                        text_body = msg.get_payload(decode=True).decode(errors='ignore')
                    except Exception:
                        pass
            else:
                try:
                    html_body = msg.get_content()
                except Exception:
                    try:
                        html_body = msg.get_payload(decode=True).decode(errors='ignore')
                    except Exception:
                        pass

        body = text_body or html_body or ""

        # Flags -> read/unread (very naive)
        flags_text = (flags_blob or b"").decode(errors='ignore')
        is_read = "\\Seen" in flags_text

        return {
            "id": seq_num,
            "folder": folder,
            "subject": subject,
            "body": body,
            "from_address": from_addr,
            "to_addresses": to_addrs,
            "cc_addresses": cc_addrs,
            "bcc_addresses": bcc_addrs,
            "is_read": is_read,
            "attachments": attachments,
        }
    finally:
        # AGGRESSIVE CONNECTION CLEANUP - NO REUSE EVER
        try:
            print(f"DEBUG: Aggressively closing IMAP connection (get_email_imap)")
            imap.close()  # Close selected folder
        except Exception as e:
            print(f"DEBUG: IMAP close failed: {e}")
        
        try:
            imap.logout()  # Logout and close connection
            print(f"DEBUG: IMAP logout successful (get_email_imap)")
        except Exception as e:
            print(f"DEBUG: IMAP logout failed: {e}")
        
        try:
            # Force socket closure if possible
            if hasattr(imap, 'sock') and imap.sock:
                imap.sock.close()
                print(f"DEBUG: IMAP socket forcefully closed (get_email_imap)")
        except Exception as e:
            print(f"DEBUG: IMAP socket close failed: {e}")
        
        # Explicitly delete the connection object
        try:
            del imap
            print(f"DEBUG: IMAP connection object deleted (get_email_imap)")
        except Exception as e:
            print(f"DEBUG: IMAP object deletion failed: {e}")


def move_email_db(db: Session, user: User, email_id: int, target_folder: str) -> Optional[Email]:
    email = db.get(Email, email_id)
    if not email or email.user_id != user.id:
        return None
    email.folder = target_folder
    db.flush()
    return email


def set_read_flag_db(db: Session, user: User, email_id: int, is_read: bool) -> Optional[Email]:
    email = db.get(Email, email_id)
    if not email or email.user_id != user.id:
        return None
    email.is_read = is_read
    db.flush()
    return email