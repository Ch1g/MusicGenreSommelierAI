# Architecture

High-level view of the Music Genre Sommelier AI codebase. The normative contract for modules and behavior is **[`CLAUDE.md`](../CLAUDE.md)**.

## Layers

| Layer | Responsibility |
|-------|------------------|
| **Frontend** | React + TypeScript SPA (Vite, MobX, React Router) under [`frontend/src/`](../frontend/src/). Served as a separate Compose service; nginx proxies `/api/*` to the app and everything else to the frontend. Auth token stored in `localStorage`; all API calls use `Authorization: Bearer <token>`. Media resources (audio stream, spectrogram images) are fetched as blobs with auth headers and exposed to `<audio>`/`<img>` via object URLs. |
| **REST / HTTP** | Request validation, JWT auth, file uploads, HTTP status mapping. FastAPI routers under [`app/music_genre_sommelier/controllers/`](../app/music_genre_sommelier/controllers/); entry point is [`main.py`](../app/music_genre_sommelier/controllers/main.py). Global `AppError` and generic 500 handlers registered on the app. JWT token creation and verification in [`utils/auth/`](../app/music_genre_sommelier/utils/auth/). |
| **Services** | Orchestration: [`AudioSpectrogramService`](../app/music_genre_sommelier/services/audio_spectrogram_service.py), [`MLTaskService`](../app/music_genre_sommelier/services/ml_task_service.py), [`RegistrationService`](../app/music_genre_sommelier/services/registration_service.py), [`StorageService`](../app/music_genre_sommelier/services/storage_service.py). |
| **Models (SQLModel)** | Persisted tables and row-level helpers (`record_*`, `_set_status`) under [`app/music_genre_sommelier/models/`](../app/music_genre_sommelier/models/). |
| **Database** | PostgreSQL; engine in [`db.py`](../app/music_genre_sommelier/utils/database/db.py); optional bootstrap in [`seed.py`](../app/music_genre_sommelier/utils/database/seed.py). |
| **Message broker** | RabbitMQ; publishers and consumers under [`app/music_genre_sommelier/utils/message_broker/`](../app/music_genre_sommelier/utils/message_broker/). Queue configs (`QueueConfig`, `InferenceMessage`) live in [`queues.py`](../app/music_genre_sommelier/utils/message_broker/queues.py). `InferencePublisher` (REST layer) and `InferenceConsumer` (worker) implement the inference queue. |
| **ML runtime** | ViT models loaded and cached via [`model_loader.py`](../app/music_genre_sommelier/utils/model_loader.py) (`lru_cache`). Worker preloads all registered models on startup before consuming messages. |

## Data flow (conceptual)

1. **Upload**: bytes → `StorageService` → `AudioFile` row (with `user_id`). Handled by `POST /audio/{user_id}`.
2. **Convert**: [`AudioSpectrogramService.convert`](../app/music_genre_sommelier/services/audio_spectrogram_service.py) → `AudioSpectrogram` + `SpectrogramFile` (+ optional PNG on disk via `StorageService`).
3. **Infer (async)**:
   - REST handler creates `Transaction` + `MLTask` rows, commits, then publishes `{"ml_task_id": <id>}` to the `inference` queue via `InferencePublisher`. Returns HTTP 201 immediately.
   - `InferenceConsumer` (worker process) receives the message, calls [`MLTaskService.process(ml_task_id)`](../app/music_genre_sommelier/services/ml_task_service.py) → `transaction.check_funds()` → `_perform_prediction` (ViT via `model_loader`) → `MLTask.record_success` / `record_failure`; `MLTaskService` then calls `Transaction.approve()` on success or `Transaction.cancel()` on generic failure.
   - On `AppError` the consumer nacks without requeue; on success it acks.

## Entity-relationship summary

Aligned with the `erDiagram` in [`README.md`](../README.md) (after corrections: no `ml_task_id` on `MLTask`; no direct `User`–`MLTask` FK).

| Entity | Key relationships |
|--------|-------------------|
| `User` | One-to-many `Transaction` (`user_id`); one-to-many `AudioFile` (`user_id`). |
| `Transaction` | `user_id` → `User`; no `ml_task_id` column. |
| `AudioFile` | `user_id` → `User`; one-to-many `AudioSpectrogram` (`audio_file_id`). |
| `SpectrogramFile` | Referenced by `AudioSpectrogram.spectrogram_file_id` (nullable until conversion completes). |
| `AudioSpectrogram` | Links `AudioFile` and optional `SpectrogramFile`; one-to-many `MLTask`. |
| `MLModel` | One-to-many `MLTask` (`ml_model_id`). |
| `MLTask` | `audio_spectrogram_id`, `transaction_id`, `ml_model_id`; links to `User` only via `Transaction` → `User`. |

## Enumerations

Persisted string enums: [`CommonStatus`](../app/music_genre_sommelier/utils/enum/common.py) (`AudioSpectrogram.status`, `MLTask.status`), [`TransactionStatus`](../app/music_genre_sommelier/utils/enum/transaction.py) (`Transaction.status`).
