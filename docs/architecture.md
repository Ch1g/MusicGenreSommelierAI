# Architecture

High-level view of the Music Genre Sommelier AI codebase. The normative contract for modules and behavior is **[`CLAUDE.md`](../CLAUDE.md)**.

## Layers

| Layer | Responsibility |
|-------|------------------|
| **REST / HTTP** | Request validation, auth, file uploads, HTTP status mapping. FastAPI routers under [`app/music_genre_sommelier/controllers/`](../app/music_genre_sommelier/controllers/); entry point is [`main.py`](../app/music_genre_sommelier/controllers/main.py). |
| **Services** | Orchestration: [`AudioSpectrogramService`](../app/music_genre_sommelier/services/audio_spectrogram_service.py), [`MLTaskService`](../app/music_genre_sommelier/services/ml_task_service.py), [`RegistrationService`](../app/music_genre_sommelier/services/registration_service.py), [`StorageService`](../app/music_genre_sommelier/services/storage_service.py). |
| **Models (SQLModel)** | Persisted tables and row-level helpers (`record_*`, `_set_status`) under [`app/music_genre_sommelier/models/`](../app/music_genre_sommelier/models/). |
| **Database** | PostgreSQL; engine in [`db.py`](../app/music_genre_sommelier/utils/database/db.py); optional bootstrap in [`seed.py`](../app/music_genre_sommelier/utils/database/seed.py). |

## Data flow (conceptual)

1. **Upload**: bytes → `StorageService` → `AudioFile` row (with `user_id`). Handled by `POST /audio/{user_id}`.
2. **Convert**: [`AudioSpectrogramService.convert`](../app/music_genre_sommelier/services/audio_spectrogram_service.py) → `AudioSpectrogram` + `SpectrogramFile` (+ optional PNG on disk via `StorageService`).
3. **Infer**: [`MLTaskService.process`](../app/music_genre_sommelier/services/ml_task_service.py) → `transaction.check_funds()` → `_perform_prediction` → `MLTask.record_success` / `record_failure` (task state only); `MLTaskService` then calls `Transaction.approve()` on success or `Transaction.cancel()` on generic failure.

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
