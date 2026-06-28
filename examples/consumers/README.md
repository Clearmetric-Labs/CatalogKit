# Consumer reference apps

Thin **read-only** viewers over a versioned **artifact bundle**. They prove the
backbone consumer pattern without duplicating policy, projection, or traversal.

```text
cm compile / cm impact
→ validated JSON bundle (bundle.manifest.json)
→ vanilla viewer reads bundle
→ no browser-side policy
```

## Quick start

From the repository root:

```bash
python -m http.server 8000 --directory examples/consumers
```

Open:

- Catalog: `http://127.0.0.1:8000/catalog-viewer/index.html?bundle=../bundles/minimal`
- Lineage: `http://127.0.0.1:8000/lineage-explorer/index.html?bundle=../bundles/minimal`

The `?bundle=` parameter is **required**. It must point at a directory containing
`bundle.manifest.json`.

## Regenerate the minimal bundle

```bash
python scripts/consumers/build_bundle.py --scenario examples/consumers/scenarios/minimal
```

## Layout

```text
examples/consumers/
  shared/artifact-kit.mjs     # loader helpers only
  catalog-viewer/             # browse catalog artifact
  lineage-explorer/           # flat impact list + links
  scenarios/                  # scenario recipes + checks.yaml
  bundles/minimal/              # committed CI fixture
```

Apps bind to **`bundle.manifest.json` + declared lanes** — never to a specific
project id in code.

## Security

Viewers display **pre-emitted** artifacts only. RBAC, RLS, masking, and
governance projection run at compile time in `policy.gate` and
`projection.apply_policy`. The browser does not re-gate.

V0 bundles use the **admin lane** (`json`, `catalog`, ungated `impact`). Lab
consumer formats (`consumer-catalog`, `frontend-contract`, `ai-context`) are
optional scenario recipes behind `CM_EXPERIMENTAL=1` — not part of the public
wedge demo.

## Specs

- [`spec/consumer-bundle.schema.json`](../../spec/consumer-bundle.schema.json)
- [`spec/impact-output.schema.json`](../../spec/impact-output.schema.json)
- [`spec/consumer-envelope.schema.json`](../../spec/consumer-envelope.schema.json)
- [`spec/catalog-artifact.schema.json`](../../spec/catalog-artifact.schema.json)

Validation is centralized in `clearmetric.core.validate`.
