"""Declarative corpus checks against consumer bundles."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml
from clearmetric.core.validate import (
    load_artifact_file,
    load_bundle_manifest_file,
    load_impact_output_file,
)


def _load_checks(path: Path) -> list[dict[str, Any]]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"checks file must be a mapping: {path}")
    cases = payload.get("cases")
    if not isinstance(cases, list):
        raise ValueError(f"checks file must contain cases list: {path}")
    return cases


def _artifact_path(
    bundle_dir: Path, manifest: dict[str, Any], artifact_key: str
) -> Path:
    artifacts = manifest["artifacts"]
    if artifact_key not in artifacts:
        raise ValueError(f"unknown artifact key: {artifact_key}")
    ref = artifacts[artifact_key]
    return bundle_dir / ref["path"]


def _impact_path(bundle_dir: Path, manifest: dict[str, Any], impact_key: str) -> Path:
    impacts = manifest["artifacts"]["impacts"]
    if impact_key not in impacts:
        raise ValueError(f"unknown impact key: {impact_key}")
    ref = impacts[impact_key]
    return bundle_dir / ref["path"]


def _matches(value: str, pattern: str) -> bool:
    if pattern.startswith("regex:"):
        return re.search(pattern.removeprefix("regex:"), value) is not None
    return value == pattern


def run_checks(
    bundle_dir: Path,
    checks_path: Path,
    *,
    manifest: dict[str, Any] | None = None,
) -> list[str]:
    """Run all checks; return violation messages (empty if all pass)."""
    if manifest is None:
        manifest = load_bundle_manifest_file(bundle_dir / "bundle.manifest.json")
    violations: list[str] = []
    for case in _load_checks(checks_path):
        case_id = str(case.get("id") or "<unnamed>")
        case_violations = _run_case(bundle_dir, manifest, case)
        for message in case_violations:
            violations.append(f"{case_id}: {message}")
    return violations


def _run_case(
    bundle_dir: Path,
    manifest: dict[str, Any],
    case: dict[str, Any],
) -> list[str]:
    violations: list[str] = []
    artifact_key = case.get("artifact")
    impact_key = case.get("impact")

    if isinstance(artifact_key, str):
        artifact = load_artifact_file(
            _artifact_path(bundle_dir, manifest, artifact_key)
        )
        node_ids = {node.id for node in artifact.nodes}
        kinds = {node.kind for node in artifact.nodes}

        for kind in case.get("expect_node_kinds") or []:
            if kind not in kinds:
                violations.append(
                    f"expected node kind {kind!r} in artifact {artifact_key!r}"
                )

        for node_id in case.get("expect_node_exists") or []:
            if node_id not in node_ids:
                violations.append(
                    f"expected node {node_id!r} in artifact {artifact_key!r}"
                )

    if isinstance(impact_key, str):
        impact = load_impact_output_file(_impact_path(bundle_dir, manifest, impact_key))
        related = list(impact.get("related_ids") or [])

        expected_selection = case.get("expect_selection_id")
        if isinstance(expected_selection, str):
            if impact.get("selection_id") != expected_selection:
                violations.append(
                    f"expected selection_id {expected_selection!r}, "
                    f"got {impact.get('selection_id')!r}"
                )

        for node_id in case.get("expect_related_includes") or []:
            if not any(_matches(related_id, node_id) for related_id in related):
                violations.append(f"expected related_ids to include {node_id!r}")

        for node_id in case.get("expect_related_excludes") or []:
            if any(_matches(related_id, node_id) for related_id in related):
                violations.append(f"expected related_ids to exclude {node_id!r}")

        warning_codes = {w.get("code") for w in impact.get("warnings") or []}
        codes = case.get("expect_warning_code") or []
        if isinstance(codes, str):
            codes = [codes]
        for code in codes:
            if code not in warning_codes:
                violations.append(
                    f"expected warning code {code!r} in impact {impact_key!r}"
                )

    return violations
