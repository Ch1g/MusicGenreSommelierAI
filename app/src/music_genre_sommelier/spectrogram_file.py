from sqlmodel import SQLModel, Field
from datetime import datetime

class SpectrogramFile(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    file_path: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)