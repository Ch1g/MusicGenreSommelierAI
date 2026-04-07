from sqlmodel import Session, SQLModel, select

from music_genre_sommelier.ml_model import MLModel
from music_genre_sommelier.user import User
from music_genre_sommelier.utils.database.db import engine

_SEED_ADMIN_EMAIL = "admin@example.com"
_SEED_USER_EMAIL = "user@example.com"
_SEED_DEFAULT_MODEL_PATH = "/models/default"


def _import_all_models() -> None:
    import music_genre_sommelier.audio_file
    import music_genre_sommelier.audio_spectrogram
    import music_genre_sommelier.ml_model
    import music_genre_sommelier.ml_task
    import music_genre_sommelier.spectrogram_file
    import music_genre_sommelier.transaction
    import music_genre_sommelier.admin_user
    import music_genre_sommelier.common_user


def create_tables() -> None:
    _import_all_models()
    SQLModel.metadata.create_all(engine)

def seed_admin_user_with_session(session: Session) -> None:
    if session.exec(select(AdminUser).where(AdminUser.email == _SEED_ADMIN_EMAIL)).first() is None:
        session.add(
            AdminUser(
                email=_SEED_ADMIN_EMAIL,
                username="admin",
                encrypted_password="not-set",
            )
        )

def seed_common_user_with_session(session: Session) -> None:
    if session.exec(select(CommonUser).where(CommonUser.email == _SEED_USER_EMAIL)).first() is None:
        session.add(
            CommonUser(
                email=_SEED_USER_EMAIL,
                username="user",
                encrypted_password="not-set",
            )
        )

def seed_transactions_for_user_with_session(session: Session, user: User) -> None:
    if session.exec(select(Transaction).where(Transaction.user_id == user.id)).first() is None:
        session.add(
            Transaction(
                user_id=user.id,
                amount=100.0,
            )
        )

def seed_database() -> None:
    with Session(engine) as session:
        if session.exec(select(User).where(User.email == _SEED_ADMIN_EMAIL)).first() is None:
            session.add(
                User(
                    email=_SEED_ADMIN_EMAIL,
                    username="admin",
                    encrypted_password="not-set",
                    is_admin=True,
                )
            )
        if session.exec(select(User).where(User.email == _SEED_USER_EMAIL)).first() is None:
            session.add(
                User(
                    email=_SEED_USER_EMAIL,
                    username="user",
                    encrypted_password="not-set",
                    is_admin=False,
                )
            )
        if (
            session.exec(select(MLModel).where(MLModel.model_path == _SEED_DEFAULT_MODEL_PATH)).first()
            is None
        ):
            session.add(
                MLModel(
                    model_path=_SEED_DEFAULT_MODEL_PATH,
                    prediction_cost=1.0,
                )
            )
        session.commit()


def run() -> None:
    create_tables()
    seed_database()


if __name__ == "__main__":
    run()
