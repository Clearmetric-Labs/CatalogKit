# The canonical graph

ClearMetric compiles configured sources into **one graph**:

```text
Adapters  →  merge + warehouse bind  →  enforce  →  emit
```

1. **Adapters** ingest warehouse JSON, dbt manifest, and/or SQL folders into partial artifacts.
2. **Compiler** merges nodes and edges, attaches warehouse physical bindings, runs cleaner + security floor.
3. **Graph** exposes impact traversal and selectors on the enforced artifact.
4. **Emitters** shape stdout (`json`, `catalog`, `openlineage`, impact, clean).

Each node has a canonical ID, kind, derivation state, optional physical bindings, and evidence.
Edges include `derives_from` for value lineage used by impact analysis.

More detail: [Architecture](../public-architecture.md) · [Artifact contract](../reference/contract.md)
