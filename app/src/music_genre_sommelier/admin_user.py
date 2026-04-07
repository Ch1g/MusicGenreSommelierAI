from sqlmodel import Field

from music_genre_sommelier.user import User

class AdminUser(User):
    is_admin: bool = Field(default=True)

    def get_balance(self) -> float:
        return float("inf")