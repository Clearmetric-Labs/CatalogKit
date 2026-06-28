# Backbone Lab (Experimental / Internal)

> **Experimental / internal architecture proof / not a shipped capability / no stability guarantee.**

This document describes **Backbone Lab** flows used to prove that Module A primitives
(contracts, intent, policy gate, consumer catalog, frontend contracts, runtime harness)
work on the same graph as the wedge. These flows are **not** part of the public product
promise in [README.md](../README.md) or [v1-boundary.md](v1-boundary.md).

## Public vs lab split

| Public wedge (always) | Lab (experimental only) |
|-----------------------|-------------------------|
| Lineage, impact, cleaner | Intent YAML ingest |
| Admin catalog | Consumer catalog |
| OpenLineage export (ungated) | Frontend contract emitter |
| | `cm query` (DuckDB harness) |

**Adoption gate** blocks expanding README / marketing / production claims — not building
these primitives in code and tests.

## Enable lab CLI

Lab commands and compile formats require:

```bash
export CM_EXPERIMENTAL=1
```

Normal `cm --help` does not advertise lab formats. With `CM_EXPERIMENTAL=1`, help marks
them as experimental.

## Demo project

See [examples/backbone-lab/README.md](../examples/backbone-lab/README.md).

```bash
export CM_EXPERIMENTAL=1
cd examples/backbone-lab
cm compile --format json > graph.json
cm compile --format catalog > catalog.json
cm compile --format consumer-catalog --identity analyst > consumer_catalog.json
cm compile --format frontend-contract --identity analyst > contracts.json
cm impact orders.amount --upstream
cm query --identity analyst query.executive_revenue
```

## Invariants (lab code)

- `policy.gate` is the sole consumer authz entry for projection, emitters, and runtime
- Missing `compiled_sql` → loud error at runtime (no `contract.sql` fallback)
- Policy exceptions → deny
- Empty rules → deny
- Admin `catalog` and `openlineage` remain ungated

## Not in lab scope

Live warehouse connector, cloud, catalog UI, dashboard renderer, AI agent product, docs
emitter, native RLS deployment, custom user checks, `cm serve`.
