# ClearMetric example notebooks

Interactive walkthroughs of the main scenarios in this repository. Each notebook
focuses on one track so you can learn the public wedge, Python API, consumer
bundles, and experimental backbone lab separately.

## Prerequisites

From the repository root:

```bash
python -m pip install -e "packages/clearmetric-core[dev,runtime]"
jupyter lab   # or: jupyter notebook
```

Open notebooks from `examples/notebooks/`. They resolve paths relative to the repo
root automatically.

## Notebooks

| Notebook | Track | What you learn |
|----------|-------|----------------|
| [01_public_wedge_lineage.ipynb](01_public_wedge_lineage.ipynb) | Public wedge | Compile the jaffle graph, explore nodes, run impact, report-only clean |
| [02_compile_formats.ipynb](02_compile_formats.ipynb) | Public wedge | Admin emit formats: `json`, `catalog`, `openlineage`, `text` |
| [03_impact_analysis.ipynb](03_impact_analysis.ipynb) | Public wedge | Upstream/downstream traversal, warnings, emitted impact JSON |
| [04_consumer_bundle.ipynb](04_consumer_bundle.ipynb) | Consumer MVP | Bundle manifest, schema validation, rebuild via `build_bundle.py` |
| [05_backbone_lab_experimental.ipynb](05_backbone_lab_experimental.ipynb) | Lab (`CM_EXPERIMENTAL`) | Policy-gated consumer emits, identity impact, DuckDB query harness |

## Related examples (non-notebook)

- [examples/wedge-jaffle](../wedge-jaffle/README.md) — CLI quickstart for the public wedge
- [examples/backbone-lab](../backbone-lab/README.md) — experimental scaffold demo
- [examples/consumers](../consumers/README.md) — artifact bundle + vanilla HTML viewers
