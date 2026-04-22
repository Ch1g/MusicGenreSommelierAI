#!/bin/sh
set -e

echo "Running seeds..."
python -m music_genre_sommelier.utils.database.seed

echo "Starting server..."
exec fastapi dev music_genre_sommelier/controllers/main.py --host 0.0.0.0 --port 3000
