from datetime import datetime, timedelta, timezone

import jwt as pyjwt
import pytest

from music_genre_sommelier.utils.auth.jwt import (
    _ALGORITHM,
    _secret,
    create_token,
    verify_token,
)
from music_genre_sommelier.utils.errors.errors import AuthenticationError


def test_create_and_verify_roundtrip():
    token = create_token(user_id=42)
    claims = verify_token(token)

    assert claims["sub"] == "42"
    assert "exp" in claims
    assert "iat" in claims


def test_expired_token_raises():
    past = datetime.now(tz=timezone.utc) - timedelta(seconds=1)
    payload = {"sub": "1", "exp": past}
    token = pyjwt.encode(payload, _secret(), algorithm=_ALGORITHM)

    with pytest.raises(AuthenticationError) as exc_info:
        verify_token(token)

    assert exc_info.value.status_code == 401


def test_invalid_token_raises():
    with pytest.raises(AuthenticationError) as exc_info:
        verify_token("not-a-real-token")

    assert exc_info.value.status_code == 401


def test_token_signed_with_different_secret_raises():
    payload = {
        "sub": "1",
        "exp": datetime.now(tz=timezone.utc) + timedelta(hours=1),
    }
    bad_token = pyjwt.encode(payload, "some-other-secret", algorithm=_ALGORITHM)

    with pytest.raises(AuthenticationError):
        verify_token(bad_token)
