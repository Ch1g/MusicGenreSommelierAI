from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from sqlmodel import Session, col, select

from music_genre_sommelier.models.audio_file import AudioFile
from music_genre_sommelier.models.audio_spectrogram import AudioSpectrogram
from music_genre_sommelier.models.ml_model import MLModel
from music_genre_sommelier.models.ml_task import MLTask
from music_genre_sommelier.models.transaction import Transaction
from music_genre_sommelier.models.user import User
from music_genre_sommelier.services.audio_spectrogram_service import AudioSpectrogramService
from music_genre_sommelier.services.storage_service import StorageService
from music_genre_sommelier.utils.auth import get_current_user_id
from music_genre_sommelier.utils.database.db import engine
from music_genre_sommelier.utils.enum.common import CommonStatus
from music_genre_sommelier.utils.errors.errors import ForbiddenError, NotFoundError, ValidationError
from music_genre_sommelier.utils.message_broker.publishers.inference_publisher import InferencePublisher

router = APIRouter(prefix="/api/inference", tags=["inference"])


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
    status_code=201,
    response_model=MLTask,
    responses={
        404: {"description": "Not found"},
        422: {"description": "Validation error"},
        500: {"description": "Internal server error"},
    },
)
def run_inference(
    body: RunInferenceRequest,
    current_user_id: int = Depends(get_current_user_id),
):
    with Session(engine) as session:
        audio_file = _get_audio_file(session, body.audio_file_id)
        if audio_file.user_id != current_user_id:
            raise ForbiddenError("Cannot run inference on another user's audio file")
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
        session.commit()

        InferencePublisher().publish({"ml_task_id": ml_task.id})

        return JSONResponse(status_code=201, content=ml_task.model_dump(mode="json"))


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
def list_tasks(
    user_id: int,
    current_user_id: int = Depends(get_current_user_id),
):
    if user_id != current_user_id:
        raise ForbiddenError("Cannot list another user's tasks")
    with Session(engine) as session:
        if session.exec(select(User).where(User.id == user_id)).first() is None:
            raise NotFoundError(f"User with id {user_id} is not found")

        ml_tasks = session.exec(
            select(MLTask).join(Transaction).where(Transaction.user_id == user_id)
        )

        return JSONResponse(
            status_code=200,
            content=[mlt.model_dump(mode="json") for mlt in ml_tasks],
        )


@router.get(
    "/spectrograms/{task_id}",
    status_code=200,
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"},
    },
)
def get_spectrogram(
    task_id: int,
    current_user_id: int = Depends(get_current_user_id),
):
    with Session(engine) as session:
        ml_task = session.exec(select(MLTask).where(MLTask.id == task_id)).first()
        if ml_task is None:
            raise NotFoundError(f"ML task with id {task_id} is not found")

        if ml_task.transaction.user_id != current_user_id:
            raise ForbiddenError("Cannot access another user's spectrogram")

        spectrogram = ml_task.audio_spectrogram
        if spectrogram is None or spectrogram.spectrogram_file_id is None:
            raise NotFoundError(f"Spectrogram for task {task_id} is not available")

        spectrogram_file = spectrogram.spectrogram_file
        if spectrogram_file is None:
            raise NotFoundError(f"Spectrogram file for task {task_id} is not found")

        return FileResponse(spectrogram_file.file_path, media_type="image/png")
