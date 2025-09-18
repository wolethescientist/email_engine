from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr
from .user import Credentials


class AttachmentIn(BaseModel):
    filename: str
    content_base64: str = Field(..., description="Base64-encoded file content")
    content_type: Optional[str] = None


class EmailComposeRequest(BaseModel):
    creds: Credentials
    subject: Optional[str] = None
    body: Optional[str] = None
    to: List[EmailStr] = []
    cc: List[EmailStr] = []
    bcc: List[EmailStr] = []
    attachments: List[AttachmentIn] = []


class DraftResponse(BaseModel):
    success: bool
    id: Optional[int] = None
    message: Optional[str] = None


class SendEmailRequest(EmailComposeRequest):
    draft_id: Optional[int] = Field(None, description="Optional: send an existing draft by ID")


class EmailItem(BaseModel):
    id: int
    folder: str
    subject: Optional[str] = None
    from_address: Optional[str] = None
    to_addresses: List[str] = []
    is_read: bool = False
    timestamp: Optional[datetime] = None
    has_attachments: bool = False
    is_flagged: bool = False


class EmailDetail(BaseModel):
    id: Optional[int] = None
    folder: str
    subject: Optional[str] = None
    body: Optional[str] = None
    from_address: Optional[str] = None
    to_addresses: List[str] = []
    cc_addresses: List[str] = []
    bcc_addresses: List[str] = []
    is_read: bool = False
    timestamp: Optional[datetime] = None
    has_attachments: bool = False
    is_flagged: bool = False
    attachments: List[str] = []  # list of filenames


class PaginatedEmails(BaseModel):
    page: int
    size: int
    total: int
    items: List[EmailItem]


# Bodies for endpoints that formerly used GET — now POST with body credentials
class ListRequest(BaseModel):
    creds: Credentials
    page: int = Field(1, ge=1)
    size: int = Field(50, ge=1, le=200)
    search_text: Optional[str] = None
    is_starred: Optional[bool] = None
    read_status: Optional[bool] = None


class EmailDetailRequest(BaseModel):
    creds: Credentials
    folder: str = "inbox"


class ModifyEmailRequest(EmailDetailRequest):
    read: Optional[bool] = None


class AttachmentDownloadRequest(EmailDetailRequest):
    pass


class StarEmailRequest(EmailDetailRequest):
    starred: bool = Field(..., description="True to star, False to unstar")