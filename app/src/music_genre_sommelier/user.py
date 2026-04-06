class User:
    def __init__(self, id: int, email: str, username: str, encrypted_password: str, is_admin: bool):
        self.id = id
        self.email = email
        self.username = username
        self.encrypted_password = encrypted_password
        self.is_admin = is_admin

    def get_balance(self) -> float:
        raise NotImplementedError("Subclasses must implement this method")