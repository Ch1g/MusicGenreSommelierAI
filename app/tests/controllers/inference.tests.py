from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlmodel import Session

from music_genre_sommelier.models.audio_file import AudioFile
from music_genre_sommelier.models.audio_spectrogram import AudioSpectrogram
from music_genre_sommelier.models.ml_model import MLModel
from music_genre_sommelier.models.ml_task import MLTask
from music_genre_sommelier.models.spectrogram_file import SpectrogramFile
from music_genre_sommelier.models.transaction import Transaction
from music_genre_sommelier.models.user import User
from music_genre_sommelier.utils.enum.common import CommonStatus


def _seed_user(session: Session) -> User:
    user = User(email="inf@test.com", username="infuser", encrypted_password="h")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def _seed_inference_prereqs(session: Session, user: User, spec_image_path: str):
    af = AudioFile(user_id=user.id, file_path="/uploads/test.wav")
    session.add(af)
    session.commit()
    session.refresh(af)

    sf = SpectrogramFile(file_path=spec_image_path)
    session.add(sf)
    session.commit()
    session.refresh(sf)

    audio_spec = AudioSpectrogram(
        audio_file_id=af.id,
        spectrogram_file_id=sf.id,
        status=CommonStatus.SUCCESS,
    )
    session.add(audio_spec)
    session.commit()
    session.refresh(audio_spec)

    ml_model = MLModel(model_path="/models/resnet.pt", prediction_cost=1.0)
    session.add(ml_model)
    session.commit()
    session.refresh(ml_model)

    return af, audio_spec, ml_model


# POST /

def test_run_inference_201(client: TestClient, test_session: Session, tmp_path):
    user = _seed_user(test_session)
    spec_img = tmp_path / "spec.png"
    spec_img.write_bytes(b"fake png")
    af, _, ml_model = _seed_inference_prereqs(test_session, user, str(spec_img))

    with patch("music_genre_sommelier.controllers.inference.InferencePublisher") as MockPub:
        resp = client.post("/api/inference/", json={
            "audio_file_id": af.id,
            "ml_model_id": ml_model.id,
        })

    assert resp.status_code == 201
    task_id = resp.json()["id"]
    MockPub.return_value.publish.assert_called_once_with({"ml_task_id": task_id})


def test_run_inference_403_other_users_audio(client: TestClient, test_session: Session):
    af = AudioFile(user_id=2, file_path="/uploads/other.wav")
    test_session.add(af)
    test_session.commit()
    test_session.refresh(af)

    resp = client.post("/api/inference/", json={"audio_file_id": af.id, "ml_model_id": 1})
    assert resp.status_code == 403


def test_run_inference_404_audio_not_found(client: TestClient):
    resp = client.post("/api/inference/", json={"audio_file_id": 999, "ml_model_id": 1})
    assert resp.status_code == 404


def test_run_inference_404_ml_model_not_found(client: TestClient, test_session: Session):
    user = _seed_user(test_session)
    af = AudioFile(user_id=user.id, file_path="/uploads/test.wav")
    test_session.add(af)
    test_session.commit()
    test_session.refresh(af)

    resp = client.post("/api/inference/", json={"audio_file_id": af.id, "ml_model_id": 999})
    assert resp.status_code == 404


def test_run_inference_422_conversion_failed(client: TestClient, test_session: Session):
    user = _seed_user(test_session)
    af = AudioFile(user_id=user.id, file_path="/uploads/test.wav")
    test_session.add(af)
    test_session.commit()
    test_session.refresh(af)

    ml_model = MLModel(model_path="/models/resnet.pt", prediction_cost=1.0)
    test_session.add(ml_model)
    test_session.commit()
    test_session.refresh(ml_model)

    with patch("music_genre_sommelier.controllers.inference.AudioSpectrogramService"), \
         patch("music_genre_sommelier.controllers.inference.StorageService"):
        resp = client.post("/api/inference/", json={
            "audio_file_id": af.id,
            "ml_model_id": ml_model.id,
        })

    assert resp.status_code == 422


# GET /{user_id}

def test_list_tasks_200(client: TestClient, test_session: Session):
    _seed_user(test_session)
    resp = client.get("/api/inference/1")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_tasks_403_other_user(client: TestClient):
    resp = client.get("/api/inference/2")
    assert resp.status_code == 403


def test_list_tasks_404_user_not_found(client: TestClient):
    resp = client.get("/api/inference/1")
    assert resp.status_code == 404


# GET /spectrograms/{task_id}

def test_get_spectrogram_200(client: TestClient, test_session: Session, tmp_path):
    user = _seed_user(test_session)
    spec_img = tmp_path / "spec.png"
    spec_img.write_bytes(b"fake png data")
    _, audio_spec, ml_model = _seed_inference_prereqs(test_session, user, str(spec_img))

    tx = Transaction(user_id=user.id, amount=-1.0)
    test_session.add(tx)
    test_session.commit()
    test_session.refresh(tx)

    task = MLTask(
        audio_spectrogram_id=audio_spec.id,
        transaction_id=tx.id,
        ml_model_id=ml_model.id,
    )
    test_session.add(task)
    test_session.commit()
    test_session.refresh(task)

    resp = client.get(f"/api/inference/spectrograms/{task.id}")
    assert resp.status_code == 200


def test_get_spectrogram_403_other_user(client: TestClient, test_session: Session):
    tx = Transaction(user_id=2, amount=-1.0)
    test_session.add(tx)
    test_session.commit()
    test_session.refresh(tx)

    audio_spec = AudioSpectrogram(audio_file_id=999)
    test_session.add(audio_spec)
    test_session.commit()
    test_session.refresh(audio_spec)

    task = MLTask(audio_spectrogram_id=audio_spec.id, transaction_id=tx.id, ml_model_id=999)
    test_session.add(task)
    test_session.commit()
    test_session.refresh(task)

    resp = client.get(f"/api/inference/spectrograms/{task.id}")
    assert resp.status_code == 403


def test_get_spectrogram_404_task_not_found(client: TestClient):
    resp = client.get("/api/inference/spectrograms/999")
    assert resp.status_code == 404


def test_get_spectrogram_404_no_spectrogram_file(client: TestClient, test_session: Session):
    tx = Transaction(user_id=1, amount=-1.0)
    test_session.add(tx)
    test_session.commit()
    test_session.refresh(tx)

    audio_spec = AudioSpectrogram(audio_file_id=999)
    test_session.add(audio_spec)
    test_session.commit()
    test_session.refresh(audio_spec)

    task = MLTask(audio_spectrogram_id=audio_spec.id, transaction_id=tx.id, ml_model_id=999)
    test_session.add(task)
    test_session.commit()
    test_session.refresh(task)

    resp = client.get(f"/api/inference/spectrograms/{task.id}")
    assert resp.status_code == 404
