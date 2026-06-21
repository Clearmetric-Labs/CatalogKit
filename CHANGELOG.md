# Changelog

All notable changes to this project will be documented in this file.

## 0.1.9 - 2026-06-21

### Changed

- `catalogkit-lineage` enforces strict value-lineage (R6–R8): `SELECT *`, `UNION`, and quoted/unresolved outputs warn without emitting unsafe `derives_from` edges
- centralized SQL shape detection and edge counting in shared engine modules
- aligned all CatalogKit packages to lockstep versioning at `0.1.9`

### Added

- enterprise adversarial manifest with independent hand-derived value-lineage oracle
- warning-cause variant fixtures and CI trust-gate coverage for oracle and variant tests

## 0.1.8 - 2026-06-21

### Changed

- aligned all CatalogKit packages to lockstep versioning at `0.1.8`
- updated the meta-package to require `catalogkit-core`, `catalogkit-query`, and `catalogkit-lineage` at the same release

## 0.1.7 - 2026-06-21

### Changed

- refreshed the root README to lead with the code-derived catalog positioning, a verified compile snippet, and accurate tool descriptions
- `build_openlineage_export` now accepts a pre-built `CatalogArtifact`, so OpenLineage export can chain after `build_catalog_artifact` without reloading the project

## 0.1.2 - 2026-06-20

### Changed

- aligned `catalogkit-lineage` package exports, README examples, and local development instructions with the existing CatalogKit module conventions
- grouped OpenLineage export inputs by output column instead of emitting one export row per lineage edge
- made lineage traversal selections and manifest compiled-path handling fail loudly on invalid input
- tightened release metadata so the coordinated `0.1.2` package set resolves to the freshly published module versions
- added publish-time version checks so package tags cannot drift from source versions

### Added

- first PyPI release of `catalogkit-lineage` for project-level SQL lineage from dbt manifests and SQL folders
- focused lineage regression coverage for grouped OpenLineage export, unknown traversal selections, manifest path escapes, and duplicate SQL-folder dataset names

### Supported

- `SELECT ...`
- `INSERT ... SELECT ...`
- `CREATE ... AS SELECT ...`

### Deferred

- output column lineage
- join semantics beyond dependency mapping
- wrapper target outputs
- warehouse-aware `SELECT *` expansion
