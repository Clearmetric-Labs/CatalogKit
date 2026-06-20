# catalogkit-lineage

`catalogkit-lineage` builds project-level SQL lineage from either:

- a dbt `manifest.json` with compiled SQL available, or
- a folder of `.sql` files

It is a headless static-analysis tool:

- input: one dbt manifest path or one SQL folder
- output: a deterministic `LineageMap` plus the shared `CatalogArtifact`
- no warehouse credentials
- no dbt execution
- no AI key

## Install

```bash
python -m pip install catalogkit-lineage
```

## Imports

```python
from catalogkit.lineage import (
    build_catalog_artifact,
    build_lineage_map,
    build_openlineage_export,
    render_json,
    render_text,
    trace_downstream,
    trace_upstream,
)
```

For local development:

```bash
python -m pip install -e ../catalogkit-core
python -m pip install -e ".[dev,release]"
```

## Quickstart

Manifest input:

```bash
catalogkit-lineage --dialect postgres ./examples/jaffle_shop/manifest.json
catalogkit-lineage --dialect postgres --format json ./examples/jaffle_shop/manifest.json
catalogkit-lineage --dialect postgres --format openlineage ./examples/jaffle_shop/manifest.json
```

Folder input:

```bash
catalogkit-lineage --dialect postgres ./examples/sql_folder
catalogkit-lineage --dialect postgres --upstream customers_report.customer_lifetime_value ./examples/sql_folder
catalogkit-lineage --dialect postgres --downstream orders_base.amount ./examples/sql_folder
```

## Output Contract

`catalogkit-lineage` exposes a module-specific `LineageMap` with:

- `version`
- `summary`
- `nodes`
- `edges`
- `warnings`

For CatalogKit composition, the package also exposes a shared
`CatalogArtifact` builder backed by `catalogkit-core`.

The shared core artifact contains:

- `version`
- `nodes`
- `edges`
- `warnings`

## Contract Docs

- [`../catalogkit-core/docs/contract.md`](../catalogkit-core/docs/contract.md)
- [`docs/limitations.md`](docs/limitations.md)
