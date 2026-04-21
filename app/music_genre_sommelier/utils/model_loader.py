import logging
from functools import lru_cache

from sqlmodel import Session, select
from transformers import ViTForImageClassification, ViTImageProcessor

from music_genre_sommelier.models.ml_model import MLModel
from music_genre_sommelier.utils.database.db import engine

logger = logging.getLogger(__name__)


@lru_cache(maxsize=None)
def load_model(model_path: str) -> tuple[ViTForImageClassification, ViTImageProcessor]:
    logger.info(f"Loading model: {model_path}")
    processor = ViTImageProcessor.from_pretrained(model_path)
    model = ViTForImageClassification.from_pretrained(model_path)
    model.eval()
    return model, processor


def preload_all_models(session: Session) -> None:
    models = session.exec(select(MLModel)).all()
    for ml_model in models:
        load_model(ml_model.model_path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    with Session(engine) as session:
        preload_all_models(session)

    logger.info("All models preloaded.")
