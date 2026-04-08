from datetime import datetime

from sqlmodel import Column, DateTime, Field, Relationship, SQLModel, func

from music_genre_sommelier.models.audio_file import AudioFile
from music_genre_sommelier.models.spectrogram_file import SpectrogramFile
from music_genre_sommelier.utils.enum.common import CommonStatus


class AudioSpectrogram(SQLModel, table=True):
    __tablename__ = "audio_spectrogram" # type: ignore

    id: int = Field(default=None, primary_key=True)
    audio_file_id: int = Field(index=True, foreign_key="audio_file.id")
    spectrogram_file_id: int | None = Field(default=None, foreign_key="spectrogram_file.id")
    status: CommonStatus = Field(default=CommonStatus.PENDING)
    error: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(DateTime, onupdate=func.now())
    )
    audio_file: AudioFile = Relationship()
    spectrogram_file: SpectrogramFile = Relationship()

    def record_failure(self, error: str):
        self.error = error
        self._set_status(CommonStatus.FAILURE)

    def record_success(self):
        self._set_status(CommonStatus.SUCCESS)

    def _set_status(self, status: CommonStatus):
        self.status = status
