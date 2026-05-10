# Kubernetes Deployment

Run Statewave on Kubernetes via the in-tree Helm chart at [`helm/statewave/`](https://github.com/smaramwbc/statewave/tree/main/helm/statewave) in the `statewave` repo.

> **Scope:** the chart deploys the **Statewave API only**. It does not deploy Postgres, the admin console, or any LLM / embedding model server. You bring a pgvector-capable Postgres reachable from the cluster; the chart wires the API to it.
>
> **Already on Kubernetes and looking for "things are slow"?** Most diagnostics are platform-agnostic — see the [Capacity Planning & Tuning Checklist](capacity-planning.md). For multi-replica specifics (connection-budget math, PgBouncer, replica-aware diagnostics) see the [Horizontal Scaling Guide](horizontal-scaling.md).

---

## Prerequisites

- Kubernetes 1.24 or newer
- Helm 3.10 or newer
- A Postgres instance reachable from the cluster, with the `pgvector` extension installed:
  - **Managed:** Neon, Supabase, RDS (with `CREATE EXTENSION vector;`), Cloud SQL, Azure Database for PostgreSQL — any provider with pgvector support.
  - **In-cluster:** any Postgres operator/chart, as long as the image has pgvector. The reference image used by the project's `docker-compose.yml` is [`pgvector/pgvector:pg16`](https://hub.docker.com/r/pgvector/pgvector).

The chart does **not** install Postgres. That is operator-managed lifecycle (backups, PITR, vacuum tuning) which does not belong in an application chart.

---

## Quick install

The shortest path that produces a working API:

```bash
helm install statewave ./helm/statewave \
  --namespace statewave --create-namespace \
  --set database.url='postgresql+asyncpg://USER:PASS@db.example.com:5432/statewave' \
  --set llm.apiKey='sk-…' \
  --set auth.apiKey='replace-me'
```

Helm will:

1. Create the chart's `ServiceAccount` and a `<release>-credentials` `Secret` holding the inline values.
2. Run a **pre-install Job** (`alembic upgrade head`) and wait for it to succeed.
3. Roll out the API `Deployment` and `ClusterIP` `Service`.

Verify:

```bash
kubectl --namespace statewave rollout status deploy/statewave
kubectl --namespace statewave port-forward svc/statewave 8100:8100
curl -fsS http://127.0.0.1:8100/healthz   # liveness — process up
curl -fsS http://127.0.0.1:8100/readyz    # readiness — DB reachable + queue healthy
```

---

## Configuration

Every chart value is documented inline in [`values.yaml`](https://github.com/smaramwbc/statewave/blob/main/helm/statewave/values.yaml). The most-changed knobs:

| Value | Default | When to change |
|---|---|---|
| `image.tag` | `""` (Chart `appVersion`) | Pin to a specific release in production. Pinning a digest is stronger. |
| `replicaCount` | `1` | Tier 3+. **Recompute the connection budget** (see below). |
| `database.url` / `database.existingSecret` | — | One is required. |
| `compiler.type` | `llm` | `heuristic` for demo / no-LLM mode. |
| `embedding.provider` | `litellm` | `stub` for demo / no-embedding mode. |
| `llm.model` | `gpt-4o-mini` | Per [LiteLLM provider syntax](https://docs.litellm.ai/docs/providers). |
| `llm.apiKey` / `llm.existingSecret` | — | Required when `compiler.type=llm` or `embedding.provider=litellm`. |
| `auth.apiKey` / `auth.existingSecret` | — | Strongly recommended in production. |
| `rateLimit.rpm` | `0` (off) | Per-IP, Postgres-backed, correct across replicas. |
| `cors.origins` | `["*"]` | Lock down for production. |
| `ingress.enabled` | `false` | Enable to expose externally — **raise proxy timeouts to ≥ 60s**. |
| `autoscaling.enabled` | `false` | HPA on CPU. Recompute connection budget when raising `maxReplicas`. |
| `supportPack.autoUpdate` | `false` | Off by default for self-hosted operators (the bundled docs pack is statewave.ai-specific content). |

---

## Secret management

The chart supports two patterns. Pick one **per credential** — you can mix.

### Inline (chart-managed Secret)

Best for dev clusters and single-environment installs:

```yaml
database:
  url: postgresql+asyncpg://user:pass@db:5432/statewave
llm:
  apiKey: sk-…
auth:
  apiKey: replace-me
```

The chart creates a single `<release>-credentials` Secret holding all inline values. **No** chart-managed Secret is created when every credential is supplied via `existingSecret` instead.

### External Secret reference (recommended for production)

Keep credentials in your Secret manager and reference the resulting Secret. Works with any of:

- [External Secrets Operator](https://external-secrets.io) (AWS Secrets Manager, GCP Secret Manager, HashiCorp Vault, Azure Key Vault, …)
- [Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets)
- [SOPS](https://github.com/getsops/sops) + [`helm-secrets`](https://github.com/jkroepke/helm-secrets)
- [CSI Secrets Store driver](https://secrets-store-csi-driver.sigs.k8s.io/) with cloud-provider plugins
- A hand-managed `Secret` (least preferred — defeats the point)

The chart consumes whatever surface produces a `Secret`:

```yaml
database:
  existingSecret: statewave-db
  existingSecretKey: STATEWAVE_DATABASE_URL

llm:
  existingSecret: statewave-llm
  existingSecretKey: STATEWAVE_LITELLM_API_KEY

auth:
  existingSecret: statewave-auth
  existingSecretKey: STATEWAVE_API_KEY
```

The chart never reads or copies the secret value — Kubernetes injects it via `secretKeyRef` at pod start.

---

## Postgres options

The chart is pgvector-extension-aware but Postgres-deployment-agnostic. Three reasonable patterns:

### A. Managed Postgres (recommended for production)

Neon / Supabase / RDS / Cloud SQL / Azure DB for PostgreSQL. You get backups, failover, pooling primitives, and a separate lifecycle from the application. Required steps:

1. Create the database.
2. Run `CREATE EXTENSION IF NOT EXISTS vector;` (most providers expose this through their console; Supabase/Neon enable it via UI toggle).
3. Set `database.url` to the SQLAlchemy async DSN: `postgresql+asyncpg://USER:PASS@HOST:5432/DB`.

### B. In-cluster Postgres operator

If you already run a Postgres operator (CloudNativePG, Crunchy PostgreSQL Operator, Zalando), use it with a pgvector-enabled image. Most operators support custom images via a single field. Statewave's reference image — `pgvector/pgvector:pg16` — works as a drop-in.

### C. In-cluster `pgvector/pgvector:pg16` Deployment

For dev / staging only. Run a single-pod Postgres with a PVC. **Not** a production posture — no failover, no automated backups. Use Pattern A or B for anything user-facing.

`infra/postgres-pgvector/` in the [`statewave`](https://github.com/smaramwbc/statewave/tree/main/infra/postgres-pgvector) repo contains a Dockerfile + runbook for the pgvector-bundled Postgres image; that's the reference for Pattern C and useful as the image-tag input for Pattern B.

---

## Migrations

Schema migrations run as a Helm **pre-install + pre-upgrade Job** (`alembic upgrade head`). The Job is created with the `before-hook-creation,hook-succeeded` delete policy so the previous Job is cleaned up before the next install/upgrade.

What this gives you:

- The Deployment never serves traffic against an out-of-date schema.
- Replicas no longer race to run migrations at startup (the anti-pattern called out in the [Horizontal Scaling Guide](horizontal-scaling.md#migrations-under-multi-instance-deploys)).
- Upgrades fail loudly — if `alembic upgrade head` fails, Helm aborts the upgrade and the existing Deployment continues serving on the old schema.

If you run migrations out-of-band (CI step, manual SRE workflow), set `migrationJob.enabled: false` and own the schema lifecycle yourself.

The migration runbook (incompatible-migration handling, rollback semantics) lives in [migrations.md](migrations.md) — k8s does not change those rules.

---

## Multi-instance deploys

Statewave coordinates correctly across replicas via Postgres (compile queue, webhook DLQ, rate limit, L2 query embedding cache). Sticky sessions are unnecessary and reduce L1 cache hit rates.

Before raising `replicaCount` past 2–3, walk the **connection-budget math**:

```
required_db_connections = replicas × (pool_size + max_overflow) + headroom
                        = replicas × 15 + ~15
```

At higher replica counts, put a **transaction-mode PgBouncer** in front of Postgres rather than raising `max_connections` indefinitely. Full multi-instance runbook (PgBouncer guidance, what coordinates correctly, multi-instance diagnostics, common mistakes): [Horizontal Scaling Guide](horizontal-scaling.md).

### HPA

The chart's HPA targets CPU and is off by default. When enabling, set `autoscaling.maxReplicas` deliberately — every additional replica adds ~15 Postgres connections under burst:

```yaml
autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 5
  targetCPUUtilizationPercentage: 70
```

CPU is the right metric here: Statewave is small per-process, and the meaningful per-pod load is request-handling CPU rather than memory. Remember that scaling from 2 → 5 replicas changes your Postgres connection requirement from `~45` to `~90`.

### PodDisruptionBudget

Off by default (only meaningful with `replicaCount > 1`). Enable for Tier 3+:

```yaml
podDisruptionBudget:
  enabled: true
  minAvailable: 1
```

---

## Ingress

Off by default. When you enable an Ingress, **raise the proxy read/send timeouts to at least 60 seconds**. Statewave's `/v1/context` can run 5–30 seconds on cold-start (semantic search + embedding-provider RTT); a default 30s proxy timeout will return 504s on cold queries even though the upstream is healthy.

Per-controller annotation cheatsheet:

| Controller | Annotation |
|---|---|
| **NGINX Ingress** | `nginx.ingress.kubernetes.io/proxy-read-timeout: "60"` and `proxy-send-timeout: "60"` |
| **Traefik** | `traefik.ingress.kubernetes.io/router.middlewares: <ns>-statewave-timeout@kubernetescrd` referencing a `Middleware` with a 60s `forwardingTimeouts.responseHeaderTimeout` |
| **GKE / Cloud Load Balancer** | `BackendConfig` with `timeoutSec: 60` |
| **AWS ALB Ingress Controller** | `alb.ingress.kubernetes.io/target-group-attributes: "deregistration_delay.timeout_seconds=30,routing.http.response.server.enabled=false"` plus a longer LB idle timeout |

Example NGINX ingress values:

```yaml
ingress:
  enabled: true
  className: nginx
  annotations:
    nginx.ingress.kubernetes.io/proxy-read-timeout: "60"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "60"
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: statewave.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: statewave-tls
      hosts:
        - statewave.example.com
```

---

## Upgrades

Roll a new image tag:

```bash
helm upgrade statewave ./helm/statewave \
  --namespace statewave \
  --reuse-values \
  --set image.tag=0.7.1
```

The pre-upgrade Job runs `alembic upgrade head` first. If migrations fail, Helm aborts the upgrade and the previous Deployment continues serving on the old schema — there is no half-upgraded state.

Schema policy: rolling upgrades require backwards-compatible schemas across **one** version (so the old replica can keep serving while the new one rolls in). The full migration runbook is in [migrations.md](migrations.md).

To roll back:

```bash
helm rollback statewave <REVISION> --namespace statewave
```

Helm rollback does **not** roll back the schema. If a migration introduced a non-backwards-compatible change, reverting requires either restoring a Postgres backup or hand-writing a downgrade migration. Plan accordingly.

---

## Troubleshooting

Generic diagnostics live in [troubleshooting.md](troubleshooting.md) and [capacity-planning.md](capacity-planning.md). The k8s-specific failure modes:

| Symptom | Likely cause | First action |
|---|---|---|
| Migration Job in `Error` / `BackoffLimitExceeded` | Wrong DB URL, missing `pgvector` extension, network policy blocking pod → DB | `kubectl logs job/<release>-migrate -n <ns>`; verify `psql` against the same URL works from a debug pod |
| Pods in `CrashLoopBackOff` after migration succeeded | LiteLLM API key invalid; missing required env; DB closed connections after migration ran (NAT / firewall idle timeout) | `kubectl logs deploy/<release> -n <ns>`; confirm Secret references resolve; check the `STATEWAVE_*` env block via `kubectl describe pod` |
| `/readyz` returns 503 with `database` error | DB unreachable from the pod, or `pool_timeout`s | Test connectivity from a debug pod; raise `STATEWAVE_DATABASE_POOL_*` if appropriate; recheck the connection-budget math |
| `/v1/context` returns 504 from the Ingress | Proxy/LB timeout shorter than the API's cold-start latency | Raise the controller's read/send timeout to ≥ 60s — see the Ingress section above |
| HPA flapping replicas up and down | `targetCPUUtilizationPercentage` too aggressive; cold-start replicas spike CPU briefly | Raise the target to 70–80%; confirm `requests.cpu` is realistic |
| `too many connections for role` error in pod logs | Replica count × per-pod pool exceeds DB `max_connections` | Recompute the connection budget; switch to PgBouncer (transaction mode) if past `~70%` of `max_connections` |
| Migration Job timing out at `activeDeadlineSeconds` | Long-running schema migration on a large DB | Raise `migrationJob.activeDeadlineSeconds` for that release; consider running the migration manually for very large DBs |
| Image pull errors with a private registry | Missing `imagePullSecrets` | Add via `imagePullSecrets: [{ name: regcred }]` in values |

### Pod-level debugging

```bash
# Look at the running env (sans secrets)
kubectl --namespace <ns> describe pod -l app.kubernetes.io/name=statewave

# Tail logs across all replicas
kubectl --namespace <ns> logs -l app.kubernetes.io/name=statewave -f --max-log-requests=10

# Exec into a replica
kubectl --namespace <ns> exec -it deploy/statewave -- /bin/sh

# Check the Helm release
helm --namespace <ns> status statewave
helm --namespace <ns> history statewave
```

---

## Uninstall

```bash
helm uninstall statewave --namespace statewave
```

Helm removes everything the chart created (Deployment, Service, Secret, ServiceAccount, optional Ingress / HPA / PDB, the migration Job's residual). **Postgres data is not touched** — the chart never owned it.

If you also want the namespace gone:

```bash
kubectl delete namespace statewave
```

---

## What this chart deliberately does not do

| Excluded | Reason |
|---|---|
| Bundled Postgres | Lifecycle (backups, PITR, vacuum tuning) does not belong in an application chart. Use Pattern A or B above. |
| Admin console (`statewave-admin`) | Separate deployable with its own auth surface. Bundle it via a separate chart or overlay if you want it on the same cluster. |
| Self-hosted model server (vLLM / Ollama / TEI) | GPU scheduling + its own runbook. See [Hardware & Scaling](hardware-and-scaling.md) for the layered sizing model. |
| NetworkPolicy | Cluster-wide network policy is operator-defined; the chart would either be too permissive or too restrictive for any given environment. Define your own. |

---

## See also

- Chart README: [`helm/statewave/README.md`](https://github.com/smaramwbc/statewave/blob/main/helm/statewave/README.md) (in the `statewave` repo)
- [Deployment Guide](guide.md) — Docker / Fly / Railway recipes
- [Deployment Sizing Guide](sizing.md) — single-instance sizing and topology patterns
- [Horizontal Scaling Guide](horizontal-scaling.md) — multi-instance runbook (connection budget, PgBouncer, replica diagnostics)
- [Capacity Planning & Tuning Checklist](capacity-planning.md) — symptom → action diagnostics
- [Migration & Upgrade Runbook](migrations.md) — schema migrations
- [Deployment Troubleshooting](troubleshooting.md) — incident runbooks
- [Roadmap](../roadmap.md)
