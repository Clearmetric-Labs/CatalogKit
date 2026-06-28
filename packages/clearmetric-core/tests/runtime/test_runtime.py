"""Runtime project query tests."""

from __future__ import annotations

import importlib
from pathlib import Path
from unittest.mock import patch

import pytest
from clearmetric.compiler.compile import compile as compile_project
from clearmetric.core.errors import (
    CompilerError,
    PolicyDeniedError,
    PolicyError,
    QueryExecutionError,
)
from clearmetric.runtime import execute_project_query
from tests.backbone_lab.helpers import setup_backbone_lab_project


def test_execute_project_query_returns_rows(tmp_path: Path):
    project_dir = setup_backbone_lab_project(tmp_path / "lab")
    compiled = compile_project(project_dir)
    rows = execute_project_query(
        compiled.artifact,
        identity="analyst",
        rules_path=compiled.project.policy.rules,
        query_selection="query:executive_revenue",
        project_dir=project_dir,
    )
    assert rows[0]["net_revenue"] == 100


def test_execute_project_query_missing_seed_raises(tmp_path: Path):
    project_dir = setup_backbone_lab_project(tmp_path / "lab")
    compiled = compile_project(project_dir)
    seed_path = project_dir / "fixtures" / "seed.sql"
    seed_path.unlink()
    with pytest.raises(QueryExecutionError, match="fixture seed not found"):
        execute_project_query(
            compiled.artifact,
            identity="analyst",
            rules_path=compiled.project.policy.rules,
            query_selection="query:executive_revenue",
            project_dir=project_dir,
        )


def test_execute_project_query_denied_identity_raises(tmp_path: Path):
    project_dir = setup_backbone_lab_project(tmp_path / "lab")
    compiled = compile_project(project_dir)
    with pytest.raises(PolicyDeniedError):
        execute_project_query(
            compiled.artifact,
            identity="viewer",
            rules_path=compiled.project.policy.rules,
            query_selection="query:executive_revenue",
            project_dir=project_dir,
        )


def test_execute_project_query_blank_identity_raises(tmp_path: Path):
    project_dir = setup_backbone_lab_project(tmp_path / "lab")
    compiled = compile_project(project_dir)
    for bad_identity in (None, ""):
        with pytest.raises(PolicyError, match="requires identity"):
            execute_project_query(
                compiled.artifact,
                identity=bad_identity,  # type: ignore[arg-type]
                rules_path=compiled.project.policy.rules,
                query_selection="query:executive_revenue",
                project_dir=project_dir,
            )


def test_execute_project_query_missing_compiled_sql_raises(tmp_path: Path):
    project_dir = setup_backbone_lab_project(tmp_path / "lab")
    compiled = compile_project(project_dir)
    node = next(
        item for item in compiled.artifact.nodes if item.id == "query:executive_revenue"
    )
    aspects = dict(node.aspects or {})
    query_aspect = dict(aspects["query"])
    query_aspect.pop("compiled_sql", None)
    aspects["query"] = query_aspect
    broken = node.model_copy(update={"aspects": aspects})
    artifact = compiled.artifact.model_copy(
        update={
            "nodes": [
                broken if item.id == node.id else item
                for item in compiled.artifact.nodes
            ]
        }
    )
    with pytest.raises(CompilerError, match="compiled_sql"):
        execute_project_query(
            artifact,
            identity="analyst",
            rules_path=compiled.project.policy.rules,
            query_selection="query:executive_revenue",
            project_dir=project_dir,
        )


def test_importing_runtime_without_duckdb_installed():
    import clearmetric.runtime

    importlib.reload(clearmetric.runtime)
    real_import = __import__

    def fake_import(name, *args, **kwargs):
        if name == "duckdb":
            raise ImportError("no duckdb")
        return real_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=fake_import):
        with pytest.raises(QueryExecutionError, match="duckdb is required"):
            clearmetric.runtime.execute_query("SELECT 1")


def test_importing_runtime_module_succeeds_without_duckdb():
    import clearmetric.runtime

    importlib.reload(clearmetric.runtime)
    assert hasattr(clearmetric.runtime, "execute_project_query")
