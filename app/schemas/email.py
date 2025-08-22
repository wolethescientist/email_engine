from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr


class AttachmentIn(BaseModel):
    filename: str
    content_base64: str = Field(..., description="Base64-encoded file content")
    content_type: Optional[str] = None


class EmailComposeRequest(BaseModel):
    subject: Optional[str] = None
    body: Optional[str] = None
    to: List[EmailStr] = []
    cc: List[EmailStr] = []
    bcc: List[EmailStr] = []
    attachments: List[AttachmentIn] = []


class DraftResponse(BaseModel):
    id: int


class SendEmailRequest(EmailComposeRequest):
    draft_id: Optional[int] = Field(None, description="Optional: send an existing draft by ID")


class EmailItem(BaseModel):
    id: int
    folder: str
    subject: Optional[str] = None
    from_address: Optional[str] = None
    to_addresses: List[str] = []
    is_read: bool = False


class EmailDetail(BaseModel):
    id: int
    folder: str
    subject: Optional[str] = None
    body: Optional[str] = None
    from_address: Optional[str] = None
    to_addresses: List[str] = []
    cc_addresses: List[str] = []
    bcc_addresses: List[str] = []
    is_read: bool = False
    attachments: List[str] = []  # list of filenames


class PaginatedEmails(BaseModel):
    page: int
    size: int
    total: int
    items: List[EmailItem]