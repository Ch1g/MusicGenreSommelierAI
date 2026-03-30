from music_genre_sommelier.utils.enum.transaction import TransactionStatus

class Transaction:
    def __init__(self, id: int, user_id: int, ml_task_id: int, amount: float):
        self.id = id
        self.user_id = user_id
        self.ml_task_id = ml_task_id
        self.amount = amount
        self.status = TransactionStatus.PENDING

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
    
    # TODO: Реализовать после подключения к БД
    @staticmethod
    def get_balance(user_id: int) -> float:
        return 0  