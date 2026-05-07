# Deployment Guide

This guide covers running Statewave in different environments.

Statewave is **vendor-neutral**: the API is a plain Python /
ASGI process that reads its config from `STATEWAVE_*` environment
variables and talks to a Postgres database. Anywhere you can run a
Python or Docker process — your laptop, a VPS, a container platform,
Kubernetes, a hyperscaler — Statewave runs the same way. The
**Docker single-container** recipe (Section 3) is the canonical
production deploy; the **Fly.io** and **Railway** sections that follow
are concrete examples of that recipe on two specific platforms, not a
preferred path.

> **Hardware:** Statewave's API process is CPU-only — no GPU is required, and none of the deployment recipes below assume one. GPUs only enter the picture if you choose to self-host an LLM compiler or embedding model. See [Hardware & Scaling](hardware-and-scaling.md).
>
> **Sizing:** for tier-by-tier hardware profiles (local / small production / growing / enterprise) and topology patterns, see the [Deployment Sizing Guide](sizing.md).
>
> **Already running, things are slow?** See the [Capacity Planning & Tuning Checklist](capacity-planning.md) — diagnostic flow, tuning order, and when to move up a tier.

---

## 1. Local Development (Docker Compose)

The fastest way to run Statewave locally.

### Prerequisites

- Docker & Docker Compose
- Git

### Steps

```bash
git clone https://github.com/smaramwbc/statewave.git
cd statewave

# Copy and optionally edit environment config
cp .env.example .env

# Start Postgres + API
docker compose up -d

# Run migrations
docker compose exec api alembic upgrade head

# Verify
curl http://localhost:8100/healthz```

The API is available at `http://localhost:8100`. Postgres data persists in the `pgdata` volume.

### Useful commands

```bash
docker compose logs -f api     # tail API logs
docker compose down            # stop services
docker compose down -v         # stop + delete data
```

---

## 2. Local Development (bare metal)

Run without Docker — useful for debugging or IDE integration.

### Prerequisites

- Python 3.11+
- PostgreSQL 16 with pgvector extension
- Git

### Steps

```bash
git clone https://github.com/smaramwbc/statewave.git
cd statewave

# Create and activate venv
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Start Postgres (or use docker compose up db -d for just the database)
# Ensure pgvector extension is installed:
#   CREATE EXTENSION IF NOT EXISTS vector;

# Set connection string
export STATEWAVE_DATABASE_URL=postgresql+asyncpg://statewave:statewave@localhost:5432/statewave

# Run migrations
alembic upgrade head

# Start server
uvicorn server.app:app --reload --port 8100
```

---

## 3. Single-Container Deployment (canonical production recipe)

Deploy Statewave as a single container pointing to an external Postgres
with the pgvector extension. This is the recipe every platform-specific
section below builds on — the only thing that changes from one platform
to the next is *how* you set the environment variables and *who* runs
the container.

```bash
docker build -t statewave .

docker run -d \
  --name statewave \
  -p 8100:8100 \
  -e STATEWAVE_DATABASE_URL=postgresql+asyncpg://user:pass@your-db-host:5432/statewave \
  -e STATEWAVE_DEBUG=false \
  -e STATEWAVE_API_KEY=your-secret-key \
  statewave
```

Run migrations against the remote database before first start:

```bash
docker run --rm \
  -e STATEWAVE_DATABASE_URL=postgresql+asyncpg://user:pass@your-db-host:5432/statewave \
  statewave \
  alembic upgrade head
```

---

## 4. Fly.io (platform example)

> One concrete platform recipe for the single-container deploy in
> Section 3. Choosing Fly is a vendor decision — Statewave itself has
> no Fly-specific code path. Skip this section if you're deploying
> elsewhere; nothing in the rest of the docs depends on Fly.

### Prerequisites

- `flyctl` CLI installed and authenticated
- A Fly Postgres cluster (or external Postgres)

### Steps

```bash
cd statewave

# Create app
fly launch --no-deploy

# Set secrets
fly secrets set \
  STATEWAVE_DATABASE_URL=postgresql+asyncpg://user:pass@your-fly-db.internal:5432/statewave \
  STATEWAVE_API_KEY=your-secret-key

# Deploy
fly deploy

# Run migrations (one-off machine)
fly machine run . --command "alembic upgrade head" --rm
```

A minimal `fly.toml`:

```toml
[http_service]
  internal_port = 8100
  force_https = true

[env]
  STATEWAVE_HOST = "0.0.0.0"
  STATEWAVE_PORT = "8100"
  STATEWAVE_DEBUG = "false"
```

---

## 5. Railway (platform example)

> Another concrete recipe for the single-container deploy in Section 3.
> Railway provisions Postgres for you and wires it through. As with
> Fly, this section is a worked example, not a recommendation.

### Steps

1. Connect your `statewave` repo to Railway
2. Add a **Postgres** service (Railway provisions pgvector-capable Postgres)
3. Set environment variables:
   - `STATEWAVE_DATABASE_URL` → Railway provides `DATABASE_URL`; convert to asyncpg format: replace `postgresql://` with `postgresql+asyncpg://`
   - `STATEWAVE_API_KEY` → your secret
   - `STATEWAVE_DEBUG` → `false`
4. Set start command: `alembic upgrade head && uvicorn server.app:app --host 0.0.0.0 --port $PORT`
5. Deploy

---

## Environment Variables Reference

See [`.env.example`](https://github.com/smaramwbc/statewave/blob/main/.env.example) for all available `STATEWAVE_*` configuration options.

## Production Checklist

- [ ] `STATEWAVE_DEBUG=false`
- [ ] `STATEWAVE_API_KEY` set to a strong secret
- [ ] `STATEWAVE_CORS_ORIGINS` restricted to your domain(s)
- [ ] `STATEWAVE_RATE_LIMIT_RPM` set (e.g., 120)
- [ ] Database backups configured
- [ ] Migrations run before first request
- [ ] Health endpoint monitored (`GET /healthz`)

---

## Admin Console (optional)

For operator visibility into your running Statewave instance, you can deploy the admin console.

See [statewave-admin](https://github.com/smaramwbc/statewave-admin) for setup instructions.

The admin console provides:
- System readiness and database health status
- Compile job monitoring
- Webhook delivery status
- Usage metering (episodes, memories, compiles)
- Subject health distribution

**Important:** The admin console is an internal tool. Deploy it behind an access gateway (Cloudflare Access, OAuth2 Proxy, etc.) — do not expose publicly.
