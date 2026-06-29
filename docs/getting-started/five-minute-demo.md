# Five-minute demo

Run this in a clean environment with the published package. Commands below were captured from
`pip install clearmetric-core` and the [`lineage-demo`](https://github.com/ClearMetric-Labs/ClearMetric-Core/tree/main/examples/lineage-demo) example.

```bash
pip install clearmetric-core
cd examples/lineage-demo   # from a clone, or copy that folder

cm connect warehouse --information-schema ./warehouse_schema.json
cm scan
cm compile --format json > graph.json
cm impact orders_base.amount --downstream --format json
cm impact customers_report.customer_lifetime_value --upstream --format json
cm clean
cm contract graph.json
```

Column selections accept forms like `orders_base.amount` or `column:orders_base.amount`.

## Scan

```text
config: …/lineage-demo/clearmetric.yaml
dialect: postgres
source: warehouse -> …/warehouse_schema.json
source: sql -> …/sql
```

## Impact downstream from `orders_base.amount`

Expected `related_ids`:

- `column:customer_totals.total_amount`
- `column:customers_report.customer_lifetime_value`

Example output (truncated):

```json
{
  "selection": "orders_base.amount",
  "selection_id": "column:orders_base.amount",
  "related_ids": [
    "column:customer_totals.total_amount",
    "column:customers_report.customer_lifetime_value"
  ],
  "warnings": [
    {
      "code": "warehouse_bind_unresolved",
      "message": "column:orders_base.amount parent table could not be uniquely bound to warehouse metadata (match_status=unresolved)",
      "subject_id": "column:orders_base.amount"
    }
  ]
}
```

## Impact upstream to `customers_report.customer_lifetime_value`

Expected `related_ids`:

- `column:customer_totals.total_amount`
- `column:orders_base.amount`
- `column:raw_orders.amount`

## Clean and contract

`cm clean` prints warehouse binding warnings for this demo (SQL model names do not match every
warehouse table name). Warnings do not fail exit; errors would.

`cm contract graph.json` prints `contract: valid (graph.json)` when the artifact passes schema and enforce checks.

Next: [run on your own project](your-project.md) or [check lineage yourself](../validation/check-lineage.md).
