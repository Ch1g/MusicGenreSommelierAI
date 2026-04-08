from sqlmodel import Session

from music_genre_sommelier.models.ml_model import MLModel
from music_genre_sommelier.models.ml_task import MLTask
from music_genre_sommelier.models.spectrogram_file import SpectrogramFile
from music_genre_sommelier.utils.enum.transaction import TransactionStatus

class InsufficientFundsError(Exception):
    pass

class MLTaskService:
    def __init__(self, session: Session):
        self.session = session

    def process(self, ml_task: MLTask) -> dict | None:
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

            return result
        except InsufficientFundsError as e:
            ml_task.record_failure(str(e))
            return None
        except Exception as e:
            ml_task.record_failure(str(e))
            return None
        finally:
            self.session.add(ml_task)
            self.session.commit()

    def _perform_prediction(self, ml_model: MLModel, spectrogram_file: SpectrogramFile) -> dict:
        # ... Реализовать позже

        return {}
