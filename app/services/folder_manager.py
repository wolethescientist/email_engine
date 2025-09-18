"""
Folder management module for email service.
Handles folder discovery, classification, and resolution.
"""
import ssl
from typing import Optional, List, Dict, Set, Tuple
from ..core.config import get_settings
from ..core.security import decrypt_secret
from ..core.connection_pool import get_imap_client
from typing import Protocol


class UserLike(Protocol):
    email: str
    encrypted_password: str
    smtp_host: str
    smtp_port: int
    imap_host: str
    imap_port: int


# Attribute mapping for folder classification (RFC 6154 / XLIST)
_ATTR_MAP = {
    r"\inbox": "inbox",
    r"\sent": "sent",
    r"\drafts": "drafts", 
    r"\trash": "trash",
    r"\junk": "spam",
    r"\spam": "spam",
    r"\archive": "archive",
    r"\all": "archive",
    r"\allmail": "archive",
    r"\flagged": "custom",
    r"\important": "custom",
}


def _decode_imap_bytes(b: bytes) -> str:
    try:
        return b.decode("utf-8")
    except Exception:
        return b.decode("latin-1", errors="ignore")


def _parse_list_line(line: bytes) -> tuple[set[str], str, str] | None:
    """Parse a single LIST/XLIST response line into (attrs, delim, name)."""
    if not line:
        return None
    try:
        line_str = _decode_imap_bytes(line)
        if not line_str.startswith("("):
            return None
        close_paren = line_str.find(")")
        if close_paren == -1:
            return None
        attrs_str = line_str[1:close_paren]
        attrs = {a.strip().lower() for a in attrs_str.split() if a.strip()}
        remainder = line_str[close_paren + 1:].strip()
        parts = remainder.split(None, 1)
        if len(parts) < 2:
            return None
        delim = parts[0].strip('"')
        name = parts[1].strip('"')
    except Exception:
        return None
    return attrs, delim, name


def _leaf_name(path: str, delim: str) -> str:
    # Use server-reported delimiter if sensible, else split on common ones
    if delim and delim != "NIL" and delim in path:
        leaf = path.split(delim)[-1]
    else:
        for d in [".", "/", "\\"]:
            if d in path:
                leaf = path.split(d)[-1]
                break
        else:
            leaf = path
    return leaf


def _classify_folder(name: str, attrs: set[str], delim: str) -> str:
    # Attribute-based detection first (RFC 6154 / XLIST)
    for a in attrs:
        t = _ATTR_MAP.get(a.lower())
        if t:
            return t
    # Name-based heuristics
    n = name.lower()
    # Handle INBOX prefix patterns
    folder_basename = n
    if n.startswith("inbox."):
        folder_basename = n[6:]  # Remove "inbox." prefix
    elif n.startswith("inbox/"):
        folder_basename = n[6:]  # Remove "inbox/" prefix
    
    if "inbox" in n:
        return "inbox"
    elif any(x in folder_basename for x in ["sent", "sent items", "sent messages", "sent mail"]):
        return "sent"
    elif "draft" in folder_basename:
        return "drafts"
    elif any(x in folder_basename for x in ["trash", "deleted", "bin"]):
        return "trash"
    elif any(x in folder_basename for x in ["spam", "junk", "bulk"]):
        return "spam"
    elif any(x in folder_basename for x in ["archive", "all mail"]):
        return "archive"
    return "custom"


async def _collect_provider_folders(user: UserLike) -> list[dict]:
    """Collect folders from provider using LIST command, parse and classify."""
    import logging
    logger = logging.getLogger(__name__)
    
    async with get_imap_client(user) as imap:
        folders: list[dict] = []
        # Use alternative LIST syntax that works
        try:
            logger.info("Using alternative LIST syntax")
            status, data = await imap.list('""', "*")
            logger.info(f"Alternative LIST status: {status}, data length: {len(data) if data else 0}")
        except Exception as e:
            logger.error(f"LIST command failed: {e}")
            status, data = "BAD", []
        
        if status == "OK" and data:
            for line in data:
                parsed = _parse_list_line(line)
                if parsed:
                    attrs, delim, name = parsed
                    ftype = _classify_folder(name, attrs, delim)
                    folders.append({"name": name, "type": ftype, "delim": delim})
                    logger.debug(f"Found folder via LIST: {name} (type: {ftype})")
        # Add display names
        for folder in folders:
            name = folder["name"]
            delim = folder.get("delim", "/")
            folder["display_name"] = _leaf_name(name, delim)
        return folders


async def list_folders(user: UserLike) -> list[dict]:
    """Return a list of folders with standardized type for frontend display."""
    folders = await _collect_provider_folders(user)
    # Prefer a single entry per special type with a nice display name, but keep customs too
    display_map = {
        "inbox": "Inbox",
        "sent": "Sent",
        "drafts": "Drafts",
        "spam": "Spam",
        "trash": "Trash",
        "archive": "Archive",
    }
    result: list[dict] = []
    seen_types = set()
    for folder in folders:
        ftype = folder["type"]
        if ftype in display_map and ftype not in seen_types:
            result.append({
                "name": folder["name"],
                "display_name": display_map[ftype],
                "type": ftype,
            })
            seen_types.add(ftype)
        elif ftype == "custom":
            result.append({
                "name": folder["name"],
                "display_name": folder["display_name"],
                "type": ftype,
            })
    return result


async def resolve_special_folder(user: UserLike, key: str) -> str | None:
    """Resolve a standardized key (inbox/sent/drafts/spam/trash/archive/junk) to the provider's actual folder path.
    Falls back to best heuristics if not found explicitly.
    """
    folders = await _collect_provider_folders(user)
    # First pass: exact type match
    for folder in folders:
        if folder["type"] == key:
            return folder["name"]
    # Second pass: heuristics for common names
    if key == "inbox":
        for folder in folders:
            if folder["name"].upper() == "INBOX":
                return folder["name"]
    elif key == "sent":
        candidates = ["Sent", "Sent Items", "Sent Messages", "Sent Mail", "[Gmail]/Sent Mail", "INBOX.Sent", "INBOX.sent", "INBOX/Sent"]
        for cand in candidates:
            for folder in folders:
                if folder["name"] == cand:
                    return folder["name"]
    elif key == "drafts":
        candidates = ["Drafts", "[Gmail]/Drafts", "INBOX.Drafts", "INBOX.drafts", "INBOX/Drafts"]
        for cand in candidates:
            for folder in folders:
                if folder["name"] == cand:
                    return folder["name"]
    elif key == "trash":
        candidates = ["Trash", "[Gmail]/Trash", "Deleted Items", "Deleted Messages", "Bin", "INBOX.Trash", "INBOX.trash", "INBOX/Trash"]
        for cand in candidates:
            for folder in folders:
                if folder["name"] == cand:
                    return folder["name"]
    elif key == "spam" or key == "junk":
        candidates = ["Spam", "[Gmail]/Spam", "Junk", "Junk Email", "Junk E-mail", "Bulk", "Bulk Mail", "INBOX.Spam", "INBOX.spam", "INBOX/Spam"]
        for cand in candidates:
            for folder in folders:
                if folder["name"] == cand:
                    return folder["name"]
    elif key == "archive":
        candidates = ["Archive", "[Gmail]/All Mail", "All Mail", "[Gmail]/Archive", "INBOX.Archive", "INBOX.archive", "INBOX/Archive"]
        for cand in candidates:
            for folder in folders:
                if folder["name"] == cand:
                    return folder["name"]
    return None


def resolve_special_folder_sync(user: UserLike, key: str) -> str | None:
    """Synchronous fallback that returns common folder names without IMAP lookup."""
    # Simple heuristics without IMAP connection
    if key == "inbox":
        return "INBOX"
    elif key == "sent":
        return "Sent"
    elif key == "drafts":
        return "Drafts"
    elif key == "trash":
        return "Trash"
    elif key == "spam" or key == "junk":
        return "Spam"
    elif key == "archive":
        return "Archive"
    return None


def _key_from_folder_hint(folder: str) -> str | None:
    f = (folder or "").strip().lower()
    if f in {"inbox", "sent", "sent items", "sent messages", "sent mail", "draft", "drafts", "spam", "junk", "junk email", "junk e-mail", "bulk", "bulk mail", "trash", "deleted items", "deleted messages", "bin", "archive", "all mail"}:
        if f in {"sent items", "sent messages", "sent mail"}: return "sent"
        if f in {"draft"}: return "drafts"
        if f in {"junk", "junk email", "junk e-mail", "bulk", "bulk mail"}: return "spam"
        if f in {"deleted items", "deleted messages", "bin"}: return "trash"
        if f in {"all mail"}: return "archive"
        return f
    return None
