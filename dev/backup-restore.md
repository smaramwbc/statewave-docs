# Backup & Restore

Statewave provides two levels of backup:

1. **Subject-level export/import** — portable JSON via admin API (Statewave-managed)
2. **Full database backup** — pg_dump/pg_restore (Postgres-native)

---

## Subject export/import (admin API)

Use this for:
- Backing up a subject before risky operations
- Migrating subjects between Statewave instances
- Moving subjects between tenants
- Creating portable archives for compliance

### Export a subject

```bash
curl -s http://localhost:8100/admin/export/user-123 | jq . > user-123-backup.json
```

With tenant scope:
```bash
curl -s "http://localhost:8100/admin/export/user-123?tenant_id=org-a" > user-123-backup.json
```

The export includes:
- All episodes (with payloads, metadata, provenance, timestamps)
- All memories (with confidence, embeddings, status, provenance)
- SHA-256 checksum for integrity verification
- Format version for forward compatibility

### Import a subject

```bash
curl -X POST http://localhost:8100/admin/import \
  -H "Content-Type: application/json" \
  -d '{
    "document": '"$(cat user-123-backup.json)"',
    "target_subject_id": "user-123-restored",
    "preserve_ids": true
  }'
```

Options:
| Option | Default | Description |
|--------|---------|-------------|
| `target_subject_id` | original | Override the subject_id on import |
| `target_tenant_id` | original | Override the tenant_id on import |
| `preserve_ids` | `true` | Keep original UUIDs (false = generate new) |

### Safety checks

Import validates:
- Format version compatibility
- SHA-256 checksum integrity (detects corruption/tampering)
- ID conflicts when `preserve_ids=true`

### Difference from Subject Snapshots

| | Subject Export/Import | Subject Snapshots |
|---|---|---|
| Purpose | Portable backup, migration | In-DB bootstrap/demo |
| Storage | External JSON file | Same Postgres database |
| Portable | ✅ Yes | ❌ No (same instance only) |
| Operator use | Backup before upgrades, migration | Demo seeding, testing |
| Feature flag | Always available | Requires `ENABLE_SNAPSHOTS=true` |

---

## Full database backup (Postgres-native)

For complete disaster recovery, use Postgres tools:

```bash
# Backup
pg_dump -h localhost -U statewave statewave > statewave-full-backup.sql

# Restore
psql -h localhost -U statewave statewave < statewave-full-backup.sql
```

Use full DB backups for:
- Disaster recovery
- Before schema migrations
- Environment cloning
- Point-in-time recovery (with WAL archiving)

Statewave's subject export/import does NOT replace pg_dump. It complements it for subject-level operations.

---

## What is NOT backed up by subject export

- Compile jobs (ephemeral operational state)
- Webhook delivery events (transient)
- Rate limit counters (transient)
- Subject snapshots (use pg_dump for those)

These are all ephemeral/operational data that doesn't need portable backup.
