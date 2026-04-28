# Subject Snapshots — Admin Operations Guide

> **Audience:** Operators, platform admins, advanced internal users.  
> **Not** part of the public developer API. Gated behind `STATEWAVE_ENABLE_SNAPSHOTS=true`.

## What Subject Snapshots Are

Subject Snapshots allow operators to capture a subject's full state (episodes + compiled memories) and restore it into new subjects instantly (~200ms vs ~5s for re-ingestion + compilation).

They are an **advanced admin/bootstrap capability** — a way to clone known-good subject state for operational purposes.

## What They Are For

- **Demo environments** — instant persona bootstrapping without re-running LLM compilation
- **Staging/QA** — reproduce known subject states for testing
- **Onboarding templates** — pre-built starter subjects for new tenants
- **Migration/backup** — snapshot before destructive operations
- **Development** — seed realistic data into dev environments

## What They Are NOT

- **Not the normal beginner workflow** — developers build subjects by ingesting episodes and compiling memories
- **Not part of the public `/v1` API** — lives under `/admin` only
- **Not exposed in SDKs** — neither statewave-py nor statewave-ts include snapshot methods
- **Not documented in getting-started or beginner materials** — intentionally hidden from the simple product story
- **Not a replacement for the episode→compile→context lifecycle** — snapshots produce subjects that went through that lifecycle, they don't replace it

## Architecture

```
Source subject → create_snapshot() → _snapshot/{name}/v{version}
                                       ↓
                              SubjectSnapshotRow (metadata)
                                       ↓
                              restore_snapshot() → target subject (new UUIDs)
```

Snapshot source data lives under `_snapshot/*` prefixes and is:
- Hidden from `GET /v1/subjects` (filtered in `list_subjects`)
- Protected from cleanup (explicitly excluded)
- Never exposed to end-user API calls

## Feature Flag

```bash
# Enable (production, staging)
STATEWAVE_ENABLE_SNAPSHOTS=true

# Disable (default — public-facing instances)
STATEWAVE_ENABLE_SNAPSHOTS=false
```

When disabled, all `/admin/snapshots*` and `/admin/cleanup` endpoints return 404.

## Endpoints

### `GET /admin/snapshots`
List all available snapshots.

### `POST /admin/snapshots/{snapshot_id}/restore`
Restore a snapshot by UUID into a target subject.

```json
{ "target_subject_id": "live_sarah_1234567890" }
```

### `POST /admin/snapshots/restore-by-name`
Restore by snapshot name (uses latest version).

```json
{ "name": "sarah-startup", "target_subject_id": "live_sarah_1234567890" }
```

### `POST /admin/cleanup`
Clean up stale ephemeral subjects (e.g., abandoned demo sessions).

Query params: `prefix` (default `live_`), `max_age_hours` (default `24`).

## Restore Behavior

When a snapshot is restored:

1. **New UUIDs** — all episode and memory IDs are regenerated
2. **Provenance remapped** — `source_episode_ids` in memories point to new episode IDs
3. **Timestamps shifted** — relative offsets preserved, newest episode anchored to `now()`
4. **Metadata annotated** — provenance includes `restored_from_snapshot` and `original_episode_id`

The restored subject is indistinguishable from one built organically.

## Creating Snapshots

Snapshot creation is done via the service layer (not exposed as API endpoint in v1):

```python
from server.services.snapshots import create_snapshot

snap = await create_snapshot(
    name="sarah-startup",
    source_subject_id="some-source-subject",
    version=1,
    metadata={"persona": "startup founder"},
)
```

See `scripts/bootstrap_snapshots.py` for the production bootstrap script.

## Cleanup Loop

When enabled, the app runs an hourly background loop that calls `cleanup_ephemeral_subjects()`. This deletes `live_*` subjects older than 24 hours (configurable).

Snapshot source subjects (`_snapshot/*`) are explicitly excluded from cleanup regardless of age.

## Deployment

On Fly.io:
```bash
fly secrets set STATEWAVE_ENABLE_SNAPSHOTS=true
```

Bootstrap snapshots after deploy:
```bash
STATEWAVE_URL=https://statewave-api.fly.dev \
STATEWAVE_API_KEY=<key> \
python scripts/bootstrap_snapshots.py
```

## Safety Guarantees

- Snapshots are append-only (no update/delete API in v1)
- `_snapshot/*` subjects never appear in user-facing endpoints
- Feature flag prevents accidental exposure on public instances
- Cleanup never touches snapshot data
- Restore always creates new IDs (no collision risk)
