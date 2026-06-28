"""Discover report tests."""

from __future__ import annotations

from clearmetric.compiler.discover import discover

from tests.backbone_lab.helpers import setup_backbone_lab_project


def test_discover_includes_intent_paths(tmp_path):
    project_dir = setup_backbone_lab_project(tmp_path / "lab")
    report = discover(project_dir)
    kinds = {source.kind for source in report.sources}
    assert "intent" in kinds
    assert any(source.kind == "intent" for source in report.sources)
