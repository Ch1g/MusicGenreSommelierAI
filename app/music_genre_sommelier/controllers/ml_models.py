import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlmodel import Session, select

from music_genre_sommelier.models.ml_model import MLModel
from music_genre_sommelier.utils.database.db import engine

router = APIRouter(prefix="/api/ml-models", tags=["ml-models"])


@router.get(
    "/",
    status_code=200,
    response_model=list[MLModel],
    responses={
        500: {"description": "Internal server error"},
    },
)
def list_models():
    with Session(engine) as session:
        try:
            models = session.exec(select(MLModel)).all()
            return JSONResponse(
                status_code=200,
                content=[m.model_dump(mode="json") for m in models],
            )
        except Exception as e:
            logging.exception(str(e))
            return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})
