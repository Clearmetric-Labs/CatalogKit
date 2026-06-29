# Help test on real projects

Resolver quality on messy real-world SQL is the main product gate. If you run ClearMetric on
your dbt or SQL project, you can help more than any internal fixture run.

## What we need

Open a [GitHub issue](https://github.com/ClearMetric-Labs/ClearMetric-Core/issues/new) with:

| Field | Example |
|-------|---------|
| **Project type** | dbt + Snowflake export / SQL folder only |
| **ClearMetric version** | output of `cm --version` |
| **Commands run** | exact `cm` invocations |
| **SQL or model** | minimal snippet or model name (redact secrets) |
| **Warnings** | paste compile/impact warning JSON or stderr |
| **Expected lineage** | which columns should connect and why |
| **Actual lineage** | `related_ids` from `cm impact … --format json` |
| **Why expected is correct** | one paragraph — join keys, grain, business definition |

Redact credentials and customer data. A trimmed SQL repro is enough.

## How to reproduce locally

```bash
cm scan
cm compile --format json > graph.json 2> warnings.log
cm impact YOUR_COLUMN --upstream --format json
cm impact YOUR_COLUMN --downstream --format json
```

Attach `warnings.log` and impact JSON. If the project cannot be shared, a minimal repro SQL file
plus warehouse column list is still valuable.

## Out of scope for this feedback

- `CM_EXPERIMENTAL`, `cm serve`, live warehouse connectors
- Power BI / backbone lab modules

Public wedge only — see [What it does today](../current-scope.md).

## After you file

Issues with repro SQL drive resolver fixes and become regression tests. Thank you for testing
on real projects.
