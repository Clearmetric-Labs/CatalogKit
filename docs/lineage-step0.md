# `catalogkit-lineage` Step 0 Kill-Test

## Verdict

**GO**. The gap over raw `sqlglot.lineage` is real enough to justify a dedicated
`catalogkit-lineage` package.

The deciding factor is **not** that sqlglot can trace across multiple queries.
It can, as long as the caller manually supplies the right `sources` map and root
`schema`. The gap is that project users still have to assemble that graph
themselves, normalize identities consistently, reverse the graph for downstream
impact, and shape everything into a mergeable artifact. That orchestration is
exactly the primitive this module should own.

If this prototype had shown only "a thinner CLI around `sqlglot.lineage`," the
correct recommendation would have been to stop and switch Module 2 to
`catalogkit-dedupe`. It did more than that, so continuing is justified.

## Fixture

The kill-test uses a minimal vendored slice of the public
`dbt-labs/jaffle-shop-classic` project:

- `stg_customers`
- `stg_orders`
- `stg_payments`
- `orders`
- `customers`

The fixture lives under
[`prototypes/catalogkit-lineage-step0/fixtures/jaffle_shop/`](../prototypes/catalogkit-lineage-step0/fixtures/jaffle_shop/)
and contains:

- a small manifest-like project index
- compiled SQL files derived from the public dbt models
- root seed column schemas

## Compared Approaches

### Baseline A: raw `sqlglot.lineage`

Used directly via:

- target SQL string
- manually assembled `sources` mapping
- manually assembled root `schema`

This works for targeted upstream tracing, but the caller must still:

1. choose the correct subset of upstream models
2. avoid source-name collisions with local CTE names
3. batch every relevant output column across the project
4. reverse the resulting graph to answer downstream impact
5. normalize the result into stable CatalogKit IDs and artifact shape

### Candidate B: tiny project resolver

Implemented in
[`prototypes/catalogkit-lineage-step0/compare_sqlglot_lineage.py`](../prototypes/catalogkit-lineage-step0/compare_sqlglot_lineage.py).

The prototype:

- loads a project fixture once
- builds the transitive upstream `sources` map per model
- derives root schemas from project metadata
- emits canonical `table:` and `column:` IDs using `catalogkit-core`
- produces a `CatalogArtifact`
- supports both `upstream` and `downstream` queries
- merges cleanly with per-file `catalogkit-query` artifacts
- preserves warning-rich behavior for messy but supported SQL

## Concrete Results

### Raw upstream

For `customers.customer_lifetime_value`, direct `sqlglot.lineage` returns the
useful leaf origin:

- `raw_payments.amount`

It also exposes many intermediate local nodes:

- `customer_payments.total_amount`
- `payments.amount`
- `stg_payments.amount`
- `renamed.amount`
- `source.amount`

That is valuable, but still caller-oriented rather than project-oriented.

### Raw downstream

`sqlglot.lineage` has no native project-level downstream query. To answer
"what changes if `raw_payments.amount` changes?" the prototype had to scan all
modeled outputs across the project and build a reverse index itself.

That reverse scan found 7 impacted columns:

- `stg_payments.amount`
- `orders.credit_card_amount`
- `orders.coupon_amount`
- `orders.bank_transfer_amount`
- `orders.gift_card_amount`
- `orders.amount`
- `customers.customer_lifetime_value`

That reverse-indexing step is meaningful orchestration, not wrapper code.

### Prototype artifact

The project resolver produced a normalized `CatalogArtifact` with:

- 46 nodes
- 39 edges
- 1 warning

The warning was the expected recoverable one from the staged `SELECT *` usage:

- `select_star`

That is the right behavior: supported but messy SQL stays warning-rich instead
of becoming a hard failure.

### Merge with `catalogkit-query`

The resolver artifact merged with per-file `catalogkit-query` artifacts into a
combined graph with:

- 55 nodes
- 57 edges
- 1 warning

This matters because it proves the package is not just a lineage tracer. It is
also a **project normalization layer** that composes with the existing
CatalogKit query primitive.

## What the Prototype Proved

The kill-test cleared the bar in four ways:

1. **Project-resolution ergonomics**: the module can own the manifest/file
   loading, source-graph assembly, and root schema derivation that raw
   `sqlglot.lineage` leaves to the caller.
2. **Downstream impact**: the package can answer reverse-graph questions that
   the raw library does not expose as a first-class project primitive.
3. **Artifact normalization**: the package can emit stable CatalogKit IDs and a
   mergeable `CatalogArtifact` instead of an ad hoc lineage tree.
4. **Composability with existing OSS**: the output can merge with
   `catalogkit-query` rather than becoming a separate silo.

## Important Constraints Confirmed

### The package should not claim a larger gap than exists

The value is **not** "sqlglot cannot do cross-file lineage." It can.

The value is:

- loading a real project cleanly
- building the right transitive source map
- making downstream impact first-class
- normalizing the result into CatalogKit’s artifact contract

### Clean-room extraction still matters

The enterprise platform remains reference-only. This prototype used public dbt
inputs plus the existing CatalogKit OSS packages. It did not import or copy
enterprise lineage, governance, comparator, DB-context, or workspace logic.

### ID parity remains high risk

The prototype intentionally uses `table:` and `column:` IDs so it can merge with
`catalogkit-query` on overlapping SQL entities. That identity decision should be
kept under direct test as the package hardens.

## Decision

Proceed to scaffold `catalogkit-lineage`.

The next step is to turn this throwaway resolver into a package that:

- supports dbt manifest input and SQL-folder input through one resolver path
- keeps unsupported invocation shapes as loud failures
- stays recoverable-and-warning-rich on ugly but valid project SQL
- reuses `catalogkit-core` IDs and merge behavior
- proves query/lineage ID parity with overlapping-input tests
