"""Tests for packaged JSON schema loading."""

from __future__ import annotations

from pathlib import Path

from clearmetric.core.validate import _load_schema

REPO_ROOT = Path(__file__).resolve().parents[4]


def test_repo_root_spec_directory_is_removed() -> None:
    assert not (REPO_ROOT / "spec").exists(), (
        "repo-root spec/ must not exist; schemas live in clearmetric.spec package data"
    )


def test_packaged_project_schema_loads() -> None:
    schema = _load_schema("clearmetric-project.schema.json")
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"


def test_packaged_artifact_schema_loads() -> None:
    schema = _load_schema("catalog-artifact.schema.json")
    assert "properties" in schema
