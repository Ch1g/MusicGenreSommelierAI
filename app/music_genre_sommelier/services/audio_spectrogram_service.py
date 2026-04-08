from io import BytesIO
from pathlib import Path
from typing import Tuple

import librosa
import librosa.display
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from numpy.typing import NDArray
from sqlmodel import Session

from music_genre_sommelier.models.audio_file import AudioFile
from music_genre_sommelier.models.audio_spectrogram import AudioSpectrogram
from music_genre_sommelier.models.spectrogram_file import SpectrogramFile
from music_genre_sommelier.services.storage_service import StorageDirectory, StorageService

matplotlib.use('Agg')


class AudioFileNotFoundError(Exception):
    pass


class AudioSpectrogramService:
    DEFAULT_SAMPLE_RATE = 22050
    DEFAULT_N_FFT = 2048
    DEFAULT_HOP_LENGTH = 512
    DEFAULT_N_MELS = 128
    
    def __init__(
        self,
        session: Session,
        storage_service: StorageService,
    ):
        self.session = session
        self.storage_service = storage_service

    def convert(
        self,
        audio_file: AudioFile,
        save_image: bool = True,
    ) -> NDArray[np.floating] | None:
        audio_spectrogram = AudioSpectrogram(audio_file_id=audio_file.id)

        try:
            spectrogram_data, output_path = self._perform_conversion(
                audio_file,
                save_image,
            )

            if output_path:
                spectrogram_file = SpectrogramFile(file_path=str(output_path))
                self.session.add(spectrogram_file)
                self.session.flush()
                audio_spectrogram.spectrogram_file_id = spectrogram_file.id

            audio_spectrogram.record_success()

            return spectrogram_data

        except Exception as e:
            audio_spectrogram.record_failure(str(e))
            raise
        finally:
            self.session.add(audio_spectrogram)
            self.session.commit()

    def _perform_conversion(
        self,
        audio_file: AudioFile,
        save_image: bool,
    ) -> Tuple[NDArray[np.floating], Path | None]:
        samples, sr = self._load_audio(audio_file.file_path)

        spectrogram = self._compute_mel(samples, sr)

        spectrogram_db = librosa.power_to_db(spectrogram, ref=np.max)

        output_path = None
        if save_image:
            output_path = self._save_spectrogram_image(
                spectrogram_db,
                audio_file,
                sr,
            )

        return spectrogram_db, output_path

    def _load_audio(
        self,
        file_path: str,
        sr: int = DEFAULT_SAMPLE_RATE,
    ) -> Tuple[NDArray[np.floating], int | float]:
        path = Path(file_path)
        if not path.exists():
            raise AudioFileNotFoundError(f"Audio file not found: {file_path}")

        samples, sample_rate = librosa.load(str(path), sr=sr)
        return samples, sample_rate

    def _compute_mel(
        self,
        samples: NDArray[np.floating],
        sr: int | float,
        n_fft: int = DEFAULT_N_FFT,
        hop_length: int = DEFAULT_HOP_LENGTH,
        n_mels: int = DEFAULT_N_MELS,
    ) -> NDArray[np.floating]:
        return librosa.feature.melspectrogram(
            y=samples,
            sr=sr,
            n_fft=n_fft,
            hop_length=hop_length,
            n_mels=n_mels,
        )

    def _save_spectrogram_image(
        self,
        spectrogram_db: NDArray[np.floating],
        audio_file: AudioFile,
        sr: int | float,
    ) -> Path:
        source_name = Path(audio_file.file_path).stem
        output_filename = f"{source_name}_mel_spectrogram.png"

        fig, ax = plt.subplots(figsize=(10, 4))

        img = librosa.display.specshow(
            spectrogram_db,
            sr=sr,
            hop_length=self.DEFAULT_HOP_LENGTH,
            x_axis='time',
            y_axis='mel',
            ax=ax,
        )

        fig.colorbar(img, ax=ax, format='%+2.0f dB')
        ax.set_title('Mel Spectrogram')

        plt.tight_layout()
        buffer = BytesIO()
        fig.savefig(buffer, dpi=150, bbox_inches='tight', format='png')
        plt.close(fig)

        buffer.seek(0)
        output_path = self.storage_service.store(
            file=buffer.read(),
            target_directory=StorageDirectory.SPECTROGRAMS,
            filename=output_filename,
        )

        return output_path
