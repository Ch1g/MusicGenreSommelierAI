from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlmodel import Session, select

from music_genre_sommelier.models.ml_model import MLModel
from music_genre_sommelier.utils.database.db import get_session

router = APIRouter(prefix="/api/ml-models", tags=["ml-models"])


@router.get(
    "/",
    status_code=200,
    response_model=list[MLModel],
    responses={
        500: {"description": "Internal server error"},
    },
)
def list_models(session: Session = Depends(get_session)):
    models = session.exec(select(MLModel)).all()
    return JSONResponse(
        status_code=200,
        content=[m.model_dump(mode="json") for m in models],
    )
