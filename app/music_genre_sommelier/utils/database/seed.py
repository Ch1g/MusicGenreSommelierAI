from sqlmodel import Session, SQLModel, select

from music_genre_sommelier.models.admin_user import AdminUser
from music_genre_sommelier.models.common_user import CommonUser
from music_genre_sommelier.models.ml_model import MLModel
from music_genre_sommelier.models.transaction import Transaction
from music_genre_sommelier.models.user import User
from music_genre_sommelier.services.registration_service import RegistrationService
from music_genre_sommelier.utils.database.db import engine
from music_genre_sommelier.utils.enum.transaction import TransactionStatus

_SEED_ADMIN_EMAIL = "admin@example.com"
_SEED_COMMON_EMAIL = "user@example.com"
_SEED_ADMIN_PASSWORD = "admin-123"
_SEED_COMMON_PASSWORD = "common-123"
_SEED_DEFAULT_MODEL_PATH = "google/vit-base-patch16-224"


def create_tables() -> None:
    SQLModel.metadata.create_all(engine)

def seed_admin_user_with_session(session: Session) -> None:
    if session.exec(select(User).where(User.email == _SEED_ADMIN_EMAIL)).first() is None:
        session.add(
            User(
                email=_SEED_ADMIN_EMAIL,
                username="admin",
                encrypted_password=RegistrationService._encrypt_password(_SEED_ADMIN_PASSWORD),
                is_admin=False
            )
        )

def seed_common_user_with_session(session: Session) -> None:
    if session.exec(select(User).where(User.email == _SEED_COMMON_EMAIL)).first() is None:
        session.add(
            User(
                email=_SEED_COMMON_EMAIL,
                username="user",
                encrypted_password=RegistrationService._encrypt_password(_SEED_COMMON_PASSWORD),
                is_admin=True
            )
        )

def seed_transactions_for_user_with_session(session: Session, user: User) -> None:
    if session.exec(select(Transaction).where(Transaction.user_id == user.id)).first() is None:
        # Пополнение
        session.add(
            Transaction(
                user_id=user.id,
                amount=100.0,
                status=TransactionStatus.SUCCESS
            )
        )
        # Пополнение в процессе
        session.add(
            Transaction(
                user_id=user.id,
                amount=100.0,
                status=TransactionStatus.PENDING
            )
        )
        # Трата в процессе
        session.add(
            Transaction(
                user_id=user.id,
                amount=-15,
                status=TransactionStatus.PENDING
            )
        )
        # Трата
        session.add(
            Transaction(
                user_id=user.id,
                amount=-15,
                status=TransactionStatus.SUCCESS
            )
        )
        # Трата: отмена
        session.add(
            Transaction(
                user_id=user.id,
                amount=-15,
                status=TransactionStatus.FAIL_CANCELED
            )
        )
        # Трата: нехватка средств
        session.add(
            Transaction(
                user_id=user.id,
                amount=-15,
                status=TransactionStatus.FAIL_INSUFFICIENT_FUNDS
            )
        )

def seed_ml_model_with_session(session) -> None:
    if (
        session.exec(select(MLModel).where(MLModel.model_path == _SEED_DEFAULT_MODEL_PATH)).first()
        is None
    ):
        session.add(
            MLModel(
                model_path=_SEED_DEFAULT_MODEL_PATH,
                prediction_cost=15.0,
            )
        )

def seed_database() -> None:
    with Session(engine) as session:
        seed_admin_user_with_session(session)
        admin = session.exec(select(User).where(User.email == _SEED_ADMIN_EMAIL)).one()
        seed_transactions_for_user_with_session(session, admin)

        seed_common_user_with_session(session)
        common = session.exec(select(User).where(User.email == _SEED_COMMON_EMAIL)).one()
        seed_transactions_for_user_with_session(session, common)

        seed_ml_model_with_session(session)

        session.commit()


def run() -> None:
    create_tables()
    seed_database()
    print("Seeds done.")
