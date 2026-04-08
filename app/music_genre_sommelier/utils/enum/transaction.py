from enum import Enum

class TransactionStatus(str, Enum):
    PENDING = 'pending'
    SUCCESS = 'success'
    FAIL_INSUFFICIENT_FUNDS = 'fail_insufficient_funds'
    FAIL_CANCELED = 'fail_canceled'
