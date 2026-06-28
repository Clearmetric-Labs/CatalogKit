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

REPO_ROOT = Path(__file__).resolve().parents[4]
BUILD_SCRIPT = REPO_ROOT / "scripts" / "consumers" / "build_bundle.py"
MINIMAL_SCENARIO = REPO_ROOT / "examples" / "consumers" / "scenarios" / "minimal"
COMMITTED_BUNDLE = REPO_ROOT / "examples" / "consumers" / "bundles" / "minimal"


def test_build_minimal_bundle_to_tmp(tmp_path: Path):
    out_dir = tmp_path / "bundle"
    result = subprocess.run(
        [
            sys.executable,
            str(BUILD_SCRIPT),
            "--scenario",
            str(MINIMAL_SCENARIO),
            "--out",
            str(out_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(REPO_ROOT),
    )
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
    result = subprocess.run(
        [
            sys.executable,
            str(BUILD_SCRIPT),
            "--scenario",
            str(scenario_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert (bundle_dir / "meta.json").is_file()
