# Deployment Troubleshooting

Common production issues and how to resolve them.

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

Switch to in-memory rate limiting if running a single instance:

```bash
fly secrets set STATEWAVE_RATE_LIMIT_STRATEGY=memory
```

**When to use distributed:**

Only use `distributed` when:
- Running multiple app instances that need shared counters
- Your Postgres has sufficient connection headroom (pool_size + rate_limit traffic)
- You've configured a separate connection pool or Redis for rate limiting

**When to use memory:**

Use `memory` (recommended for single-instance deployments) when:
- Running 1 machine on Fly.io
- Using shared/limited Postgres
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

Run migrations:

```bash
fly ssh console -C "alembic upgrade head"
```

Or manually add the column:

```bash
fly ssh console -C "python -c \"
import asyncio, os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    e = create_async_engine(os.environ['DATABASE_URL'])
    async with e.begin() as conn:
        await conn.execute(text('ALTER TABLE <table> ADD COLUMN IF NOT EXISTS <column> <type>'))
    await e.dispose()

asyncio.run(main())
\""
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

Update the origins list (JSON array):

```bash
fly secrets set 'STATEWAVE_CORS_ORIGINS=["https://admin.statewave.ai","https://www.statewave.ai","https://statewave.ai","http://localhost:5173"]'
```

**Verify:**

```bash
curl -I -X OPTIONS "https://statewave-api.fly.dev/healthz" \
  -H "Origin: https://admin.statewave.ai" \
  -H "Access-Control-Request-Method: GET"
# Should include: access-control-allow-origin: https://admin.statewave.ai
```

---

## STATEWAVE-TS-004: Vercel Serverless Proxy Returns 500

**Symptoms:**

- Admin dashboard shows "Failed to reach backend"
- `/api/proxy?path=/admin/dashboard` returns `{"error": "STATEWAVE_API_URL not configured"}`

**Root cause:**

Vercel environment variables (`STATEWAVE_API_URL`, `STATEWAVE_API_KEY`) are not set for the project.

**Fix:**

```bash
cd statewave-admin
vercel env add STATEWAVE_API_URL production   # https://statewave-api.fly.dev
vercel env add STATEWAVE_API_KEY production   # your API key
vercel --prod --yes                           # redeploy
```

---

## General: Reading Fly.io Logs

```bash
# Live tail
fly logs -a statewave-api

# Check app status
fly status -a statewave-api

# SSH into running container
fly ssh console -a statewave-api
```
