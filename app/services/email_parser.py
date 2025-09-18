"""
Email parsing and formatting module.
Handles email content parsing, header processing, and message formatting.
"""
import time
from datetime import datetime
from email.message import EmailMessage
from email.header import decode_header, make_header
from email.parser import BytesParser
from email import policy
from email.utils import getaddresses, formataddr, formatdate, make_msgid, parsedate_to_datetime
from typing import List, Optional, Tuple, Any, Dict
from .attachment_handler import extract_attachments_from_message
from typing import Protocol


class UserLike(Protocol):
    email: str
    encrypted_password: str
    smtp_host: str
    smtp_port: int
    imap_host: str
    imap_port: int


def _parse_timestamp(date_str: str) -> Optional[datetime]:
    """Parse IMAP INTERNALDATE with robust fallbacks."""
    if not date_str:
        return None
    try:
        # Try parsedate_to_datetime first (handles RFC 2822 format)
        return parsedate_to_datetime(date_str)
    except Exception:
        try:
            # Fallback: manual parsing for IMAP INTERNALDATE format
            # Format: "17-Jul-1996 02:44:25 -0700"
            return datetime.strptime(date_str[:20], "%d-%b-%Y %H:%M:%S")
        except Exception:
            return None


def _infer_importance_from_headers(headers: dict) -> bool:
    """Infer importance from headers if not server-flagged."""
    x_priority = headers.get('X-Priority', '').strip()
    if x_priority in ['1', '2']:
        return True
    importance = headers.get('Importance', '').strip().lower()
    if importance == 'high':
        return True
    return False


def parse_email_headers(msg) -> Dict[str, Any]:
    """Parse email headers into a standardized format."""
    # Subject
    dh = decode_header(msg.get("Subject", ""))
    subject = str(make_header(dh)) if dh else None
    
    # From
    from_parsed = getaddresses([msg.get("From", "")])
    from_addr = formataddr(from_parsed[0]) if from_parsed else None
    
    # To
    to_parsed = getaddresses([msg.get("To", "")])
    to_addrs = [formataddr(t) for t in to_parsed] if to_parsed else []
    
    # CC
    cc_parsed = getaddresses([msg.get("Cc", "")])
    cc_addrs = [formataddr(t) for t in cc_parsed] if cc_parsed else []
    
    # BCC
    bcc_parsed = getaddresses([msg.get("Bcc", "")])
    bcc_addrs = [formataddr(t) for t in bcc_parsed] if bcc_parsed else []
    
    # Date
    date_str = msg.get("Date", "")
    timestamp = _parse_timestamp(date_str)
    
    # Message ID
    message_id = msg.get("Message-ID", "")
    
    return {
        "subject": subject,
        "from": from_addr,
        "to": to_addrs,
        "cc": cc_addrs,
        "bcc": bcc_addrs,
        "date": date_str,
        "timestamp": timestamp,
        "message_id": message_id,
        "headers": dict(msg.items())
    }


def parse_email_body(msg) -> Dict[str, Optional[str]]:
    """Parse email body content (text and HTML)."""
    import logging
    logger = logging.getLogger(__name__)
    
    text_body: Optional[str] = None
    html_body: Optional[str] = None
    
    logger.debug(f"Parsing email body - is_multipart: {msg.is_multipart()}")
    
    if msg.is_multipart():
        for part in msg.walk():
            disp = (part.get_content_disposition() or "").lower()
            ctype = part.get_content_type()
            
            logger.debug(f"Processing part: content_type={ctype}, disposition={disp}")
            
            if disp == "attachment":
                continue
            elif ctype == "text/plain" and text_body is None:
                try:
                    text_body = part.get_content()
                    logger.debug(f"Extracted text body: {len(text_body) if text_body else 0} chars")
                except Exception as e:
                    logger.debug(f"Failed to get text content: {e}")
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            text_body = payload.decode(errors="ignore")
                            logger.debug(f"Extracted text body from payload: {len(text_body)} chars")
                    except Exception as e2:
                        logger.debug(f"Failed to get text payload: {e2}")
            elif ctype == "text/html" and html_body is None:
                try:
                    html_body = part.get_content()
                    logger.debug(f"Extracted HTML body: {len(html_body) if html_body else 0} chars")
                except Exception as e:
                    logger.debug(f"Failed to get HTML content: {e}")
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            html_body = payload.decode(errors="ignore")
                            logger.debug(f"Extracted HTML body from payload: {len(html_body)} chars")
                    except Exception as e2:
                        logger.debug(f"Failed to get HTML payload: {e2}")
    else:
        # Single part message
        ctype = msg.get_content_type()
        logger.debug(f"Single part message: content_type={ctype}")
        
        if ctype == "text/plain":
            try:
                text_body = msg.get_content()
                logger.debug(f"Extracted single text body: {len(text_body) if text_body else 0} chars")
            except Exception as e:
                logger.debug(f"Failed to get single text content: {e}")
                try:
                    payload = msg.get_payload(decode=True)
                    if payload:
                        text_body = payload.decode(errors="ignore")
                        logger.debug(f"Extracted single text body from payload: {len(text_body)} chars")
                except Exception as e2:
                    logger.debug(f"Failed to get single text payload: {e2}")
        elif ctype == "text/html":
            try:
                html_body = msg.get_content()
                logger.debug(f"Extracted single HTML body: {len(html_body) if html_body else 0} chars")
            except Exception as e:
                logger.debug(f"Failed to get single HTML content: {e}")
                try:
                    payload = msg.get_payload(decode=True)
                    if payload:
                        html_body = payload.decode(errors="ignore")
                        logger.debug(f"Extracted single HTML body from payload: {len(html_body)} chars")
                except Exception as e2:
                    logger.debug(f"Failed to get single HTML payload: {e2}")
    
    # Prefer HTML body, fallback to text body
    body = html_body if html_body else text_body
    
    return {
        "body": body,
        "text_body": text_body,
        "html_body": html_body
    }


def parse_email_flags(flags_blob: bytes) -> Dict[str, bool]:
    """Parse IMAP flags from response."""
    flags_str = flags_blob.decode(errors="ignore").lower()
    
    return {
        "is_read": r"\seen" in flags_str,
        "is_flagged": r"\flagged" in flags_str,
        "is_draft": r"\draft" in flags_str,
        "is_answered": r"\answered" in flags_str,
        "is_deleted": r"\deleted" in flags_str
    }


def create_email_message(
    from_addr: str,
    to: List[str],
    cc: List[str],
    bcc: List[str],
    subject: Optional[str],
    body: Optional[str],
    attachments: List[Tuple[str, Optional[str], bytes]] = None
) -> EmailMessage:
    """Create a properly formatted email message."""
    msg = EmailMessage()
    msg["From"] = from_addr
    
    if to:
        msg["To"] = ", ".join(to)
    if cc:
        msg["Cc"] = ", ".join(cc)
    if bcc:
        msg["Bcc"] = ", ".join(bcc)
    
    msg["Subject"] = subject or ""
    
    if "Date" not in msg:
        msg["Date"] = formatdate(localtime=True)
    
    if "Message-ID" not in msg:
        msg["Message-ID"] = make_msgid()
    
    # Set body content
    body_content = body or ""
    if body_content and ("<" in body_content and ">" in body_content):
        msg.set_content(body_content, subtype="html")
    else:
        msg.set_content(body_content)
    
    # Add attachments if provided
    if attachments:
        from .attachment_handler import add_attachments_to_message
        add_attachments_to_message(msg, attachments)
    
    return msg


def parse_full_email(raw_bytes: bytes, flags_blob: bytes = b"") -> Dict[str, Any]:
    """Parse a complete email from raw bytes."""
    try:
        msg = BytesParser(policy=policy.default).parsebytes(raw_bytes)
    except Exception:
        return None
    
    # Parse headers
    headers = parse_email_headers(msg)
    
    # Parse body
    body = parse_email_body(msg)
    
    # Parse flags
    flags = parse_email_flags(flags_blob)
    
    # Extract attachments
    attachments = extract_attachments_from_message(msg)
    
    # Combine all data
    return {
        **headers,
        **body,
        **flags,
        "attachments": attachments,
        "has_attachments": len(attachments) > 0
    }


def format_email_summary(email_data: Dict[str, Any], uid: int, folder: str) -> Dict[str, Any]:
    """Format email data for list display."""
    return {
        "id": uid,  # Use UID as the ID for Pydantic validation
        "folder": folder,
        "subject": email_data.get("subject"),
        "from_address": email_data.get("from"),  # Match Pydantic field name
        "to_addresses": email_data.get("to", []),  # Match Pydantic field name
        "timestamp": email_data.get("timestamp"),
        "is_read": email_data.get("is_read", False),
        "is_flagged": email_data.get("is_flagged", False),
        "has_attachments": email_data.get("has_attachments", False)
    }
