import base64
import os
import secrets
import hashlib
from typing import Tuple, Dict, Any
from datetime import datetime, timedelta, timezone

import jwt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .config import get_settings


def _get_aes_key() -> bytes:
    settings = get_settings()
    if not settings.AES_SECRET_KEY:
        # For safety, never auto-generate silently in production; raise an error.
        raise ValueError("AES_SECRET_KEY is not set. Provide a base64-encoded 32-byte key in environment.")
    try:
        key = base64.b64decode(settings.AES_SECRET_KEY)
    except Exception as e:
        raise ValueError("AES_SECRET_KEY must be base64-encoded.") from e
    if len(key) != 32:
        raise ValueError("AES_SECRET_KEY must decode to 32 bytes for AES-256-GCM.")
    return key


def encrypt_secret(plaintext: str) -> str:
    """Encrypt sensitive text using AES-256-GCM. Returns base64 string nonce|ciphertext|tag.
    Do not log plaintext. Store only ciphertext.
    """
    key = _get_aes_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    cipher = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), associated_data=None)
    payload = nonce + cipher  # cipher includes tag at the end
    return base64.b64encode(payload).decode("utf-8")


def decrypt_secret(ciphertext_b64: str) -> str:
    key = _get_aes_key()
    aesgcm = AESGCM(key)
    raw = base64.b64decode(ciphertext_b64)
    nonce, cipher = raw[:12], raw[12:]
    plain = aesgcm.decrypt(nonce, cipher, associated_data=None)
    return plain.decode("utf-8")

# ==== JWT utilities ====

def create_access_token(*, subject: str | int, role: str, expires_minutes: int | None = None) -> str:
    settings = get_settings()
    expire_delta = timedelta(minutes=expires_minutes or settings.JWT_EXPIRES_MINUTES)
    now = datetime.now(timezone.utc)
    payload: Dict[str, Any] = {
        "sub": str(subject),
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + expire_delta).timestamp()),
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token


def decode_access_token(token: str) -> Dict[str, Any]:
    settings = get_settings()
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    return payload