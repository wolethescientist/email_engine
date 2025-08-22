from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, LargeBinary
from sqlalchemy.orm import relationship

from ..session import Base


class Email(Base):
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)

    folder = Column(String(32), index=True, nullable=False)  # Inbox, Sent, Drafts, Trash, Archive
    subject = Column(String(998), nullable=True)
    body = Column(Text, nullable=True)

    from_address = Column(String(320), nullable=True)
    to_addresses = Column(Text, nullable=True)  # JSON string of list[str]
    cc_addresses = Column(Text, nullable=True)
    bcc_addresses = Column(Text, nullable=True)

    is_read = Column(Boolean, default=False, index=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="emails")
    attachments = relationship("Attachment", back_populates="email", cascade="all, delete-orphan")


class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True)
    email_id = Column(Integer, ForeignKey("emails.id", ondelete="CASCADE"), index=True, nullable=False)
    filename = Column(String(512), nullable=False)
    content_type = Column(String(128), nullable=True)
    blob = Column(LargeBinary, nullable=True)  # Optional: store file content in DB

    email = relationship("Email", back_populates="attachments")