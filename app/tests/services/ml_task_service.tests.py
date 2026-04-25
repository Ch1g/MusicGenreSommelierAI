import pytest
from unittest.mock import patch
from sqlmodel import Session

from music_genre_sommelier.models.audio_file import AudioFile
from music_genre_sommelier.models.audio_spectrogram import AudioSpectrogram
from music_genre_sommelier.models.ml_model import MLModel
from music_genre_sommelier.models.ml_task import MLTask
from music_genre_sommelier.models.spectrogram_file import SpectrogramFile
from music_genre_sommelier.models.transaction import Transaction
from music_genre_sommelier.models.user import User
from music_genre_sommelier.services.ml_task_service import MLTaskService
from music_genre_sommelier.utils.enum.common import CommonStatus
from music_genre_sommelier.utils.enum.transaction import TransactionStatus
from music_genre_sommelier.utils.errors.errors import NotFoundError


def _seed_ml_task(session: Session) -> MLTask:
    user = User(email="ml@test.com", username="mluser", encrypted_password="h")
    session.add(user)
    session.commit()
    session.refresh(user)

    tx = Transaction(user_id=user.id, amount=-1.0)
    session.add(tx)
    session.commit()
    session.refresh(tx)

    af = AudioFile(user_id=user.id, file_path="/uploads/test.wav")
    session.add(af)
    session.commit()
    session.refresh(af)

    sf = SpectrogramFile(file_path="/spectrograms/test.png")
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

    task = MLTask(
        audio_spectrogram_id=audio_spec.id,
        transaction_id=tx.id,
        ml_model_id=ml_model.id,
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def test_process_success(test_session: Session):
    task = _seed_ml_task(test_session)
    svc = MLTaskService(session=test_session)
    prediction = {"label": "jazz", "score": 0.95}

    with patch("music_genre_sommelier.models.transaction.Transaction.get_balance", return_value=100.0), \
         patch.object(svc, "_perform_prediction", return_value=prediction):
        result = svc.process(task.id)

    assert result == prediction
    test_session.refresh(task)
    assert task.status == CommonStatus.SUCCESS
    assert task.result == prediction
    assert task.transaction.status == TransactionStatus.SUCCESS


def test_process_insufficient_funds(test_session: Session):
    task = _seed_ml_task(test_session)
    svc = MLTaskService(session=test_session)

    with patch("music_genre_sommelier.models.transaction.Transaction.get_balance", return_value=0.0):
        result = svc.process(task.id)

    assert result is None
    test_session.refresh(task)
    assert task.status == CommonStatus.FAILURE
    assert task.transaction.status == TransactionStatus.FAIL_INSUFFICIENT_FUNDS


def test_process_generic_error(test_session: Session):
    task = _seed_ml_task(test_session)
    svc = MLTaskService(session=test_session)

    with patch("music_genre_sommelier.models.transaction.Transaction.get_balance", return_value=100.0), \
         patch.object(svc, "_perform_prediction", side_effect=RuntimeError("model crash")):
        result = svc.process(task.id)

    assert result is None
    test_session.refresh(task)
    assert task.status == CommonStatus.FAILURE
    assert task.transaction.status == TransactionStatus.FAIL_CANCELED


def test_process_raises_not_found(test_session: Session):
    svc = MLTaskService(session=test_session)
    with pytest.raises(NotFoundError):
        svc.process(999)
