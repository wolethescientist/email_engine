import base64
import imaplib
import smtplib
import ssl
from typing import Optional

from ..core.config import get_settings


def validate_imap(email: str, host: str, port: int, password: Optional[str] = None, access_token: Optional[str] = None) -> None:
    settings = get_settings()
    if settings.IMAP_USE_SSL:
        imap = imaplib.IMAP4_SSL(host=host, port=port, timeout=settings.IMAP_TIMEOUT_SECONDS)
    else:
        imap = imaplib.IMAP4(host=host, port=port, timeout=settings.IMAP_TIMEOUT_SECONDS)
        imap.starttls(ssl_context=ssl.create_default_context())
    try:
        if access_token:
            auth_str = f"user={email}\x01auth=Bearer {access_token}\x01\x01".encode("utf-8")
            imap.authenticate("XOAUTH2", lambda x: auth_str)
        elif password:
            imap.login(email, password)
        else:
            raise ValueError("Provide either password or access_token for IMAP")
        imap.logout()
    except imaplib.IMAP4.error as e:
        raise ValueError(f"IMAP login failed: {e}")


def validate_smtp(email: str, host: str, port: int, password: Optional[str] = None, access_token: Optional[str] = None) -> None:
    settings = get_settings()
    context = ssl.create_default_context()
    if settings.SMTP_USE_SSL:
        server = smtplib.SMTP_SSL(host=host, port=port, timeout=settings.SMTP_TIMEOUT_SECONDS, context=context)
        server.ehlo()
    else:
        server = smtplib.SMTP(host=host, port=port, timeout=settings.SMTP_TIMEOUT_SECONDS)
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
    try:
        if access_token:
            auth_str = f"user={email}\x01auth=Bearer {access_token}\x01\x01"
            b64 = base64.b64encode(auth_str.encode()).decode()
            code, resp = server.docmd("AUTH", "XOAUTH2 " + b64)
            if code != 235:
                raise ValueError(f"SMTP login failed: {resp}")
        elif password:
            server.login(email, password)
        else:
            raise ValueError("Provide either password or access_token for SMTP")
    except smtplib.SMTPException as e:
        raise ValueError(f"SMTP login failed: {e}")
    finally:
        try:
            server.quit()
        except Exception:
            pass


def validate_connection(email: str, imap_host: str, imap_port: int, smtp_host: str, smtp_port: int, password: Optional[str] = None, access_token: Optional[str] = None) -> None:
    validate_imap(email=email, host=imap_host, port=imap_port, password=password, access_token=access_token)
    validate_smtp(email=email, host=smtp_host, port=smtp_port, password=password, access_token=access_token)