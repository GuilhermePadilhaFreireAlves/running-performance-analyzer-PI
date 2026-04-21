from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

JWT_ALGORITHM = "HS256"
DEFAULT_TOKEN_TTL_MINUTES = 60
DEFAULT_SECRET_KEY = "dev-secret-change-me-in-production-please"


def hash_password(senha: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(senha.encode("utf-8"), salt).decode("utf-8")


def verify_password(senha: str, senha_hash: str) -> bool:
    return bcrypt.checkpw(senha.encode("utf-8"), senha_hash.encode("utf-8"))


def get_secret_key() -> str:
    return os.environ.get("SECRET_KEY", DEFAULT_SECRET_KEY)


def create_access_token(
    subject: str | int,
    expires_minutes: int = DEFAULT_TOKEN_TTL_MINUTES,
) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
    }
    return jwt.encode(payload, get_secret_key(), algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    decoded: dict[str, Any] = jwt.decode(
        token, get_secret_key(), algorithms=[JWT_ALGORITHM]
    )
    return decoded
