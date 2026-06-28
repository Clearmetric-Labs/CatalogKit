# Wedge Jaffle Example

Warehouse-connected wedge walkthrough using the jaffle shop dbt manifest fixture and a credential-free `information_schema` JSON metadata file.

## Prerequisites

```bash
pip install clearmetric-core   # or: pip install -e "packages/clearmetric-core[dev]"
cd examples/wedge-jaffle
```
```

The example references committed fixtures under `packages/clearmetric-core/tests/fixtures/` for the jaffle manifest, compiled SQL, and warehouse metadata schema.

## Commands

```bash
cm scan
cm compile --format json > graph.json
cm impact orders.amount --upstream --format json
cm clean
cm contract graph.json
```

To attach local warehouse metadata instead of the shared fixture path:

```bash
cm connect warehouse --information-schema ../../packages/clearmetric-core/tests/fixtures/wedge/jaffle_warehouse_schema.json
```

## What this demonstrates

- Project-first CLI via `clearmetric.yaml` (no positional manifest paths, no `--dialect` flag)
- Warehouse metadata ingestion with physical bindings on table/column nodes
- dbt manifest lineage merged with warehouse metadata
- Report-only `cm clean` (structural/security findings, schema drift as warnings)
- Contract validation against `spec/catalog-artifact.schema.json`

Power BI remains available as `clearmetric.powerbi` but is not part of the v0 warehouse source registry.
