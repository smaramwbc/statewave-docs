# Migration & Upgrade Runbook

This guide is for operators upgrading Statewave in production.

---

## Overview

Statewave uses [Alembic](https://alembic.sqlalchemy.org/) for database migrations. Migrations are applied via `alembic upgrade head` and are **forward-only** in normal operation.

The app includes safety features:
- **Preflight script** — verifies DB reachability and migration state before you commit
- **Startup schema guard** — warns (or blocks) if the app's expected schema doesn't match the DB
- **`/ops/migrations` endpoint** — live introspection of migration state

---

## Before upgrading

### 1. Run the preflight check

```bash
cd statewave/
python scripts/preflight.py
```

This will report:
- Current DB revision
- Expected head revision for this app version
- Number of pending migrations
- Go/no-go recommendation

### 2. Back up the database

```bash
pg_dump -Fc statewave > backup_$(date +%Y%m%d_%H%M%S).dump
```

### 3. Stop the old app version

Ensure no active connections are writing to the database during migration.

---

## Applying migrations

```bash
alembic upgrade head
```

For a dry-run (SQL only, no changes):

```bash
alembic upgrade head --sql
```

To apply one migration at a time:

```bash
alembic upgrade +1
```

---

## After upgrading

### 1. Re-run preflight

```bash
python scripts/preflight.py
```

Should report: `✅ Schema is up to date. No migration needed.`

### 2. Start the new app version

```bash
./start.sh
# or: uvicorn server.app:app --host 0.0.0.0 --port 8100
```

### 3. Verify via endpoint

```bash
curl http://localhost:8100/ops/migrations
```

Expected response:
```json
{
  "current_revision": "0012_add_health_cache",
  "expected_head": "0012_add_health_cache",
  "is_compatible": true,
  "pending_count": 0,
  "pending_revisions": [],
  "error": null,
  "summary": "Schema is up to date"
}
```

### 4. Check readiness

```bash
curl http://localhost:8100/readyz
```

---

## Rollback

If a migration fails or the new version is broken:

### 1. Downgrade to previous revision

```bash
alembic downgrade <previous_revision>
```

Example:
```bash
alembic downgrade 0011
```

### 2. Redeploy the previous app version

The previous app version expects the previous schema. Deploy the matching tag/commit.

### 3. Verify

```bash
python scripts/preflight.py
curl http://localhost:8100/ops/migrations
```

---

## Strict schema mode

By default, the app **warns** on schema mismatch but still starts. To make it **refuse to start** if the schema doesn't match:

```bash
export STATEWAVE_STRICT_SCHEMA=1
```

This is recommended for production deployments where you want to guarantee app/DB compatibility.

---

## Version compatibility matrix

| App Version | Expected Head Revision | Min Compatible Revision |
|-------------|----------------------|------------------------|
| 0.6.1       | 0012_add_health_cache | 0012_add_health_cache  |
| 0.6.0       | 0012_add_health_cache | 0010                   |
| 0.5.0       | 0009_add_rate_limit_table | 0009_add_rate_limit_table |
| 0.4.0       | 0008_add_tenant_id_columns | 0005                 |
| 0.3.0       | 0005_webhook_events  | 0004                   |
| 0.2.0       | 0004_embedding_as_text | 0001                  |
| 0.1.0       | 0001               | 0001                    |

---

## Troubleshooting

### "Schema mismatch" warning at startup

The app detected that the DB revision doesn't match what it expects. Run:

```bash
python scripts/preflight.py
```

Then apply pending migrations.

### "alembic_version table not found"

Fresh database. Run `alembic upgrade head` to initialize.

### Migration fails mid-way

1. Check which revision succeeded: `alembic current`
2. Fix the issue (often a missing extension like pgvector)
3. Re-run: `alembic upgrade head`
4. If unrecoverable: restore from backup

### Stuck compilation jobs after upgrade

Some in-flight jobs may be orphaned after an upgrade. The `/readyz` endpoint will report them as "degraded". They will self-recover after 30 minutes, or you can manually reset them:

```sql
UPDATE compilation_jobs SET status = 'pending', claimed_at = NULL
WHERE status = 'running' AND claimed_at < NOW() - INTERVAL '30 minutes';
```
