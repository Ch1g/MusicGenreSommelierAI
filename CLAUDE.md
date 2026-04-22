# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Music Genre Sommelier AI — Architectural Contract

This document is the **architectural contract** for the Music Genre Sommelier AI system. Implementation (Python, REST, OOP) must conform to it. The product accepts user-uploaded audio, converts it to spectrograms, classifies genre via a computer-vision model, and gates access by debiting user balance only on successful inference.

**Docs maintenance:** Any new domain module, renamed file, or dependency edge must be reflected here, in `docs/architecture.md`, and in `docs/drift-check.md` (grep paths and module lists) before the change is considered complete. **Platform stack** (Compose, nginx, Postgres, RabbitMQ, Python operations) is documented in **`docs/stack.md`**; related ADRs live in **`docs/decisions.md`**.

---

## Development

### Running the stack

```bash
docker compose up          # start all services (nginx, app, RabbitMQ, PostgreSQL)
docker compose up app      # rebuild and start app only
```

### Running locally (outside Docker)

```bash
cd app
PYTHONPATH=. fastapi dev music_genre_sommelier/controllers/main.py --host 0.0.0.0 --port 3000
```

Requires a running PostgreSQL instance with credentials matching `.db.env` (see file at repo root for defaults).

DB schema seeding runs automatically on container start via `entrypoint.sh`. To run it manually:

```bash
cd app && PYTHONPATH=. python -m music_genre_sommelier.utils.database.seed --flush
```

### Dependencies

No `pyproject.toml` — dependencies are in `app/requirements.txt`.

```bash
pip install -r app/requirements.txt
```

### Linting and type checking

No linter is configured in the repo. Apply per global standards:

```bash
ruff check app/ && ruff format app/
ty check app/
```

### Tests

No test suite exists yet. When adding tests, place them in `tests/` mirroring package structure and run:

```bash
cd app && PYTHONPATH=. pytest -q
```

### Environment variables

`.db.env` at repo root is bind-mounted into both `app` and `database` containers. Contains
`POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST`, `POSTGRES_PORT`.

---

## Known stubs (not yet implemented)

- **JWT tokens** — `auth.py` returns `"placeholder"` for `jwt_token` in both signup and signin responses.
- **`MLTaskService._perform_prediction`** — inference logic is not implemented; ML model weights and
  the CV prediction pipeline are pending.

---

## Source layout (implementation contract)

Python package **`music_genre_sommelier`** lives under **`app/music_genre_sommelier/`**. The **`app/`** directory is the Docker build context for the application image (`docker-compose.yml` service `app`; compose bind-mounts **`./app`** → **`/src`** in the container, and `WORKDIR` is `/src`). There is **no** `app/src/` directory on disk; imports resolve as `music_genre_sommelier` from the package root.

| Domain / concern | Module path |
|------------------|-------------|
| `AudioFile` | `app/music_genre_sommelier/models/audio_file.py` |
| `SpectrogramFile` | `app/music_genre_sommelier/models/spectrogram_file.py` |
| `AudioSpectrogram` | `app/music_genre_sommelier/models/audio_spectrogram.py` |
| `MLModel` | `app/music_genre_sommelier/models/ml_model.py` |
| `MLTask` | `app/music_genre_sommelier/models/ml_task.py` |
| `Transaction` | `app/music_genre_sommelier/models/transaction.py` |
| `User` | `app/music_genre_sommelier/models/user.py` |
| `CommonUser` | `app/music_genre_sommelier/models/common_user.py` |
| `AdminUser` | `app/music_genre_sommelier/models/admin_user.py` |
| Conversion orchestration | `app/music_genre_sommelier/services/audio_spectrogram_service.py` (`AudioSpectrogramService`) |
| Inference orchestration | `app/music_genre_sommelier/services/ml_task_service.py` (`MLTaskService`) |
| Registration / credentials helpers | `app/music_genre_sommelier/services/registration_service.py` (`RegistrationService`) |
| Filesystem storage layout | `app/music_genre_sommelier/services/storage_service.py` (`StorageService`) |
| DB engine | `app/music_genre_sommelier/utils/database/db.py` |
| Schema seed / bootstrap | `app/music_genre_sommelier/utils/database/seed.py` |
| `CommonStatus` (shared row statuses) | `app/music_genre_sommelier/utils/enum/common.py` |
| `TransactionStatus` | `app/music_genre_sommelier/utils/enum/transaction.py` |
| `AppError` hierarchy | `app/music_genre_sommelier/utils/errors/errors.py` |
| Auth endpoints (signup / signin) | `app/music_genre_sommelier/controllers/auth.py` |
| Audio upload / list / delete | `app/music_genre_sommelier/controllers/audio.py` |
| Inference endpoint | `app/music_genre_sommelier/controllers/inference.py` |
| Transaction / balance endpoints | `app/music_genre_sommelier/controllers/transactions.py` |
| FastAPI app entry point | `app/music_genre_sommelier/controllers/main.py` |

**Import convention:** With `PYTHONPATH` including `app/` at repo root (or `/src` in the app container): `from music_genre_sommelier.models...`, `from music_genre_sommelier.services...`, etc. Enum modules under `utils/enum/` are **not** domain entities; they hold persisted/API enum values only and must not import the service layer or REST adapters.

---

## Module Map

Explicit ownership. Format: `[module] owns X / does not own Y`.

- **`AudioFile`** — owns persisted upload metadata (`file_path`); does not own conversion, spectrogram generation, or inference. Upload is synchronous — the HTTP response communicates success or failure; only successful uploads are persisted. Inbound byte streaming and path wiring are expected from REST/storage orchestration (future or adapters), not from `SpectrogramFile` or `MLTask`.

- **`SpectrogramFile`** — owns the storage record of the spectrogram artifact (path and timestamps); does not own conversion logic, ML, or transactional settlement (no methods beyond the SQLModel row).

- **`AudioSpectrogram`** — owns row-level **`status`** / **`error`** for the conversion outcome and **`record_success`** / **`record_failure`**; does not own the conversion algorithm or session lifecycle. **`AudioSpectrogramService`** performs conversion and updates these rows.

- **`AudioSpectrogramService`** — owns the conversion pipeline from audio file path to mel spectrogram data and optional image artifact, persistence of `SpectrogramFile`, linking `audio_spectrogram.spectrogram_file_id`, and committing the session; does not own inference or ledger rules.

- **`MLModel`** — persistence row for **`model_path`**, **`prediction_cost`**, **`input_width`**, and **`input_height`**; does not own `predict` or task state. Inference is implemented in **`MLTaskService`** (e.g. `_perform_prediction`) using model metadata and spectrogram paths.

- **`MLTask`** — owns task row state (**`status`**, **`result`**, **`error`**) and **`record_success`** / **`record_failure`**, which update task state only. Does not call **`transaction.approve()`** or **`transaction.cancel()`** — settlement is the caller's responsibility (see **Settlement coupling** below). Does not implement fund checks (those run on **`Transaction`** before work) or open raw audio files for inference.

- **`MLTaskService`** — owns **`process(ml_task)`**: fund check via **`transaction.check_funds()`**, prediction, **`ml_task.record_success`** / **`record_failure`**, and explicit settlement calls (**`transaction.approve()`** on success, **`transaction.cancel()`** on generic failure); does not replace entity rules inside models (it coordinates calls and session commit).

- **`Transaction`** — owns ledger row state (`pending` → terminal statuses), **`approve`**, **`cancel`**, **`fail_insufficient_funds`**, instance **`check_funds()`** (may set **`fail_insufficient_funds`** when insufficient), and static **`get_balance(user_id)`**. **`MLTask`** references the ledger row via **`transaction_id`**; the **`transaction`** table has **no** `ml_task_id` column.

- **`User` / `CommonUser` / `AdminUser`** — identity and **`get_balance()`** contract (`CommonUser` delegates to **`Transaction.get_balance`**; **`AdminUser`** returns **`float('inf')`** without DB); does not own sessions, OAuth, or payment providers.

### Settlement coupling (implementation)

Settlement is owned by **`MLTaskService.process`**, not by **`MLTask`** row methods. After a successful prediction, the service calls **`ml_task.record_success`** (task state only) then **`transaction.approve()`**. On generic failure, it calls **`ml_task.record_failure`** then **`transaction.cancel()`**. On insufficient funds, **`transaction.check_funds()`** already sets the transaction to **`fail_insufficient_funds`** — the service calls only **`ml_task.record_failure`** without an additional cancel. Fund sufficiency is evaluated via **`transaction.check_funds()`** before prediction. New code must keep **`approve()`** only after a successful prediction path and avoid speculative debits (see **RULE-02**).

### Status field encapsulation (implementation)

For **`AudioSpectrogram`** (`status`), **`MLTask`** (`status`), and **`Transaction`** (`status`), implementations **should** route persistence-backed status changes through a **private** **`_set_status`** used only from **`record_*`**, **`approve`**, **`cancel`**, **`fail_insufficient_funds`**, or equivalent public methods on the same class. Callers **must not** invoke **`_set_status`** from outside the class.

---

## Contracts Between Modules

For each interaction: **Input** — what is passed in; **Output** — what is returned; **Side-effect policy** — what mutates vs read-only.

### 1. Upload and `AudioFile` (REST / storage layer)

| Aspect | Definition |
|--------|------------|
| **Input** | Inbound upload content, filename/MIME hints, owning `user_id`, storage adapter. |
| **Output** | Persisted `AudioFile` with `file_path` on success; storage failure raises and no record is written. |
| **Side-effect policy** | **Mutates:** `AudioFile` row and blob storage as implemented. **Read-only:** no conversion or `MLTask` in this step. |

### 2. `AudioSpectrogramService.convert(audio_file, ...)`

| Aspect | Definition |
|--------|------------|
| **Input** | `AudioFile` readable at `file_path`; session and `StorageService` configured. |
| **Output** | Spectrogram array data or `None` on failure; persisted `AudioSpectrogram` with linked `SpectrogramFile` when image save succeeds; **`record_success`** or **`record_failure`** on the spectrogram row. |
| **Side-effect policy** | **Mutates:** new/updated `AudioSpectrogram`, optional `SpectrogramFile`, session **commit** in current implementation. **Does not** run inference or mutate `Transaction` except indirectly if a future pipeline does so (not in this service). |

### 3. Accessing the spectrogram artifact

| Aspect | Definition |
|--------|------------|
| **Input** | `AudioSpectrogram` with `status=success` and `spectrogram_file_id` set (ORM load or explicit query). |
| **Output** | Related **`SpectrogramFile`** (path) via relationship or join. |
| **Side-effect policy** | **Read-only** for status when only reading paths. |

### 4. `MLTaskService.process(ml_task)`

| Aspect | Definition |
|--------|------------|
| **Input** | `MLTask` with related **`transaction`**, **`ml_model`**, **`audio_spectrogram`** (and spectrogram file); funds must be sufficient after **`check_funds()`** unless the row is already failed for insufficient funds. |
| **Output** | Prediction **`dict`** or `None` on failure; **`ml_task.record_success`** / **`record_failure`** set terminal status, **`result`** / **`error`** as implemented. |
| **Side-effect policy** | **Mutates:** task row via **`record_*`**; transaction status via explicit **`approve()`** / **`cancel()`** calls; session **add/commit** in **`finally`**. **Must not** read **`AudioFile`** for inference; uses **`SpectrogramFile`** / model metadata only. |

### 5. `Transaction.check_funds()` (instance)

| Aspect | Definition |
|--------|------------|
| **Input** | Implicit `user_id` and **`amount`** on the row. |
| **Output** | **`None`**; if insufficient, **`fail_insufficient_funds()`** is invoked. |
| **Side-effect policy** | **May mutate** the **`transaction`** row status to **`fail_insufficient_funds`**. Reads balance via **`get_balance`** / **`_is_sufficient`**. |

### 6. `Transaction.get_balance(user_id)`

| Aspect | Definition |
|--------|------------|
| **Input** | `user_id`. |
| **Output** | Numeric balance from summed **successful** ledger rows (domain convention). |
| **Side-effect policy** | **Read-only** (opens a read session for the aggregate query). |

### 7. `Transaction.approve()` / `cancel()` / `fail_insufficient_funds()`

| Aspect | Definition |
|--------|------------|
| **Input** | Row in an eligible state per product rules. |
| **Output** | Terminal **`status`** (`success`, `fail_canceled`, `fail_insufficient_funds`). |
| **Side-effect policy** | **Mutates:** **`status`** via **`_set_status`**. **`approve()`** is invoked from **`MLTaskService`** after a successful prediction path. **`cancel()`** is invoked from **`MLTaskService`** on generic failure. **`fail_insufficient_funds()`** is invoked from **`check_funds()`** when balance is insufficient. |

### 8. `CommonUser.get_balance()` / `AdminUser.get_balance()`

| Aspect | Definition |
|--------|------------|
| **Input** | Implicit `user_id` for common users. |
| **Output** | Balance or **`float('inf')`** for admins. |
| **Side-effect policy** | **Read-only** for **`CommonUser`** (delegates to **`Transaction.get_balance`**). **`AdminUser`** does not query the DB. |

---

## Prohibited Patterns

Named rules with concrete violation examples.

- **RULE-01 — Services own cross-entity orchestration**  
  `MLTaskService` must not call `AudioSpectrogramService.convert()` in the middle of a task in a way that violates pipeline ordering; conversion completes before `MLTask` processing.  
  *Violation:* starting `MLTask.process` and then invoking `convert()` for the same upload.

- **RULE-02 — No speculative transactions**  
  **`approve()`** runs only after a successful prediction path inside **`MLTaskService`** (then **`record_success`**). Do not debit before inference succeeds.  
  *Violation:* calling **`approve()`** before **`_perform_prediction`** returns.

- **RULE-03 — No balance math inside `MLTask` row methods**  
  Sufficiency is enforced via **`Transaction.check_funds()`** in **`MLTaskService`** (or equivalent orchestration), not inside **`MLTask.record_*`** alone.  
  *Violation:* `if Transaction.get_balance(...) < amount` inside **`MLTask`** without going through the established **`check_funds`** flow.

- **RULE-04 — No raw audio access in `MLTaskService` inference**  
  Inference uses **`SpectrogramFile`** / **`MLModel`** metadata, not **`AudioFile`**.  
  *Violation:* `_perform_prediction` opening `audio_file.file_path`.

- **RULE-05 — No behavior on `SpectrogramFile`**  
  `SpectrogramFile` remains a storage record only.  
  *Violation:* adding transform or validation methods beyond the ORM row.

- **RULE-06 — AdminUser balance is a sentinel, not a skip**  
  Do not branch on `isinstance(user, AdminUser)` at fund-check call sites to skip checks; **`AdminUser.get_balance()`** returns **`float('inf')`** so generic comparisons succeed.  
  *Violation:* `if not isinstance(user, AdminUser) and not sufficient_funds:` at the expense of consistent APIs.

- **RULE-07 — Conversion before task processing**  
  **`AudioSpectrogram`** for the job must be in a success state before **`MLTaskService.process`** runs.  
  *Violation:* calling **`process`** while spectrogram conversion has not succeeded.

---

## Test Scope

### Covered (future)

- **`Transaction.check_funds()`** / **`_is_sufficient`** / **`get_balance`** — balance edge cases; admin path via **`float('inf')`** where applicable.
- **`Transaction.approve()`** / **`cancel()`** / **`fail_insufficient_funds()`** — transitions and no double settlement.
- **`AudioSpectrogramService.convert`** — success/failure paths and `AudioSpectrogram` **`record_*`**.
- **`MLTaskService.process`** — preconditions, **`result`** on success, **`error`** on failure, no audio path in `_perform_prediction`.

### Intentionally excluded

- **`MLTaskService._perform_prediction`** internals (model weights, CV stack) beyond contract — integration tests when implemented.
- **`AdminUser.get_balance()`** — trivial sentinel.
- Heavy filesystem I/O — mock storage and paths in unit tests.

---

## Drift Check Procedure

The repeatable procedure for verifying conformance lives in **`docs/drift-check.md`**.

### Invariants checked (summary)

1. **`MLTaskService.process`** does not call **`AudioSpectrogramService.convert`** mid-flight; conversion is a prior step.
2. **`approve()`** and **`cancel()`** are called explicitly by **`MLTaskService`**, not from within **`MLTask.record_*`** methods. **`approve()`** is not reached except after a successful prediction path.
3. **`SpectrogramFile`** has no domain methods beyond the SQLModel definition.
4. **`AdminUser.get_balance()`** returns **`float('inf')`** without a DB query.

Additional checks are listed in **`docs/drift-check.md`**.
