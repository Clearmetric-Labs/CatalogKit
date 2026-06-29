# Install

## Public install

```bash
pip install clearmetric-core
cm --version
```

Package on PyPI: `clearmetric-core` (includes the `cm` CLI).

## Try the demo project

```bash
git clone https://github.com/ClearMetric-Labs/ClearMetric-Core.git
cd ClearMetric-Core/examples/lineage-demo
```

Or copy that folder from the repo. Then follow the [five-minute demo](five-minute-demo.md).

## Warehouse metadata

ClearMetric reads a **local INFORMATION_SCHEMA JSON export** — not a live warehouse connection.
You export metadata once, point `cm connect warehouse --information-schema` at the file, and compile offline.

## Contributors

Editable install from a clone:

```bash
python -m pip install -e "packages/clearmetric-core[dev,runtime,release]"
```

See [Development](../development.md).
