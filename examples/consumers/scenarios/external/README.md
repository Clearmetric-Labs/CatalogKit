# External dbt project runbook

Use this path to prove the consumer bundle on **real** dbt projects without
committing large manifests to the repository.

## Steps

1. **Clone** an external dbt project locally (outside or inside a gitignored path).

2. **Compile dbt** so `target/manifest.json` includes `compiled_code`:

   ```bash
   cd /path/to/external-dbt-project
   dbt deps
   dbt compile
   ```

   ClearMetric requires compiled SQL in the manifest — `dbt parse` alone is not
   sufficient.

3. **Create a ClearMetric project** (`clearmetric.yaml`) pointing at the manifest
   and optional warehouse INFORMATION_SCHEMA JSON export.

4. **Add a scenario** under `examples/consumers/scenarios/external/<project>/`:

   ```yaml
   id: gitlab-local
   label: GitLab analytics (local)
   mode: project
   project_dir: /absolute/path/to/clearmetric-project
   provenance: gitlab-data/analytics transform/snowflake-dbt
   outputs:
     - compile_format: json
       out: graph.json
     - compile_format: catalog
       out: catalog.json
   impacts:
     - selection: column.you.hand.traced
       direction: upstream
       manifest_key: example_upstream
       out: impacts/example_upstream.json
   checks: checks.yaml
   ```

5. **Build the bundle** (output stays gitignored unless you choose to commit):

   ```bash
   python scripts/consumers/build_bundle.py \
     --scenario examples/consumers/scenarios/external/gitlab-local
   ```

   Default output: `examples/consumers/bundles/gitlab-local/`

6. **Open viewers** with zero app changes:

   ```text
   catalog-viewer/index.html?bundle=../bundles/gitlab-local
   lineage-explorer/index.html?bundle=../bundles/gitlab-local
   ```

7. **Hand-trace** a few columns in the compiled SQL. Encode verified expectations
   in `checks.yaml` and run:

   ```bash
   pytest packages/clearmetric-core/tests/consumers/test_corpus_checks.py -k gitlab
   ```

## Reference projects (documentation only)

These are suggested external targets — **do not** reference them in viewer code:

| Project | Notes |
|---------|-------|
| [GitLab analytics](https://gitlab.com/gitlab-data/analytics) | Production-scale; Snowflake + env vars for `dbt compile` |
| [Mattermost data warehouse](https://github.com/mattermost/mattermost-data-warehouse) | Real company analytics repo |
| [stellar-dbt-public](https://github.com/stellar/stellar-dbt-public) | BigQuery staging/marts |
| [RA data warehouse](https://github.com/rittmananalytics/ra_data_warehouse) | Dual-target macros; pick one warehouse |

## Admin lane first

V0 viewers expect **admin-lane** bundles (`json`, `catalog`, ungated `impact`).

Lab consumer formats require `CM_EXPERIMENTAL=1`, `--identity`, and
`lane: consumer` in the bundle manifest — add later as optional scenarios, not
in the first public demo.

## Prebuilt mode

If you already have a bundle directory with artifacts and
`bundle.manifest.json`:

```yaml
mode: prebuilt
bundle_dir: ../bundles/gitlab-local
```

`build_bundle.py` validates schemas only — no `cm` invocation.
