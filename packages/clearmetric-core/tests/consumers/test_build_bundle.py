"""Build bundle integration tests."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from clearmetric.core.errors import ValidationError
from clearmetric.core.validate import (
    load_artifact_file,
    load_bundle_manifest_file,
)

from tests.consumers.checks_runner import run_checks

REPO_ROOT = Path(__file__).resolve().parents[4]
BUILD_SCRIPT = REPO_ROOT / "scripts" / "consumers" / "build_bundle.py"
MINIMAL_SCENARIO = REPO_ROOT / "examples" / "consumers" / "scenarios" / "minimal"
LINEAGE_SCENARIO = REPO_ROOT / "examples" / "consumers" / "scenarios" / "lineage-demo"
COMMITTED_BUNDLE = REPO_ROOT / "examples" / "consumers" / "bundles" / "minimal"


def _run_build(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(BUILD_SCRIPT), *args],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(REPO_ROOT),
    )


def test_build_minimal_bundle_to_tmp(tmp_path: Path):
    out_dir = tmp_path / "bundle"
    result = _run_build("--scenario", str(MINIMAL_SCENARIO), "--out", str(out_dir))
    assert result.returncode == 0, result.stderr or result.stdout

    manifest = load_bundle_manifest_file(out_dir / "bundle.manifest.json")

    graph_path = out_dir / manifest["artifacts"]["graph"]["path"]
    catalog_path = out_dir / manifest["artifacts"]["catalog"]["path"]
    load_artifact_file(graph_path)
    load_artifact_file(catalog_path)

    for impact_ref in manifest["artifacts"]["impacts"].values():
        assert (out_dir / impact_ref["path"]).is_file()

    checks_path = MINIMAL_SCENARIO / "checks.yaml"
    checks = yaml.safe_load(checks_path.read_text(encoding="utf-8"))
    impact_keys = set(manifest["artifacts"]["impacts"])
    for case in checks["cases"]:
        impact_key = case.get("impact")
        if impact_key is not None:
            assert impact_key in impact_keys


def test_committed_minimal_bundle_valid():
    manifest = load_bundle_manifest_file(COMMITTED_BUNDLE / "bundle.manifest.json")
    load_artifact_file(COMMITTED_BUNDLE / manifest["artifacts"]["graph"]["path"])
    load_artifact_file(COMMITTED_BUNDLE / manifest["artifacts"]["catalog"]["path"])


def test_admin_lane_envelope_rejected(tmp_path: Path):
    from clearmetric.core.validate import validate_bundle_artifact_file

    wrapped = {
        "format": "consumer-catalog",
        "version": "1",
        "identity": "analyst",
        "node_count": 0,
        "edge_count": 0,
        "payload": {"version": "1", "nodes": [], "edges": [], "warnings": []},
    }
    path = tmp_path / "wrapped.json"
    path.write_text(json.dumps(wrapped), encoding="utf-8")
    with pytest.raises(ValidationError, match="must not be wrapped"):
        validate_bundle_artifact_file(path, lane="admin")


def test_consumer_lane_missing_envelope_rejected(tmp_path: Path):
    from clearmetric.core.validate import validate_bundle_artifact_file

    raw = {"version": "1", "nodes": [], "edges": [], "warnings": []}
    path = tmp_path / "raw.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ValidationError, match="consumer-envelope.schema.json"):
        validate_bundle_artifact_file(path, lane="consumer")


def test_prebuilt_mode_resolves_bundle_dir(tmp_path: Path):
    bundle_dir = tmp_path / "bundle"
    shutil.copytree(COMMITTED_BUNDLE, bundle_dir)
    scenario_dir = tmp_path / "scenario"
    scenario_dir.mkdir()
    (scenario_dir / "scenario.yaml").write_text(
        yaml.safe_dump(
            {
                "id": "prebuilt-test",
                "label": "prebuilt",
                "mode": "prebuilt",
                "bundle_dir": "../bundle",
            }
        ),
        encoding="utf-8",
    )
    result = _run_build("--scenario", str(scenario_dir))
    assert result.returncode == 0, result.stderr or result.stdout
    assert (bundle_dir / "meta.json").is_file()


def test_build_lineage_demo_to_tmp(tmp_path: Path):
    out_dir = tmp_path / "bundle"
    result = _run_build("--scenario", str(LINEAGE_SCENARIO), "--out", str(out_dir))
    assert result.returncode == 0, result.stderr or result.stdout

    manifest = load_bundle_manifest_file(out_dir / "bundle.manifest.json")
    assert manifest["defaults"]["impact_key"] == "orders_base.amount_downstream"

    violations = run_checks(
        out_dir, LINEAGE_SCENARIO / "checks.yaml", manifest=manifest
    )
    assert violations == []


def test_atomic_failure_preserves_existing_bundle(tmp_path: Path):
    bundle_dir = tmp_path / "bundle"
    shutil.copytree(COMMITTED_BUNDLE, bundle_dir)
    original_manifest = (bundle_dir / "bundle.manifest.json").read_bytes()

    scenario_dir = tmp_path / "scenario"
    scenario_dir.mkdir()
    (scenario_dir / "scenario.yaml").write_text(
        yaml.safe_dump(
            {
                "id": "fail-test",
                "label": "fail",
                "mode": "project",
                "project_dir": str(REPO_ROOT / "examples" / "lineage-demo"),
                "outputs": [
                    {"compile_format": "json", "out": "graph.json"},
                    {"compile_format": "catalog", "out": "catalog.json"},
                ],
                "impacts": [
                    {
                        "selection": "no.such.column",
                        "direction": "upstream",
                        "manifest_key": "bad",
                        "out": "impacts/bad.json",
                    }
                ],
                "defaults": {"impact_key": "bad"},
            }
        ),
        encoding="utf-8",
    )

    result = _run_build("--scenario", str(scenario_dir), "--out", str(bundle_dir))
    assert result.returncode != 0, result.stdout
    assert (bundle_dir / "bundle.manifest.json").read_bytes() == original_manifest


def test_rejects_consumer_catalog_format(tmp_path: Path):
    scenario_dir = tmp_path / "scenario"
    scenario_dir.mkdir()
    (scenario_dir / "scenario.yaml").write_text(
        yaml.safe_dump(
            {
                "id": "bad-format",
                "label": "bad",
                "mode": "project",
                "project_dir": str(REPO_ROOT / "examples" / "lineage-demo"),
                "outputs": [
                    {"compile_format": "consumer-catalog", "out": "catalog.json"},
                ],
                "impacts": [
                    {
                        "selection": "orders.amount",
                        "direction": "upstream",
                        "manifest_key": "k",
                        "out": "impacts/k.json",
                    }
                ],
                "defaults": {"impact_key": "k"},
            }
        ),
        encoding="utf-8",
    )
    result = _run_build("--scenario", str(scenario_dir), "--out", str(tmp_path / "out"))
    assert result.returncode != 0
    assert "V0 bundle builder" in (result.stderr or result.stdout)
    assert "consumer-catalog" in (result.stderr or result.stdout)


def test_rejects_consumer_lane(tmp_path: Path):
    scenario_dir = tmp_path / "scenario"
    scenario_dir.mkdir()
    (scenario_dir / "scenario.yaml").write_text(
        yaml.safe_dump(
            {
                "id": "bad-lane",
                "label": "bad",
                "mode": "project",
                "project_dir": str(REPO_ROOT / "examples" / "lineage-demo"),
                "outputs": [
                    {
                        "compile_format": "json",
                        "out": "graph.json",
                        "lane": "consumer",
                    },
                    {"compile_format": "catalog", "out": "catalog.json"},
                ],
                "impacts": [
                    {
                        "selection": "orders.amount",
                        "direction": "upstream",
                        "manifest_key": "k",
                        "out": "impacts/k.json",
                    }
                ],
                "defaults": {"impact_key": "k"},
            }
        ),
        encoding="utf-8",
    )
    result = _run_build("--scenario", str(scenario_dir), "--out", str(tmp_path / "out"))
    assert result.returncode != 0
    assert "admin" in (result.stderr or result.stdout)


def test_requires_defaults_impact_key(tmp_path: Path):
    scenario_dir = tmp_path / "scenario"
    scenario_dir.mkdir()
    (scenario_dir / "scenario.yaml").write_text(
        yaml.safe_dump(
            {
                "id": "no-defaults",
                "label": "bad",
                "mode": "project",
                "project_dir": str(REPO_ROOT / "examples" / "lineage-demo"),
                "outputs": [
                    {"compile_format": "json", "out": "graph.json"},
                    {"compile_format": "catalog", "out": "catalog.json"},
                ],
                "impacts": [
                    {
                        "selection": "orders.amount",
                        "direction": "upstream",
                        "manifest_key": "k",
                        "out": "impacts/k.json",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    result = _run_build("--scenario", str(scenario_dir), "--out", str(tmp_path / "out"))
    assert result.returncode != 0
    assert "defaults.impact_key" in (result.stderr or result.stdout)
