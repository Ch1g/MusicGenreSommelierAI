import os

from sqlmodel import create_engine


def _database_url() -> str:
    user = os.environ.get("POSTGRES_USER")
    password = os.environ.get("POSTGRES_PASSWORD")
    db = os.environ.get("POSTGRES_DB")
    host = os.environ.get("POSTGRES_HOST")
    port = os.environ.get("POSTGRES_PORT", "5432")

    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}"


engine = create_engine(_database_url(), echo=False)
