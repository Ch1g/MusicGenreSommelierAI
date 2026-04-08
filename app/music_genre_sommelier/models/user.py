from sqlmodel import Column, DateTime, SQLModel, Field, func
from datetime import datetime

class User(SQLModel, table=True):
    __tablename__ = "user" # type: ignore

    id: int = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    username: str = Field(index=True)
    encrypted_password: str = Field()
    is_admin: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(DateTime, onupdate=func.now())
    )

    def get_balance(self) -> float:
        raise NotImplementedError("Subclasses must implement this method")
