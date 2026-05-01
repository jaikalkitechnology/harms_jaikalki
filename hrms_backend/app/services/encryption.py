"""AES-GCM-256 field-level encryption for the Justice Portal.

Public surface:
- `encrypt(plaintext) -> str` returns a base64-url ciphertext that bundles
  a random 12-byte nonce + 16-byte tag + ciphertext.
- `decrypt(ciphertext) -> str` reverses it.
- `is_encrypted(value) -> bool` cheap heuristic.

The key comes from `settings.JUSTICE_ENCRYPTION_KEY` (base64 of 32 bytes).
If unset, a key is derived deterministically from `JWT_SECRET_KEY` via
HKDF-SHA256 — adequate for dev. Production must set the env var.
"""
from __future__ import annotations

import base64
import os
from functools import lru_cache
from typing import Optional

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from app.config import settings


_PREFIX = "v1:"  # version prefix to allow future key/algorithm rotation


@lru_cache
def _key() -> bytes:
    raw = settings.JUSTICE_ENCRYPTION_KEY
    if raw:
        try:
            key = base64.urlsafe_b64decode(raw.encode())
        except Exception as exc:
            raise RuntimeError(
                "JUSTICE_ENCRYPTION_KEY must be base64url of 32 raw bytes"
            ) from exc
        if len(key) != 32:
            raise RuntimeError(
                f"JUSTICE_ENCRYPTION_KEY must be 32 bytes; got {len(key)}"
            )
        return key
    # Dev-only fallback: derive from JWT secret. Production should never hit this.
    seed = settings.JWT_SECRET_KEY.encode()
    return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"jaikalki-justice-v1",
        info=b"justice-portal-aes-gcm-256",
    ).derive(seed)


def encrypt(plaintext: Optional[str]) -> Optional[str]:
    if plaintext is None:
        return None
    if not isinstance(plaintext, str):
        plaintext = str(plaintext)
    if not plaintext:
        return ""
    nonce = os.urandom(12)
    cipher = AESGCM(_key())
    ct = cipher.encrypt(nonce, plaintext.encode("utf-8"), associated_data=None)
    blob = nonce + ct
    return _PREFIX + base64.urlsafe_b64encode(blob).decode("ascii")


def decrypt(ciphertext: Optional[str]) -> Optional[str]:
    if ciphertext is None:
        return None
    if not ciphertext:
        return ""
    if not ciphertext.startswith(_PREFIX):
        # Already plaintext (e.g. legacy seed data) — return unchanged.
        return ciphertext
    blob = base64.urlsafe_b64decode(ciphertext[len(_PREFIX):].encode())
    nonce, ct = blob[:12], blob[12:]
    cipher = AESGCM(_key())
    return cipher.decrypt(nonce, ct, associated_data=None).decode("utf-8")


def is_encrypted(value: Optional[str]) -> bool:
    return bool(value) and value.startswith(_PREFIX)
