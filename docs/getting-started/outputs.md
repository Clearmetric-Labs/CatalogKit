# Understanding the outputs

All public emitters read the **same compiled graph** after build + enforce.

## Compile formats

| `--format` | Use |
|------------|-----|
| `json` | Full graph artifact (nodes, edges, warnings) — default |
| `catalog` | Table/column/model catalog slice |
| `openlineage` | OpenLineage-compatible event JSON |
| `text` | Human-readable summary |

```bash
cm compile --format json > graph.json
cm compile --format catalog > catalog.json
cm compile --format openlineage > openlineage.json
```

## Impact

```bash
cm impact COLUMN --upstream --format json
cm impact COLUMN --downstream --format json
```

JSON includes `related_ids`, `traversed_edges`, and any warnings scoped to the traversal.

## Clean and contract

```bash
cm clean              # report findings; exit 1 on severity error only
cm contract graph.json  # CI gate: schema + enforce
```

## Schema detail

Artifact shape and ID rules: [Artifact contract](../reference/contract.md).

Format reference table: [Input and output formats](../reference/io-formats.md).

CLI flags: [CLI reference](../reference/cli.md) (generated from `cm --help`).
