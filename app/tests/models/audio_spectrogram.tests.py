from sqlmodel import Session

from music_genre_sommelier.models.audio_file import AudioFile
from music_genre_sommelier.models.audio_spectrogram import AudioSpectrogram
from music_genre_sommelier.models.user import User
from music_genre_sommelier.utils.enum.common import CommonStatus


def _seed_audio_file(session: Session) -> AudioFile:
    user = User(email="as@example.com", username="asuser", encrypted_password="h")
    session.add(user)
    session.commit()
    session.refresh(user)
    af = AudioFile(user_id=user.id, file_path="/uploads/test.wav")
    session.add(af)
    session.commit()
    session.refresh(af)
    return af


def test_create_audio_spectrogram(test_session: Session):
    audio_file = _seed_audio_file(test_session)
    spec = AudioSpectrogram(audio_file_id=audio_file.id)
    test_session.add(spec)
    test_session.commit()
    test_session.refresh(spec)

    assert spec.id is not None
    assert spec.status == CommonStatus.PENDING
    assert spec.error is None


def test_record_success():
    spec = AudioSpectrogram(audio_file_id=1)
    spec.record_success()
    assert spec.status == CommonStatus.SUCCESS


def test_record_failure():
    spec = AudioSpectrogram(audio_file_id=1)
    spec.record_failure("conversion failed")
    assert spec.status == CommonStatus.FAILURE
    assert spec.error == "conversion failed"
