# Platform stack

Runtime and infrastructure for local and containerized development. Compose is the source of truth; see [`docker-compose.yml`](../docker-compose.yml).

## Services

| Compose service | Role |
|-----------------|------|
| `web-proxy` | nginx reverse proxy; build context [`web-proxy/`](../web-proxy/); volumes `./web-proxy/conf.d` → `/etc/nginx/conf.d`; ports **80**, **443**. Depends on `app`. |
| `app` | Python application image; build context [`app/`](../app/); bind-mount **`./app`** → **`/src`** in container (`WORKDIR /src` in [`app/Dockerfile`](../app/Dockerfile)); env from [`.db.env`](../.db.env) at repo root. |
| `message-broker` | RabbitMQ **4.2-management-alpine**; ports **5672** (AMQP), **15672** (management UI); volume `rabbitmq-data`. There is no separate `mb/` folder in the repo—the broker is defined only in Compose. |
| `database` | PostgreSQL **18.3-alpine3.23**; env from root [`.db.env`](../.db.env) (see [`docker-compose.yml`](../docker-compose.yml)); volume **`postgres-data`** mounted at **`/var/lib/postgresql/data`** (persistence across restarts). |

## Network

Single bridge network `app-network` for inter-service DNS (`database`, `app`, etc.).

## Environment

- **Database URL** (app): built in [`db.py`](../app/music_genre_sommelier/utils/database/db.py) from `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST`, `POSTGRES_PORT` (see [`.db.env`](../.db.env) for `POSTGRES_HOST=database` in Compose).

## Related documentation

- Operational invariants and grep checks: [`docs/drift-check.md`](drift-check.md).
- Architectural decisions: [`docs/decisions.md`](decisions.md).
