from music_genre_sommelier.utils.message_broker import queues
from music_genre_sommelier.utils.message_broker.publishers.base_publisher import BasePublisher

class InferencePublisher(BasePublisher[queues.InferenceMessage]):

    def _queue_config(self) -> queues.QueueConfig:
        return queues.INFERENCE
