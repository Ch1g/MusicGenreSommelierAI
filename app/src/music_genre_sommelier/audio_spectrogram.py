from music_genre_sommelier.utils.enum.common import CommonStatus

class AudioSpectrogram:
    def __init__(self, id: int, audio_file_id: int, spectrogram_file_id: int | None = None, status: CommonStatus = CommonStatus.PENDING, error: str | None = None):
        self.id = id
        self.audio_file_id = audio_file_id
        self.spectrogram_file_id = spectrogram_file_id
        self.status = status
        self.error = error

    # TODO: Реализовать позже
    def convert(self):
        return
    
    def _record_failure(self, error: str):
        self.error = error
        self._set_status(CommonStatus.FAILURE)
    
    def _record_success(self):
        self._set_status(CommonStatus.SUCCESS)

    def _set_status(self, status: CommonStatus):
        self.status = status