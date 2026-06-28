# Lineage Demo

Self-contained plain-SQL lineage example. Three SQL files form a small pipeline from `raw_orders` through `orders_base` → `customer_totals` → `customers_report`, merged with a local warehouse metadata export.

## Prerequisites

```bash
pip install clearmetric-core
cd examples/lineage-demo
```

## Commands

```bash
cm scan
cm compile --format json > graph.json
cm impact orders_base.amount --downstream --format json
cm impact customers_report.customer_lifetime_value --upstream --format json
cm compile --format catalog > catalog.json
cm clean
cm contract graph.json
```

The downstream impact probe on `orders_base.amount` returns two related columns:

```bash
cm impact orders_base.amount --downstream --format json
```

Expected `related_ids`:

- `column:customer_totals.total_amount`
- `column:customers_report.customer_lifetime_value`

## What this demonstrates

- Plain SQL folder ingestion with column-level `derives_from` edges
- Warehouse metadata merged into the same graph (physical bindings on table/column nodes)
- Non-empty upstream/downstream impact traversal
- Catalog output limited to table, column, and model nodes
