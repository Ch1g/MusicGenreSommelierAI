from datetime import datetime
from sqlmodel import Column, DateTime, Field, Relationship, Session, SQLModel, func, select
from music_genre_sommelier.utils.database import engine
from music_genre_sommelier.utils.enum.transaction import TransactionStatus
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from music_genre_sommelier.models.user import User

class Transaction(SQLModel, table=True):
    __tablename__ = "transaction" # type: ignore

    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, foreign_key="user.id")
    amount: float = Field()
    status: TransactionStatus = Field(default=TransactionStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(DateTime, onupdate=func.now())
    )
    user: Optional["User"] = Relationship(back_populates='transactions')

    def approve(self):
        self._set_status(TransactionStatus.SUCCESS)

    def cancel(self):
        self._set_status(TransactionStatus.FAIL_CANCELED)

    def fail_insufficient_funds(self):
        self._set_status(TransactionStatus.FAIL_INSUFFICIENT_FUNDS)

    def check_funds(self) -> None:
        if self._is_sufficient() is False:
            self.fail_insufficient_funds()

    def _is_sufficient(self) -> bool:
        return Transaction.get_balance(self.user_id) >= -self.amount

    def _set_status(self, status: TransactionStatus) -> None:
        self.status = status

    @staticmethod
    def get_balance(user_id: int) -> float:
        query = select(func.coalesce(func.sum(Transaction.amount), 0.0)).where(
            Transaction.user_id == user_id,
            Transaction.status == TransactionStatus.SUCCESS,
        )
        with Session(engine) as session:
            total = session.exec(query).one()
        return float(total)
