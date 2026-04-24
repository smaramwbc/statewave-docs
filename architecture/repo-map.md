# Repo Map

| Repo | Purpose | Version | License |
|------|---------|---------|---------|
| `statewave` | Core server, API, domain model, DB, services, deployment | 0.2.0 | AGPL-3.0 |
| `statewave-py` | Official Python SDK (sync + async, typed exceptions) | 0.2.0 | Apache-2.0 |
| `statewave-ts` | Official TypeScript SDK (typed errors, ESM) | 0.2.0 | Apache-2.0 |
| `statewave-examples` | Example apps and quickstarts | — | Apache-2.0 |
| `statewave-docs` | Architecture, specs, ADRs, coordination (no runtime code) | — | Apache-2.0 |

## Dependency direction

```
statewave-examples → statewave-py / statewave-ts → statewave (API)
```

SDKs depend on the API contract. Examples depend on SDKs. Docs depend on nothing.

## Test counts (as of v0.2)

| Repo | Tests | Framework |
|------|-------|-----------|
| `statewave` | 40 (25 unit + 15 integration) | pytest |
| `statewave-py` | 14 | pytest |
| `statewave-ts` | 10 | vitest |

## Available examples

| Example | Language | Description |
|---------|----------|-------------|
| `minimal-quickstart` | Python | Basic record → compile → context loop |
| `support-agent-python` | Python | 2-session support agent demo with ranked context and provenance |
