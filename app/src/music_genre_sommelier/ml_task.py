from music_genre_sommelier.utils.enum.common import CommonStatus

class MLTask:
    def __init__(self, id: int, audio_spectrogram_id: int, user_id: int, model_id: int, status: CommonStatus = CommonStatus.PENDING, result: dict | None = None, error: str | None = None):
        self.id = id
        self.audio_spectrogram_id = audio_spectrogram_id
        self.user_id = user_id
        self.model_id = model_id
        self.status = status
        self.result = result
        self.error = error

    # TODO: Реализовать позже
    def process(self): 
        return
    
    def _record_failure(self, error: str):
        self.error = error
        self._set_status(CommonStatus.FAILURE)
    
    def _record_success(self, result: dict):
        self.result = result
        self._set_status(CommonStatus.SUCCESS)

    def _set_status(self, status: CommonStatus):
        self.status = status