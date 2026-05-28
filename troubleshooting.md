# Troubleshooting — common first-run issues

The predictable cluster of problems people hit on a fresh `docker compose up -d`. Each entry is **Symptom → Cause → Fix**. For the inline quick-reference table see [getting-started.md](getting-started.md#if-something-goes-wrong); for production/deployment issues see [deployment/troubleshooting.md](deployment/troubleshooting.md).

---

## `/readyz` shows `"llm": ... "STATEWAVE_LITELLM_API_KEY is not set"`

**Symptom.** `curl http://localhost:8100/readyz` returns `status: ready`, but the `llm` check reads `STATEWAVE_LITELLM_API_KEY is not set`.

**Cause.** This is **expected in demo mode**. With no LLM key configured, Statewave runs the heuristic compiler and hash-based (stub) embeddings — fully local, zero egress. There is no provider to check, so the `llm` line reports the missing key. Overall status is still `ready`.

**Fix.** Nothing to fix for demo mode — every quickstart step works without a key. To turn on real LLM extraction and semantic search, set `STATEWAVE_LITELLM_API_KEY` (and optionally `STATEWAVE_LITELLM_MODEL` / `STATEWAVE_LITELLM_EMBEDDING_MODEL`) in `.env`, then `docker compose up -d` to restart the API. Confirm with `curl .../readyz` — the `llm` check makes a real provider call once a key is set.

---

## LLM not configured / compilation produces only heuristic memories

**Symptom.** Compiled memories look shallow, or you expected semantic search to work and it doesn't.

**Cause.** Same root as above — demo mode (no `STATEWAVE_LITELLM_API_KEY`) uses the heuristic compiler + stub embeddings. Stub embeddings do not do real semantic similarity.

**Fix.** Set the LLM key + embedding model in `.env` and restart. See [getting-started.md → Turn on a real LLM provider](getting-started.md#turn-on-a-real-llm-provider). The heuristic path is intentional and supported (zero-egress default); the LLM path is the enhancement.

---

## Port 8100 already in use

**Symptom.** `docker compose up -d` fails with `Bind for 0.0.0.0:8100 failed: port is already allocated`, or `/healthz` hits a different service than you expect.

**Cause.** Another process (a previous Statewave stack that wasn't torn down, or an unrelated service) already holds host port 8100.

**Fix.** Find and stop the holder, or remap the host port:

```bash
# What's on 8100?
lsof -i :8100            # macOS / Linux
# A stale Statewave stack? Tear it down:
docker compose ps        # from the same directory you ran `up` in
docker compose down

# Or run Statewave on a different host port without editing compose:
STATEWAVE_API_HOST_PORT=8101 docker compose up -d
curl http://localhost:8101/readyz
```

The compose file reads `STATEWAVE_API_HOST_PORT` (default `8100`); `STATEWAVE_DB_HOST_PORT` (default `5432`) and `STATEWAVE_ADMIN_HOST_PORT` work the same way if those ports collide too.

---

## Postgres connection refused

**Symptom.** `curl: (7) Connection refused` on `localhost:8100`, or `/readyz` shows the `database` check failing / returns `503`. API logs mention a connection error to `db`.

**Cause.** Most commonly the Postgres container hasn't finished its first-boot initialization (the pgvector image takes 10–20 s on first start), or the API didn't pick up the database URL because a host `.env` overrode it.

**Fix.**

```bash
docker compose ps          # `db` should be "healthy", `api` should be "running"
docker compose logs db     # watch for "database system is ready to accept connections"
docker compose logs api    # confirm it connected after the db became healthy
```

Wait ~10–20 s on the very first boot and retry `/readyz`. If it persists: confirm your host `.env` is **not** overriding `STATEWAVE_DATABASE_URL` with a host that the API container can't reach — inside the compose network the database is `db`, not `localhost`. The compose file sets the correct in-network URL by default.

---

## Returning user: pulled an old image, fixes/features look missing

**Symptom.** You ran Statewave weeks ago, `docker compose up -d` again, and a documented fix or feature isn't present — or the server reports an older version than expected.

**Cause.** `docker compose up -d` reuses whatever image is already cached locally. `:latest` is only re-fetched when you explicitly pull. A host that pulled `:latest` weeks ago stays on that older image.

**Fix.** Refresh the cached image before starting:

```bash
docker compose pull        # fetch the current :latest
docker compose up -d       # recreate the container on the new image
```

Confirm the running version:

```bash
docker exec "$(docker compose ps -q api)" pip show statewave | grep -i version
```

To pin a specific version instead of floating on `:latest`, set `STATEWAVE_VERSION=X.Y.Z` in `.env`.

---

## Still stuck?

- Inline quick reference: [getting-started.md → If something goes wrong](getting-started.md#if-something-goes-wrong)
- Production / deployment issues: [deployment/troubleshooting.md](deployment/troubleshooting.md)
- Ask in [Discussions](https://github.com/smaramwbc/statewave/discussions) or open an issue on the [central tracker](https://github.com/smaramwbc/statewave/issues).
