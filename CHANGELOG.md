# Changelog

All notable changes to this project will be documented in this file.

## 0.1.0 - Unreleased

Initial public OSS release candidate.

### Added

- deterministic relation extraction for supported single-statement SQL inputs
- canonical `QueryMap` artifact with stable top-level shape
- CLI text and JSON output modes
- contract docs, governance files, and release validation workflow

### Supported

- `SELECT ...`
- `INSERT ... SELECT ...`
- `CREATE ... AS SELECT ...`

### Deferred

- output column lineage
- join semantics beyond dependency mapping
- wrapper target outputs
- warehouse-aware `SELECT *` expansion
