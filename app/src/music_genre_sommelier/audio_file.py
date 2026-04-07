from io import FileIO
from music_genre_sommelier.utils.enum.common import CommonStatus
from sqlmodel import SQLModel, Field
from datetime import datetime

class AudioFile(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    file_path: str = Field(index=True)
    upload_status: CommonStatus = Field(default=CommonStatus.PENDING)
    upload_error: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # TODO: Реализовать загрузку файла 
    def upload(self, file: FileIO):
        try: 
            self.file_path = 'dummy_file_path'
            self._record_success()
        except Exception as e:
            self._record_failure(str(e))

    def _record_failure(self, error: str):
        self.upload_error = error
        self._set_status(CommonStatus.FAILURE)

    def _record_success(self):
        self._set_status(CommonStatus.SUCCESS)

    def _set_status(self, status: CommonStatus):
        self.upload_status = status