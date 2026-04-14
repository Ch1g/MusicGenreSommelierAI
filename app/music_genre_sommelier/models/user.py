from sqlmodel import Column, DateTime, Relationship, SQLModel, Field, func
from datetime import datetime
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from music_genre_sommelier.models.audio_file import AudioFile
    from music_genre_sommelier.models.transaction import Transaction

class User(SQLModel, table=True):
    __tablename__ = "user" # type: ignore

    id: int = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    username: str = Field(index=True)
    encrypted_password: str = Field()
    is_admin: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(DateTime, onupdate=func.now())
    )
    transactions: List["Transaction"] = Relationship(back_populates="user")
    audio_files: List["AudioFile"] = Relationship(back_populates="user")

    def get_balance(self) -> float:
        if self.is_admin:
            return float("inf")
        else:
            from music_genre_sommelier.models.transaction import Transaction
            return Transaction.get_balance(self.id)
