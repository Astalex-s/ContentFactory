"""Fernet encryption for sensitive data (OAuth tokens)."""

import base64
import logging
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

log = logging.getLogger(__name__)


def _derive_key(secret: str, salt: bytes = b"contentfactory_oauth") -> bytes:
    """Derive a Fernet-compatible key from secret."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(secret.encode()))
    return key


def encrypt_token(plain: str, secret_key: str) -> str:
    """Encrypt token with Fernet. Returns base64 string."""
    if not plain:
        return ""
    if not secret_key:
        raise ValueError("OAUTH_SECRET_KEY is required for token encryption")
    key = _derive_key(secret_key)
    f = Fernet(key)
    return f.encrypt(plain.encode()).decode()


def decrypt_token(encrypted: str, secret_key: str) -> Optional[str]:
    """Decrypt token. Returns None on failure."""
    if not encrypted or not secret_key:
        return None
    try:
        key = _derive_key(secret_key)
        f = Fernet(key)
        return f.decrypt(encrypted.encode()).decode()
    except (InvalidToken, Exception) as e:
        log.warning("Token decryption failed: %s", e)
        return None
