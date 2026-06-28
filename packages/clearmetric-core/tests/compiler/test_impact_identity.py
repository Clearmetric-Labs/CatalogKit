"""Impact identity gating tests."""

from __future__ import annotations

import pytest
from clearmetric.compiler.impact import impact
from clearmetric.core.errors import PolicyDeniedError

from tests.backbone_lab.helpers import setup_backbone_lab_project
from tests.wedge.helpers import run_cm_subprocess


def test_impact_identity_denies_viewer_on_selection(tmp_path):
    project_dir = setup_backbone_lab_project(tmp_path / "lab")
    with pytest.raises(PolicyDeniedError, match="denied by policy"):
        impact(
            project_dir,
            selection="orders.amount",
            direction="upstream",
            identity="viewer",
        )


def test_impact_identity_analyst_filters_related_ids_to_allow_only(tmp_path):
    project_dir = setup_backbone_lab_project(tmp_path / "lab")
    _compiled, result = impact(
        project_dir,
        selection="orders.amount",
        direction="upstream",
        identity="analyst",
    )
    assert result.selection_id == "column:orders.amount"
    assert isinstance(result.related_ids, list)


def test_impact_identity_cli_denies_viewer(tmp_path):
    project_dir = setup_backbone_lab_project(tmp_path / "lab")
    result = run_cm_subprocess(
        project_dir,
        "impact",
        "orders.amount",
        "--upstream",
        "--format",
        "json",
        "--identity",
        "viewer",
        experimental=True,
    )
    assert result.returncode != 0
    assert "denied by policy" in result.stderr.lower()
    assert "Traceback" not in result.stderr
