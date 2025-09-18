"""
SMTP operations module for email service.
Handles SMTP-specific operations like sending emails.
"""
import ssl
import smtplib
from typing import List, Optional, Tuple, Any
from ..core.config import get_settings
from ..core.security import decrypt_secret
from ..core.connection_pool import get_smtp_client, get_imap_client
from .folder_manager import resolve_special_folder
from .email_parser import create_email_message
from .imap_operations import move_email_imap
from typing import Protocol


class UserLike(Protocol):
    email: str
    encrypted_password: str
    smtp_host: str
    smtp_port: int
    imap_host: str
    imap_port: int


async def send_email(
    user: UserLike,
    subject: Optional[str],
    body: Optional[str],
    to: List[str],
    cc: List[str],
    bcc: List[str],
    attachments: List[Tuple[str, Optional[str], bytes]],
    draft_id: Optional[int] = None,
) -> Any:
    """Send an email via SMTP with optional attachments."""
    # Build message
    msg = create_email_message(
        from_addr=user.email,
        to=to,
        cc=cc,
        bcc=bcc,
        subject=subject,
        body=body,
        attachments=attachments
    )

    # Send via SMTP using connection pool
    async with get_smtp_client(user) as smtp:
        await smtp.send_message(msg)
        
        # If successful, delete draft if provided
        if draft_id:
            await move_email_imap(user, "drafts", draft_id, "trash")
        
        return {"status": "sent", "message_id": msg.get("Message-ID")}


def _make_smtp(user: UserLike):
    """Create SMTP connection (legacy function for compatibility)."""
    settings = get_settings()
    context = ssl.create_default_context()
    
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
    
    # Establish connection
    if settings.SMTP_USE_SSL:
        server = smtplib.SMTP_SSL(
            user.smtp_host, 
            user.smtp_port, 
            context=context, 
            timeout=settings.SMTP_TIMEOUT_SECONDS
        )
    else:
        server = smtplib.SMTP(
            user.smtp_host, 
            user.smtp_port, 
            timeout=settings.SMTP_TIMEOUT_SECONDS
        )
        # Try STARTTLS if available
        try:
            server.starttls(context=context)
        except Exception:
            pass  # Not all servers support STARTTLS
    
    # Authenticate
    try:
        server.login(user.email, password)
    except smtplib.SMTPAuthenticationError as e:
        server.quit()
        raise ValueError(f"SMTP authentication failed: {e}")
    except Exception as e:
        server.quit()
        raise ValueError(f"SMTP connection failed: {e}")
    
    return server
