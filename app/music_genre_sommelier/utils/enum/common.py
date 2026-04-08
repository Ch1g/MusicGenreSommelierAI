from enum import Enum


class CommonStatus(str, Enum):
    PENDING = 'pending'
    SUCCESS = 'success'
    FAILURE = 'failure'
