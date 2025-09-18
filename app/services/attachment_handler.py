"""
Attachment handling module for email service.
Handles attachment processing, encoding, and content type detection.
"""
import base64
from typing import List, Tuple, Optional
from email.message import EmailMessage
from email.header import decode_header, make_header
from email.parser import BytesParser
from email import policy
from typing import Protocol


class UserLike(Protocol):
    email: str
    encrypted_password: str
    smtp_host: str
    smtp_port: int
    imap_host: str
    imap_port: int


def guess_content_type(filename: str) -> str:
    """Guess content type based on file extension."""
    ft = filename.lower()
    if ft.endswith(".pdf"):
        return "application/pdf"
    elif ft.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    elif ft.endswith(".png"):
        return "image/png"
    elif ft.endswith(".txt"):
        return "text/plain"
    elif ft.endswith(".doc"):
        return "application/msword"
    elif ft.endswith(".docx"):
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif ft.endswith(".xls"):
        return "application/vnd.ms-excel"
    elif ft.endswith(".xlsx"):
        return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif ft.endswith(".ppt"):
        return "application/vnd.ms-powerpoint"
    elif ft.endswith(".pptx"):
        return "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    elif ft.endswith(".zip"):
        return "application/zip"
    elif ft.endswith(".rar"):
        return "application/x-rar-compressed"
    elif ft.endswith(".7z"):
        return "application/x-7z-compressed"
    elif ft.endswith(".mp3"):
        return "audio/mpeg"
    elif ft.endswith(".wav"):
        return "audio/wav"
    elif ft.endswith(".mp4"):
        return "video/mp4"
    elif ft.endswith(".avi"):
        return "video/x-msvideo"
    elif ft.endswith(".mov"):
        return "video/quicktime"
    else:
        return "application/octet-stream"


def add_attachments_to_message(msg: EmailMessage, attachments: List[Tuple[str, Optional[str], bytes]]) -> None:
    """Add attachments to an email message."""
    for filename, content_type, content in attachments:
        if not content_type or "/" not in content_type:
            content_type = guess_content_type(filename)
        
        maintype, subtype = content_type.split("/", 1)
        msg.add_attachment(content, maintype=maintype, subtype=subtype, filename=filename)


def extract_attachments_from_message(msg) -> List[str]:
    """Extract attachment filenames from an email message."""
    attachments: List[str] = []
    
    if msg.is_multipart():
        for part in msg.walk():
            disp = (part.get_content_disposition() or "").lower()
            if disp == "attachment":
                filename = part.get_filename()
                if filename:
                    try:
                        filename = str(make_header(decode_header(filename)))
                    except Exception:
                        pass
                    attachments.append(filename)
    else:
        # Single part message might have attachment-like content
        disp = (msg.get_content_disposition() or "").lower()
        if disp == "attachment":
            filename = msg.get_filename()
            if filename:
                try:
                    filename = str(make_header(decode_header(filename)))
                except Exception:
                    pass
                attachments.append(filename)
    
    return attachments


def find_attachment_in_message(msg, target_filename: str) -> Tuple[bytes, str, str] | None:
    """Find and extract a specific attachment from an email message.
    
    Returns:
        Tuple of (content_bytes, content_type, safe_filename) or None if not found
    """
    target_name = target_filename.strip()
    
    for part in msg.walk():
        disp = (part.get_content_disposition() or "").lower()
        if disp != "attachment":
            continue
            
        part_name = part.get_filename() or ""
        try:
            part_name = str(make_header(decode_header(part_name)))
        except Exception:
            pass
            
        if part_name == target_name:
            content = part.get_payload(decode=True) or b""
            ctype = part.get_content_type() or "application/octet-stream"
            return content, ctype, part_name
    
    return None


def decode_attachment_content(content: str, encoding: str = "base64") -> bytes:
    """Decode attachment content from various encodings."""
    try:
        if encoding.lower() == "base64":
            return base64.b64decode(content)
        elif encoding.lower() == "quoted-printable":
            import quopri
            return quopri.decodestring(content.encode())
        else:
            return content.encode()
    except Exception:
        return content.encode() if isinstance(content, str) else content


def encode_attachment_content(content: bytes, encoding: str = "base64") -> str:
    """Encode attachment content to various encodings."""
    try:
        if encoding.lower() == "base64":
            return base64.b64encode(content).decode()
        elif encoding.lower() == "quoted-printable":
            import quopri
            return quopri.encodestring(content).decode()
        else:
            return content.decode() if isinstance(content, bytes) else content
    except Exception:
        return str(content)


def validate_attachment_size(content: bytes, max_size_mb: int = 25) -> bool:
    """Validate attachment size against limits."""
    max_size_bytes = max_size_mb * 1024 * 1024
    return len(content) <= max_size_bytes


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage/transmission."""
    import re
    # Remove or replace dangerous characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip(' .')
    # Ensure it's not empty
    if not sanitized:
        sanitized = "attachment"
    return sanitized
