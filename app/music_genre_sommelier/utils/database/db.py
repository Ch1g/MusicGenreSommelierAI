import os
from collections.abc import Generator

from sqlmodel import Session, create_engine


def _database_url() -> str:
    user = os.environ.get("POSTGRES_USER")
    password = os.environ.get("POSTGRES_PASSWORD")
    db = os.environ.get("POSTGRES_DB")
    host = os.environ.get("POSTGRES_HOST")
    port = os.environ.get("POSTGRES_PORT", "5432")

    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}"


engine = create_engine(_database_url(), echo=False)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
