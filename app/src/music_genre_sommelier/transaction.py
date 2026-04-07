from datetime import datetime

from sqlalchemy import func
from sqlmodel import Field, Session, SQLModel, select

from music_genre_sommelier.utils.database import engine
from music_genre_sommelier.utils.enum.transaction import TransactionStatus

class Transaction(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, foreign_key="user.id")
    ml_task_id: int | None = Field(default=None, foreign_key="ml_task.id")
    amount: float = Field()
    status: TransactionStatus = Field(default=TransactionStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def approve(self):
        self._set_status(TransactionStatus.SUCCESS)

    def cancel(self):
        self._set_status(TransactionStatus.FAIL_CANCELED)

    def fail_insufficient_funds(self):
        self._set_status(TransactionStatus.FAIL_INSUFFICIENT_FUNDS)

    def _set_status(self, status: TransactionStatus) -> None:
        self.status = status

    @staticmethod
    def check_funds(user_id: int, amount: float) -> bool:
        return Transaction.get_balance(user_id) >= amount
    
    @staticmethod
    def get_balance(user_id: int) -> float:
        query = select(func.coalesce(func.sum(Transaction.amount), 0.0)).where(
            Transaction.user_id == user_id,
            Transaction.status == TransactionStatus.SUCCESS,
        )
        with Session(engine) as session:
            total = session.exec(query).one()
        return float(total)