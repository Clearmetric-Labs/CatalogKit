"""Path security tests for manifest-relative compiled SQL loading."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from clearmetric.lineage.errors import LineageInputError
from clearmetric.lineage.loaders import load_project


def _write_manifest(root: Path, *, compiled_path: str) -> Path:
    manifest = {
        "metadata": {"project_name": "escape-test"},
        "nodes": {
            "model.test.orders": {
                "resource_type": "model",
                "name": "orders",
                "compiled_path": compiled_path,
                "depends_on": {"nodes": []},
            }
        },
    }
    manifest_path = root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    compiled_dir = root / "target" / "compiled"
    compiled_dir.mkdir(parents=True, exist_ok=True)
    (compiled_dir / "orders.sql").write_text("select 1 as id", encoding="utf-8")
    return manifest_path


def test_manifest_compiled_path_escape_is_rejected(tmp_path: Path):
    manifest_path = _write_manifest(tmp_path, compiled_path="../../../etc/passwd")
    with pytest.raises(LineageInputError, match="escapes the manifest directory"):
        load_project(manifest_path, dialect="postgres")


def test_manifest_compiled_path_symlink_escape_is_rejected(tmp_path: Path):
    outside_root = Path("/tmp") / f"cm-outside-{tmp_path.name}"
    outside_root.mkdir(exist_ok=True)
    outside = outside_root / "outside"
    outside.mkdir(exist_ok=True)
    (outside / "secret.sql").write_text("select 1 as secret", encoding="utf-8")
    link = tmp_path / "link.sql"
    link.symlink_to(outside / "secret.sql")
    manifest_path = _write_manifest(tmp_path, compiled_path="link.sql")
    with pytest.raises(LineageInputError, match="escapes the manifest directory"):
        load_project(manifest_path, dialect="postgres")
