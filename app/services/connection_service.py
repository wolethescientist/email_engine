import imaplib
import smtplib
import ssl

from ..core.config import get_settings


def validate_imap(email: str, password: str, host: str, port: int) -> None:
    settings = get_settings()
    if settings.IMAP_USE_SSL:
        imap = imaplib.IMAP4_SSL(host=host, port=port, timeout=settings.IMAP_TIMEOUT_SECONDS)
    else:
        imap = imaplib.IMAP4(host=host, port=port, timeout=settings.IMAP_TIMEOUT_SECONDS)
        imap.starttls(ssl_context=ssl.create_default_context())
    try:
        imap.login(email, password)
        imap.logout()
    except imaplib.IMAP4.error as e:
        raise ValueError(f"IMAP login failed: {e}")


def validate_smtp(email: str, password: str, host: str, port: int) -> None:
    settings = get_settings()
    context = ssl.create_default_context()
    if settings.SMTP_USE_SSL:
        server = smtplib.SMTP_SSL(host=host, port=port, timeout=settings.SMTP_TIMEOUT_SECONDS, context=context)
    else:
        server = smtplib.SMTP(host=host, port=port, timeout=settings.SMTP_TIMEOUT_SECONDS)
        server.starttls(context=context)
    try:
        server.login(email, password)
    except smtplib.SMTPException as e:
        raise ValueError(f"SMTP login failed: {e}")
    finally:
        try:
            server.quit()
        except Exception:
            pass


def validate_connection(email: str, password: str, imap_host: str, imap_port: int, smtp_host: str, smtp_port: int) -> None:
    validate_imap(email, password, imap_host, imap_port)
    validate_smtp(email, password, smtp_host, smtp_port)