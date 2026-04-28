# Architecture Decision Records (ADRs)

Short-lived log of decisions that shape the codebase. The full contract remains in **[`CLAUDE.md`](../CLAUDE.md)**.

## ADR-001 — Package under `app/music_genre_sommelier/`

**Context:** Earlier layout used repo-root `src/music_genre_sommelier/` with stub modules.

**Decision:** Colocate the installable package under **`app/music_genre_sommelier/`**. Docker build context is **`app/`**; Compose mounts **`./app`** to **`/src`** so `music_genre_sommelier` imports resolve in the container.

**Consequences:** No `app/src/` directory; documentation and `PYTHONPATH` examples must say `app/`, not `app/src/`.

---

## ADR-002 — SQLModel `models/` and service layer

**Context:** Domain types are persisted as SQLModel tables.

**Decision:** Keep **entity modules** (`models/`) separate from **orchestration** (`services/`): conversion in `AudioSpectrogramService`, inference in `MLTaskService`, registration in `RegistrationService`, paths in `StorageService`.

**Consequences:** Entity classes expose `record_success` / `record_failure` / `_set_status`; long-running flows are not methods named `convert` / `process` on the ORM classes for the full pipeline.

---

## ADR-003 — Settlement owned by `MLTaskService`, not `MLTask.record_*`

**Context:** Early design had `MLTask.record_success` call `transaction.approve()` directly. This coupled the row model to settlement logic and made it impossible to test task state transitions independently.

**Decision:** Settlement is owned exclusively by **`MLTaskService.process`**. `MLTask.record_success` / `record_failure` update task state only (status + result/error). After a successful prediction, the service calls `record_success` then `transaction.approve()`. On generic failure it calls `record_failure` then `transaction.cancel()`. On insufficient funds, `transaction.check_funds()` already sets `FAIL_INSUFFICIENT_FUNDS` — the service calls only `record_failure`. **`MLTask`** holds `transaction_id`; **`Transaction`** does **not** store `ml_task_id`.

**Consequences:** Task row methods are pure state machines; settlement is never triggered twice (see **RULE-02** in `CLAUDE.md`). Tests can verify task state and transaction state independently.

---

## ADR-004 — Instance `Transaction.check_funds()`

**Context:** Prior contract described a static `check_funds(user_id, amount)` returning `bool` without writes.

**Decision:** **`check_funds()`** is an instance method that may call **`fail_insufficient_funds()`** when **`_is_sufficient()`** is false.

**Consequences:** Callers must treat **`check_funds`** as potentially mutating the row; **read-only** balance queries remain **`Transaction.get_balance(user_id)`**.

---

## ADR-005 — Injectable session via `Depends(get_session)`

**Context:** Controllers originally opened their own `Session(engine)` inline. This made the session impossible to override in tests, requiring a real PostgreSQL connection to run any controller test.

**Decision:** Extract `get_session()` as a FastAPI dependency in `utils/database/db.py`. All controllers accept `session: Session = Depends(get_session)`. Tests override this via `app.dependency_overrides[get_session]` with an in-memory SQLite session.

**Consequences:** Controller tests run fully in-memory without Docker. The same override mechanism is used for `get_current_user_id` to fix the authenticated user to `id=1` in tests.
