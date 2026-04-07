from music_genre_sommelier.utils.enum.common import CommonStatus
from sqlmodel import SQLModel, Field
from datetime import datetime

class MLTask(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    audio_spectrogram_id: int = Field(index=True, foreign_key="audio_spectrogram.id")
    user_id: int = Field(index=True, foreign_key="user.id")
    model_id: int = Field(index=True, foreign_key="ml_model.id")
    status: CommonStatus = Field(default=CommonStatus.PENDING)
    result: dict | None = Field(default=None)
    error: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # TODO: Реализовать позже
    def process(self): 
        self.audio_spectrogram

    
    def _record_failure(self, error: str):
        self.error = error
        self._set_status(CommonStatus.FAILURE)
    
    def _record_success(self, result: dict):
        self.result = result
        self._set_status(CommonStatus.SUCCESS)

    def _set_status(self, status: CommonStatus):
        self.status = status