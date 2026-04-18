#!/bin/sh
set -e

echo "Preloading models..."
python -m music_genre_sommelier.utils.model_loader

echo "Starting inference worker..."
exec python -m music_genre_sommelier.utils.message_broker.consumers.inference_consumer
