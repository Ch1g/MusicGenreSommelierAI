import torch
from PIL import Image
from sqlmodel import Session, select

from music_genre_sommelier.models.ml_model import MLModel
from music_genre_sommelier.models.ml_task import MLTask
from music_genre_sommelier.models.spectrogram_file import SpectrogramFile
from music_genre_sommelier.utils.enum.transaction import TransactionStatus
from music_genre_sommelier.utils.errors.errors import NotFoundError
from music_genre_sommelier.utils.model_loader import load_model

class InsufficientFundsError(Exception):
    def __init__(self, message: str = "Insufficient funds"):
        super().__init__(message)

class MLTaskService:
    def __init__(self, session: Session):
        self.session = session

    def process(self, ml_task_id: int) -> dict | None:
        ml_task = self._load_ml_task(ml_task_id)
        transaction = ml_task.transaction
        ml_model = ml_task.ml_model
        audio_spectrogram = ml_task.audio_spectrogram
        spectrogram_file = audio_spectrogram.spectrogram_file
        try:
            transaction.check_funds()
            if transaction.status == TransactionStatus.FAIL_INSUFFICIENT_FUNDS:
                raise InsufficientFundsError

            result = self._perform_prediction(ml_model, spectrogram_file)

            ml_task.record_success(result)
            transaction.approve()

            return result
        except InsufficientFundsError as e:
            ml_task.record_failure(str(e))
            return None
        except Exception as e:
            ml_task.record_failure(str(e))
            transaction.cancel()
            return None
        finally:
            self.session.add(ml_task)
            self.session.add(transaction)
            self.session.commit()

    def _load_ml_task(self, ml_task_id: int) -> MLTask:
        statement = (
            select(MLTask)
            .where(MLTask.id == ml_task_id)
        )
        ml_task = self.session.exec(statement).first()
        if ml_task is None:
            raise NotFoundError(f"ML Task with id {ml_task_id} is not found")
        return ml_task

    def _perform_prediction(self, ml_model: MLModel, spectrogram_file: SpectrogramFile) -> dict:
        model, processor = load_model(ml_model.model_path)

        image = Image.open(spectrogram_file.file_path).convert("RGB")
        inputs = processor(images=image, return_tensors="pt")

        with torch.no_grad():
            logits = model(**inputs).logits

        probs = torch.nn.functional.softmax(logits, dim=-1)[0]
        top_idx = int(probs.argmax())

        return {
            "label": model.config.id2label[top_idx],
            "score": round(probs[top_idx].item(), 4),
        }
