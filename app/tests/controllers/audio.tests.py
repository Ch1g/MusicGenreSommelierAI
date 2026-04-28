from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlmodel import Session

from music_genre_sommelier.models.audio_file import AudioFile
from music_genre_sommelier.models.audio_spectrogram import AudioSpectrogram
from music_genre_sommelier.models.user import User


def _seed_user(session: Session) -> User:
    user = User(email="audio@test.com", username="audiouser", encrypted_password="h")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def _seed_audio_file(session: Session, user_id: int, file_path: str = "/fake/audio.wav") -> AudioFile:
    af = AudioFile(user_id=user_id, file_path=file_path)
    session.add(af)
    session.commit()
    session.refresh(af)
    return af


# POST /{user_id}

def test_upload_audio_201(client: TestClient, test_session: Session):
    _seed_user(test_session)
    with patch("music_genre_sommelier.controllers.audio.StorageService") as MockStorage:
        MockStorage.return_value.store.return_value = Path("/fake/audio.wav")
        resp = client.post(
            "/api/audio/1",
            files={"file": ("test.wav", b"fake audio content", "audio/wav")},
        )
    assert resp.status_code == 201
    assert resp.json()["file_path"] == "/fake/audio.wav"


def test_upload_audio_403_other_user(client: TestClient):
    resp = client.post(
        "/api/audio/2",
        files={"file": ("test.wav", b"audio", "audio/wav")},
    )
    assert resp.status_code == 403


def test_upload_audio_404_user_not_found(client: TestClient):
    resp = client.post(
        "/api/audio/1",
        files={"file": ("test.wav", b"audio content", "audio/wav")},
    )
    assert resp.status_code == 404


def test_upload_audio_422_wrong_content_type(client: TestClient):
    resp = client.post(
        "/api/audio/1",
        files={"file": ("test.txt", b"not audio", "text/plain")},
    )
    assert resp.status_code == 422


def test_upload_audio_422_empty_file(client: TestClient):
    resp = client.post(
        "/api/audio/1",
        files={"file": ("test.wav", b"", "audio/wav")},
    )
    assert resp.status_code == 422


# GET /{user_id}


def test_list_audios_200(client: TestClient, test_session: Session):
    user = _seed_user(test_session)
    _seed_audio_file(test_session, user.id, "/fake/a.wav")
    _seed_audio_file(test_session, user.id, "/fake/b.wav")

    resp = client.get("/api/audio/1")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_audios_403_other_user(client: TestClient):
    resp = client.get("/api/audio/2")
    assert resp.status_code == 403


def test_list_audios_404_user_not_found(client: TestClient):
    resp = client.get("/api/audio/1")
    assert resp.status_code == 404


# DELETE /files/{audio_id}

def test_delete_audio_204(client: TestClient, test_session: Session):
    user = _seed_user(test_session)
    af = _seed_audio_file(test_session, user.id)
    with patch("music_genre_sommelier.controllers.audio.StorageService"):
        resp = client.delete(f"/api/audio/files/{af.id}")
    assert resp.status_code == 204


def test_delete_audio_403_other_user(client: TestClient, test_session: Session):
    af = _seed_audio_file(test_session, user_id=2)
    resp = client.delete(f"/api/audio/files/{af.id}")
    assert resp.status_code == 403


def test_delete_audio_404_not_found(client: TestClient):
    resp = client.delete("/api/audio/files/999")
    assert resp.status_code == 404


def test_delete_audio_422_has_spectrograms(client: TestClient, test_session: Session):
    user = _seed_user(test_session)
    af = _seed_audio_file(test_session, user.id)
    test_session.add(AudioSpectrogram(audio_file_id=af.id))
    test_session.commit()

    resp = client.delete(f"/api/audio/files/{af.id}")
    assert resp.status_code == 422


# GET /files/{audio_id}/stream

def test_stream_audio_200(client: TestClient, test_session: Session, tmp_path):
    user = _seed_user(test_session)
    audio_file = tmp_path / "test.wav"
    audio_file.write_bytes(b"fake audio data")
    af = _seed_audio_file(test_session, user.id, str(audio_file))

    resp = client.get(f"/api/audio/files/{af.id}/stream")
    assert resp.status_code == 200


def test_stream_audio_403_other_user(client: TestClient, test_session: Session, tmp_path):
    audio_file = tmp_path / "test.wav"
    audio_file.write_bytes(b"fake audio data")
    af = _seed_audio_file(test_session, user_id=2, file_path=str(audio_file))

    resp = client.get(f"/api/audio/files/{af.id}/stream")
    assert resp.status_code == 403


def test_stream_audio_404_not_found(client: TestClient):
    resp = client.get("/api/audio/files/999/stream")
    assert resp.status_code == 404
