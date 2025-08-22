from typing import List
import base64

from fastapi import APIRouter, Depends, HTTPException, Query, Response, Request
from sqlalchemy.orm import Session

from ...core.auth import get_current_user, require_roles, CurrentUser
from ...db.session import get_db
from ...db.models.email import Email, Attachment
from ...schemas.email import (
    EmailComposeRequest,
    DraftResponse,
    SendEmailRequest,
    EmailItem,
    PaginatedEmails,
    EmailDetail,
)
from ...services.email_service import save_draft, send_email, list_mailbox, get_email_imap, move_email_db, set_read_flag_db, _deserialize_addresses, debug_imap_connection, poll_for_new_emails, imap_idle_monitor

router = APIRouter(prefix="/emails", tags=["emails"])


@router.post("/compose", response_model=DraftResponse, dependencies=[Depends(require_roles(["admin", "user"]))])
def compose_email(body: EmailComposeRequest, user_ctx: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    print(f"DEBUG: Saving draft for user {user_ctx.user.id} ({user_ctx.user.email})")
    print(f"DEBUG: Draft details - Subject: '{body.subject}', To: {body.to}, CC: {body.cc}, BCC: {body.bcc}")
    print(f"DEBUG: Draft body length: {len(body.body) if body.body else 0}")
    print(f"DEBUG: Draft attachments count: {len(body.attachments)}")
    
    attachments_data = []
    for a in body.attachments:
        try:
            content = base64.b64decode(a.content_base64)
            print(f"DEBUG: Processed attachment '{a.filename}' - size: {len(content)} bytes, type: {a.content_type}")
        except Exception as e:
            print(f"DEBUG: Failed to decode attachment '{a.filename}': {e}")
            raise HTTPException(status_code=400, detail=f"Invalid base64 for attachment {a.filename}")
        attachments_data.append((a.filename, a.content_type, content))

    draft = save_draft(
        db=db,
        user=user_ctx.user,
        subject=body.subject,
        body=body.body,
        to=[str(x) for x in body.to],
        cc=[str(x) for x in body.cc],
        bcc=[str(x) for x in body.bcc],
        attachments=attachments_data,
    )
    
    print(f"DEBUG: Draft saved successfully with ID: {draft.id}")
    print(f"DEBUG: Draft folder: '{draft.folder}', Subject: '{draft.subject}'")
    
    # Verify the draft was saved properly
    db.commit()  # Ensure transaction is committed
    saved_draft = db.get(Email, draft.id)
    if saved_draft:
        print(f"DEBUG: Verification - Draft {draft.id} exists in DB with folder: '{saved_draft.folder}'")
    else:
        print(f"DEBUG: WARNING - Draft {draft.id} not found in DB after saving!")
    
    return DraftResponse(id=draft.id)


@router.post("/send", response_model=EmailDetail, dependencies=[Depends(require_roles(["admin", "user"]))])
async def send_mail(request: Request, body: SendEmailRequest, user_ctx: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    # Get raw request body for debugging
    raw_body = await request.body()
    print(f"DEBUG: Raw request size: {len(raw_body)} bytes")
    
    print(f"DEBUG: Received request body:")
    print(f"DEBUG: - Subject: {body.subject}")
    print(f"DEBUG: - To: {body.to}")
    print(f"DEBUG: - Attachments count: {len(body.attachments)}")
    print(f"DEBUG: - Body type: {type(body)}")
    
    # Print first 500 chars of raw body to see structure
    raw_str = raw_body.decode('utf-8', errors='ignore')[:500]
    print(f"DEBUG: Raw body preview: {raw_str}")
    
    if hasattr(body, 'attachments') and body.attachments:
        print(f"DEBUG: Attachments details:")
        for i, att in enumerate(body.attachments):
            print(f"DEBUG:   [{i}] filename: {att.filename}")
            print(f"DEBUG:   [{i}] content_type: {att.content_type}")
            print(f"DEBUG:   [{i}] base64 length: {len(att.content_base64) if att.content_base64 else 0}")
    else:
        print(f"DEBUG: No attachments found in request")
    
    attachments_data = []
    for a in body.attachments:
        print(f"DEBUG: Processing attachment {a.filename}, content_type: {a.content_type}, base64 length: {len(a.content_base64)}")
        try:
            content = base64.b64decode(a.content_base64)
            print(f"DEBUG: Decoded attachment {a.filename}, size: {len(content)} bytes")
        except Exception as e:
            print(f"DEBUG: Base64 decode failed for {a.filename}: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid base64 for attachment {a.filename}")
        attachments_data.append((a.filename, a.content_type, content))

    sent = send_email(
        db=db,
        user=user_ctx.user,
        subject=body.subject,
        body=body.body,
        to=[str(x) for x in body.to],
        cc=[str(x) for x in body.cc],
        bcc=[str(x) for x in body.bcc],
        attachments=attachments_data,
        draft_id=body.draft_id,
    )

    return EmailDetail(
        id=sent.id,
        folder=sent.folder,
        subject=sent.subject,
        body=sent.body,
        from_address=sent.from_address,
        to_addresses=_deserialize_addresses(sent.to_addresses),
        cc_addresses=_deserialize_addresses(sent.cc_addresses),
        bcc_addresses=_deserialize_addresses(sent.bcc_addresses),
        is_read=sent.is_read,
        attachments=[a.filename for a in sent.attachments],
    )


@router.get("/inbox", response_model=PaginatedEmails, dependencies=[Depends(require_roles(["admin", "user"]))])
def get_inbox(user_ctx: CurrentUser = Depends(get_current_user), page: int = Query(1, ge=1), size: int = Query(50, ge=1, le=200)):
    try:
        payload = list_mailbox(user_ctx.user, folder="INBOX", page=page, size=size)
        items = [EmailItem(**item) for item in payload.get("items", [])]
        return PaginatedEmails(page=page, size=size, total=payload.get("total", 0), items=items)
    except ValueError as e:
        if "IMAP authentication failed" in str(e):
            raise HTTPException(status_code=400, detail="IMAP authentication failed. Please reconnect your email account.")
        raise HTTPException(status_code=500, detail=f"Failed to fetch inbox: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch inbox: {str(e)}")


@router.get("/sent", response_model=PaginatedEmails, dependencies=[Depends(require_roles(["admin", "user"]))])
def get_sent(user_ctx: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db), page: int = Query(1, ge=1), size: int = Query(50, ge=1, le=200), source: str = Query("imap")):
    source = (source or "db").lower()
    
    if source == "imap":
        # Try IMAP first
        try:
            payload = list_mailbox(user_ctx.user, folder="Sent", page=page, size=size)
            if payload.get("total", 0) > 0:
                items = [EmailItem(**item) for item in payload.get("items", [])]
                return PaginatedEmails(page=page, size=size, total=payload.get("total", 0), items=items)
        except ValueError as e:
            if "IMAP authentication failed" in str(e):
                raise HTTPException(status_code=400, detail="IMAP authentication failed. Please reconnect your email account.")
            pass  # Fall through to DB
        except Exception:
            pass  # Fall through to DB
    
    # Use DB (default) or fallback from IMAP
    q = db.query(Email).filter(Email.user_id == user_ctx.user.id, Email.folder == "Sent").order_by(Email.created_at.desc())
    total = q.count()
    rows = q.offset((page - 1) * size).limit(size).all()
    items = [EmailItem(id=e.id, folder=e.folder, subject=e.subject, from_address=e.from_address, to_addresses=_deserialize_addresses(e.to_addresses), is_read=e.is_read) for e in rows]
    return PaginatedEmails(page=page, size=size, total=total, items=items)


@router.get("/drafts", response_model=PaginatedEmails, dependencies=[Depends(require_roles(["admin", "user"]))])
def get_drafts(user_ctx: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db), page: int = Query(1, ge=1), size: int = Query(50, ge=1, le=200), source: str = Query("imap")):
    source = (source or "imap").lower()
    
    if source == "imap":
        # Try IMAP first
        try:
            payload = list_mailbox(user_ctx.user, folder="Drafts", page=page, size=size)
            if payload.get("total", 0) > 0:
                items = [EmailItem(**item) for item in payload.get("items", [])]
                return PaginatedEmails(page=page, size=size, total=payload.get("total", 0), items=items)
        except ValueError as e:
            if "IMAP authentication failed" in str(e):
                raise HTTPException(status_code=400, detail="IMAP authentication failed. Please reconnect your email account.")
            pass  # Fall through to DB
        except Exception:
            pass  # Fall through to DB
    
    # Use DB (default) or fallback from IMAP
    print(f"DEBUG: Fetching emails for {user_ctx.user.email} in Drafts (page {page}, size {size})")
    print(f"DEBUG: Selected DB.Drafts (fallback)")
    
    q = db.query(Email).filter(Email.user_id == user_ctx.user.id, Email.folder == "Drafts").order_by(Email.created_at.desc())
    total = q.count()
    print(f"DEBUG: Found {total} emails in Drafts")
    
    rows = q.offset((page - 1) * size).limit(size).all()
    items_to_process = len(rows)
    print(f"DEBUG: Processing {items_to_process} emails for page {page}")
    
    items = []
    for e in rows:
        item = EmailItem(
            id=e.id, 
            folder=e.folder, 
            subject=e.subject, 
            from_address=e.from_address, 
            to_addresses=_deserialize_addresses(e.to_addresses), 
            is_read=e.is_read
        )
        items.append(item)
    
    result = PaginatedEmails(page=page, size=size, total=total, items=items)
    print(f"DEBUG: Completed fetch - Total: {total}, Items: {len(result.items)}")
    return result


@router.get("/trash", response_model=PaginatedEmails, dependencies=[Depends(require_roles(["admin", "user"]))])
def get_trash(user_ctx: CurrentUser = Depends(get_current_user), page: int = Query(1, ge=1), size: int = Query(50, ge=1, le=200)):
    try:
        payload = list_mailbox(user_ctx.user, folder="Trash", page=page, size=size)
        items = [EmailItem(**item) for item in payload.get("items", [])]
        return PaginatedEmails(page=page, size=size, total=payload.get("total", 0), items=items)
    except ValueError as e:
        if "IMAP authentication failed" in str(e):
            raise HTTPException(status_code=400, detail="IMAP authentication failed. Please reconnect your email account.")
        raise HTTPException(status_code=500, detail=f"Failed to fetch trash: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch trash: {str(e)}")


@router.get("/archive", response_model=PaginatedEmails, dependencies=[Depends(require_roles(["admin", "user"]))])
def get_archive(user_ctx: CurrentUser = Depends(get_current_user), page: int = Query(1, ge=1), size: int = Query(50, ge=1, le=200)):
    try:
        payload = list_mailbox(user_ctx.user, folder="Archive", page=page, size=size)
        items = [EmailItem(**item) for item in payload.get("items", [])]
        return PaginatedEmails(page=page, size=size, total=payload.get("total", 0), items=items)
    except ValueError as e:
        if "IMAP authentication failed" in str(e):
            raise HTTPException(status_code=400, detail="IMAP authentication failed. Please reconnect your email account.")
        raise HTTPException(status_code=500, detail=f"Failed to fetch archive: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch archive: {str(e)}")


@router.get("/spam", response_model=PaginatedEmails, dependencies=[Depends(require_roles(["admin", "user"]))])
def get_spam(user_ctx: CurrentUser = Depends(get_current_user), page: int = Query(1, ge=1), size: int = Query(50, ge=1, le=200)):
    try:
        payload = list_mailbox(user_ctx.user, folder="Spam", page=page, size=size)
        items = [EmailItem(**item) for item in payload.get("items", [])]
        return PaginatedEmails(page=page, size=size, total=payload.get("total", 0), items=items)
    except ValueError as e:
        if "IMAP authentication failed" in str(e):
            raise HTTPException(status_code=400, detail="IMAP authentication failed. Please reconnect your email account.")
        raise HTTPException(status_code=500, detail=f"Failed to fetch spam: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch spam: {str(e)}")


@router.get("/debug/all-emails", dependencies=[Depends(require_roles(["admin", "user"]))])
def debug_all_emails(user_ctx: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """Debug endpoint to see all emails in the local database for the current user (not IMAP emails)."""
    emails = db.query(Email).filter(Email.user_id == user_ctx.user.id).order_by(Email.created_at.desc()).all()
    
    result = []
    for email in emails:
        result.append({
            "id": email.id,
            "folder": email.folder,
            "subject": email.subject,
            "from_address": email.from_address,
            "to_addresses": _deserialize_addresses(email.to_addresses),
            "cc_addresses": _deserialize_addresses(email.cc_addresses),
            "bcc_addresses": _deserialize_addresses(email.bcc_addresses),
            "is_read": email.is_read,
            "created_at": email.created_at.isoformat(),
            "updated_at": email.updated_at.isoformat(),
            "body_preview": (email.body[:100] + "...") if email.body and len(email.body) > 100 else email.body,
            "attachments_count": len(email.attachments),
            "attachments": [{"filename": a.filename, "content_type": a.content_type} for a in email.attachments]
        })
    
    return {
        "total_emails": len(result),
        "folders": list(set([e["folder"] for e in result])),
        "drafts_count": len([e for e in result if e["folder"] == "Drafts"]),
        "emails": result
    }


@router.get("/debug/drafts-detailed", dependencies=[Depends(require_roles(["admin", "user"]))])
def debug_drafts_detailed(user_ctx: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """Debug endpoint to see detailed information about drafts stored in the local database (not IMAP drafts)."""
    drafts = db.query(Email).filter(
        Email.user_id == user_ctx.user.id, 
        Email.folder == "Drafts"
    ).order_by(Email.created_at.desc()).all()
    
    result = []
    for draft in drafts:
        result.append({
            "id": draft.id,
            "user_id": draft.user_id,
            "folder": draft.folder,
            "subject": draft.subject,
            "body": draft.body,
            "from_address": draft.from_address,
            "to_addresses_raw": draft.to_addresses,
            "to_addresses_parsed": _deserialize_addresses(draft.to_addresses),
            "cc_addresses_raw": draft.cc_addresses,
            "cc_addresses_parsed": _deserialize_addresses(draft.cc_addresses),
            "bcc_addresses_raw": draft.bcc_addresses,
            "bcc_addresses_parsed": _deserialize_addresses(draft.bcc_addresses),
            "is_read": draft.is_read,
            "created_at": draft.created_at.isoformat(),
            "updated_at": draft.updated_at.isoformat(),
            "attachments": [
                {
                    "id": a.id,
                    "filename": a.filename,
                    "content_type": a.content_type,
                    "size_bytes": len(a.blob) if a.blob else 0
                } 
                for a in draft.attachments
            ]
        })
    
    return {
        "user_id": user_ctx.user.id,
        "user_email": user_ctx.user.email,
        "total_drafts": len(result),
        "drafts": result
    }


@router.get("/debug/imap-drafts-test", dependencies=[Depends(require_roles(["admin", "user"]))])
def debug_imap_drafts_test(user_ctx: CurrentUser = Depends(get_current_user)):
    """Debug endpoint to test IMAP drafts folder connectivity and list available folders."""
    try:
        # Test IMAP drafts connectivity
        payload = list_mailbox(user_ctx.user, folder="Drafts", page=1, size=10)
        return {
            "status": "success",
            "user_email": user_ctx.user.email,
            "imap_drafts_accessible": True,
            "total_drafts_in_imap": payload.get("total", 0),
            "sample_drafts": payload.get("items", []),
            "message": f"Successfully connected to IMAP drafts folder. Found {payload.get('total', 0)} drafts."
        }
    except ValueError as e:
        if "IMAP authentication failed" in str(e):
            return {
                "status": "error",
                "user_email": user_ctx.user.email,
                "imap_drafts_accessible": False,
                "error": "IMAP authentication failed",
                "message": "Please reconnect your email account."
            }
        return {
            "status": "error", 
            "user_email": user_ctx.user.email,
            "imap_drafts_accessible": False,
            "error": str(e),
            "message": "IMAP connection error"
        }
    except Exception as e:
        return {
            "status": "error",
            "user_email": user_ctx.user.email,
            "imap_drafts_accessible": False,
            "error": str(e),
            "message": "Failed to connect to IMAP drafts folder"
        }


@router.get("/{email_id}", response_model=EmailDetail, dependencies=[Depends(require_roles(["admin", "user"]))])
def get_email(email_id: int, folder: str = Query("INBOX"), source: str = Query("auto"), user_ctx: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    # Normalize common folder names
    folder_map = {
        "inbox": "INBOX",
        "sent": "Sent",
        "trash": "Trash",
        "archive": "Archive",
        "drafts": "Drafts",
        "spam": "Spam",
    }
    normalized = folder_map.get(folder.lower(), folder)

    # For Drafts, try IMAP first, then fall back to DB
    if normalized == "Drafts":
        if source == "db":
            # Force DB lookup
            e = db.get(Email, email_id)
            if not e or e.user_id != user_ctx.user.id or e.folder != normalized:
                raise HTTPException(status_code=404, detail="Email not found")
            return EmailDetail(
                id=e.id,
                folder=e.folder,
                subject=e.subject,
                body=e.body,
                from_address=e.from_address,
                to_addresses=_deserialize_addresses(e.to_addresses),
                cc_addresses=_deserialize_addresses(e.cc_addresses),
                bcc_addresses=_deserialize_addresses(e.bcc_addresses),
                is_read=e.is_read,
                attachments=[a.filename for a in e.attachments],
            )
        else:
            # Try IMAP first (default behavior), then fall back to DB
            try:
                detail = get_email_imap(user_ctx.user, folder=normalized, seq_num=email_id)
                if detail:
                    return EmailDetail(**detail)
            except ValueError as e:
                if "IMAP authentication failed" in str(e):
                    raise HTTPException(status_code=400, detail="IMAP authentication failed. Please reconnect your email account.")
                # Fall through to DB
            except Exception:
                # Fall through to DB
                pass
            
            # Fallback to DB
            e = db.get(Email, email_id)
            if not e or e.user_id != user_ctx.user.id or e.folder != normalized:
                raise HTTPException(status_code=404, detail="Email not found")
            return EmailDetail(
                id=e.id,
                folder=e.folder,
                subject=e.subject,
                body=e.body,
                from_address=e.from_address,
                to_addresses=_deserialize_addresses(e.to_addresses),
                cc_addresses=_deserialize_addresses(e.cc_addresses),
                bcc_addresses=_deserialize_addresses(e.bcc_addresses),
                is_read=e.is_read,
                attachments=[a.filename for a in e.attachments],
            )

    # For Sent emails, try both IMAP and DB based on source parameter
    if normalized == "Sent":
        if source == "db":
            # Force DB lookup
            e = db.get(Email, email_id)
            if not e or e.user_id != user_ctx.user.id or e.folder != normalized:
                raise HTTPException(status_code=404, detail="Email not found")
            return EmailDetail(
                id=e.id,
                folder=e.folder,
                subject=e.subject,
                body=e.body,
                from_address=e.from_address,
                to_addresses=_deserialize_addresses(e.to_addresses),
                cc_addresses=_deserialize_addresses(e.cc_addresses),
                bcc_addresses=_deserialize_addresses(e.bcc_addresses),
                is_read=e.is_read,
                attachments=[a.filename for a in e.attachments],
            )
        else:
            # Try IMAP first (default behavior), then fall back to DB
            try:
                detail = get_email_imap(user_ctx.user, folder=normalized, seq_num=email_id)
                if detail:
                    return EmailDetail(**detail)
            except ValueError as e:
                if "IMAP authentication failed" in str(e):
                    raise HTTPException(status_code=400, detail="IMAP authentication failed. Please reconnect your email account.")
                # Fall through to DB
            except Exception:
                # Fall through to DB
                pass
            
            # Fallback to DB
            e = db.get(Email, email_id)
            if not e or e.user_id != user_ctx.user.id or e.folder != normalized:
                raise HTTPException(status_code=404, detail="Email not found")
            return EmailDetail(
                id=e.id,
                folder=e.folder,
                subject=e.subject,
                body=e.body,
                from_address=e.from_address,
                to_addresses=_deserialize_addresses(e.to_addresses),
                cc_addresses=_deserialize_addresses(e.cc_addresses),
                bcc_addresses=_deserialize_addresses(e.bcc_addresses),
                is_read=e.is_read,
                attachments=[a.filename for a in e.attachments],
            )

    # For all other folders (INBOX, Trash, Archive, Spam), use IMAP
    try:
        detail = get_email_imap(user_ctx.user, folder=normalized, seq_num=email_id)
        if not detail:
            raise HTTPException(status_code=404, detail="Email not found")
        return EmailDetail(**detail)
    except ValueError as e:
        if "IMAP authentication failed" in str(e):
            raise HTTPException(status_code=400, detail="IMAP authentication failed. Please reconnect your email account.")
        raise HTTPException(status_code=500, detail=f"Failed to fetch email: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch email: {str(e)}")


@router.delete("/{email_id}", dependencies=[Depends(require_roles(["admin", "user"]))])
def delete_email(email_id: int, user_ctx: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    e = move_email_db(db, user_ctx.user, email_id, target_folder="Trash")
    if not e:
        raise HTTPException(status_code=404, detail="Email not found")
    return {"status": "ok"}


@router.patch("/{email_id}/archive", dependencies=[Depends(require_roles(["admin", "user"]))])
def archive_email(email_id: int, user_ctx: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    e = move_email_db(db, user_ctx.user, email_id, target_folder="Archive")
    if not e:
        raise HTTPException(status_code=404, detail="Email not found")
    return {"status": "ok"}


@router.patch("/{email_id}/read", dependencies=[Depends(require_roles(["admin", "user"]))])
def mark_read(email_id: int, read: bool, user_ctx: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    e = set_read_flag_db(db, user_ctx.user, email_id, is_read=read)
    if not e:
        raise HTTPException(status_code=404, detail="Email not found")
    return {"status": "ok"}


@router.get("/{email_id}/attachments/{filename}", dependencies=[Depends(require_roles(["admin", "user"]))])
def download_attachment(email_id: int, filename: str, user_ctx: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    # Ensure email exists and belongs to current user
    e = db.get(Email, email_id)
    if not e or e.user_id != user_ctx.user.id:
        raise HTTPException(status_code=404, detail="Email not found")

    # Find attachment by filename for that email
    att = (
        db.query(Attachment)
        .filter(Attachment.email_id == email_id, Attachment.filename == filename)
        .first()
    )
    if not att or not att.blob:
        raise HTTPException(status_code=404, detail="Attachment not found")

    headers = {
        "Content-Disposition": f"attachment; filename=\"{att.filename}\""
    }
    return Response(content=att.blob, media_type=att.content_type or "application/octet-stream", headers=headers)


@router.get("/debug/imap", dependencies=[Depends(require_roles(["admin", "user"]))])
def debug_imap_connection(user_ctx: CurrentUser = Depends(get_current_user)):
    """Debug endpoint to check IMAP connection and folder status"""
    import imaplib
    from ...core.security import decrypt_secret
    from ...core.config import get_settings
    import ssl
    
    try:
        settings = get_settings()
        password = decrypt_secret(user_ctx.user.encrypted_password)
        
        # Create IMAP connection
        if settings.IMAP_USE_SSL:
            imap = imaplib.IMAP4_SSL(host=user_ctx.user.imap_host, port=user_ctx.user.imap_port, timeout=settings.IMAP_TIMEOUT_SECONDS)
        else:
            imap = imaplib.IMAP4(host=user_ctx.user.imap_host, port=user_ctx.user.imap_port, timeout=settings.IMAP_TIMEOUT_SECONDS)
            imap.starttls(ssl_context=ssl.create_default_context())
        
        imap.login(user_ctx.user.email, password)
        
        # List all folders
        status, folders = imap.list()
        folder_list = []
        if status == "OK":
            for folder in folders:
                folder_str = folder.decode() if isinstance(folder, bytes) else str(folder)
                folder_list.append(folder_str)
        
        # Check INBOX specifically
        status, _ = imap.select("INBOX", readonly=True)
        inbox_status = status
        inbox_count = 0
        inbox_recent = 0
        
        if status == "OK":
            # Get total count
            status, data = imap.search(None, "ALL")
            if status == "OK" and data and data[0]:
                inbox_count = len(data[0].split())
            
            # Get recent count
            status, data = imap.search(None, "RECENT")
            if status == "OK" and data and data[0]:
                inbox_recent = len(data[0].split())
        
        imap.logout()
        
        return {
            "status": "success",
            "imap_host": user_ctx.user.imap_host,
            "imap_port": user_ctx.user.imap_port,
            "folders": folder_list,
            "inbox_status": inbox_status,
            "inbox_total_emails": inbox_count,
            "inbox_recent_emails": inbox_recent,
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "imap_host": user_ctx.user.imap_host,
            "imap_port": user_ctx.user.imap_port,
        }


@router.get("/debug/imap", dependencies=[Depends(require_roles(["admin", "user"]))])
def debug_imap(user_ctx: CurrentUser = Depends(get_current_user)):
    """Debug IMAP connection and return detailed server information"""
    return debug_imap_connection(user_ctx.user)


@router.get("/poll", dependencies=[Depends(require_roles(["admin", "user"]))])
def poll_emails(folder: str = Query("INBOX"), timeout: int = Query(30, ge=5, le=120), user_ctx: CurrentUser = Depends(get_current_user)):
    """
    Poll for new emails with comprehensive refresh strategy.
    This endpoint forces a fresh connection and uses multiple techniques to ensure new emails are detected.
    """
    return poll_for_new_emails(user_ctx.user, folder=folder, timeout_seconds=timeout)


@router.get("/idle", dependencies=[Depends(require_roles(["admin", "user"]))])
def idle_monitor(folder: str = Query("INBOX"), timeout: int = Query(300, ge=30, le=600), user_ctx: CurrentUser = Depends(get_current_user)):
    """
    Use IMAP IDLE to monitor for new emails in real-time.
    This is more efficient than polling but requires server support for IDLE.
    """
    return imap_idle_monitor(user_ctx.user, folder=folder, timeout_seconds=timeout)


@router.get("/force-refresh", dependencies=[Depends(require_roles(["admin", "user"]))])
def force_refresh_inbox(user_ctx: CurrentUser = Depends(get_current_user)):
    """
    NUCLEAR OPTION: Force complete refresh of INBOX to detect new emails.
    This uses the most aggressive refresh strategy possible.
    """
    try:
        # Use the aggressive list_mailbox function to force refresh
        result = list_mailbox(user_ctx.user, folder="INBOX", page=1, size=10)
        
        # Extract key information
        total = result.get("total", 0)
        items = result.get("items", [])
        
        # Count unread emails
        unread_count = sum(1 for item in items if not item.get("is_read", True))
        
        return {
            "success": True,
            "message": "INBOX forcefully refreshed",
            "total_emails": total,
            "fetched_emails": len(items),
            "unread_emails": unread_count,
            "latest_emails": [
                {
                    "id": item.get("id"),
                    "subject": item.get("subject"),
                    "from": item.get("from_address"),
                    "is_read": item.get("is_read", True)
                }
                for item in items[:5]  # Show first 5 emails
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Force refresh failed: {str(e)}")
