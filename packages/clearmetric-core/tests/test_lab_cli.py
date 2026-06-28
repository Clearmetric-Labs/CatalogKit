"""Lab CLI subprocess tests."""

from __future__ import annotations

from pathlib import Path

from tests.backbone_lab.helpers import setup_backbone_lab_project
from tests.wedge.helpers import run_cm_subprocess


def test_lab_format_requires_experimental_env(tmp_path: Path):
    project_dir = setup_backbone_lab_project(tmp_path / "lab")
    result = run_cm_subprocess(
        project_dir,
        "compile",
        "--format",
        "consumer-catalog",
        "--identity",
        "analyst",
    )
    assert result.returncode != 0
    assert (
        "CM_EXPERIMENTAL=1" in result.stderr
        or "invalid choice" in result.stderr.lower()
    )


def test_consumer_catalog_requires_identity(tmp_path: Path):
    project_dir = setup_backbone_lab_project(tmp_path / "lab")
    result = run_cm_subprocess(
        project_dir,
        "compile",
        "--format",
        "consumer-catalog",
        experimental=True,
    )
    assert result.returncode != 0
    assert "--identity required" in result.stderr


def test_cm_query_without_experimental_is_unknown_command(tmp_path: Path):
    project_dir = setup_backbone_lab_project(tmp_path / "lab")
    result = run_cm_subprocess(
        project_dir,
        "query",
        "--identity",
        "analyst",
        "query:executive_revenue",
    )
    assert result.returncode != 0
    assert (
        "invalid choice" in result.stderr.lower() or "unknown" in result.stderr.lower()
    )
    assert "Traceback" not in result.stderr


def test_cm_query_denied_for_wrong_identity(tmp_path: Path):
    project_dir = setup_backbone_lab_project(tmp_path / "lab")
    result = run_cm_subprocess(
        project_dir,
        "query",
        "--identity",
        "viewer",
        "query:executive_revenue",
        experimental=True,
    )
    assert result.returncode != 0
    assert "denied by policy" in result.stderr.lower()


def test_wedge_catalog_and_openlineage_without_experimental(tmp_path: Path):
    from tests.wedge.helpers import setup_wedge_project

    project_dir = setup_wedge_project(tmp_path / "wedge")
    catalog = run_cm_subprocess(project_dir, "compile", "--format", "catalog")
    assert catalog.returncode == 0, catalog.stderr
    openlineage = run_cm_subprocess(project_dir, "compile", "--format", "openlineage")
    assert openlineage.returncode == 0, openlineage.stderr
