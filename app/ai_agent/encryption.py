from cryptography.fernet import Fernet

from app.config import settings


def _get_fernet() -> Fernet:
    # `Settings` defines the variable as `AI_AGENT_ENCRYPTION_KEY` (uppercase),
    # so read that attribute name here.
    key = getattr(settings, "AI_AGENT_ENCRYPTION_KEY", None)

    if not key:
        raise RuntimeError(
            "AI_AGENT_ENCRYPTION_KEY is not configured."
        )

    return Fernet(key)


def encrypt_api_token(api_token: str) -> str:
    fernet = _get_fernet()

    return fernet.encrypt(
        api_token.encode("utf-8")
    ).decode("utf-8")


def decrypt_api_token(encrypted_token: str) -> str:
    fernet = _get_fernet()

    return fernet.decrypt(
        encrypted_token.encode("utf-8")
    ).decode("utf-8")