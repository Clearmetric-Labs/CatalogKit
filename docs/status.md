# Project status

**Release stage:** early development (0.x). Pin `clearmetric-core` versions in production use.

**Adoption gate:** **NOT PASSED** — public product claims stay scoped to the warehouse wedge until external evidence exists. Details: [adoption-gate.md](adoption-gate.md).

## What to expect

- Column lineage and impact work on parseable SQL with known upstream schema.
- Star-heavy or ambiguous SQL produces **explicit warnings**, not silent guesses.
- Warehouse binding uses local metadata exports; unresolved bindings are flagged honestly.
- Resolver correctness on messy real-world SQL is an ongoing track — see [Validation](validation/what-works.md).

## Where limits live

- [What works today](validation/what-works.md) — practical trust boundaries
- [SQL support and limits](validation/sql-limits.md) — pointer to the full resolver spec
- [Help test on real projects](validation/help-test.md) — report gaps on your SQL

Planning docs (not shipping promises): [Roadmap](roadmap.md).
