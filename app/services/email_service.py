import json
import imaplib
import smtplib
import ssl
import time
from email.message import EmailMessage
from email.header import decode_header, make_header
from email.parser import BytesParser
from email import policy
from email.utils import getaddresses, formataddr, formatdate, make_msgid
from typing import List, Optional, Tuple, Any



from ..core.config import get_settings
from ..core.security import decrypt_secret

from typing import Protocol

class UserLike(Protocol):
    email: str
    encrypted_password: str
    smtp_host: str
    smtp_port: int
    imap_host: str
    imap_port: int


# SMTP/IMAP helpers

def _make_smtp(user: UserLike):
    settings = get_settings()
    context = ssl.create_default_context()
    # Establish connection
    if settings.SMTP_USE_SSL:
        server = smtplib.SMTP_SSL(
            host=user.smtp_host,
            port=user.smtp_port,
            timeout=settings.SMTP_TIMEOUT_SECONDS,
            context=context,
        )
        server.ehlo()
    else:
        server = smtplib.SMTP(
            host=user.smtp_host,
            port=user.smtp_port,
            timeout=settings.SMTP_TIMEOUT_SECONDS,
        )
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
    # Authenticate (XOAUTH2 if token provided, else password)
    if getattr(user, "access_token", None):
        import base64
        auth_str = f"user={user.email}\x01auth=Bearer {user.access_token}\x01\x01"
        b64 = base64.b64encode(auth_str.encode()).decode()
        code, resp = server.docmd("AUTH", "XOAUTH2 " + b64)
        if code != 235:
            try:
                server.quit()
            except Exception:
                pass
            raise smtplib.SMTPAuthenticationError(code, resp)
    elif getattr(user, "password", None):
        server.login(user.email, user.password)  # type: ignore[arg-type]
    else:
        try:
            server.quit()
        except Exception:
            pass
        raise smtplib.SMTPAuthenticationError(535, b"No credentials provided")
    return server


def _make_imap(user: UserLike, timeout_seconds: Optional[int] = None):
    settings = get_settings()
    
    # Handle both encrypted (database mode) and plain text (stateless mode) passwords
    if hasattr(user, 'password') and user.password:
        # Stateless mode: password is already plain text
        password = user.password
    elif hasattr(user, 'encrypted_password') and user.encrypted_password:
        # Database mode: password is encrypted and needs decryption
        password = decrypt_secret(user.encrypted_password)
    else:
        raise ValueError("No password provided for IMAP authentication")
    
    timeout = timeout_seconds or settings.IMAP_TIMEOUT_SECONDS

    try:
        if settings.IMAP_USE_SSL:
            imap = imaplib.IMAP4_SSL(host=user.imap_host, port=user.imap_port, timeout=timeout)
        else:
            imap = imaplib.IMAP4(host=user.imap_host, port=user.imap_port, timeout=timeout)
            imap.starttls(ssl_context=ssl.create_default_context())

        # Handle OAuth2 authentication if access_token is provided
        if hasattr(user, 'access_token') and user.access_token:
            import base64
            auth_str = f"user={user.email}\x01auth=Bearer {user.access_token}\x01\x01".encode("utf-8")
            imap.authenticate("XOAUTH2", lambda x: auth_str)
        else:
            imap.login(user.email, password)
        return imap
    except imaplib.IMAP4.error as e:
        raise ValueError(f"IMAP authentication failed: {e}")
    except Exception as e:
        raise ValueError(f"IMAP connection failed: {e}")


# Mailbox discovery and normalization
# - Dynamically list provider folders
# - Classify special-use folders (Inbox, Sent, Drafts, Spam/Junk, Trash, Archive)
# - Resolve standardized keys to actual provider paths
import re

_STANDARD_TYPES = {
    "inbox", "sent", "drafts", "spam", "trash", "archive",
}
# Common synonyms used by providers/clients
_SYNONYMS = {
    "sent": {"sent", "sent items", "sent mail", "sent messages"},
    "drafts": {"draft", "drafts"},
    "spam": {"spam", "junk", "junk e-mail", "junk email", "bulk", "bulk mail"},
    "trash": {"trash", "deleted items", "deleted messages", "bin"},
    "archive": {"archive", "all mail", "archives"},
}
# Map IMAP special-use attributes to standard types
_ATTR_MAP = {
    "\\inbox": "inbox",
    "\\sent": "sent",
    "\\drafts": "drafts",
    "\\junk": "spam",
    "\\spam": "spam",
    "\\trash": "trash",
    "\\archive": "archive",
    "\\all": "archive",
    "\\allmail": "archive",
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
    s = _decode_imap_bytes(line).strip()
    # Typical format: (\HasNoChildren \Sent) "/" "[Gmail]/Sent Mail"
    m = re.match(r"^\(([^)]*)\)\s+\"([^\"]+)\"\s+(.*)$", s)
    if not m:
        # Some servers may omit quotes around delimiter/name; try a looser parse
        # Fallback: try to find the last quoted string as name
        parts = s.split(" ")
        # Best-effort: name is last token, strip quotes
        name = parts[-1].strip()
        if name.startswith('"') and name.endswith('"'):
            name = name[1:-1]
        return set(), "/", name
    attrs_raw, delim, name = m.groups()
    name = name.strip()
    if name.startswith('"') and name.endswith('"'):
        name = name[1:-1]
    attrs = set(a.strip().lower() for a in attrs_raw.split() if a.strip())
    return attrs, delim, name


def _leaf_name(path: str, delim: str) -> str:
    # Use server-reported delimiter if sensible, else split on common ones
    if delim and delim != "NIL" and delim in path:
        leaf = path.split(delim)[-1]
    else:
        # Try common
        leaf = path.split("/")[-1].split(".")[-1]
    # For Gmail folders like [Gmail]/Spam, leaf is already the last component
    return leaf


def _classify_folder(name: str, attrs: set[str], delim: str) -> str:
    # Attribute-based detection first (RFC 6154 / XLIST)
    for a in attrs:
        t = _ATTR_MAP.get(a.lower())
        if t:
            # Inbox attribute can be applied to INBOX only
            return t
    # Fallback by name heuristics
    leaf = _leaf_name(name, delim).lower()
    base = leaf.strip()
    if base == "inbox":
        return "inbox"
    for std, synonyms in _SYNONYMS.items():
        if base in synonyms:
            return std
    return "custom"


def _collect_provider_folders(user: UserLike) -> list[dict]:
    """Collect folders from provider using LIST (and XLIST best-effort), parse and classify."""
    imap = _make_imap(user, timeout_seconds=30)
    try:
        folders: list[dict] = []
        # Prefer LIST; many servers include special-use attributes
        typ, data = imap.list()
        lines = data or []
        # Try XLIST legacy for Gmail if LIST had nothing
        if not lines:
            try:
                # Send XLIST command (not part of imaplib API, but works with _simple_command)
                typ2, data2 = imap._simple_command("XLIST", '""', '"*"')  # type: ignore[attr-defined]
                typ2, lines2 = imap._untagged_response(typ2, data2, "XLIST")  # type: ignore[attr-defined]
                lines = lines2 or []
            except Exception:
                pass
        for line in lines:
            parsed = _parse_list_line(line)
            if not parsed:
                continue
            attrs, delim, name = parsed
            ftype = _classify_folder(name, attrs, delim)
            folders.append({
                "path": name,            # exact IMAP mailbox name for SELECT/UID
                "attrs": sorted(list(attrs)),
                "delimiter": delim,
                "leaf": _leaf_name(name, delim),
                "type": ftype,
            })
        return folders
    finally:
        try:
            imap.logout()
        except Exception:
            pass


def list_folders(user: UserLike) -> list[dict]:
    """Return a list of folders with standardized type for frontend display."""
    folders = _collect_provider_folders(user)
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
    for f in folders:
        ftype = f["type"]
        display = display_map.get(ftype, f["leaf"]) if ftype != "custom" else f["leaf"]
        result.append({
            "path": f["path"],
            "type": ftype,
            "label": display,
            "leaf": f["leaf"],
            "attrs": f["attrs"],
        })
    return result


def resolve_special_folder(user: UserLike, key: str) -> str | None:
    """Resolve a standardized key (inbox/sent/drafts/spam/trash/archive/junk) to the provider's actual folder path.
    Falls back to best heuristics if not found explicitly.
    """
    if not key:
        return None
    k = key.strip().lower()
    if k == "junk":
        k = "spam"
    if k not in _STANDARD_TYPES:
        return None

    folders = _collect_provider_folders(user)
    # Prefer folders with matching type (attribute-based)
    typed = [f for f in folders if f["type"] == k]
    if typed:
        # If multiple, prefer ones with explicit special-use attr (not just heuristic leaf match)
        def has_special_attr(f: dict) -> bool:
            attrs = set(f.get("attrs") or [])
            target_attrs = {a for a, t in _ATTR_MAP.items() if t == k}
            return any(a in attrs for a in target_attrs)
        typed.sort(key=lambda f: (not has_special_attr(f), len(f["path"])) )
        return typed[0]["path"]

    # Heuristic fallback: search by common names across all paths
    candidates_by_key: dict[str, list[str]] = {
        "inbox": ["INBOX"],
        "sent": [
            "Sent", "INBOX.Sent", "INBOX.sent", "Sent Items", "Sent Mail", "Sent Messages", "[Gmail]/Sent Mail",
        ],
        "drafts": ["Drafts", "INBOX.Drafts", "INBOX.drafts", "[Gmail]/Drafts"],
        "spam": [
            "Spam", "INBOX.Spam", "INBOX.spam", "Junk", "Junk E-mail", "Junk Email", "Bulk", "Bulk Mail", "[Gmail]/Spam",
        ],
        "trash": [
            "Trash", "INBOX.Trash", "INBOX.trash", "Deleted Items", "Deleted Messages", "Bin", "[Gmail]/Trash",
        ],
        "archive": [
            "Archive", "INBOX.Archive", "INBOX.archive", "All Mail", "[Gmail]/All Mail",
        ],
    }
    paths_lower = {f["path"].lower(): f["path"] for f in folders}
    for cand in candidates_by_key.get(k, []):
        if cand.lower() in paths_lower:
            return paths_lower[cand.lower()]

    # Last resort: pick a folder whose leaf matches a synonym
    for f in folders:
        leaf = f["leaf"].lower()
        if k == "inbox" and leaf == "inbox":
            return f["path"]
        if leaf in _SYNONYMS.get(k, set()):
            return f["path"]

    # Hard fallback
    defaults = {
        "inbox": "INBOX",
        "sent": "Sent",
        "drafts": "Drafts",
        "spam": "Spam",
        "trash": "Trash",
        "archive": "Archive",
    }
    return defaults.get(k)


# Address helpers

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
# DB-based draft persistence removed; drafts are appended directly to IMAP.


# Send email

def send_email(
    db: Any | None,  # kept for API compatibility; unused
    user: UserLike,
    subject: Optional[str],
    body: Optional[str],
    to: List[str],
    cc: List[str],
    bcc: List[str],
    attachments: List[Tuple[str, Optional[str], bytes]],
    draft_id: Optional[int] = None,
) -> Any:
    # Build message
    msg = EmailMessage()
    msg["From"] = user.email
    msg["To"] = ", ".join(to)
    if cc:
        msg["Cc"] = ", ".join(cc)
    msg["Subject"] = subject or ""
    if "Date" not in msg:
        msg["Date"] = formatdate(localtime=True)
    msg.set_content(body or "")

    # Attachments
    for filename, content_type, content in attachments:
        if not content_type or "/" not in content_type:
            # Minimal guessing for content type
            ft = filename.lower()
            if ft.endswith(".pdf"):
                content_type = "application/pdf"
            elif ft.endswith((".jpg", ".jpeg")):
                content_type = "image/jpeg"
            elif ft.endswith(".png"):
                content_type = "image/png"
            elif ft.endswith(".txt"):
                content_type = "text/plain"
            elif ft.endswith(".doc"):
                content_type = "application/msword"
            elif ft.endswith(".docx"):
                content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            else:
                content_type = "application/octet-stream"
        maintype, subtype = content_type.split("/", 1)
        msg.add_attachment(content, maintype=maintype, subtype=subtype, filename=filename)

    # SMTP send
    server = _make_smtp(user)
    try:
        recipients = list({*to, *cc, *bcc})
        server.send_message(msg, from_addr=user.email, to_addrs=recipients)
    finally:
        try:
            server.quit()
        except Exception:
            pass

    # Best-effort: append to provider's Sent folder (resolved dynamically)
    try:
        imap = _make_imap(user, timeout_seconds=60)
        try:
            sent_folder = resolve_special_folder(user, "sent") or "Sent"
            raw = msg.as_bytes().replace(b"\n", b"\r\n").replace(b"\r\r\n", b"\r\n")
            flags = r"(\Seen)"
            timestamp = imaplib.Time2Internaldate(time.time())
            status, _ = imap.append(sent_folder, flags, timestamp, raw)
            if status != "OK":
                # Minimal fallback: try minimal append once
                imap.append(sent_folder, None, None, raw)
        finally:
            try:
                imap.close()
            except Exception:
                pass
            try:
                imap.logout()
            except Exception:
                pass
    except Exception:
        # Ignore append errors
        pass

    # Do not persist to DB. Return a minimal structure for API response compatibility.
    return type('SentStub', (), {
        'id': None,
        'folder': 'Sent',
        'subject': subject,
        'body': body,
        'from_address': user.email,
        'to_addresses': _serialize_addresses(to),
        'cc_addresses': _serialize_addresses(cc),
        'bcc_addresses': _serialize_addresses(bcc),
        'is_read': True,
        'attachments': [],
    })()


# Mailbox listing via IMAP (no caching for real-time data)

def _key_from_folder_hint(folder: str) -> str | None:
    f = (folder or "").strip().lower()
    if f in {"inbox", "sent", "sent items", "sent messages", "sent mail", "draft", "drafts", "spam", "junk", "junk email", "junk e-mail", "bulk", "bulk mail", "trash", "deleted items", "deleted messages", "bin", "archive", "all mail"}:
        if f in {"sent items", "sent messages", "sent mail"}: return "sent"
        if f in {"draft", "drafts"}: return "drafts"
        if f in {"junk", "junk email", "junk e-mail", "bulk", "bulk mail"}: return "spam"
        if f in {"deleted items", "deleted messages", "bin", "trash"}: return "trash"
        if f in {"all mail", "archive"}: return "archive"
        return f
    return None


def list_mailbox(user: UserLike, folder: str, page: int, size: int):
    """Return (total, items) for a mailbox using IMAP.
    - Accepts either exact provider path or a standardized hint (e.g., "inbox", "sent").
    - If direct select fails, resolves to provider-specific path via discovery.
    """
    timeout_seconds = 15
    imap = _make_imap(user, timeout_seconds=timeout_seconds)
    try:
        effective_folder = folder
        status, _ = imap.select(effective_folder, readonly=True)
        if status != "OK":
            # Try resolve using standardized key if possible
            key = _key_from_folder_hint(folder)
            if key:
                resolved = resolve_special_folder(user, key)
                if resolved:
                    effective_folder = resolved
                    status, _ = imap.select(effective_folder, readonly=True)
        if status != "OK":
            return {"total": 0, "items": []}

        # Use UIDs consistently
        status, data = imap.uid("SEARCH", None, "ALL")
        if status != "OK" or not data or not data[0]:
            return {"total": 0, "items": []}

        all_uids = data[0].split()
        total = len(all_uids)

        # Sort by UID descending (newest first)
        try:
            all_uids.sort(key=lambda x: int(x), reverse=True)
        except Exception:
            all_uids = list(reversed(all_uids))

        # Page
        start = (page - 1) * size
        end = start + size
        page_uids = all_uids[start:end]

        items = []
        for uid in page_uids:
            try:
                uid_s = uid.decode() if isinstance(uid, (bytes, bytearray)) else str(uid)
                status, msg_data = imap.uid("FETCH", uid_s, "(BODY.PEEK[HEADER] FLAGS)")
                if status != "OK" or not msg_data:
                    continue

                raw_bytes = b""
                flags_blob = b""
                for part in msg_data:
                    if isinstance(part, tuple):
                        # part[0] often contains FETCH metadata including FLAGS; part[1] is the header bytes
                        try:
                            flags_blob += part[0] or b""
                        except Exception:
                            pass
                        raw_bytes += part[1]
                flags_text = (flags_blob or b"").decode(errors="ignore")
                is_read = "\\Seen" in flags_text

                # Parse headers
                try:
                    msg = BytesParser(policy=policy.default).parsebytes(raw_bytes)
                    dh = decode_header(msg.get("Subject", ""))
                    subject = str(make_header(dh)) if dh else None
                    from_parsed = getaddresses([msg.get("From", "")])
                    from_addr = formataddr(from_parsed[0]) if from_parsed else None
                    to_parsed = getaddresses([msg.get("To", "")])
                    to_addrs = [formataddr(t) for t in to_parsed] if to_parsed else []
                except Exception:
                    header_text = raw_bytes.decode(errors="ignore")
                    subject = header_text.split("\nSubject:", 1)[-1].split("\n", 1)[0].strip() if "Subject:" in header_text else None
                    from_addr = header_text.split("\nFrom:", 1)[-1].split("\n", 1)[0].strip() if "From:" in header_text else None
                    to_addrs = [p.strip() for p in (header_text.split("\nTo:", 1)[-1].split("\n", 1)[0] if "To:" in header_text else "").split(",") if p.strip()]

                try:
                    item_id = int(uid)
                except Exception:
                    item_id = int.from_bytes(uid, "big")

                items.append(
                    {
                        "id": item_id,  # UID
                        "folder": effective_folder,
                        "subject": subject,
                        "from_address": from_addr,
                        "to_addresses": to_addrs,
                        "is_read": is_read,
                    }
                )
            except Exception:
                continue

        return {"total": total, "items": items}
    finally:
        try:
            imap.close()
        except Exception:
            pass
        try:
            imap.logout()
        except Exception:
            pass


def get_email_imap(user: UserLike, folder: str, uid: int):
    """Fetch a single email detail from IMAP by UID in the folder.
    Accepts exact provider path or standardized hint; resolves if needed.
    """
    imap = _make_imap(user)
    try:
        effective_folder = folder
        status, _ = imap.select(effective_folder, readonly=True)
        if status != "OK":
            key = _key_from_folder_hint(folder)
            if key:
                resolved = resolve_special_folder(user, key)
                if resolved:
                    effective_folder = resolved
                    status, _ = imap.select(effective_folder, readonly=True)
        if status != "OK":
            return None
        status, msg_data = imap.uid("FETCH", str(uid), "(BODY.PEEK[] FLAGS)")
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

        # Headers
        dh = decode_header(msg.get("Subject", ""))
        subject = str(make_header(dh)) if dh else None
        from_parsed = getaddresses([msg.get("From", "")])
        from_addr = formataddr(from_parsed[0]) if from_parsed else None
        to_parsed = getaddresses([msg.get("To", "")])
        to_addrs = [formataddr(t) for t in to_parsed] if to_parsed else []
        cc_parsed = getaddresses([msg.get("Cc", "")])
        cc_addrs = [formataddr(t) for t in cc_parsed] if cc_parsed else []
        bcc_parsed = getaddresses([msg.get("Bcc", "")])
        bcc_addrs = [formataddr(t) for t in bcc_parsed] if bcc_parsed else []

        # Body & attachments
        text_body: Optional[str] = None
        html_body: Optional[str] = None
        attachments: List[str] = []
        if msg.is_multipart():
            for part in msg.walk():
                disp = (part.get_content_disposition() or "").lower()
                ctype = part.get_content_type()
                if disp == "attachment":
                    filename = part.get_filename()
                    if filename:
                        try:
                            filename = str(make_header(decode_header(filename)))
                        except Exception:
                            pass
                        attachments.append(filename)
                elif ctype == "text/plain" and text_body is None:
                    try:
                        text_body = part.get_content()
                    except Exception:
                        try:
                            text_body = part.get_payload(decode=True).decode(errors="ignore")
                        except Exception:
                            pass
                elif ctype == "text/html" and html_body is None:
                    try:
                        html_body = part.get_content()
                    except Exception:
                        try:
                            html_body = part.get_payload(decode=True).decode(errors="ignore")
                        except Exception:
                            pass
        else:
            ctype = msg.get_content_type()
            if ctype == "text/plain":
                try:
                    text_body = msg.get_content()
                except Exception:
                    try:
                        text_body = msg.get_payload(decode=True).decode(errors="ignore")
                    except Exception:
                        pass
            else:
                try:
                    html_body = msg.get_content()
                except Exception:
                    try:
                        html_body = msg.get_payload(decode=True).decode(errors="ignore")
                    except Exception:
                        pass

        body = text_body or html_body or ""

        flags_text = (flags_blob or b"").decode(errors="ignore")
        is_read = "\\Seen" in flags_text

        return {
            "id": uid,  # UID
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
        try:
            imap.close()
        except Exception:
            pass
        try:
            imap.logout()
        except Exception:
            pass


# IMAP actions using exact folder names (UID-based)

def set_read_flag_imap(user: UserLike, folder: str, uid: int, is_read: bool) -> bool:
    imap = _make_imap(user)
    try:
        effective_folder = folder
        status, _ = imap.select(effective_folder, readonly=False)
        if status != "OK":
            key = _key_from_folder_hint(folder)
            if key:
                resolved = resolve_special_folder(user, key)
                if resolved:
                    effective_folder = resolved
                    status, _ = imap.select(effective_folder, readonly=False)
        if status != "OK":
            return False
        flag_cmd = "+FLAGS.SILENT" if is_read else "-FLAGS.SILENT"
        status, _ = imap.uid("STORE", str(uid), flag_cmd, "(\\Seen)")
        return status == "OK"
    finally:
        try:
            imap.close()
        except Exception:
            pass
        try:
            imap.logout()
        except Exception:
            pass


def move_email_imap(user: UserLike, src_folder: str, uid: int, target_folder: str) -> bool:
    """Move a message by UID from src_folder to target_folder.
    - Accepts exact folder paths or standardized hints for both source and target.
    - Resolves provider-specific paths dynamically and tries common aliases.
    """
    imap = _make_imap(user)
    try:
        # Resolve/select source folder first
        effective_src = src_folder
        status, _ = imap.select(effective_src, readonly=False)
        if status != "OK":
            src_key = _key_from_folder_hint(src_folder)
            if src_key:
                resolved_src = resolve_special_folder(user, src_key)
                if resolved_src:
                    effective_src = resolved_src
                    status, _ = imap.select(effective_src, readonly=False)
        if status != "OK":
            return False

        # Build candidate target folders
        tf = (target_folder or "").strip()
        target_key = _key_from_folder_hint(tf)
        candidates: list[str] = []
        if target_key:
            resolved = resolve_special_folder(user, target_key)
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
                    status, _ = imap.uid("MOVE", str(uid), mailbox_arg)
                    if status == "OK":
                        return True
                status, _ = imap.uid("COPY", str(uid), mailbox_arg)
                if status != "OK":
                    continue
                status, _ = imap.uid("STORE", str(uid), "+FLAGS.SILENT", "(\\Deleted)")
                if status != "OK":
                    continue
                try:
                    imap.expunge()
                except Exception:
                    try:
                        imap.close()
                        imap.select(effective_src, readonly=False)
                        imap.expunge()
                    except Exception:
                        pass
                return True
            except Exception:
                continue

        return False
    finally:
        try:
            imap.close()
        except Exception:
            pass
        try:
            imap.logout()
        except Exception:
            pass


def download_attachment_imap(user: UserLike, folder: str, uid: int, filename: str) -> tuple[bytes, str, str] | None:
    """Return (content_bytes, content_type, safe_filename) for the attachment with matching filename by UID."""
    imap = _make_imap(user)
    try:
        effective_folder = folder
        status, _ = imap.select(effective_folder, readonly=True)
        if status != "OK":
            key = _key_from_folder_hint(folder)
            if key:
                resolved = resolve_special_folder(user, key)
                if resolved:
                    effective_folder = resolved
                    status, _ = imap.select(effective_folder, readonly=True)
        if status != "OK":
            return None
        status, msg_data = imap.uid("FETCH", str(uid), "(BODY.PEEK[])")
        if status != "OK" or not msg_data:
            return None
        raw_bytes = b""
        for part in msg_data:
            if isinstance(part, tuple):
                raw_bytes += part[1]
        msg = BytesParser(policy=policy.default).parsebytes(raw_bytes)
        target_name = filename.strip()
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
    finally:
        try:
            imap.close()
        except Exception:
            pass
        try:
            imap.logout()
        except Exception:
            pass


def append_draft_imap(
    user: UserLike,
    subject: Optional[str],
    body: Optional[str],
    to: List[str],
    cc: List[str],
    bcc: List[str],
    attachments: List[Tuple[str, Optional[str], bytes]],
) -> bool:
    """Create a draft message and append it to IMAP Drafts folder (exact name)."""
    msg = EmailMessage()
    msg["From"] = user.email
    if to:
        msg["To"] = ", ".join(to)
    if cc:
        msg["Cc"] = ", ".join(cc)
    msg["Subject"] = subject or ""
    if "Date" not in msg:
        msg["Date"] = formatdate(localtime=True)
    msg.set_content(body or "")

    for filename, content_type, content in attachments:
        if not content_type or "/" not in content_type:
            ft = filename.lower()
            if ft.endswith(".pdf"):
                content_type = "application/pdf"
            elif ft.endswith((".jpg", ".jpeg")):
                content_type = "image/jpeg"
            elif ft.endswith(".png"):
                content_type = "image/png"
            elif ft.endswith(".txt"):
                content_type = "text/plain"
            elif ft.endswith(".doc"):
                content_type = "application/msword"
            elif ft.endswith(".docx"):
                content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            else:
                content_type = "application/octet-stream"
        maintype, subtype = content_type.split("/", 1)
        msg.add_attachment(content, maintype=maintype, subtype=subtype, filename=filename)

    imap = _make_imap(user, timeout_seconds=60)
    try:
        drafts_folder = resolve_special_folder(user, "drafts") or "Drafts"
        raw = msg.as_bytes().replace(b"\n", b"\r\n").replace(b"\r\r\n", b"\r\n")
        flags = r"(\\Draft)"
        timestamp = imaplib.Time2Internaldate(time.time())
        status, _ = imap.append(drafts_folder, flags, timestamp, raw)
        if status != "OK":
            status, _ = imap.append(drafts_folder, None, None, raw)
        return status == "OK"
    except Exception:
        return False
    finally:
        try:
            imap.close()
        except Exception:
            pass
        try:
            imap.logout()
        except Exception:
            pass