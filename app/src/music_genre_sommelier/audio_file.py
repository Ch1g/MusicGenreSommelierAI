from music_genre_sommelier.utils.enum.common import CommonStatus

class AudioFile:
    def __init__(self, id: int, file_path: str, upload_status: CommonStatus = CommonStatus.PENDING, upload_error: str | None = None):
        self.id = id
        self.file_path = file_path
        self.upload_status = upload_status
        self.upload_error = upload_error

    # TODO: Реализовать позже
    def upload(self):
        return 

    def _record_failure(self, error: str):
        self.upload_error = error
        self._set_status(CommonStatus.FAILURE)

    def _record_success(self):
        self._set_status(CommonStatus.SUCCESS)

    def _set_status(self, status: CommonStatus):
        self.upload_status = status