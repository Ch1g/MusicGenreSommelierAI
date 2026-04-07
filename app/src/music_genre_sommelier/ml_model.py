from sqlmodel import SQLModel, Field
from datetime import datetime

class MLModel(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    model_path: str = Field(index=True)
    prediction_cost: float = Field()
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # TODO: Реализовать позже
    def predict(self, spectrogram_path: str):
        return