from fastapi import Header

from music_genre_sommelier.utils.auth.jwt import verify_token
from music_genre_sommelier.utils.errors.errors import AuthenticationError


def get_current_user_id(
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> int:
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthenticationError("Missing or malformed Authorization header")

    token = authorization[len("Bearer "):].strip()
    if not token:
        raise AuthenticationError("Missing bearer token")

    claims = verify_token(token)

    try:
        return int(claims["sub"])
    except (KeyError, TypeError, ValueError) as exc:
        raise AuthenticationError("Invalid token subject") from exc
