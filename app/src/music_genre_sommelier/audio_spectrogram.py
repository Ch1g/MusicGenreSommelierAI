from datetime import datetime

from sqlmodel import Field, SQLModel, Session

from music_genre_sommelier.spectrogram_file import SpectrogramFile
from music_genre_sommelier.utils.database.db import engine
from music_genre_sommelier.utils.enum.common import CommonStatus


class AudioSpectrogram(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    audio_file_id: int = Field(index=True, foreign_key="audio_file.id")
    spectrogram_file_id: int | None = Field(default=None, foreign_key="spectrogram_file.id")
    status: CommonStatus = Field(default=CommonStatus.PENDING)
    error: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # TODO: Реализовать конвертацию в спектрограмму
    def convert(self):
        with Session(engine) as session:
            try:
                spectrogram_file = SpectrogramFile(file_path='dummy_file_path')
                session.add(spectrogram_file)
                session.commit()
                self.spectrogram_file_id = spectrogram_file.id
                self._record_success()
            except Exception as e:
                self._record_failure(str(e))

    
    def _record_failure(self, error: str):
        self.error = error
        self._set_status(CommonStatus.FAILURE)
    
    def _record_success(self):
        self._set_status(CommonStatus.SUCCESS)

    def _set_status(self, status: CommonStatus):
        self.status = status