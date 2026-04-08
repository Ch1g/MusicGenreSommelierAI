import hashlib
import hmac
from sqlmodel import Session, select

from music_genre_sommelier.models import User


PASSWORD_SECRET_KEY = "music-sommelier-secret-2026"


class AuthError(Exception):
    status_code: int

class ValidationError(AuthError):
    status_code = 422

class EmailAlreadyExistsError(AuthError):
    status_code = 409

class AuthenticationError(AuthError):
    status_code = 401


class RegistrationService:
    def __init__(self, session: Session):
        self.session = session

    def register(self, email: str, username: str, password: str) -> User:
        self._validate_credentials(email, password)

        if self._email_exists(email):
            raise EmailAlreadyExistsError(f"Email '{email}' is already registered")

        encrypted_password = self._encrypt_password(password)

        user = User(
            email=email,
            username=username,
            encrypted_password=encrypted_password,
        )

        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)

        return user

    def verify_password(self, email: str, password: str) -> User:
        user = self._get_user_by_email(email)
        if user is None:
            raise AuthenticationError("Invalid email or password")

        encrypted_password = self._encrypt_password(password)

        if hmac.compare_digest(user.encrypted_password, encrypted_password) is False:
            raise AuthenticationError("Invalid email or password")

        return user

    def _validate_credentials(self, email: str, password: str) -> None:
        if not email or not isinstance(email, str):
            raise ValidationError("Email is required")

        if "@" not in email or "." not in email:
            raise ValidationError("Invalid email format")

        if not password or not isinstance(password, str):
            raise ValidationError("Password is required")

        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters")

    def _email_exists(self, email: str) -> bool:
        return self._get_user_by_email(email) is not None

    def _get_user_by_email(self, email: str) -> User | None:
        query = select(User).where(User.email == email)
        return self.session.exec(query).first()

    @staticmethod
    def _encrypt_password(password: str) -> str:
        return hmac.new(
            PASSWORD_SECRET_KEY.encode("utf-8"),
            password.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
