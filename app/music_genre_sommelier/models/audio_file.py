from music_genre_sommelier.utils.enum.common import CommonStatus
from sqlmodel import Column, DateTime, SQLModel, Field, func
from datetime import datetime

class AudioFile(SQLModel, table=True):
    __tablename__ = "audio_file" # type: ignore

    id: int = Field(default=None, primary_key=True)
    file_path: str = Field(default=None, index=True)
    upload_status: CommonStatus = Field(default=CommonStatus.PENDING)
    upload_error: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(DateTime, onupdate=func.now())
    )

    def record_failure(self, error: str):
        self.upload_error = error
        self.set_status(CommonStatus.FAILURE)

    def record_success(self):
        self.set_status(CommonStatus.SUCCESS)

    def set_status(self, status: CommonStatus):
        self.upload_status = status
