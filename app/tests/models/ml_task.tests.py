from sqlmodel import Session

from music_genre_sommelier.models.audio_file import AudioFile
from music_genre_sommelier.models.audio_spectrogram import AudioSpectrogram
from music_genre_sommelier.models.ml_model import MLModel
from music_genre_sommelier.models.ml_task import MLTask
from music_genre_sommelier.models.spectrogram_file import SpectrogramFile
from music_genre_sommelier.models.transaction import Transaction
from music_genre_sommelier.models.user import User
from music_genre_sommelier.utils.enum.common import CommonStatus


def _seed_prerequisites(session: Session):
    user = User(email="ml@example.com", username="mluser", encrypted_password="h")
    session.add(user)
    session.commit()
    session.refresh(user)

    audio_file = AudioFile(user_id=user.id, file_path="/uploads/test.wav")
    session.add(audio_file)
    session.commit()
    session.refresh(audio_file)

    spec_file = SpectrogramFile(file_path="/tmp/spec.png")
    session.add(spec_file)
    session.commit()
    session.refresh(spec_file)

    audio_spec = AudioSpectrogram(
        audio_file_id=audio_file.id, spectrogram_file_id=spec_file.id
    )
    session.add(audio_spec)
    session.commit()
    session.refresh(audio_spec)

    ml_model = MLModel(model_path="/models/resnet.pt", prediction_cost=1.0)
    session.add(ml_model)
    session.commit()
    session.refresh(ml_model)

    tx = Transaction(user_id=user.id, amount=-1.0)
    session.add(tx)
    session.commit()
    session.refresh(tx)

    return audio_spec, tx, ml_model


def test_create_ml_task(test_session: Session):
    audio_spec, tx, ml_model = _seed_prerequisites(test_session)
    task = MLTask(
        audio_spectrogram_id=audio_spec.id,
        transaction_id=tx.id,
        ml_model_id=ml_model.id,
    )
    test_session.add(task)
    test_session.commit()
    test_session.refresh(task)

    assert task.id is not None
    assert task.status == CommonStatus.PENDING
    assert task.result is None
    assert task.error is None


def test_record_success():
    task = MLTask(audio_spectrogram_id=1, transaction_id=1, ml_model_id=1)
    task.record_success({"genre": "jazz", "confidence": 0.95})
    assert task.status == CommonStatus.SUCCESS
    assert task.result == {"genre": "jazz", "confidence": 0.95}


def test_record_failure():
    task = MLTask(audio_spectrogram_id=1, transaction_id=1, ml_model_id=1)
    task.record_failure("inference error")
    assert task.status == CommonStatus.FAILURE
    assert task.error == "inference error"
