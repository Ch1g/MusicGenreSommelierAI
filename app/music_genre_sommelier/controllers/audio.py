import logging
import uuid

from fastapi import APIRouter, UploadFile
from fastapi.responses import JSONResponse, Response
from sqlmodel import Session, select

from music_genre_sommelier.models.audio_file import AudioFile
from music_genre_sommelier.models.audio_spectrogram import AudioSpectrogram
from music_genre_sommelier.models.user import User
from music_genre_sommelier.services.storage_service import StorageDirectory, StorageService
from music_genre_sommelier.utils.database.db import engine
from music_genre_sommelier.utils.errors.errors import AppError, NotFoundError, ValidationError

router = APIRouter(prefix="/audio", tags=["audio"])


def _get_user(session: Session, user_id: int) -> User:
    user = session.exec(select(User).where(User.id == user_id)).first()
    if user is None:
        raise NotFoundError(f"User with id {user_id} is not found")
    return user


@router.post(
    "/{user_id}",
    status_code=201,
    response_model=AudioFile,
    responses={
        404: {"description": "Not found"},
        422: {"description": "Validation error"},
        500: {"description": "Internal server error"},
    },
)
async def upload_audio(user_id: int, file: UploadFile):
    with Session(engine) as session:
        try:
            if not file.content_type or not file.content_type.startswith("audio/"):
                raise ValidationError(
                    f"Invalid content type: {file.content_type!r}. Expected audio/*"
                )

            data = await file.read()
            if not data:
                raise ValidationError("File is empty")

            _get_user(session, user_id)

            filename = f"{uuid.uuid4()}_{file.filename}"
            storage = StorageService()
            path = storage.store(data, StorageDirectory.AUDIOS, filename)

            audio_file = AudioFile(user_id=user_id, file_path=str(path))
            session.add(audio_file)
            try:
                session.commit()
            except Exception:
                storage.delete(str(path))
                raise
            session.refresh(audio_file)

            return JSONResponse(status_code=201, content=audio_file.model_dump(mode="json"))
        except AppError as e:
            return JSONResponse(status_code=e.status_code, content={"detail": str(e)})
        except Exception as e:
            logging.exception(str(e))
            return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})


@router.get(
    "/{user_id}",
    status_code=200,
    response_model=list[AudioFile],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"},
    },
)
def list_audios(user_id: int):
    with Session(engine) as session:
        try:
            user = _get_user(session, user_id)
            return JSONResponse(
                status_code=200,
                content=[af.model_dump(mode="json") for af in user.audio_files],
            )
        except AppError as e:
            return JSONResponse(status_code=e.status_code, content={"detail": str(e)})
        except Exception as e:
            logging.exception(str(e))
            return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})


@router.delete(
    "/files/{audio_id}",
    status_code=204,
    responses={
        404: {"description": "Not found"},
        422: {"description": "Validation error"},
        500: {"description": "Internal server error"},
    },
)
def delete_audio(audio_id: int):
    with Session(engine) as session:
        try:
            audio_file = session.exec(
                select(AudioFile).where(AudioFile.id == audio_id)
            ).first()
            if audio_file is None:
                raise NotFoundError(f"Audio file with id {audio_id} is not found")

            has_spectrograms = session.exec(
                select(AudioSpectrogram).where(AudioSpectrogram.audio_file_id == audio_id)
            ).first()
            if has_spectrograms:
                raise ValidationError("Audio file has associated tasks and cannot be deleted")

            StorageService().delete(audio_file.file_path)

            session.delete(audio_file)
            session.commit()

            return Response(status_code=204)
        except AppError as e:
            return JSONResponse(status_code=e.status_code, content={"detail": str(e)})
        except Exception as e:
            logging.exception(str(e))
            return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})
