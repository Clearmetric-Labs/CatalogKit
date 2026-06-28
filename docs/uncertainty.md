# Uncertainty model

ClearMetric stamps nodes and edges with **derivation state** and **confidence** so consumers
know what was inferred versus observed.

## Derivation status

| Status | Meaning |
|--------|---------|
| `complete` | Resolution succeeded with expected evidence |
| `partial` | Some structure known; column lineage may be incomplete |
| `failed` | Resolution failed for this node |
| `skipped` | Source intentionally not resolved |

## Warnings

Warnings (for example `select_star`, `unresolved_lineage`, `warehouse_bind_ambiguous`) appear
on the artifact and may surface as cleaner findings depending on project **posture**:

- **strict** — warn-tier checks report as warnings; error-tier checks fail enforce
- **standard** — most checks report as warnings
- **permissive** — non-structural checks suppressed

## Compile diagnostics

When a graph compiles with **zero** `derives_from` edges, `cm compile` exits 0 but prints a
`LINEAGE WARNING` to stderr. The graph may still have model/table structure and `depends_on`
edges — column impact will be incomplete until inputs improve.

Run `cm clean` for posture-aware findings including `check.zero_column_lineage`.
