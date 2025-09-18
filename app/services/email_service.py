"""
Email service module for ConnexxionEngine.
Main orchestrator that imports functionality from specialized modules.
"""
from typing import List, Optional, Tuple, Any, Protocol

# Import all functionality from specialized modules
from .folder_manager import list_folders, resolve_special_folder
from .attachment_handler import find_attachment_in_message
from .email_parser import parse_full_email, format_email_summary, create_email_message
from .imap_operations import (
    list_mailbox,
    get_email_imap,
    set_read_flag_imap,
    set_flagged_status_imap,
    move_email_imap,
    download_attachment_imap,
    append_draft_imap,
    _make_imap
)
from .smtp_operations import send_email, _make_smtp


class UserLike(Protocol):
    email: str
    encrypted_password: str
    smtp_host: str
    smtp_port: int
    imap_host: str
    imap_port: int


# Re-export all the main functions for backward compatibility
__all__ = [
    # Folder operations
    'list_folders',
    'resolve_special_folder',
    
    # Email operations
    'list_mailbox',
    'get_email_imap',
    'send_email',
    
    # Email actions
    'set_read_flag_imap',
    'set_flagged_status_imap',
    'move_email_imap',
    
    # Attachment operations
    'download_attachment_imap',
    'find_attachment_in_message',
    
    # Draft operations
    'append_draft_imap',
    
    # Email parsing
    'parse_full_email',
    'format_email_summary',
    'create_email_message',
    
    # Legacy SMTP helper
    '_make_smtp',
    
    # Connection validation helpers
    '_make_imap',
    
    # Protocol
    'UserLike'
]


# Convenience functions that combine multiple operations

async def compose_draft(
    user: UserLike,
    subject: Optional[str],
    body: Optional[str],
    to: List[str],
    cc: List[str] = None,
    bcc: List[str] = None,
    attachments: List[Tuple[str, Optional[str], bytes]] = None,
) -> bool:
    """Compose and save a draft email."""
    return await append_draft_imap(
        user=user,
        subject=subject,
        body=body,
        to=to,
        cc=cc or [],
        bcc=bcc or [],
        attachments=attachments or []
    )


async def archive_email(user: UserLike, folder: str, uid: int) -> bool:
    """Archive an email by moving it to the archive folder."""
    return await move_email_imap(user, folder, uid, "archive")


async def delete_email(user: UserLike, folder: str, uid: int) -> bool:
    """Delete an email by moving it to the trash folder."""
    return await move_email_imap(user, folder, uid, "trash")


async def unarchive_email(user: UserLike, folder: str, uid: int) -> bool:
    """Unarchive an email by moving it back to inbox."""
    return await move_email_imap(user, folder, uid, "inbox")


async def mark_as_read(user: UserLike, folder: str, uid: int) -> bool:
    """Mark an email as read."""
    return await set_read_flag_imap(user, folder, uid, True)


async def mark_as_unread(user: UserLike, folder: str, uid: int) -> bool:
    """Mark an email as unread."""
    return await set_read_flag_imap(user, folder, uid, False)


async def star_email(user: UserLike, folder: str, uid: int) -> bool:
    """Star/flag an email as important."""
    return await set_flagged_status_imap(user, folder, uid, True)


async def unstar_email(user: UserLike, folder: str, uid: int) -> bool:
    """Remove star/flag from an email."""
    return await set_flagged_status_imap(user, folder, uid, False)
