from sqlmodel import Field
from music_genre_sommelier.models.transaction import Transaction
from music_genre_sommelier.models.user import User

class CommonUser(User):
    is_admin: bool = Field(default=False)

    def get_balance(self) -> float:
        return Transaction.get_balance(self.id)
