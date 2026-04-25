import pytest
from sqlmodel import Session

from music_genre_sommelier.services.registration_service import RegistrationService
from music_genre_sommelier.utils.errors.errors import AuthenticationError, EmailAlreadyExistsError, ValidationError


def test_register_creates_user(test_session: Session):
    svc = RegistrationService(session=test_session)
    user = svc.register("new@test.com", "newuser", "password123")
    assert user.id is not None
    assert user.email == "new@test.com"


def test_register_raises_on_duplicate_email(test_session: Session):
    svc = RegistrationService(session=test_session)
    svc.register("dup@test.com", "user1", "password123")
    with pytest.raises(EmailAlreadyExistsError):
        svc.register("dup@test.com", "user2", "password123")


def test_register_raises_on_invalid_email(test_session: Session):
    svc = RegistrationService(session=test_session)
    with pytest.raises(ValidationError):
        svc.register("not-an-email", "u", "password123")


def test_register_raises_on_short_password(test_session: Session):
    svc = RegistrationService(session=test_session)
    with pytest.raises(ValidationError):
        svc.register("ok@test.com", "u", "short")


def test_verify_password_returns_user(test_session: Session):
    svc = RegistrationService(session=test_session)
    svc.register("login@test.com", "u", "password123")
    user = svc.verify_password("login@test.com", "password123")
    assert user.email == "login@test.com"


def test_verify_password_raises_on_wrong_password(test_session: Session):
    svc = RegistrationService(session=test_session)
    svc.register("wp@test.com", "u", "password123")
    with pytest.raises(AuthenticationError):
        svc.verify_password("wp@test.com", "wrongpassword")


def test_verify_password_raises_on_unknown_email(test_session: Session):
    svc = RegistrationService(session=test_session)
    with pytest.raises(AuthenticationError):
        svc.verify_password("nobody@test.com", "password123")
