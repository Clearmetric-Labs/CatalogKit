# Artifact-Level Orchestration (Optional)

Each ClearMetric Core module is **standalone and headless**. The v0 wedge path uses
`clearmetric.compiler.compile()` to orchestrate warehouse metadata + dbt + SQL from
`clearmetric.yaml`.

Composition with Power BI or query artifacts remains **optional** via `clearmetric.core.merge()`.

Full contract: [`packages/clearmetric-core/docs/contract.md`](../packages/clearmetric-core/docs/contract.md)

## Wedge usage (recommended)

```bash
pip install clearmetric-core
cm init
cm connect warehouse --information-schema ./warehouse_schema.json
cm compile --format json > graph.json
```

```python
from pathlib import Path
from clearmetric.compiler import compile

compiled = compile(Path("."))
artifact = compiled.artifact
```

## Standalone module usage

```python
from clearmetric.lineage import build_catalog_artifact_from_project, load_project

project = load_project("./target/manifest.json", dialect="postgres")
artifact = build_catalog_artifact_from_project(project, dialect="postgres")
```

Power BI PBIP lineage via Python API (not in v0 CLI source registry):

```python
from clearmetric.powerbi import build_catalog_artifact

artifact = build_catalog_artifact("./MyReport.pbip")
```

## Optional composition

```python
from clearmetric.core import load_table_alias_map, merge
from clearmetric.lineage import build_catalog_artifact_from_project, load_project
from clearmetric.powerbi import build_catalog_artifact as build_powerbi, merge_with_warehouse

project = load_project("./target/manifest.json", dialect="postgres")
warehouse = build_catalog_artifact_from_project(project, dialect="postgres")
powerbi = build_powerbi("./MyReport.pbip")

alias_map = load_table_alias_map("./aliases.yaml")  # optional
merged = merge_with_warehouse(powerbi, warehouse, alias_map=alias_map)
```

## Rules

1. Module build paths use **`clearmetric.core` only** — sibling imports happen at orchestration/merge time, not inside module parsers.
2. One merge contract — `clearmetric.core.merge()` and core interop helpers only.
3. Cross-source disagreements on non-structural facts become `source_disagreement` / `schema_drift` warnings; structural impossibilities raise `MergeConflictError`.

## CI

`cm contract graph.json` validates compiled artifacts against `spec/catalog-artifact.schema.json` and enforces structural checks.
