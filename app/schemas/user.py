from pydantic import BaseModel, Field, EmailStr, SecretStr
from typing import Optional
from enum import Enum


class UserRole(str, Enum):
    admin = "admin"
    user = "user"


class ConnectionRequest(BaseModel):
    email: EmailStr
    password: SecretStr = Field(..., description="Email account password (will be encrypted at rest)")
    imap_host: str
    imap_port: int = 993
    smtp_host: str
    smtp_port: int = 465


class ConnectionResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: UserRole = UserRole.user