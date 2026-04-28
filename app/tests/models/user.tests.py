import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session
from unittest.mock import patch

from music_genre_sommelier.models.user import User


def _make_user(**kwargs) -> User:
    defaults = {
        "email": "test@example.com",
        "username": "testuser",
        "encrypted_password": "hashed",
    }
    return User(**{**defaults, **kwargs})


def test_create_user(test_session: Session):
    user = _make_user()
    test_session.add(user)
    test_session.commit()
    test_session.refresh(user)

    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.is_admin is False


def test_duplicate_email_raises(test_session: Session):
    test_session.add(_make_user(email="dup@example.com"))
    test_session.commit()

    test_session.add(_make_user(email="dup@example.com", username="other"))
    with pytest.raises(IntegrityError):
        test_session.commit()


def test_get_balance_admin():
    user = _make_user(is_admin=True)
    assert user.get_balance() == float("inf")


def test_get_balance_non_admin_delegates():
    user = _make_user(is_admin=False)
    user.id = 42

    with patch(
        "music_genre_sommelier.models.transaction.Transaction.get_balance",
        return_value=99.5,
    ) as mock_bal:
        result = user.get_balance()

    mock_bal.assert_called_once_with(42)
    assert result == 99.5
