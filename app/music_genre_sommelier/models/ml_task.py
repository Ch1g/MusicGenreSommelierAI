from music_genre_sommelier.models.transaction import Transaction
from music_genre_sommelier.models.audio_spectrogram import AudioSpectrogram
from music_genre_sommelier.models.ml_model import MLModel
from music_genre_sommelier.utils.enum.common import CommonStatus
from sqlmodel import JSON, Column, DateTime, Relationship, SQLModel, Field, func
from datetime import datetime

class MLTask(SQLModel, table=True):
    __tablename__ = "ml_task" # type: ignore

    id: int = Field(default=None, primary_key=True)
    audio_spectrogram_id: int = Field(index=True, foreign_key="audio_spectrogram.id")
    transaction_id: int = Field(index=True, foreign_key="transaction.id")
    ml_model_id: int = Field(index=True, foreign_key="ml_model.id")
    status: CommonStatus = Field(default=CommonStatus.PENDING)
    result: dict | None = Field(default=None, sa_type=JSON)
    error: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(DateTime, onupdate=func.now())
    )
    audio_spectrogram: AudioSpectrogram = Relationship()
    transaction: Transaction = Relationship()
    ml_model: MLModel = Relationship()

    def record_failure(self, error: str):
        self.error = error
        self._set_status(CommonStatus.FAILURE)

    def record_success(self, result: dict):
        self.result = result
        self._set_status(CommonStatus.SUCCESS)

    def _set_status(self, status: CommonStatus):
        self.status = status
