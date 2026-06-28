# Vision

ClearMetric aims to be the **analytics backbone**: one canonical, queryable graph of tables,
columns, models, and metrics compiled from infrastructure you already operate (dbt, SQL,
warehouse metadata).

## Long-term consumers (post-v1)

These read the same graph; they are not separate source-of-truth products:

- Governed query contracts and BI frontends
- Policy-filtered projections and AI context exports
- Automated documentation emitted from graph structure
- Access governance compiled to warehouse policies

v1 delivers the **compiler, graph, lineage, impact, catalog, and honesty primitives** so
later consumers attach without re-implementing lineage.

## Principles

- **Derived structure, authored meaning** — lineage comes from SQL; semantics you cannot infer stay explicit.
- **Honest partial resolution** — warnings and derivation state instead of silent guesses.
- **Open artifacts** — JSON schemas and CLI output you can version, diff, and own.

See [`public-architecture.md`](public-architecture.md) for what ships today.
