# clearmetric-core

One PyPI package. All ClearMetric Core modules ship inside this distribution.

## Install

```bash
python -m pip install clearmetric-core
```

## CLI (project-first)

```bash
cm init
cm connect warehouse --information-schema ./warehouse_schema.json
cm scan
cm compile --format json > graph.json
cm impact orders.amount --upstream
cm clean
cm contract graph.json
```

If `cm` is occupied on your PATH:

```bash
python -m clearmetric.cli --project-dir . compile --format json
```

## Modules

| Module | Purpose |
|--------|---------|
| `clearmetric.compiler` | Discover → adapters → merge → policy/cleaner spine |
| `clearmetric.core` | Artifact schema, canonical IDs, merge, validation |
| `clearmetric.lineage` | Project-level SQL lineage from dbt manifests and SQL folders |
| `clearmetric.query` | Single-statement SQL structure mapping |
| `clearmetric.powerbi` | PBIP file lineage (not in v0 warehouse CLI registry) |
| `clearmetric.cli` | `cm` command router |

## Imports

```python
from pathlib import Path
from clearmetric.compiler import compile
from clearmetric.core import CatalogArtifact, merge, parse_column_selection
from clearmetric.lineage import (
    build_catalog_artifact_from_project,
    load_project,
    trace_upstream_from_project,
)
```

For local development:

```bash
python -m pip install -e ".[dev,release]"
```

## Contract

The source of truth for the shared artifact contract is
[`docs/contract.md`](docs/contract.md).

Project config schema: [`../../spec/clearmetric-project.schema.json`](../../spec/clearmetric-project.schema.json)

Example project: [`../../examples/wedge-jaffle`](../../examples/wedge-jaffle)
