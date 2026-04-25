from sqlmodel import Session

from music_genre_sommelier.models.audio_file import AudioFile
from music_genre_sommelier.models.user import User


def _seed_user(session: Session) -> User:
    user = User(email="af@example.com", username="afuser", encrypted_password="h")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def test_create_audio_file(test_session: Session):
    user = _seed_user(test_session)
    af = AudioFile(user_id=user.id, file_path="/uploads/audio.wav")
    test_session.add(af)
    test_session.commit()
    test_session.refresh(af)

    assert af.id is not None
    assert af.user_id == user.id
    assert af.file_path == "/uploads/audio.wav"
