from music_genre_sommelier.transaction import Transaction
from music_genre_sommelier.user import User

class CommonUser(User):
    def __init__(self, id: int, email: str, username: str, encrypted_password: str):
        super().__init__(id, email, username, encrypted_password, is_admin=False)

    def get_balance(self) -> float:
        return Transaction.get_balance(self.id)