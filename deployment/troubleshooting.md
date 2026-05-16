# Deployment Troubleshooting

Common production issues and how to resolve them.

The fixes below are written in terms of the underlying `STATEWAVE_*`
environment variables, which is what actually changes the API's
behaviour regardless of where you run it. Below each generic recipe is
a short row of platform-specific commands (Docker, Fly.io, Vercel,
Railway, raw shell) so you can run whichever fits your deploy without
translating from another platform's syntax.

---

## STATEWAVE-TS-001: Database Connection Timeout (Rate Limiter)

**Symptoms:**

- API requests hang or return 502/504
- Logs show `distributed_rate_limit_db_error` warnings
- `TimeoutError` in asyncpg connection stack traces
- `asyncio.exceptions.CancelledError` in rate limit code path

**Example log:**

```
distributed_rate_limit_db_error key=172.16.22.98 request_id=...
TimeoutError
```

**Root cause:**

The distributed rate limiter (`STATEWAVE_RATE_LIMIT_STRATEGY=distributed`) opens a database connection for every incoming request to check/increment a counter. On constrained Postgres instances (e.g., Fly.io shared Postgres with limited connection slots), this exhausts the connection pool. Once the pool is full, actual API queries (episodes, memories, search) cannot acquire connections and time out.

**Fix:**

Switch to in-memory rate limiting if running a single instance — set
`STATEWAVE_RATE_LIMIT_STRATEGY=memory` on the API process and restart.
On the platform you run on, that's:

| Platform | Command |
|---|---|
| Docker Compose | edit `.env` → `STATEWAVE_RATE_LIMIT_STRATEGY=memory`, then `docker compose up -d --force-recreate api` |
| `docker run` | add `-e STATEWAVE_RATE_LIMIT_STRATEGY=memory` and re-run the container |
| Fly.io | `fly secrets set STATEWAVE_RATE_LIMIT_STRATEGY=memory` |
| Railway | set `STATEWAVE_RATE_LIMIT_STRATEGY=memory` in the project's variables UI |
| systemd / bare metal | export the variable in your service's `Environment=` (or `.env` file) and restart |

**When to use distributed:**

Only use `distributed` when:
- Running multiple app instances that need shared counters
- Your Postgres has sufficient connection headroom (pool_size + rate_limit traffic)
- You've configured a separate connection pool or Redis for rate limiting

**When to use memory:**

Use `memory` (recommended for single-instance deployments) when:
- Running a single API process / one machine
- Using shared or connection-limited Postgres
- Rate limit accuracy across restarts isn't critical

**Prevention:**

If you need distributed rate limiting without DB pressure, consider:
- Dedicated Redis for rate limiting (future)
- Separate connection pool with lower timeout for rate limit queries
- Increasing Postgres `max_connections`

---

## STATEWAVE-TS-002: Missing Database Column

**Symptoms:**

- Health check shows `"status": "degraded"` for queue
- `UndefinedColumnError: column "X" does not exist`

**Root cause:**

A migration added a column that wasn't applied to the production database, or the column was added in code but the migration wasn't created yet.

**Fix:**

Run `alembic upgrade head` against the same `STATEWAVE_DATABASE_URL`
the API process is using. From the easiest path to the most explicit:

| Platform | Command |
|---|---|
| Docker Compose | `docker compose exec api alembic upgrade head` |
| `docker run` | `docker run --rm -e STATEWAVE_DATABASE_URL=… statewave alembic upgrade head` |
| Fly.io | `fly ssh console -C "alembic upgrade head" -a statewave-api` |
| Railway | run `alembic upgrade head` from the Railway shell on the API service |
| systemd / bare metal | `STATEWAVE_DATABASE_URL=… alembic upgrade head` from the project root |

If for some reason migrations can't be run (e.g. Alembic state is out
of sync) and you need to backfill a single column directly, run a
one-shot SQL against the DB. From a Docker host pointing at the same
DB the API is using:

```bash
docker compose exec db psql -U statewave -d statewave \
  -c 'ALTER TABLE <table> ADD COLUMN IF NOT EXISTS <column> <type>;'
```

---

## STATEWAVE-TS-003: CORS Errors from Frontend

**Symptoms:**

- Browser console shows `Access to fetch blocked by CORS policy`
- `access-control-allow-origin` header missing from responses
- Website or admin console can't reach the API

**Root cause:**

`STATEWAVE_CORS_ORIGINS` doesn't include the requesting domain.

**Fix:**

Update `STATEWAVE_CORS_ORIGINS` to a JSON array of every origin the
API should respond to (including `http://localhost:5173` while you're
running the website locally). The value below is just an example —
substitute your own host names:

```
STATEWAVE_CORS_ORIGINS=["https://admin.example.com","https://www.example.com","http://localhost:5173"]
```

How to set it on each platform:

| Platform | Command |
|---|---|
| Docker Compose | edit `.env`, then `docker compose up -d --force-recreate api` |
| `docker run` | pass `-e STATEWAVE_CORS_ORIGINS='[…]'` and re-run |
| Fly.io | `fly secrets set 'STATEWAVE_CORS_ORIGINS=[…]'` |
| Railway | edit the variable in the project's variables UI |
| systemd / bare metal | export the variable and restart the service |

**Verify** (substitute your own API host + an origin you just added):

```bash
curl -I -X OPTIONS "https://api.example.com/healthz" \
  -H "Origin: https://admin.example.com" \
  -H "Access-Control-Request-Method: GET"
# Should include: access-control-allow-origin: https://admin.example.com
```

---

## STATEWAVE-TS-004: Admin Console Can't Reach the Backend

**Symptoms:**

- Admin dashboard shows "Failed to reach backend"
- `/api/proxy?path=/admin/dashboard` returns `{"error": "STATEWAVE_API_URL not configured"}` or 502 / connection-refused
- Browser network tab shows the admin's `/api/*` route returning 5xx

**Root cause:**

The admin console's server-side proxy needs `STATEWAVE_API_URL` (the
URL of your running Statewave API) and `STATEWAVE_API_KEY` (the API
key the API is configured with) on the *admin* host's environment.
One of them is missing, empty, or pointing at a host the admin process
can't reach over the network.

**Fix:**

Set both on the admin host:

```
STATEWAVE_API_URL=https://your-statewave-api.example.com
STATEWAVE_API_KEY=your-api-key
```

How to set them on each platform statewave-admin can run on:

| Platform | Commands |
|---|---|
| Docker (`docker run`) | `docker run -e STATEWAVE_API_URL=… -e STATEWAVE_API_KEY=… statewave-admin` |
| Docker Compose | edit `.env` next to `docker-compose.yml`, then `docker compose up -d --force-recreate admin` |
| Standalone Node (`npm start`) | export both vars in your shell or systemd unit before running `npm start` |
| Vercel | `vercel env add STATEWAVE_API_URL production` and `vercel env add STATEWAVE_API_KEY production`, then redeploy with `vercel --prod` |
| Railway | add both as project variables and redeploy |

**Verify** the admin process can actually reach the API host (network /
DNS / firewall / Cloudflare-Access pinning are common failure modes
distinct from the env var missing):

```bash
# From inside the admin container or host:
curl -fsS -H "X-API-Key: $STATEWAVE_API_KEY" "$STATEWAVE_API_URL/admin/webhooks/stats"
# Expected: {"pending": 0, "delivered": 0, "dead_letter": 0, "total": 0}
```

---

## General: Reading Logs

The Statewave API logs to stdout in JSON via `structlog`. How to tail
those logs depends only on where you run it:

| Platform | Tail logs | App / process status |
|---|---|---|
| Docker Compose | `docker compose logs -f api` | `docker compose ps` |
| `docker run` | `docker logs -f <container-name>` | `docker ps -a` |
| Fly.io | `fly logs -a <app-name>` | `fly status -a <app-name>` (`fly ssh console -a <app-name>` for an interactive shell) |
| Railway | the Logs tab in the service UI, or `railway logs` from the CLI | the service overview page |
| systemd / bare metal | `journalctl -u <unit> -f` | `systemctl status <unit>` |

Useful structured-log queries (work the same on every platform once
you've got a stream):

```bash
# Errors only (jq):
… | jq 'select(.level == "error")'

# Compile-job lifecycle for one job_id:
… | jq 'select(.event | startswith("compile_job_") and (.job_id == "abc123"))'

# Embedding-stub-active warning (fired once at first use when
# STATEWAVE_EMBEDDING_PROVIDER=stub — semantic search will not work):
… | jq 'select(.event == "embedding_provider_stub_active")'
```
