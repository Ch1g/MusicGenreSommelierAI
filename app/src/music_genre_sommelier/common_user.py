from music_genre_sommelier.transaction import Transaction
from music_genre_sommelier.user import User

class CommonUser(User):
    is_admin: bool = Field(default=False)

    def get_balance(self) -> float:
        return Transaction.get_balance(self.id)