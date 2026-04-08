from sqlmodel import Column, DateTime, SQLModel, Field, func
from datetime import datetime

class SpectrogramFile(SQLModel, table=True):
    __tablename__ = "spectrogram_file" # type: ignore

    id: int = Field(default=None, primary_key=True)
    file_path: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(DateTime, onupdate=func.now())
    )
