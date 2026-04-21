import logging
import time
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

import pika
import pika.exceptions

from music_genre_sommelier.utils.message_broker import queues
from music_genre_sommelier.utils.message_broker.mb import get_connection

logger = logging.getLogger(__name__)

T = TypeVar("T")

class BaseConsumer(ABC, Generic[T]):

    @abstractmethod
    def _queue_config(self) -> queues.QueueConfig: ...

    @abstractmethod
    def _parse_body(self, body: bytes) -> T: ...

    @abstractmethod
    def _handle_message(self, ch, method, _properties, body: bytes) -> None: ...

    def consume(self) -> None:
        while True:
            config = self._queue_config()

            try:
                connection = get_connection()
                channel = connection.channel()
                channel.queue_declare(
                    queue=config["queue"],
                    durable=config["durable"],
                    arguments=config["arguments"],
                )
                channel.basic_qos(prefetch_count=1)
                channel.basic_consume(queue=config["queue"], on_message_callback=self._handle_message)

                logger.info("Worker ready, waiting for messages")
                channel.start_consuming()

            except pika.exceptions.AMQPConnectionError as e:
                logger.warning(f"Connection lost: {e} — retrying in {config['reconnect_delay']}")
                time.sleep(config["reconnect_delay"])
            except KeyboardInterrupt:
                logger.info("Worker stopped")
                break
