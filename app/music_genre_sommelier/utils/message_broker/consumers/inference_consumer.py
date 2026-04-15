import json
import logging

from sqlmodel import Session

from music_genre_sommelier.services.ml_task_service import MLTaskService
from music_genre_sommelier.utils.errors.errors import AppError
from music_genre_sommelier.utils.message_broker import queues
from music_genre_sommelier.utils.message_broker.consumers.base_consumer import BaseConsumer
from music_genre_sommelier.utils.database.db import engine

logger = logging.getLogger(__name__)

class InferenceConsumer(BaseConsumer[queues.InferenceMessage]):

    def _queue_config(self) -> queues.QueueConfig:
        return queues.INFERENCE

    def _parse_body(self, body: bytes) -> queues.InferenceMessage:
        return json.loads(body)

    def _handle_message(self, ch, method, _properties, body: bytes) -> None:
        logger.info(f"Inference request received: {body}")
        try:
            data = self._parse_body(body)
            ml_task_id = data["ml_task_id"]
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Malformed message, discarding: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return
        logger.info(f"MLTask {ml_task_id} is being processed")

        with Session(engine) as session:
            try:
                MLTaskService(session).process(ml_task_id)
            except AppError as e:
                logger.error(e)
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                return

        ch.basic_ack(delivery_tag=method.delivery_tag)
        logger.info(f"MLTask {ml_task_id} processed")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    InferenceConsumer().consume()
