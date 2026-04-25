import os

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

os.environ.setdefault("JWT_SECRET", "test-secret-for-unit-tests-only-not-for-production-use")


@pytest.fixture
def test_engine():
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(test_engine)
    yield test_engine
    test_engine.dispose()


@pytest.fixture
def test_session(test_engine) -> Generator[Session, None, None]:
    with Session(test_engine) as session:
        yield session


@pytest.fixture
def client(test_engine) -> Generator[TestClient, None, None]:
    from music_genre_sommelier.controllers.main import app
    from music_genre_sommelier.utils.database.db import get_session
    from music_genre_sommelier.utils.auth import get_current_user_id

    def get_session_override() -> Generator[Session, None, None]:
        with Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[get_current_user_id] = lambda: 1
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
