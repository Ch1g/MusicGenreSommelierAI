"""ORM hooks: bump `updated_at` before each UPDATE is emitted (same SQL round-trip as other columns)."""

from __future__ import annotations

from datetime import datetime
from typing import Type

from sqlalchemy import event
from sqlmodel import SQLModel


def _touch_updated_at(_mapper, _connection, target: object) -> None:
    if hasattr(target, "updated_at"):
        target.updated_at = datetime.now()


_registered: set[Type[SQLModel]] = set()


def register_updated_at_listener(model: Type[SQLModel]) -> None:
    if model in _registered:
        return
    event.listen(model, "before_update", _touch_updated_at, propagate=True)
    _registered.add(model)


def register_timestamp_listeners() -> None:
    from music_genre_sommelier.audio_file import AudioFile
    from music_genre_sommelier.audio_spectrogram import AudioSpectrogram
    from music_genre_sommelier.ml_model import MLModel
    from music_genre_sommelier.ml_task import MLTask
    from music_genre_sommelier.spectrogram_file import SpectrogramFile
    from music_genre_sommelier.transaction import Transaction
    from music_genre_sommelier.user import User

    for model in (
        AudioFile,
        AudioSpectrogram,
        MLModel,
        MLTask,
        SpectrogramFile,
        Transaction,
        User,
    ):
        register_updated_at_listener(model)
