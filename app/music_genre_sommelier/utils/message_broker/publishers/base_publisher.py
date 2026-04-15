import json
import logging
from typing import Generic, TypeVar

import pika

from music_genre_sommelier.utils.message_broker import queues
from music_genre_sommelier.utils.message_broker.mb import get_connection

logger = logging.getLogger(__name__)

T = TypeVar("T")

class BasePublisher(Generic[T]):

    def _queue_config(self) -> queues.QueueConfig:
        raise NotImplementedError("Subclasses must implement this method")

    def publish(self, body: T) -> None:
        config = self._queue_config()

        connection = get_connection()
        channel = connection.channel()
        channel.queue_declare(
            queue=config["queue"],
            durable=config["durable"],
            arguments=config["arguments"],
        )
        channel.basic_publish(
            exchange='',
            routing_key=config["queue"],
            body=json.dumps(body),
            properties=pika.BasicProperties(
                delivery_mode=pika.DeliveryMode.Persistent
            ))

        logger.info(f"Sent {body} to queue {config['queue']}")
        connection.close()


