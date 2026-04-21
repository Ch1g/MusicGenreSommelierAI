from typing import TypedDict

class QueueConfig(TypedDict):
    queue: str
    durable: bool
    arguments: dict
    reconnect_delay: int

class InferenceMessage(TypedDict):
    ml_task_id: int

INFERENCE: QueueConfig = {
    "queue": "inference",
    "durable": True,
    "arguments": {"x-queue-type": "quorum"},
    "reconnect_delay": 5,
}
