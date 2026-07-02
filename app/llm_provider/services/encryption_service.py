import base64
import hashlib
import os
from typing import Final

from app.config import settings

try:
    from cryptography.fernet import Fernet
except ImportError:  # pragma: no cover - depends on environment
    Fernet = None

_ENCRYPTION_KEY_ENV: Final[str] = "LLM_PROVIDER_ENCRYPTION_KEY"


def _get_fernet():
    key = os.getenv(_ENCRYPTION_KEY_ENV, settings.SECRET_KEY)
    if not key:
        raise RuntimeError("Encryption key is not configured")

    if not isinstance(key, str):
        raise RuntimeError("Encryption key must be a string")

    if Fernet is not None:
        key_bytes = hashlib.sha256(key.encode("utf-8")).digest()
        return Fernet(base64.urlsafe_b64encode(key_bytes))

    raise RuntimeError("cryptography package is required for API key encryption")


def encrypt_api_key(api_key: str) -> str:
    if not api_key or not api_key.strip():
        raise ValueError("API key cannot be empty")
    return _get_fernet().encrypt(api_key.encode("utf-8")).decode("utf-8")


def decrypt_api_key(encrypted_api_key: str) -> str:
    if not encrypted_api_key:
        raise ValueError("Encrypted API key is missing")
    return _get_fernet().decrypt(encrypted_api_key.encode("utf-8")).decode("utf-8")
