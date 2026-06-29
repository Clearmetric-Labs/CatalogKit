# Canonical IDs and bindings

Every node in the graph has a stable **canonical ID** owned by `clearmetric.core`. Tools must not invent local ID formats — merge and impact depend on identical normalization.

Examples:

- `table:orders_base`
- `column:orders_base.amount`
- `model:customer_totals`

**Physical bindings** attach warehouse metadata (database, schema, table, column) to lineage nodes after merge. Unresolved or ambiguous bindings emit warnings — they are not silently invented.

Full rules (normalization, merge, cross-graph interop): [Artifact contract](../reference/contract.md) — sections *Canonical ID Rules* and *Cross-Graph Interop*.
