# SQL support and limits

ClearMetric resolves column lineage with sqlglot-backed analysis on supported dialects. Behavior
for stars, unions, CTEs, joins, and warehouse binding is specified in one place:

**[Lineage support and limits](../reference/lineage-limitations.md)** — canonical resolver spec.

This page is a nav pointer only. Do not duplicate the spec here; update
`reference/lineage-limitations.md` when resolver behavior changes.

Practical trust boundaries: [What works today](what-works.md).
