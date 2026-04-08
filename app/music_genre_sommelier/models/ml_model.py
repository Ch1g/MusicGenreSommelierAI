from sqlmodel import Column, DateTime, SQLModel, Field, func
from datetime import datetime

class MLModel(SQLModel, table=True):
    __tablename__ = "ml_model" # type: ignore

    id: int = Field(default=None, primary_key=True)
    model_path: str = Field(index=True)
    prediction_cost: float = Field()
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(DateTime, onupdate=func.now())
    )

    def touch_updated_at(self) -> None:
        self.updated_at = datetime.now()
