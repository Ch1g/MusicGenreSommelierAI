import pytest
import numpy as np
from unittest.mock import patch
from sqlmodel import Session, select

from music_genre_sommelier.models.audio_file import AudioFile
from music_genre_sommelier.models.audio_spectrogram import AudioSpectrogram
from music_genre_sommelier.models.user import User
from music_genre_sommelier.services.audio_spectrogram_service import AudioSpectrogramService
from music_genre_sommelier.services.storage_service import StorageService
from music_genre_sommelier.utils.enum.common import CommonStatus


def _seed_audio_file(session: Session) -> AudioFile:
    user = User(email="spec@test.com", username="specuser", encrypted_password="h")
    session.add(user)
    session.commit()
    session.refresh(user)
    af = AudioFile(user_id=user.id, file_path="/fake/audio.wav")
    session.add(af)
    session.commit()
    session.refresh(af)
    return af


def test_segment_audio_pads_short_audio():
    sr = 22050
    short = np.zeros(int(sr * 10))
    result = AudioSpectrogramService._segment_audio(short, sr)
    assert len(result) == int(30 * sr)


def test_segment_audio_trims_long_audio():
    sr = 22050
    long_ = np.zeros(int(sr * 60))
    result = AudioSpectrogramService._segment_audio(long_, sr)
    assert len(result) == int(30 * sr)


def test_convert_success_with_image(test_session: Session, tmp_path):
    af = _seed_audio_file(test_session)
    storage = StorageService(base_path=tmp_path)
    svc = AudioSpectrogramService(session=test_session, storage_service=storage)
    fake_path = tmp_path / "spectrograms" / "audio_mel_spectrogram.png"

    with patch.object(svc, "_perform_conversion", return_value=(np.zeros((128, 100)), fake_path)):
        result = svc.convert(af, save_image=True)

    assert result is not None
    audio_spec = test_session.exec(select(AudioSpectrogram)).first()
    assert audio_spec is not None
    assert audio_spec.status == CommonStatus.SUCCESS
    assert audio_spec.spectrogram_file_id is not None


def test_convert_success_without_image(test_session: Session, tmp_path):
    af = _seed_audio_file(test_session)
    storage = StorageService(base_path=tmp_path)
    svc = AudioSpectrogramService(session=test_session, storage_service=storage)

    with patch.object(svc, "_perform_conversion", return_value=(np.zeros((128, 100)), None)):
        result = svc.convert(af, save_image=False)

    assert result is not None
    audio_spec = test_session.exec(select(AudioSpectrogram)).first()
    assert audio_spec is not None
    assert audio_spec.status == CommonStatus.SUCCESS
    assert audio_spec.spectrogram_file_id is None


def test_convert_failure_records_error_and_reraises(test_session: Session, tmp_path):
    af = _seed_audio_file(test_session)
    storage = StorageService(base_path=tmp_path)
    svc = AudioSpectrogramService(session=test_session, storage_service=storage)

    with patch.object(svc, "_perform_conversion", side_effect=RuntimeError("bad audio")):
        with pytest.raises(RuntimeError, match="bad audio"):
            svc.convert(af)

    audio_spec = test_session.exec(select(AudioSpectrogram)).first()
    assert audio_spec is not None
    assert audio_spec.status == CommonStatus.FAILURE
    assert audio_spec.error is not None and "bad audio" in audio_spec.error
