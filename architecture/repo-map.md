# Repo Map

| Repo | Purpose | License |
|------|---------|---------|
| `statewave` | Core server, API, domain model, DB, services, deployment | BUSL-1.1 |
| `statewave-py` | Official Python SDK | Apache-2.0 |
| `statewave-ts` | Official TypeScript SDK | Apache-2.0 |
| `statewave-examples` | Example apps and quickstarts | Apache-2.0 |
| `statewave-docs` | Architecture, specs, ADRs, coordination (no runtime code) | Apache-2.0 |

## Dependency direction

```
statewave-examples → statewave-py / statewave-ts → statewave (API)
```

SDKs depend on the API contract. Examples depend on SDKs. Docs depend on nothing.
