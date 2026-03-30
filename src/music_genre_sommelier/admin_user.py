from music_genre_sommelier.user import User

class AdminUser(User):
    def __init__(self, id: int, email: str, username: str, encrypted_password: str):
        super().__init__(id, email, username, encrypted_password, is_admin=True)

    def get_balance(self) -> float:
        return float("inf")