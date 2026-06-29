# ClearMetric Core

**One canonical graph of your analytics layer** — compiled from SQL, dbt, and warehouse
metadata you already have.

ClearMetric merges local warehouse metadata exports, dbt artifacts, and SQL folders into
one graph with column lineage, impact analysis, catalog output, and explicit warnings when
something cannot be resolved.

```bash
pip install clearmetric-core
```

**Status:** early development (0.x). Pin versions in production use.

## Start here

Answer these in order:

1. [What it does today](current-scope.md) — shipped public wedge
2. [Project status](status.md) — 0.x honesty and adoption gate
3. [Install](getting-started/install.md) then [five-minute demo](getting-started/five-minute-demo.md)
4. [Run on your own project](getting-started/your-project.md)
5. [Understanding the outputs](getting-started/outputs.md)
6. [Validation](validation/what-works.md) — what to rely on, [check lineage](validation/check-lineage.md), [help test on real SQL](validation/help-test.md)

Full manual lives on this site. The [README](https://github.com/ClearMetric-Labs/ClearMetric-Core/blob/main/README.md) is the repo landing page for deciding whether to try ClearMetric.
