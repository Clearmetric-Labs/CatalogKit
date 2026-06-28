from __future__ import annotations

from pathlib import Path

import yaml

from .project_helpers import build_catalog_artifact, build_lineage_map

ADVERSARIAL_ROOT = (
    Path(__file__).resolve().parents[1] / "fixtures" / "lineage" / "adversarial"
)


def test_unparseable_sibling_edge_is_complete():
    case_root = ADVERSARIAL_ROOT / "unparseable_sibling"
    artifact = build_catalog_artifact(case_root, dialect="postgres")
    edge = next(
        edge
        for edge in artifact.edges
        if edge.kind == "derives_from" and edge.source_id == "column:valid.amount"
    )
    assert edge.derivation is not None
    assert edge.derivation.status == "complete"
    assert edge.derivation.confidence == "high"


def test_broken_sql_marks_derivation_failed():
    case_root = ADVERSARIAL_ROOT / "unparseable_sibling"
    lineage_map = build_lineage_map(case_root, dialect="postgres")
    broken_table = next(node for node in lineage_map.nodes if node.id == "table:broken")
    assert broken_table.derivation is not None
    assert broken_table.derivation.status == "failed"
    assert broken_table.derivation.confidence == "low"


def test_select_star_cases_are_partial_not_complete():
    case_root = ADVERSARIAL_ROOT / "select_star_no_schema"
    artifact = build_catalog_artifact(case_root, dialect="postgres")
    assert any(warning.code == "select_star" for warning in artifact.warnings)
    report_table = next(node for node in artifact.nodes if node.id == "table:report")
    assert report_table.derivation is not None
    assert report_table.derivation.status == "partial"
    assert report_table.derivation.confidence == "medium"


def test_enterprise_adversarial_expected_edges_have_derivation():
    expected_path = (
        ADVERSARIAL_ROOT / "enterprise_adversarial_manifest" / "expected.yaml"
    )
    payload = yaml.safe_load(expected_path.read_text(encoding="utf-8"))
    manifest_path = expected_path.parent / "manifest.json"
    artifact = build_catalog_artifact(manifest_path, dialect=payload["dialect"])
    edge_map = {
        (edge.source_id, edge.target_id): edge
        for edge in artifact.edges
        if edge.kind == "derives_from"
    }
    for source_id, target_id in payload["derives_from"]:
        edge = edge_map[(source_id, target_id)]
        assert edge.derivation is not None
        assert edge.derivation.status in {"complete", "partial"}
