from pydantic import BaseModel, Field, EmailStr, SecretStr
from typing import Optional
from enum import Enum


class UserRole(str, Enum):
    admin = "admin"
    user = "user"


class Credentials(BaseModel):
    email: EmailStr
    password: Optional[SecretStr] = Field(None, description="Email account password")
    access_token: Optional[str] = Field(None, description="OAuth2 access token for XOAUTH2")
    imap_host: str
    imap_port: int = 993
    smtp_host: str
    smtp_port: int = 465


class ConnectValidateRequest(Credentials):
    pass


class ConnectValidateResponse(BaseModel):
    success: bool
    message: Optional[str] = None