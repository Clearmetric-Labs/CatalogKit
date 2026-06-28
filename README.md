# ClearMetric Core

**Build a data catalog from your code, not a platform.** ClearMetric Core is an open-source compiler and graph engine that derives lineage, structure, and a mergeable catalog graph from dbt projects, SQL, and warehouse metadata — locally, with no platform to stand up.

```bash
pip install clearmetric-core
cd my-dbt-project
cm init
cm connect warehouse --information-schema ./warehouse_schema.json
cm compile --format json > graph.json
cm impact orders.amount --upstream
```

```
upstream: orders.amount
selection_id: column:orders.amount
related_ids: []
```

Ask any column *"what feeds this?"* or *"what breaks if I change it?"* and get a real answer, traced from your code and warehouse metadata.

> **Status:** early development (0.x), release 0.3.0. Pin your versions.

## Why it's different

Most catalogs are heavy platforms you log into and maintain by hand — and they drift out of sync with the code. ClearMetric Core is the opposite: a single package that derives the catalog *from* the code, so it stays fresh, lives in your repo, and runs in CI. When it can't resolve something, it flags it instead of guessing.

## Quickstart

```bash
pip install clearmetric-core
cm init
cm scan
cm compile --format json > graph.json
cm impact orders.amount --upstream
cm clean
cm contract graph.json
```

See [`examples/wedge-jaffle/README.md`](examples/wedge-jaffle/README.md) for a full walkthrough.

If another program already occupies `cm` on your PATH, use the module entry instead:

```bash
python -m clearmetric.cli --project-dir . compile --format json
```

## Compile a catalog

The compiler spine merges warehouse metadata, dbt manifests, and SQL folders into one graph artifact. Every module still emits the same mergeable artifact shape for optional composition.

```python
from pathlib import Path
from clearmetric.compiler import compile

compiled = compile(Path("./my-project"))
artifact = compiled.artifact
```

## Modules

One install (`pip install clearmetric-core`) gives you every module below. These are
Python subpackages, not separate PyPI packages.

| Module | What it does | Status |
|--------|--------------|--------|
| **`clearmetric.compiler`** | Project-first orchestration: discover → adapters → merge → policy/cleaner | Shipped (wedge) |
| **`clearmetric.lineage`** | Column-level lineage from dbt manifests and SQL folders | Shipped |
| **`clearmetric.query`** | Maps a single SQL statement into its tables and dependencies | Shipped |
| **`clearmetric.powerbi`** | PBIP lineage (shipped module; not in v0 warehouse CLI registry) | V1 |
| **`clearmetric.core`** | Shared artifact, canonical IDs, merge, validation | Shipped |

## Shipped wedge commands

- `cm init` — scaffold `clearmetric.yaml` + `policy/rules.yaml`
- `cm connect warehouse --information-schema PATH` — credential-free metadata fixture
- `cm scan` — discover configured sources
- `cm compile` — compile project graph to stdout
- `cm impact` — upstream/downstream column lineage
- `cm clean` — report-only structural/security/drift findings
- `cm contract` — validate compiled artifact JSON in CI

[Open an issue](https://github.com/ClearMetric-Labs/ClearMetric-Core/issues) if there's a primitive you wish existed.

## Limits

Static analysis for SQL/dbt lineage; warehouse **metadata** ingestion in v0 (no query execution). On star-heavy SQL (`SELECT *` without schema), it flags what it can't resolve rather than guessing. [Full limitations →](packages/clearmetric-core/docs/lineage/limitations.md)

## Feedback & contact

Built in the open, and feedback shapes the roadmap.

- **Bugs / features:** [open an issue](https://github.com/ClearMetric-Labs/ClearMetric-Core/issues)
- **Questions / ideas:** [Discussions](https://github.com/ClearMetric-Labs/ClearMetric-Core/discussions)
- **Using it or want to talk?** Reach out on [LinkedIn](https://www.linkedin.com/in/kim-jon).

## License

Apache 2.0.

---

<details>
<summary><strong>Architecture & contributing</strong></summary>

ClearMetric Core is a single Python package at `packages/clearmetric-core` with submodules under the `clearmetric` namespace. Each module composes through `clearmetric.core` and emits artifacts that merge into one graph.

**Modules**
- `clearmetric.core` — shared artifact models, canonical IDs, serialization, merge, validation
- `clearmetric.query` — single-statement SQL structure mapping
- `clearmetric.lineage` — project-level lineage, catalog artifact, and OpenLineage export for dbt manifests and SQL folders
- `clearmetric.powerbi` — PBIP file lineage: M upstream sources, report visual bindings, cross-graph merge metadata
- `clearmetric.cli` — `cm` command router

```python
from clearmetric.core import Node, Edge, Evidence
from clearmetric.compiler import compile
from clearmetric.lineage import build_catalog_artifact_from_project, load_project
```

**Core rules**
- `version` = shared artifact *schema* version, owned by `clearmetric.core`.
- Canonical IDs and merge semantics defined once in `clearmetric.core`.
- No duplicate shared models or fallback code paths.

**Local development**
```bash
python -m pip install -e "packages/clearmetric-core[dev,release]"
python -m pytest -v
```

**Docs:** [contract](packages/clearmetric-core/docs/contract.md) · [query limits](packages/clearmetric-core/docs/limitations/query/limitations.md) · [lineage limits](packages/clearmetric-core/docs/lineage/limitations.md) · [powerbi limits](packages/clearmetric-core/docs/limitations/powerbi/limitations.md) · [architecture](clearmetric-architecture.md) · [orchestration](docs/orchestration.md)

Contributions require agreeing to the [CLA](CLA.md). See [CONTRIBUTING.md](CONTRIBUTING.md).

</details>
