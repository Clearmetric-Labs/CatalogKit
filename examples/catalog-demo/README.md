# Catalog Demo

Self-contained warehouse + dbt example. A minimal dbt manifest (seeds, staging models, and `orders`) with compiled SQL is merged against a local INFORMATION_SCHEMA JSON export.

## Prerequisites

```bash
pip install clearmetric-core
cd examples/catalog-demo
```

## Commands

```bash
cm scan
cm compile --format json > graph.json
cm compile --format catalog > catalog.json
cm clean
cm contract graph.json
```

Catalog output includes table and column nodes from the merged warehouse + dbt graph:

```bash
cm compile --format catalog | python -c "import json,sys; c=json.load(sys.stdin); print(sorted({n['kind'] for n in c['nodes']}))"
```

## What this demonstrates

- dbt manifest ingestion with compiled SQL for column-level lineage
- Warehouse metadata merged with physical bindings on table/column nodes
- Catalog compile (`--format catalog`) as a table/column projection of the merged graph
