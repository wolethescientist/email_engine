from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum, SmallInteger
from sqlalchemy.orm import relationship

from ..session import Base


class UserRole(str, Enum):
    admin = "admin"
    user = "user"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    encrypted_password = Column(String, nullable=False)  # AES-GCM base64 string
    imap_host = Column(String(255), nullable=False)
    imap_port = Column(SmallInteger, nullable=False)
    smtp_host = Column(String(255), nullable=False)
    smtp_port = Column(SmallInteger, nullable=False)
    role = Column(SAEnum(UserRole), default=UserRole.user, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    emails = relationship("Email", back_populates="user", cascade="all, delete-orphan")