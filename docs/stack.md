# Platform stack

Runtime and infrastructure for local and containerized development. Compose is the source of truth; see [`docker-compose.yml`](../docker-compose.yml).

## Services

| Compose service | Role |
|-----------------|------|
| `web-proxy` | nginx reverse proxy; build context [`web-proxy/`](../web-proxy/); volumes `./web-proxy/conf.d` → `/etc/nginx/conf.d`; ports **80**, **443**. Routes `/api/*` → `app:3000`, everything else → `frontend:8080`. Depends on `app` and `frontend`. |
| `app` | Python application image; build context [`app/`](../app/); command `./entrypoint.sh` (runs seed then FastAPI server); bind-mount **`./app`** → **`/src`** (`WORKDIR /src`); env from [`.db.env`](../.db.env) and [`.app.env`](../.app.env); volume **`file-storage`** → **`/src/storage`**. |
| `frontend` | React/TypeScript SPA; build context [`frontend/`](../frontend/); dev server on port **8080**; bind-mount **`./frontend`** → **`/src`**; volume **`file-storage`** → **`/src/storage`**; `node_modules` isolated via anonymous volume. |
| `worker` | Separate image built from [`worker/`](../worker/); entrypoint preloads all ML models then starts `InferenceConsumer`; bind-mount **`./app/music_genre_sommelier`** → **`/src/music_genre_sommelier`** (shares package, not the full context); volume **`file-storage`** → **`/src/storage`**; **replicas: 2**; depends on `database` and `message-broker`. |
| `message-broker` | RabbitMQ **4.2-management-alpine**; ports **5672** (AMQP), **15672** (management UI); volume `rabbitmq-data`. Stock image — no custom build context. |
| `database` | PostgreSQL **18.3-alpine3.23**; env from root [`.db.env`](../.db.env) (see [`docker-compose.yml`](../docker-compose.yml)); volume **`postgres-data`** mounted at **`/var/lib/postgresql/data`** (persistence across restarts). |

## Network

Single bridge network `app-network` for inter-service DNS (`database`, `app`, etc.).

## Environment

- **Database URL** (app): built in [`db.py`](../app/music_genre_sommelier/utils/database/db.py) from `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST`, `POSTGRES_PORT` (see [`.db.env.example`](../.db.env.example) for defaults; `POSTGRES_HOST=database` in Compose).
- **JWT secret** (app): `JWT_SECRET` in [`.app.env`](../.app.env) (see [`.app.env.example`](../.app.env.example)); required for token creation and verification (`utils/auth/`).
- **Shared storage** (app, worker): named volume `file-storage` mounted at `/src/storage` in both `app` and `worker` containers, ensuring uploaded audio files and generated spectrograms are accessible to both services.

## Related documentation

- Operational invariants and grep checks: [`docs/drift-check.md`](drift-check.md).
- Architectural decisions: [`docs/decisions.md`](decisions.md).
