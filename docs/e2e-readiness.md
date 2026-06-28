# E2E Readiness Checkpoint

This document defines when backbone **primitives** are ready for deep e2e testing and example consumer applications. It does not expand the public product promise — see [adoption-gate.md](adoption-gate.md).

## Checkpoint criteria (0.7.1)

All must be true:

- Boundary leaks closed: impact `--identity` validates identity and gates selection loudly; `apply_policy` filters warnings and strips governance aspects; compile batches malformed contract aspects; runtime validates identity at API boundary
- Centralized surfaces enforced (see table below)
- Boundary tests green: projection, policy, impact identity, compile contracts, runtime, emitters, CLI lab hiding
- Regression green: `test_mvp_demo.py`, `test_wedge_e2e.py`, repository boundary suite
- No new public README / v1-boundary claims for lab formats

## Centralized surface contract

| Concern | Sole owner | Callers |
|---------|-----------|---------|
| Warning visibility | `core.models.filter_warnings_for_ids` | `graph.select`, `projection.apply_policy` |
| Node authz | `policy.gate` | `projection.apply_policy`, `require_allow`, `filter_allow_only_ids` |
| Execute authz (loud) | `policy.require_allow` | `runtime.execute_project_query`, `compiler.impact` (selection) |
| Allow-only ID filter | `policy.filter_allow_only_ids` | `compiler.impact` (related_ids) |
| Identity validation | `policy.require_gated_identity` | CLI experimental, `compiler.impact`, runtime, `gated_context` |
| Consumer node prep | `projection.apply_policy` | `emitters.registry` (consumer lane) |
| Governance aspect strip | `policy.models.strip_sensitive_aspects` | `projection.apply_policy` only |
| Compile dispatch | `emitters.registry.emit_compile` | CLI `_run_compile` |
| Rules load (emit) | `policy.gated_context` | `emitters.registry` only |
| Rules load (runtime/impact) | `policy.load_rules` | runtime, impact |

Pipeline shape for every consumer:

```text
select → gate → apply_policy → emit
```

## Deferred: robust e2e matrix

Build when example apps exist to drive scenarios:

- Cross-format canonical ID parity (graph → consumer-catalog → frontend-contract → impact → query)
- Negative paths per surface (deny, mask, missing compiled_sql, missing seed)
- Serve HTTP contract tests beyond existing MVP demo block

Run lab tests with `CM_EXPERIMENTAL=1`. Keep wedge regression without experimental env.

## Deferred: example consumer applications

Thin apps under `examples/consumers/` — **zero** duplicated policy/projection logic:

| App | Input | UI job |
|-----|-------|--------|
| `bi-minimal` | `compile --format frontend-contract --identity X` | Bind SQL + render table |
| `catalog-viewer` | `compile --format consumer-catalog --identity X` | Browse enveloped nodes |
| `ai-host` | `compile --format ai-context --identity X` | Feed payload to BYO LLM |
| `lineage-explorer` | `graph.json` + ungated `impact` | Visualize traversal |

Each app calls one CLI command or `emit_compile` — no reimplementation of gate or projection.

## Deferred: resolver corpus

Graph correctness on messy real SQL is a **parallel track**, not gated by this checkpoint. See [packages/clearmetric-core/docs/lineage/limitations.md](../packages/clearmetric-core/docs/lineage/limitations.md).

## Stop condition

After this checkpoint: next work is example apps + e2e OR resolver corpus — not more substrate rewrites.
