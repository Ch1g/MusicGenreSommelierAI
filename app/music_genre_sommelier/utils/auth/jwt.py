import os
from datetime import datetime, timedelta, timezone

import jwt

from music_genre_sommelier.utils.errors.errors import AuthenticationError

_ALGORITHM = "HS256"
_TOKEN_TTL = timedelta(hours=24)


def _secret() -> str:
    try:
        return os.environ["JWT_SECRET"]
    except KeyError as exc:
        raise RuntimeError(
            "JWT_SECRET environment variable is not set. "
            "Define it in .db.env (see .db.env.example)."
        ) from exc


def create_token(user_id: int) -> str:
    now = datetime.now(tz=timezone.utc)
    payload = {
        "sub": str(user_id),
        "exp": now + _TOKEN_TTL,
        "iat": now,
    }
    return jwt.encode(payload, _secret(), algorithm=_ALGORITHM)


def verify_token(token: str) -> dict:
    try:
        return jwt.decode(token, _secret(), algorithms=[_ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise AuthenticationError("Token has expired") from exc
    except jwt.InvalidTokenError as exc:
        raise AuthenticationError("Invalid token") from exc
