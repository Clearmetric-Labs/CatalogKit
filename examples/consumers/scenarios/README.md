# Consumer scenarios

Scenarios describe how to produce or validate a **consumer bundle** under
`examples/consumers/bundles/<scenario-id>/`.

## Add a scenario

1. Copy `scenarios/_template/` to `scenarios/<your-id>/`.
2. Edit `scenario.yaml`:
   - `mode: project` — runs `cm compile` / `cm impact` via `build_bundle.py`
   - `mode: prebuilt` — validates an existing bundle at `bundle_dir`
3. Add `checks.yaml` with hand-verified expectations (optional but recommended).
4. Register in `registry.yaml` (`ci: true` only for CI-safe fixtures).
5. Run:

```bash
python scripts/consumers/build_bundle.py --scenario examples/consumers/scenarios/minimal
```

6. Open viewers with `?bundle=../bundles/<your-id>`.

Apps bind to `bundle.manifest.json` only — never hardcode scenario ids in viewer code.
