# catalogkit-lineage Limitations

`catalogkit-lineage` is intentionally deterministic and headless.

## Supported Input

`catalogkit-lineage` accepts exactly one project input per invocation:

- a dbt `manifest.json` file
- a folder containing one or more `.sql` files

The tool does not run dbt. Manifest input must already point at compiled SQL.

## Guarantees

`catalogkit-lineage` guarantees:

- one supported project input per invocation
- dialect-aware lineage tracing through `sqlglot`
- deterministic table and column IDs through `catalogkit-core`
- project-level upstream and downstream traversal
- a mergeable `CatalogArtifact`
- loud failure on unsupported invocation shapes

## Current Boundaries

`catalogkit-lineage` does **not** currently provide:

- warehouse execution
- dbt compile / parse orchestration
- connector credentials or live metadata hydration
- intermediate CTE column nodes in the public artifact
- a full OpenLineage event emitter

Folder input is intentionally lighter-weight than dbt manifest input. When a SQL
folder does not provide root-table schema metadata, `SELECT *` leaves at the
external boundary may remain unresolved and will emit warnings instead of
invented column lineage.

## Warning-Based Behavior

`catalogkit-lineage` warns instead of failing when the project input is valid but
individual SQL files remain messy:

- `SELECT *`
- ambiguous output sources
- unresolved lineage leaves
- per-dataset lineage resolution failures

That recoverable behavior applies inside supported manifest/folder inputs. It
does not relax the top-level input contract.

## Identity Rule

For SQL lineage composition, dbt models are currently represented as SQL
datasets with `table:` and `column:` IDs so they merge cleanly with
`catalogkit-query` artifacts built from compiled SQL.
