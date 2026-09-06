"""Encrypted store for broker credentials.

Fernet symmetric encryption; the key lives in .encryption_key (gitignored) next
to this project. Trimmed from TradingBot/settings_manager.py — just the three
crypto helpers, nothing else.
"""
import base64
from pathlib import Path

from cryptography.fernet import Fernet

KEY_FILE = Path(__file__).resolve().parent.parent / ".encryption_key"


def _key() -> bytes:
    if KEY_FILE.exists():
        return KEY_FILE.read_bytes()
    k = Fernet.generate_key()
    KEY_FILE.write_bytes(k)
    print("New .encryption_key generated — keep it, back it up, never commit it.")
    return k


def encrypt(value: str) -> str:
    return base64.b64encode(Fernet(_key()).encrypt(value.encode())).decode()


def decrypt(value: str) -> str:
    if not value:
        return ""
    try:
        return Fernet(_key()).decrypt(base64.b64decode(value.encode())).decode()
    except Exception:
        return value  # not encrypted yet (first run / hand-edited) — treat as plain


if __name__ == "__main__":
    assert decrypt(encrypt("hunter2")) == "hunter2"
    assert decrypt("") == ""
    print("settings_store: round-trip OK")
