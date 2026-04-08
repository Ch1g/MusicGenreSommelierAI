# Architecture Decision Records (ADRs)

Short-lived log of decisions that shape the codebase. The full contract remains in **[`AGENTS.md`](../AGENTS.md)**.

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

## ADR-003 — Settlement hooks on `MLTask.record_*`

**Context:** Alternative design keeps `Transaction` unaware of tasks and settles only in a top-level service.

**Decision:** **`MLTask.record_success`** calls **`transaction.approve()`**; **`MLTask.record_failure`** calls **`transaction.cancel()`**. **`MLTask`** holds **`transaction_id`**; **`Transaction`** does **not** store `ml_task_id`.

**Consequences:** Task rows and ledger rows are explicitly linked by FK; agents must not reintroduce “speculative” `approve` before inference (see **RULE-02** in `AGENTS.md`). Any future refactor to decouple settlement should update `AGENTS.md` and this file together.

---

## ADR-004 — Instance `Transaction.check_funds()`

**Context:** Prior contract described a static `check_funds(user_id, amount)` returning `bool` without writes.

**Decision:** **`check_funds()`** is an instance method that may call **`fail_insufficient_funds()`** when **`_is_sufficient()`** is false.

**Consequences:** Callers must treat **`check_funds`** as potentially mutating the row; **read-only** balance queries remain **`Transaction.get_balance(user_id)`**.
