# Drift check

Repeatable checks to confirm implementation still matches **[`AGENTS.md`](../AGENTS.md)** and this repo’s layout. Run from repo root.

## 1. Package layout

- [ ] Domain tables live under `app/music_genre_sommelier/models/` (not repo-root `src/`).
- [ ] Services live under `app/music_genre_sommelier/services/`.
- [ ] Enums in `app/music_genre_sommelier/utils/enum/`; DB engine in `app/music_genre_sommelier/utils/database/`.

```bash
test -d app/music_genre_sommelier/models
test -d app/music_genre_sommelier/services
```

## 2. Orchestration boundaries

- [ ] **`MLTaskService.process`** is the entry point for inference orchestration (not `MLTask` alone).
- [ ] **`AudioSpectrogramService.convert`** is the entry point for conversion (not `AudioSpectrogram.convert` on the model).

```bash
rg "def process" app/music_genre_sommelier/services/ml_task_service.py
rg "def convert" app/music_genre_sommelier/services/audio_spectrogram_service.py
```

## 3. No raw audio in inference path

- [ ] **`MLTaskService`** must not reference `AudioFile` for prediction.

```bash
rg "AudioFile" app/music_genre_sommelier/services/ml_task_service.py && echo "FAIL: AudioFile in ml_task_service" || true
```

(Expect no matches in `ml_task_service.py`.)

## 4. SpectrogramFile is persistence-only

- [ ] `spectrogram_file.py` should not define behavior beyond the SQLModel table.

```bash
wc -l app/music_genre_sommelier/models/spectrogram_file.py
```

## 5. Schema documentation parity

- [ ] `Transaction` has no `ml_task_id` in models; `MLTask` has `transaction_id`.

```bash
rg "ml_task_id" app/music_genre_sommelier/models/transaction.py && echo "unexpected ml_task_id on Transaction" || true
rg "transaction_id" app/music_genre_sommelier/models/ml_task.py
```

## 6. Admin balance sentinel

- [ ] `AdminUser.get_balance` returns `float("inf")` without opening a DB session in that method.

```bash
rg -A3 "def get_balance" app/music_genre_sommelier/models/admin_user.py
```

## 7. Settlement ordering (spot-check)

- [ ] **`approve`** is only invoked from **`MLTask.record_success`** (or equivalent); **`MLTaskService`** calls **`record_success`** after **`_perform_prediction`**.

```bash
rg "approve" app/music_genre_sommelier/models/ml_task.py
rg "record_success" app/music_genre_sommelier/services/ml_task_service.py
```

Update this file when adding modules, renaming paths, or changing dependency edges so grep targets stay accurate.
