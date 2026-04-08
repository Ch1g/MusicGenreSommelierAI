# Music Genre Sommelier AI — Agent Contract

This document is the **architectural contract** for the Music Genre Sommelier AI system. Implementation (Python, REST, OOP) must conform to it. The product accepts user-uploaded audio, converts it to spectrograms, classifies genre via a computer-vision model, and gates access by debiting user balance only on successful inference.

**Docs maintenance:** Any new domain module, renamed file, or dependency edge must be reflected here, in `docs/architecture.md`, and in `docs/drift-check.md` (grep paths and module lists) before the change is considered complete. **Platform stack** (Compose, nginx, Postgres, RabbitMQ, Python operations) is documented in **`docs/stack.md`**; related ADRs live in **`docs/decisions.md`**.

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

**Import convention:** With `PYTHONPATH` including `app/` at repo root (or `/src` in the app container): `from music_genre_sommelier.models...`, `from music_genre_sommelier.services...`, etc. Enum modules under `utils/enum/` are **not** domain entities; they hold persisted/API enum values only and must not import the service layer or REST adapters.

---

## Module Map

Explicit ownership. Format: `[module] owns X / does not own Y`.

- **`AudioFile`** — owns persisted upload metadata (`file_path`, `upload_status`, `upload_error`) and **`record_success`** / **`record_failure`** (via **`_set_status`** for `upload_status`); does not own conversion, spectrogram generation, or inference. Inbound byte streaming and path wiring are expected from REST/storage orchestration (future or adapters), not from `SpectrogramFile` or `MLTask`.

- **`SpectrogramFile`** — owns the storage record of the spectrogram artifact (path and timestamps); does not own conversion logic, ML, or transactional settlement (no methods beyond the SQLModel row).

- **`AudioSpectrogram`** — owns row-level **`status`** / **`error`** for the conversion outcome and **`record_success`** / **`record_failure`**; does not own the conversion algorithm or session lifecycle. **`AudioSpectrogramService`** performs conversion and updates these rows.

- **`AudioSpectrogramService`** — owns the conversion pipeline from audio file path to mel spectrogram data and optional image artifact, persistence of `SpectrogramFile`, linking `audio_spectrogram.spectrogram_file_id`, and committing the session; does not own inference or ledger rules.

- **`MLModel`** — persistence row for **`model_path`** and **`prediction_cost`**; does not own `predict` or task state. Inference is implemented in **`MLTaskService`** (e.g. `_perform_prediction`) using model metadata and spectrogram paths.

- **`MLTask`** — owns task row state (**`status`**, **`result`**, **`error`**) and **`record_success`** / **`record_failure`**, which call **`transaction.approve()`** on success and **`transaction.cancel()`** on failure (see **Settlement coupling** below). Does not implement fund checks (those run on **`Transaction`** before work) or open raw audio files for inference.

- **`MLTaskService`** — owns **`process(ml_task)`**: fund check via **`transaction.check_funds()`**, prediction, then **`ml_task.record_success`** / **`record_failure`**; does not replace entity rules inside models (it coordinates calls and session commit).

- **`Transaction`** — owns ledger row state (`pending` → terminal statuses), **`approve`**, **`cancel`**, **`fail_insufficient_funds`**, instance **`check_funds()`** (may set **`fail_insufficient_funds`** when insufficient), and static **`get_balance(user_id)`**. **`MLTask`** references the ledger row via **`transaction_id`**; the **`transaction`** table has **no** `ml_task_id` column.

- **`User` / `CommonUser` / `AdminUser`** — identity and **`get_balance()`** contract (`CommonUser` delegates to **`Transaction.get_balance`**; **`AdminUser`** returns **`float('inf')`** without DB); does not own sessions, OAuth, or payment providers.

### Settlement coupling (implementation)

On success, **`MLTask.record_success`** invokes **`transaction.approve()`**. On failure, **`MLTask.record_failure`** invokes **`transaction.cancel()`**. Fund sufficiency is evaluated in **`MLTaskService.process`** via **`transaction.check_funds()`** before prediction. This couples settlement side effects to task row methods by design; new code must keep **`approve()`** only after a successful prediction path and avoid speculative debits (see **RULE-02**).

### Status field encapsulation (implementation)

For **`AudioFile`** (`upload_status`), **`AudioSpectrogram`** (`status`), **`MLTask`** (`status`), and **`Transaction`** (`status`), implementations **should** route persistence-backed status changes through a **private** **`_set_status`** used only from **`record_*`**, **`approve`**, **`cancel`**, **`fail_insufficient_funds`**, or equivalent public methods on the same class. Callers **must not** invoke **`_set_status`** from outside the class.

---

## Contracts Between Modules

For each interaction: **Input** — what is passed in; **Output** — what is returned; **Side-effect policy** — what mutates vs read-only.

### 1. Upload and `AudioFile` (REST / storage layer, future)

| Aspect | Definition |
|--------|------------|
| **Input** | Inbound upload content, filename/MIME hints, owning `user_id`, storage adapter. |
| **Output** | Persisted `AudioFile` with `file_path`; **`record_success`** or **`record_failure`** sets terminal `upload_status`. |
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
| **Side-effect policy** | **Mutates:** task row and linked **`transaction`** status via **`record_*`**; session **add/commit** in **`finally`**. **Must not** read **`AudioFile`** for inference; uses **`SpectrogramFile`** / model metadata only. |

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
| **Side-effect policy** | **Mutates:** **`status`** via **`_set_status`**. **`approve()`** is invoked from **`MLTask.record_success`** after a successful prediction path. **`cancel()`** is invoked from **`MLTask.record_failure`**. |

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
2. **`approve()`** is not reached except after successful prediction in the service flow (**`record_success`**).
3. **`SpectrogramFile`** has no domain methods beyond the SQLModel definition.
4. **`AdminUser.get_balance()`** returns **`float('inf')`** without a DB query.

Additional checks are listed in **`docs/drift-check.md`**.
