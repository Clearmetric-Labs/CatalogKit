# Backbone Lab Example

> **Experimental / internal architecture proof / not a shipped capability / no stability guarantee.**

This example proves Module A primitives on the same graph as the wedge. It is **not**
part of the public product promise in the root README.

## Setup

Copy jaffle shop fixtures into this directory (or run from a project initialized with
warehouse + dbt + intent sources). See [docs/backbone-lab.md](../../docs/backbone-lab.md).

## Demo

```bash
export CM_EXPERIMENTAL=1
cm compile --format json > graph.json
cm compile --format catalog > catalog.json
cm compile --format consumer-catalog --identity analyst > consumer_catalog.json
cm compile --format frontend-contract --identity analyst > contracts.json
cm impact orders.amount --upstream
cm query --identity analyst query:executive_revenue
```
