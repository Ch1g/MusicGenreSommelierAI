import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlmodel import Session, col, select

from music_genre_sommelier.models.audio_file import AudioFile
from music_genre_sommelier.models.audio_spectrogram import AudioSpectrogram
from music_genre_sommelier.models.ml_model import MLModel
from music_genre_sommelier.models.ml_task import MLTask
from music_genre_sommelier.models.transaction import Transaction
from music_genre_sommelier.models.user import User
from music_genre_sommelier.services.audio_spectrogram_service import AudioSpectrogramService
from music_genre_sommelier.services.ml_task_service import MLTaskService
from music_genre_sommelier.services.storage_service import StorageService
from music_genre_sommelier.utils.database.db import engine
from music_genre_sommelier.utils.enum.common import CommonStatus
from music_genre_sommelier.utils.errors.errors import AppError, NotFoundError, ValidationError

router = APIRouter(prefix="/inference", tags=["inference"])


class RunInferenceRequest(BaseModel):
    audio_file_id: int
    ml_model_id: int


def _get_audio_file(session: Session, audio_file_id: int) -> AudioFile:
    audio_file = session.exec(
        select(AudioFile).where(AudioFile.id == audio_file_id)
    ).first()
    if audio_file is None:
        raise NotFoundError(f"Audio file with id {audio_file_id} is not found")
    return audio_file


def _get_ml_model(session: Session, ml_model_id: int) -> MLModel:
    ml_model = session.exec(
        select(MLModel).where(MLModel.id == ml_model_id)
    ).first()
    if ml_model is None:
        raise NotFoundError(f"ML model with id {ml_model_id} is not found")
    return ml_model


def _get_or_create_spectrogram(
    session: Session,
    audio_file: AudioFile,
    ml_model: MLModel,
) -> AudioSpectrogram:
    spectrogram = session.exec(
        select(AudioSpectrogram)
        .where(
            AudioSpectrogram.audio_file_id == audio_file.id,
            AudioSpectrogram.status == CommonStatus.SUCCESS,
        )
        .order_by(col(AudioSpectrogram.created_at).desc())
    ).first()

    if spectrogram is not None:
        return spectrogram

    AudioSpectrogramService(session, StorageService()).convert(
        audio_file,
        img_width=ml_model.input_width,
        img_height=ml_model.input_height,
    )

    spectrogram = session.exec(
        select(AudioSpectrogram)
        .where(
            AudioSpectrogram.audio_file_id == audio_file.id,
            AudioSpectrogram.status == CommonStatus.SUCCESS,
        )
        .order_by(col(AudioSpectrogram.created_at).desc())
    ).first()

    if spectrogram is None:
        raise ValidationError("Spectrogram conversion failed")

    return spectrogram


@router.post(
    "/",
    status_code=200,
    response_model=MLTask,
    responses={
        404: {"description": "Not found"},
        422: {"description": "Validation error"},
        500: {"description": "Internal server error"},
    },
)
def run_inference(body: RunInferenceRequest):
    with Session(engine) as session:
        try:
            audio_file = _get_audio_file(session, body.audio_file_id)
            ml_model = _get_ml_model(session, body.ml_model_id)

            audio_spectrogram = _get_or_create_spectrogram(session, audio_file, ml_model)

            session.refresh(audio_file)

            transaction = Transaction(
                user_id=audio_file.user_id,
                amount=-ml_model.prediction_cost,
            )
            session.add(transaction)
            session.flush()

            ml_task = MLTask(
                audio_spectrogram_id=audio_spectrogram.id,
                transaction_id=transaction.id,
                ml_model_id=ml_model.id,
            )
            session.add(ml_task)
            session.flush()

            MLTaskService(session).process(ml_task)
            session.refresh(ml_task)

            return JSONResponse(status_code=200, content=ml_task.model_dump(mode="json"))
        except AppError as e:
            return JSONResponse(status_code=e.status_code, content={"detail": str(e)})
        except Exception as e:
            logging.exception(str(e))
            return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

@router.get(
    "/{user_id}",
    status_code=200,
    response_model=list[MLTask],
    responses={
        404: {"description": "Not found"},
        422: {"description": "Validation error"},
        500: {"description": "Internal server error"},
    },
)
def list_tasks(user_id: int):
    with Session(engine) as session:
        try:
            if session.exec(select(User).where(User.id == user_id)).first() is None:
                raise NotFoundError(f"User with id {user_id} is not found")

            ml_tasks = session.exec(
                select(MLTask)
                .join(Transaction)
                .where(Transaction.user_id == user_id)
            )

            return JSONResponse(status_code=200, content=[mlt.model_dump(mode="json") for mlt in ml_tasks])
        except AppError as e:
            return JSONResponse(status_code=e.status_code, content={"detail": str(e)})
        except Exception as e:
            logging.exception(str(e))
            return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

