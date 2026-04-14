from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlmodel import Column, DateTime, Field, Relationship, SQLModel, func

if TYPE_CHECKING:
    from music_genre_sommelier.models.user import User


class AudioFile(SQLModel, table=True):
    __tablename__ = "audio_file"  # type: ignore

    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, foreign_key="user.id")
    file_path: str = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(DateTime, onupdate=func.now()),
    )

    user: Optional["User"] = Relationship(back_populates="audio_files")
