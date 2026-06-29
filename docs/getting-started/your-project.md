# Run on your own project

ClearMetric reads a project directory with `clearmetric.yaml`. Configure one or more sources, then `cm scan` and `cm compile`.

## Warehouse metadata export

1. Export INFORMATION_SCHEMA (or equivalent) to a JSON file your team already uses for catalog tooling.
2. `cm init` (or edit `clearmetric.yaml` by hand).
3. `cm connect warehouse --information-schema ./your_export.json`
4. `cm scan` — confirm the warehouse source appears.

No live connector. The JSON file is the source of truth for physical table/column bindings.

## dbt manifest

Point `clearmetric.yaml` at your compiled `target/manifest.json`:

```yaml
sources:
  dbt:
    manifest: ./target/manifest.json
```

Run `dbt compile` (or your CI artifact step) before `cm compile`. ClearMetric does not run dbt.

Optional: add warehouse metadata export to bind dbt models to physical tables.

## SQL folder

Point at a directory of `.sql` files:

```yaml
sources:
  sql:
    paths:
      - ./sql
```

Folder input is lighter than dbt: star-heavy SQL without schema metadata may stay flagged with warnings.

## First compile

```bash
cm scan
cm compile --format json > graph.json
cm clean
cm contract graph.json
```

Read warnings on stderr during compile — they indicate honest uncertainty, not silent success.

See [Understanding the outputs](outputs.md) and [Validation](../validation/check-lineage.md).
