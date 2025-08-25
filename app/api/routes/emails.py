import base64
import logging
from types import SimpleNamespace
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Request, Response, status

from ...schemas.email import (
    AttachmentDownloadRequest,
    DraftResponse,
    EmailComposeRequest,
    EmailDetail,
    EmailDetailRequest,
    EmailItem,
    ListRequest,
    ModifyEmailRequest,
    PaginatedEmails,
    SendEmailRequest,
)
from ...schemas.user import Credentials
from ...services.email_service import (
    append_draft_imap,
    download_attachment_imap,
    get_email_imap,
    list_folders,
    list_mailbox,
    move_email_imap,
    send_email,
    set_read_flag_imap,
)

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/emails", tags=["emails"])


# Helper to build a user-like object from body creds or headers/query
async def _user_from_request(request: Request, creds: Optional[Credentials]):
    if creds and (creds.password or creds.access_token):
        pwd = creds.password.get_secret_value() if creds.password else None
        return SimpleNamespace(
            email=str(creds.email),
            imap_host=creds.imap_host,
            imap_port=int(creds.imap_port),
            smtp_host=creds.smtp_host,
            smtp_port=int(creds.smtp_port),
            password=pwd,
            encrypted_password=pwd,  # For stateless mode, password is already plain text
            access_token=creds.access_token,
        )
    # Fallback to headers/query
    h = request.headers
    q = request.query_params
    imap_host = h.get("X-IMAP-Host") or q.get("imap_host")
    imap_port = h.get("X-IMAP-Port") or q.get("imap_port")
    smtp_host = h.get("X-SMTP-Host") or q.get("smtp_host")
    smtp_port = h.get("X-SMTP-Port") or q.get("smtp_port")
    email = h.get("X-Email") or q.get("username")
    password = h.get("X-Password") or q.get("password")
    access_token = h.get("X-Access-Token") or q.get("access_token")

    if not (imap_host and imap_port and smtp_host and smtp_port and email and (password or access_token)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing credentials. Provide in body (creds), headers, or query params.")
    return SimpleNamespace(
        email=str(email),
        imap_host=str(imap_host),
        imap_port=int(imap_port),
        smtp_host=str(smtp_host),
        smtp_port=int(smtp_port),
        password=str(password) if password else None,
        encrypted_password=str(password) if password else None,  # For stateless mode, password is already plain text
        access_token=str(access_token) if access_token else None,
    )


@router.post("/folders")
async def get_folders(request: Request, body: Optional[ListRequest] = None):
    user = await _user_from_request(request, body.creds if body else None)
    try:
        folders = list_folders(user)
        return {"folders": folders}
    except ValueError as e:
        logger.warning(f"Folder listing failed for {user.email}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error listing folders for {user.email}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error while listing folders.")


@router.post("/compose", response_model=DraftResponse)
async def compose_email(request: Request, body: EmailComposeRequest):
    user = await _user_from_request(request, body.creds)
    try:
        attachments_data = []
        for a in body.attachments:
            try:
                content = base64.b64decode(a.content_base64)
            except Exception:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid base64 for attachment {a.filename}")
            attachments_data.append((a.filename, a.content_type, content))

        ok = append_draft_imap(
            user,
            subject=body.subject,
            body=body.body,
            to=[str(x) for x in body.to],
            cc=[str(x) for x in body.cc],
            bcc=[str(x) for x in body.bcc],
            attachments=attachments_data,
        )

        if not ok:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to save draft to IMAP server")

        return DraftResponse(success=True, message="Draft saved to IMAP")
    except ValueError as e:
        logger.warning(f"Composing email failed for {user.email}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error composing email for {user.email}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error while composing email.")


@router.post("/send", response_model=EmailDetail)
async def send_mail(request: Request, body: SendEmailRequest):
    user = await _user_from_request(request, body.creds)
    try:
        attachments_data = []
        for a in body.attachments:
            try:
                content = base64.b64decode(a.content_base64)
            except Exception:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid base64 for attachment {a.filename}")
            attachments_data.append((a.filename, a.content_type, content))

        sent = send_email(
            db=None,
            user=user,
            subject=body.subject,
            body=body.body,
            to=[str(x) for x in body.to],
            cc=[str(x) for x in body.cc],
            bcc=[str(x) for x in body.bcc],
            attachments=attachments_data,
            draft_id=body.draft_id,
        )

        return EmailDetail(
            id=getattr(sent, 'id', None),
            folder=getattr(sent, 'folder', 'Sent'),
            subject=getattr(sent, 'subject', None),
            body=getattr(sent, 'body', None),
            from_address=getattr(sent, 'from_address', None),
            to_addresses=getattr(sent, 'to_addresses', []),
            cc_addresses=getattr(sent, 'cc_addresses', []),
            bcc_addresses=getattr(sent, 'bcc_addresses', []),
            is_read=getattr(sent, 'is_read', True),
            attachments=[],
        )
    except ValueError as e:
        logger.warning(f"Sending email failed for {user.email}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error sending email for {user.email}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error while sending email.")


def _list_handler(folder_key: str):
    async def _handler(request: Request, body: Optional[ListRequest] = None):
        user = await _user_from_request(request, body.creds if body else None)
        try:
            page = body.page if body else int(request.query_params.get("page", 1))
            size = body.size if body else int(request.query_params.get("size", 50))
            refresh = body.refresh if body else str(request.query_params.get("refresh", "false")).lower() == "true"
            payload = list_mailbox(user, folder=folder_key, page=page, size=size, refresh=refresh)
            items = [EmailItem(**item) for item in payload.get("items", [])]
            return PaginatedEmails(page=page, size=size, total=payload.get("total", 0), items=items)
        except ValueError as e:
            logger.warning(f"Failed to list mailbox '{folder_key}' for {user.email}: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            logger.error(f"Unexpected error listing mailbox '{folder_key}' for {user.email}: {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error while listing '{folder_key}'.")
    return _handler


router.post("/inbox", response_model=PaginatedEmails)(_list_handler("inbox"))
router.post("/sent", response_model=PaginatedEmails)(_list_handler("sent"))
router.post("/drafts", response_model=PaginatedEmails)(_list_handler("drafts"))
router.post("/trash", response_model=PaginatedEmails)(_list_handler("trash"))
router.post("/archive", response_model=PaginatedEmails)(_list_handler("archive"))
router.post("/spam", response_model=PaginatedEmails)(_list_handler("spam"))


@router.post("/{email_id}", response_model=EmailDetail)
async def get_email_detail(email_id: int, request: Request, body: Optional[EmailDetailRequest] = None):
    user = await _user_from_request(request, body.creds if body else None)
    folder = body.folder if body else (request.query_params.get("folder") or "inbox")
    try:
        detail = get_email_imap(user, folder=folder, uid=email_id)
        if not detail:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found")
        return EmailDetail(**detail)
    except ValueError as e:
        logger.warning(f"Failed to fetch email {email_id} for {user.email}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error fetching email {email_id} for {user.email}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error while fetching email.")


@router.post("/{email_id}/delete")
async def delete_email(email_id: int, request: Request, body: Optional[EmailDetailRequest] = None):
    user = await _user_from_request(request, body.creds if body else None)
    folder = body.folder if body else (request.query_params.get("folder") or "inbox")
    try:
        ok = move_email_imap(user, src_folder=folder, uid=email_id, target_folder="trash")
        if not ok:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found or cannot be moved")
        return {"status": "ok"}
    except ValueError as e:
        logger.warning(f"Failed to delete email {email_id} for {user.email}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error deleting email {email_id} for {user.email}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error while deleting email.")


@router.post("/{email_id}/archive")
async def archive_email(email_id: int, request: Request, body: Optional[EmailDetailRequest] = None):
    user = await _user_from_request(request, body.creds if body else None)
    folder = body.folder if body else (request.query_params.get("folder") or "inbox")
    try:
        ok = move_email_imap(user, src_folder=folder, uid=email_id, target_folder="archive")
        if not ok:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found or cannot be moved")
        return {"status": "ok"}
    except ValueError as e:
        logger.warning(f"Failed to archive email {email_id} for {user.email}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error archiving email {email_id} for {user.email}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error while archiving email.")


@router.post("/{email_id}/unarchive")
async def unarchive_email(email_id: int, request: Request, body: Optional[EmailDetailRequest] = None):
    user = await _user_from_request(request, body.creds if body else None)
    folder = body.folder if body else (request.query_params.get("folder") or "archive")
    try:
        ok = move_email_imap(user, src_folder=folder, uid=email_id, target_folder="inbox")
        if not ok:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found or cannot be moved")
        return {"status": "ok"}
    except ValueError as e:
        logger.warning(f"Failed to unarchive email {email_id} for {user.email}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error unarchiving email {email_id} for {user.email}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error while unarchiving email.")


@router.post("/{email_id}/read")
async def mark_read(email_id: int, request: Request, body: ModifyEmailRequest):
    user = await _user_from_request(request, body.creds)
    if body.read is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Field 'read' is required")
    try:
        ok = set_read_flag_imap(user, folder=body.folder, uid=email_id, is_read=body.read)
        if not ok:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found or cannot update read flag")
        return {"status": "ok"}
    except ValueError as e:
        logger.warning(f"Failed to mark email {email_id} as read for {user.email}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error marking email {email_id} as read for {user.email}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error while marking email as read.")


@router.post("/{email_id}/attachments/{filename}")
async def download_attachment(email_id: int, filename: str, request: Request, body: Optional[AttachmentDownloadRequest] = None):
    user = await _user_from_request(request, body.creds if body else None)
    folder = body.folder if body else (request.query_params.get("folder") or "inbox")
    try:
        result = download_attachment_imap(user, folder=folder, uid=email_id, filename=filename)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")
        content, content_type, safe_name = result
        headers = {"Content-Disposition": f"attachment; filename=\"{safe_name}\""}
        return Response(content=content, media_type=content_type or "application/octet-stream", headers=headers)
    except ValueError as e:
        logger.warning(f"Failed to download attachment {filename} for {user.email}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error downloading attachment {filename} for {user.email}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error while downloading attachment.")