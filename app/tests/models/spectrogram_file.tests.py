from sqlmodel import Session

from music_genre_sommelier.models.spectrogram_file import SpectrogramFile


def test_create_spectrogram_file(test_session: Session):
    sf = SpectrogramFile(file_path="/tmp/spec.png")
    test_session.add(sf)
    test_session.commit()
    test_session.refresh(sf)

    assert sf.id is not None
    assert sf.file_path == "/tmp/spec.png"
