"""
IMAP operations module for email service.
Handles IMAP-specific operations like reading, moving, flagging emails.
"""
import imaplib
import time
from datetime import datetime
from typing import List, Optional, Tuple, Any, Dict
from email.parser import BytesParser
from email import policy
from ..core.connection_pool import get_imap_client
from ..core.config import get_settings
from ..core.security import decrypt_secret
from .folder_manager import _key_from_folder_hint, resolve_special_folder, resolve_special_folder_sync
from .email_parser import parse_full_email, format_email_summary, _parse_timestamp, _infer_importance_from_headers
from .attachment_handler import find_attachment_in_message
from typing import Protocol
import imaplib


class UserLike(Protocol):
    email: str
    encrypted_password: str
    smtp_host: str
    smtp_port: int
    imap_host: str
    imap_port: int


def _build_search_query(search_text: Optional[str] = None, is_starred: Optional[bool] = None, read_status: Optional[bool] = None) -> str:
    """Build IMAP search query based on filters."""
    query_parts = []
    
    if search_text:
        # Search in subject, from, and body
        search_escaped = search_text.replace('"', '\\"')
        query_parts.append(f'(OR (OR SUBJECT "{search_escaped}" FROM "{search_escaped}") BODY "{search_escaped}")')
    
    if is_starred is not None:
        if is_starred:
            query_parts.append("FLAGGED")
        else:
            query_parts.append("UNFLAGGED")
    
    if read_status is not None:
        if read_status:
            query_parts.append("SEEN")
        else:
            query_parts.append("UNSEEN")
    
    return " ".join(query_parts) if query_parts else "ALL"


async def _safe_examine_folder(imap, folder: str, user_email: str) -> tuple[bool, str]:
    """Safely select a folder with comprehensive error handling and logging.
    Uses SELECT instead of EXAMINE to ensure proper IMAP state for UID operations.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # First check the current IMAP state
        state = getattr(imap, 'state', 'UNKNOWN')
        protocol_state = getattr(imap.protocol, 'state', 'UNKNOWN') if hasattr(imap, 'protocol') else 'UNKNOWN'
        logger.info(f"IMAP state before folder access: client={state}, protocol={protocol_state}")
        
        # Use SELECT instead of EXAMINE to ensure proper state for UID operations
        # This is necessary because aioimaplib doesn't properly track state after EXAMINE
        status, response = await imap.select(folder)
        logger.info(f"Select '{folder}' - Status: {status}, Response: {response}")
        
        if status == "OK":
            # Verify we're in the correct state after select
            new_state = getattr(imap, 'state', 'UNKNOWN')
            new_protocol_state = getattr(imap.protocol, 'state', 'UNKNOWN') if hasattr(imap, 'protocol') else 'UNKNOWN'
            logger.info(f"IMAP state after select: client={new_state}, protocol={new_protocol_state}")
            
            # SELECT should put us in SELECTED state which allows UID operations
            logger.info(f"Folder '{folder}' successfully selected - ready for UID operations")
            return True, folder
        else:
            logger.warning(f"SELECT failed for '{folder}' - Status: {status}, Response: {response}")
            return False, folder
            
    except Exception as e:
        logger.error(f"Exception during folder access of '{folder}' for {user_email}: {e}")
        return False, folder


async def list_mailbox(user: UserLike, folder: str, page: int, size: int, refresh: bool = False, search_text: Optional[str] = None, is_starred: Optional[bool] = None, read_status: Optional[bool] = None):
    """Return (total, items) for a mailbox using IMAP.
    - Accepts either exact provider path or a standardized hint (e.g., "inbox", "sent").
    - If direct select fails, resolves to provider-specific path via discovery.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Use the fixed connection pool
        async with get_imap_client(user) as imap:
            effective_folder = folder
            # For "inbox", try "INBOX" first (standard IMAP folder name)
            if folder.lower() == "inbox":
                effective_folder = "INBOX"
                # Try to examine the folder using our safe method
                success, effective_folder = await _safe_examine_folder(imap, effective_folder, user.email)
            else:
                # For non-inbox folders, use folder discovery first to avoid failed attempts
                success = False
                key = _key_from_folder_hint(folder)
                if key:
                    # Use async resolver with actual folder discovery
                    resolved = await resolve_special_folder(user, key)
                    if resolved:
                        success, effective_folder = await _safe_examine_folder(imap, resolved, user.email)
                
                # If folder discovery didn't work, try the original folder name as fallback
                if not success:
                    success, effective_folder = await _safe_examine_folder(imap, folder, user.email)
            
            if not success:
                # Last resort: try common variations if this is inbox
                if folder.lower() == "inbox":
                    for inbox_variant in ["INBOX", "Inbox", "inbox"]:
                        success, effective_folder = await _safe_examine_folder(imap, inbox_variant, user.email)
                        if success:
                            break
                
                # If still failed, log and return empty
                if not success:
                    logger.error(f"CRITICAL: Failed to examine any folder for user {user.email}. Original folder: {folder}. Cannot proceed with UID commands.")
                    return {"total": 0, "items": []}
            
            logger.info(f"Successfully examined folder '{effective_folder}' for user {user.email}. Proceeding with email search.")
            
            if refresh:
                # NOOP is a standard way to ask the server for any pending updates (e.g., new mail)
                # without changing the selected mailbox state. This forces a refresh.
                try:
                    await imap.noop()
                except Exception:
                    # Not fatal, proceed anyway
                    pass
            
            # Build search query
            search_query = _build_search_query(search_text, is_starred, read_status)
            
            # Final safety check: verify IMAP state before UID operations
            if not success:
                logger.error(f"ABORT: Cannot execute UID commands - no mailbox selected for user {user.email}")
                return {"total": 0, "items": []}
            
            # Additional state verification before UID commands
            current_state = getattr(imap, 'state', 'UNKNOWN')
            protocol_state = getattr(imap.protocol, 'state', 'UNKNOWN') if hasattr(imap, 'protocol') else 'UNKNOWN'
            logger.info(f"Pre-UID state check: client={current_state}, protocol={protocol_state}")
            
            # Diagnostic: Check aioimaplib version and internal state
            import aioimaplib
            logger.info(f"aioimaplib version: {getattr(aioimaplib, '__version__', 'unknown')}")
            
            # Search for messages - use regular SEARCH instead of UID SEARCH for better compatibility
            logger.info(f"Executing SEARCH '{search_query}' in folder '{effective_folder}'")
            status, search_data = await imap.search(search_query)
            logger.info(f"SEARCH status: {status}, data: {search_data}")
            
            if status != "OK" or not search_data or not search_data[0]:
                logger.warning(f"SEARCH failed or returned no results")
                return {"total": 0, "items": []}
            
            # Parse sequence numbers from regular SEARCH
            seq_list = search_data[0].decode().split()
            total = len(seq_list)
            
            if total == 0:
                return {"total": 0, "items": []}
            
            logger.info(f"Original sequence list: {seq_list[:10]}...")  # Log first 10 for debugging
            
            # Convert to integers and sort in descending order (newest first)
            # Higher sequence numbers are typically newer emails
            seq_numbers = [int(seq) for seq in seq_list]
            seq_numbers.sort(reverse=True)
            seq_list = [str(seq) for seq in seq_numbers]
            
            logger.info(f"Sorted sequence list: {seq_list[:10]}...")  # Log first 10 for debugging
            
            # Apply pagination (convert 1-based page to 0-based index)
            start_idx = (page - 1) * size
            end_idx = start_idx + size
            page_seqs = seq_list[start_idx:end_idx]
            
            if not page_seqs:
                return {"total": total, "items": []}
            
            # Fetch email data for the page using sequence numbers
            seq_range = ",".join(page_seqs)
            logger.info(f"Executing FETCH {seq_range} (UID BODY.PEEK[HEADER] FLAGS INTERNALDATE)")
            status, msg_data = await imap.fetch(seq_range, "(UID BODY.PEEK[HEADER] FLAGS INTERNALDATE)")
            logger.info(f"FETCH status: {status}, data length: {len(msg_data) if msg_data else 0}")
            
            if status != "OK" or not msg_data:
                logger.warning(f"FETCH failed or returned no data")
                return {"total": total, "items": []}
            
            items = []
            # Parse FETCH response - handle aioimaplib structure properly
            logger.info(f"Parsing {len(msg_data)} FETCH response items")
            
            # Debug: Log the first few items to understand structure
            for debug_i in range(min(3, len(msg_data))):
                debug_item = msg_data[debug_i]
                logger.info(f"FETCH item {debug_i}: type={type(debug_item)}, content={debug_item}")
            
            i = 0
            while i < len(msg_data):
                try:
                    item = msg_data[i]
                    
                    # Look for FETCH response line (bytes containing "FETCH")
                    if isinstance(item, bytes) and b"FETCH" in item:
                        response_line = item.decode()
                        logger.debug(f"Found FETCH response at {i}: {response_line[:100]}...")
                        
                        # Extract UID from response line
                        uid = None
                        if "UID " in response_line:
                            try:
                                uid_part = response_line.split("UID ")[1].split()[0]
                                uid = int(uid_part)
                            except (IndexError, ValueError):
                                logger.debug(f"Failed to extract UID from: {response_line}")
                                i += 1
                                continue
                        
                        if uid is None:
                            logger.debug(f"No UID found in response: {response_line}")
                            i += 1
                            continue
                        
                        # Look for header data in next item
                        header_bytes = b""
                        if i + 1 < len(msg_data):
                            next_item = msg_data[i + 1]
                            if isinstance(next_item, (bytes, bytearray)):
                                header_bytes = bytes(next_item)
                                logger.debug(f"Found header data for UID {uid}, length: {len(header_bytes)}")
                                i += 1  # Skip the header data item
                        
                        # Extract flags from response line
                        flags_bytes = b""
                        if "FLAGS " in response_line:
                            try:
                                flags_start = response_line.find("FLAGS (")
                                if flags_start != -1:
                                    flags_end = response_line.find(")", flags_start)
                                    if flags_end != -1:
                                        flags_str = response_line[flags_start:flags_end+1]
                                        flags_bytes = flags_str.encode()
                            except Exception:
                                pass
                        
                        # Parse the email data
                        if header_bytes:
                            email_data = parse_full_email(header_bytes, flags_bytes)
                            if email_data:
                                email_item = format_email_summary(email_data, uid, effective_folder)
                                items.append(email_item)
                                logger.debug(f"Successfully parsed email UID {uid}")
                            else:
                                logger.debug(f"Failed to parse email data for UID {uid}")
                        else:
                            logger.debug(f"No header data found for UID {uid}")
                    
                    i += 1
                
                except Exception as e:
                    logger.error(f"Error parsing email data at index {i}: {e}")
                    i += 1
                    continue
            
            logger.info(f"Successfully parsed {len(items)} emails from {len(msg_data)} response items")
            
            return {"total": total, "items": items}
                
    except Exception as e:
        logger.error(f"IMAP operation failed: {e}")
        return {"total": 0, "items": []}

async def get_email_imap(user: UserLike, folder: str, uid: int):
    """Fetch a single email detail from IMAP by UID in the folder.
    Accepts exact provider path or standardized hint; resolves if needed.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    async with get_imap_client(user) as imap:
        effective_folder = folder
        # For "inbox", try "INBOX" first (standard IMAP folder name)
        if folder.lower() == "inbox":
            effective_folder = "INBOX"
            status, _ = await imap.select(effective_folder)
        else:
            # For non-inbox folders, use folder discovery first
            status = "NO"
            key = _key_from_folder_hint(folder)
            if key:
                # Use async resolver with actual folder discovery
                resolved = await resolve_special_folder(user, key)
                if resolved:
                    effective_folder = resolved
                    status, _ = await imap.select(effective_folder)
            
            # If folder discovery didn't work, try the original folder name as fallback
            if status != "OK":
                effective_folder = folder
                status, _ = await imap.select(effective_folder)
        if status != "OK":
            logger.error(f"Failed to select folder {effective_folder} for email detail")
            return None
            
        # First verify the UID exists in this folder using regular SEARCH
        logger.info(f"Verifying UID {uid} exists in folder {effective_folder}")
        status, search_data = await imap.search(f"UID {uid}")
        logger.info(f"SEARCH UID status: {status}, data: {search_data}")
        
        if status != "OK" or not search_data or not search_data[0]:
            logger.warning(f"UID {uid} not found in folder {effective_folder}")
            return None
        
        # SEARCH returns sequence numbers, not UIDs, so we need to convert
        # If search found results, the UID exists
        seq_numbers = search_data[0].decode().split() if search_data[0] else []
        if not seq_numbers:
            logger.warning(f"UID {uid} not found in search results")
            return None
        
        logger.info(f"UID {uid} confirmed to exist, fetching email detail from folder {effective_folder}")
        status, msg_data = await imap.uid("FETCH", str(uid), "(BODY.PEEK[] FLAGS)")
        logger.info(f"UID FETCH status: {status}, data length: {len(msg_data) if msg_data else 0}")
        
        if status != "OK" or not msg_data:
            logger.warning(f"UID FETCH failed for UID {uid} - status: {status}, has_data: {msg_data is not None}")
            return None

        # Debug: Log the structure of msg_data
        logger.info(f"msg_data type: {type(msg_data)}, length: {len(msg_data) if msg_data else 0}")
        for i, item in enumerate(msg_data[:5]):  # Log first 5 items
            if isinstance(item, bytes):
                logger.info(f"Email detail item {i}: type=bytes, length={len(item)}, content={item[:300]}...")
            elif isinstance(item, tuple):
                logger.info(f"Email detail item {i}: type=tuple, length={len(item)}")
                for j, sub_item in enumerate(item):
                    if isinstance(sub_item, bytes):
                        logger.info(f"  sub_item {j}: type=bytes, length={len(sub_item)}, content={sub_item[:200]}...")
                    else:
                        logger.info(f"  sub_item {j}: type={type(sub_item)}, content={str(sub_item)[:200]}...")
            else:
                logger.info(f"Email detail item {i}: type={type(item)}, content={str(item)[:200]}...")

        raw_bytes = b""
        flags_blob = b""
        
        # Parse the IMAP FETCH response structure more robustly
        # The aioimaplib response format can vary, so we need to handle multiple patterns
        
        for i, item in enumerate(msg_data):
            if isinstance(item, bytes):
                item_str = item.decode(errors='ignore')
                
                # Check if this is the FETCH response line
                if "FETCH" in item_str and "BODY[]" in item_str:
                    logger.info(f"Found FETCH response line: {item_str[:200]}...")
                    
                    # Extract flags from the FETCH response line
                    if "FLAGS" in item_str and not flags_blob:
                        try:
                            flags_start = item_str.find("FLAGS (")
                            if flags_start != -1:
                                flags_end = item_str.find(")", flags_start)
                                if flags_end != -1:
                                    flags_str = item_str[flags_start:flags_end+1]
                                    flags_blob = flags_str.encode()
                                    logger.info(f"Extracted flags: {flags_str}")
                        except Exception:
                            pass
                    
                    # Look for the size indicator in BODY[] {size}
                    import re
                    size_match = re.search(r'BODY\[\]\s*\{(\d+)\}', item_str)
                    if size_match:
                        expected_size = int(size_match.group(1))
                        logger.info(f"Expected email size: {expected_size} bytes")
                        
                        # The email content should be in the next item(s)
                        remaining_items = msg_data[i+1:]
                        email_bytes = b""
                        
                        for next_item in remaining_items:
                            if isinstance(next_item, (bytes, bytearray)):
                                email_bytes += bytes(next_item)
                                if len(email_bytes) >= expected_size:
                                    break
                        
                        if email_bytes:
                            # Trim to expected size if we have extra data
                            raw_bytes = email_bytes[:expected_size]
                            logger.info(f"Extracted email content by size: {len(raw_bytes)} bytes")
                            break
                    
                    # Fallback: look for email headers in the same item
                    for header in ["Return-Path:", "Delivered-To:", "From:", "Subject:", "Date:"]:
                        if header in item_str:
                            # Find the start of the email content
                            header_pos = item_str.find(header)
                            # Look for the end of the FETCH response line
                            fetch_end = item_str.find("}\r\n")
                            if fetch_end == -1:
                                fetch_end = item_str.find("}\n")
                            if fetch_end != -1 and fetch_end < header_pos:
                                email_start_pos = fetch_end + 3 if "}\r\n" in item_str else fetch_end + 2
                            else:
                                line_start = item_str.rfind('\n', 0, header_pos)
                                email_start_pos = header_pos if line_start == -1 else line_start + 1
                            
                            email_content = item_str[email_start_pos:]
                            raw_bytes = email_content.encode('utf-8')
                            logger.info(f"Found email content embedded in FETCH response, extracted {len(raw_bytes)} bytes")
                            break
                
                # Check if this looks like pure email content (starts with email headers)
                elif any(item_str.strip().startswith(header) for header in ["Return-Path:", "Delivered-To:", "From:", "Subject:", "Date:", "Message-ID:"]):
                    raw_bytes = item
                    logger.info(f"Found pure email content item, length: {len(raw_bytes)}")
                    break
            
            elif isinstance(item, tuple) and len(item) >= 2:
                # Handle tuple format (response_line, email_data)
                response_line, email_data = item[0], item[1]
                
                if isinstance(response_line, bytes) and b"FETCH" in response_line:
                    logger.info(f"Found FETCH tuple response")
                    
                    # Extract flags from response line
                    if b"FLAGS" in response_line and not flags_blob:
                        flags_blob = response_line
                    
                    # Email data should be in the second element
                    if isinstance(email_data, (bytes, bytearray)):
                        raw_bytes = bytes(email_data)
                        logger.info(f"Extracted email data from tuple, length: {len(raw_bytes)}")
                        break
        
        # If we still don't have email data, try a more aggressive approach
        if not raw_bytes:
            logger.warning("Standard parsing failed, trying aggressive extraction")
            combined_data = b""
            
            # Combine all byte data
            for item in msg_data:
                if isinstance(item, bytes):
                    combined_data += item
                elif isinstance(item, tuple) and len(item) >= 2 and isinstance(item[1], (bytes, bytearray)):
                    combined_data += bytes(item[1])
            
            if combined_data:
                combined_str = combined_data.decode(errors='ignore')
                logger.info(f"Combined data length: {len(combined_data)} bytes")
                
                # Try to find email content after BODY[] pattern
                import re
                
                # Pattern 1: BODY[] {size}\r\n<email_content>
                body_pattern = re.compile(r'BODY\[\]\s*\{\d+\}\r?\n(.+)', re.DOTALL)
                match = body_pattern.search(combined_str)
                if match:
                    email_content = match.group(1)
                    raw_bytes = email_content.encode('utf-8')
                    logger.info(f"Extracted email using BODY[] pattern, length: {len(raw_bytes)}")
                else:
                    # Pattern 2: Look for first recognizable email header
                    for header in ["Return-Path:", "Delivered-To:", "From:", "Subject:", "Date:", "Message-ID:"]:
                        pos = combined_str.find(header)
                        if pos != -1:
                            # Find the start of the line containing this header
                            line_start = combined_str.rfind('\n', 0, pos)
                            email_start = pos if line_start == -1 else line_start + 1
                            
                            email_content = combined_str[email_start:]
                            raw_bytes = email_content.encode('utf-8')
                            logger.info(f"Extracted email using header '{header}', length: {len(raw_bytes)}")
                            break
                    
                    # Last resort: use all combined data
                    if not raw_bytes:
                        raw_bytes = combined_data
                        logger.warning("Using all combined data as fallback")
        
        logger.info(f"Extracted raw_bytes length: {len(raw_bytes)}, flags_blob length: {len(flags_blob)}")
        
        if not raw_bytes:
            logger.warning(f"No email data extracted for UID {uid}")
            return None
        
        email_data = parse_full_email(raw_bytes, flags_blob)
        if email_data:
            # Ensure proper field mapping for API compatibility
            result = {
                "uid": uid,
                "folder": effective_folder,
                "subject": email_data.get("subject"),
                "body": email_data.get("body"),
                "from": email_data.get("from"),  # Keep 'from' for API mapping
                "to": email_data.get("to", []),
                "cc": email_data.get("cc", []),
                "bcc": email_data.get("bcc", []),
                "is_read": email_data.get("is_read", False),
                "is_flagged": email_data.get("is_flagged", False),
                "timestamp": email_data.get("timestamp"),
                "has_attachments": email_data.get("has_attachments", False),
                "attachments": email_data.get("attachments", [])
            }
            logger.info(f"Successfully parsed email detail for UID {uid}: subject={result.get('subject')}, body_present={result.get('body') is not None}, body_length={len(result.get('body') or '')}")
            return result
        else:
            logger.warning(f"Failed to parse email data for UID {uid}")
            return None


async def set_read_flag_imap(user: UserLike, folder: str, uid: int, is_read: bool) -> bool:
    """Set or unset the IMAP \\Seen flag for read/unread functionality."""
    async with get_imap_client(user) as imap:
        effective_folder = folder
        # For "inbox", try "INBOX" first (standard IMAP folder name)
        if folder.lower() == "inbox":
            effective_folder = "INBOX"
            status, _ = await imap.select(effective_folder)
        else:
            # For non-inbox folders, use folder discovery first
            status = "NO"
            key = _key_from_folder_hint(folder)
            if key:
                # Use async resolver with actual folder discovery
                resolved = await resolve_special_folder(user, key)
                if resolved:
                    effective_folder = resolved
                    status, _ = await imap.select(effective_folder)
            
            # If folder discovery didn't work, try the original folder name as fallback
            if status != "OK":
                effective_folder = folder
                status, _ = await imap.select(effective_folder)
        if status != "OK":
            return False
        flag_cmd = "+FLAGS.SILENT" if is_read else "-FLAGS.SILENT"
        status, _ = await imap.uid("STORE", str(uid), flag_cmd, "(\\Seen)")
        return status == "OK"


async def set_flagged_status_imap(user: UserLike, folder: str, uid: int, is_flagged: bool) -> bool:
    """Set or unset the IMAP \\Flagged flag for star/important functionality."""
    async with get_imap_client(user) as imap:
        effective_folder = folder
        # For "inbox", try "INBOX" first (standard IMAP folder name)
        if folder.lower() == "inbox":
            effective_folder = "INBOX"
            status, _ = await imap.select(effective_folder)
        else:
            # For non-inbox folders, use folder discovery first
            status = "NO"
            key = _key_from_folder_hint(folder)
            if key:
                # Use async resolver with actual folder discovery
                resolved = await resolve_special_folder(user, key)
                if resolved:
                    effective_folder = resolved
                    status, _ = await imap.select(effective_folder)
            
            # If folder discovery didn't work, try the original folder name as fallback
            if status != "OK":
                effective_folder = folder
                status, _ = await imap.select(effective_folder)
        if status != "OK":
            return False
        flag_cmd = "+FLAGS.SILENT" if is_flagged else "-FLAGS.SILENT"
        status, _ = await imap.uid("STORE", str(uid), flag_cmd, "(\\Flagged)")
        return status == "OK"


async def move_email_imap(user: UserLike, src_folder: str, uid: int, target_folder: str) -> bool:
    """Move a message by UID from src_folder to target_folder.
    - Accepts exact folder paths or standardized hints for both source and target.
    - Resolves provider-specific paths dynamically and tries common aliases.
    """
    async with get_imap_client(user) as imap:
        # Resolve/select source folder first
        effective_src = src_folder
        # For "inbox", try "INBOX" first (standard IMAP folder name)
        if src_folder.lower() == "inbox":
            effective_src = "INBOX"
            status, _ = await imap.select(effective_src)
        else:
            # For non-inbox folders, use folder discovery first
            status = "NO"
            src_key = _key_from_folder_hint(src_folder)
            if src_key:
                # Use async resolver with actual folder discovery
                resolved_src = await resolve_special_folder(user, src_key)
                if resolved_src:
                    effective_src = resolved_src
                    status, _ = await imap.select(effective_src)
            
            # If folder discovery didn't work, try the original folder name as fallback
            if status != "OK":
                effective_src = src_folder
                status, _ = await imap.select(effective_src)
        if status != "OK":
            return False

        # Build candidate target folders
        tf = (target_folder or "").strip()
        target_key = _key_from_folder_hint(tf)
        candidates: list[str] = []
        if target_key:
            # Use async resolver with actual folder discovery
            resolved = await resolve_special_folder(user, target_key)
            if resolved:
                candidates.append(resolved)
            # Add common synonyms as fallbacks
            if target_key == "archive":
                candidates += ["[Gmail]/All Mail", "All Mail", "[Gmail]/Archive", "Archive", "INBOX.Archive", "INBOX.archive"]
            elif target_key == "trash":
                candidates += ["[Gmail]/Trash", "Trash", "Bin", "Deleted Items", "Deleted Messages", "INBOX.Trash", "INBOX.trash"]
            elif target_key == "spam":
                candidates += ["[Gmail]/Spam", "Spam", "Junk", "Junk Email", "Junk E-mail", "Bulk", "Bulk Mail", "INBOX.Spam", "INBOX.spam"]
            elif target_key == "sent":
                candidates += ["[Gmail]/Sent Mail", "Sent", "Sent Items", "INBOX.Sent", "INBOX.sent", "Sent Messages", "Sent Mail"]
            elif target_key == "drafts":
                candidates += ["[Gmail]/Drafts", "Drafts", "INBOX.Drafts", "INBOX.drafts"]
            elif target_key == "inbox":
                candidates += ["INBOX"]
        # Always also try the provided target literal as-is
        if tf:
            candidates.append(tf)

        # De-duplicate while preserving order
        seen = set()
        unique_candidates: list[str] = []
        for c in candidates:
            if c and c not in seen:
                seen.add(c)
                unique_candidates.append(c)

        # MOVE if supported, else COPY+DELETE
        has_move = False
        try:
            caps = getattr(imap, "capabilities", set()) or set()
            has_move = (b"MOVE" in caps) or ("MOVE" in caps)
        except Exception:
            has_move = False

        for cand in unique_candidates:
            mailbox_arg = f'"{cand}"'
            try:
                if has_move:
                    status, _ = await imap.uid("MOVE", str(uid), mailbox_arg)
                    if status == "OK":
                        return True
                status, _ = await imap.uid("COPY", str(uid), mailbox_arg)
                if status != "OK":
                    continue
                status, _ = await imap.uid("STORE", str(uid), "+FLAGS.SILENT", "(\\Deleted)")
                if status != "OK":
                    continue
                try:
                    await imap.expunge()
                except Exception:
                    pass
                return True
            except Exception:
                continue

        return False


async def download_attachment_imap(user: UserLike, folder: str, uid: int, filename: str) -> tuple[bytes, str, str] | None:
    """Return (content_bytes, content_type, safe_filename) for the attachment with matching filename by UID."""
    async with get_imap_client(user) as imap:
        effective_folder = folder
        # For "inbox", try "INBOX" first (standard IMAP folder name)
        if folder.lower() == "inbox":
            effective_folder = "INBOX"
            status, _ = await imap.select(effective_folder)
        else:
            # For non-inbox folders, use folder discovery first
            status = "NO"
            key = _key_from_folder_hint(folder)
            if key:
                # Use async resolver with actual folder discovery
                resolved = await resolve_special_folder(user, key)
                if resolved:
                    effective_folder = resolved
                    status, _ = await imap.select(effective_folder)
            
            # If folder discovery didn't work, try the original folder name as fallback
            if status != "OK":
                effective_folder = folder
                status, _ = await imap.select(effective_folder)
        if status != "OK":
            return None
        status, msg_data = await imap.uid("FETCH", str(uid), "(BODY.PEEK[])")
        if status != "OK" or not msg_data:
            return None
        raw_bytes = b""
        for part in msg_data:
            if isinstance(part, tuple):
                raw_bytes += part[1]
        msg = BytesParser(policy=policy.default).parsebytes(raw_bytes)
        return find_attachment_in_message(msg, filename)


async def append_draft_imap(
    user: UserLike,
    subject: Optional[str],
    body: Optional[str],
    to: List[str],
    cc: List[str],
    bcc: List[str],
    attachments: List[Tuple[str, Optional[str], bytes]],
) -> bool:
    """Create a draft message and append it to IMAP Drafts folder (exact name)."""
    from .email_parser import create_email_message
    
    msg = create_email_message(
        from_addr=user.email,
        to=to,
        cc=cc,
        bcc=bcc,
        subject=subject,
        body=body,
        attachments=attachments
    )

    async with get_imap_client(user) as imap:
        # Use async resolver with actual folder discovery
        drafts_folder = await resolve_special_folder(user, "drafts") or "Drafts"
        raw = msg.as_bytes().replace(b"\n", b"\r\n").replace(b"\r\r\n", b"\r\n")
        flags = r"(\\Draft)"
        timestamp = imaplib.Time2Internaldate(time.time())
        status, _ = await imap.append(drafts_folder, flags, timestamp, raw)
        if status != "OK":
            status, _ = await imap.append(drafts_folder, None, None, raw)
        return status == "OK"


def _make_imap(user: UserLike, timeout_seconds: int = None):
    """Create IMAP connection for validation purposes."""
    settings = get_settings()
    
    # Handle both encrypted (database mode) and plain text (stateless mode) passwords
    if hasattr(user, 'encrypted_password') and user.encrypted_password:
        try:
            password = decrypt_secret(user.encrypted_password)
        except Exception:
            # Fallback: treat as plain text
            password = user.encrypted_password
    else:
        # Direct password (stateless mode)
        password = getattr(user, 'password', '')
    
    timeout = timeout_seconds or settings.IMAP_TIMEOUT_SECONDS
    
    # Establish connection
    if settings.IMAP_USE_SSL:
        imap = imaplib.IMAP4_SSL(user.imap_host, user.imap_port, timeout=timeout)
    else:
        imap = imaplib.IMAP4(user.imap_host, user.imap_port)
        # Try STARTTLS if available
        try:
            imap.starttls()
        except Exception:
            pass  # Not all servers support STARTTLS
    
    # Authenticate
    try:
        imap.login(user.email, password)
    except imaplib.IMAP4.error as e:
        imap.logout()
        raise ValueError(f"IMAP authentication failed: {e}")
    except Exception as e:
        imap.logout()
        raise ValueError(f"IMAP connection failed: {e}")
    
    return imap
