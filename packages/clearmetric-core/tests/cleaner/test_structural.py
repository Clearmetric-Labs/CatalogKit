from __future__ import annotations

import pytest
from clearmetric.cleaner import enforce_structural_checks, run_structural_checks
from clearmetric.core.errors import StructuralCheckError
from clearmetric.core.models import CatalogArtifact, Edge, Node


def test_dangling_edge_produces_error_finding():
    artifact = CatalogArtifact(
        nodes=[Node(id="column:a.x", kind="column", name="x", qualified_name="a.x")],
        edges=[
            Edge(
                kind="derives_from",
                source_id="column:missing.y",
                target_id="column:a.x",
                label="derives_from",
            )
        ],
    )
    report = run_structural_checks(artifact)
    assert any(
        finding.check_id == "check.edges_resolve" and finding.severity == "error"
        for finding in report.findings
    )


def test_enforce_structural_checks_raises():
    artifact = CatalogArtifact(
        edges=[
            Edge(
                kind="derives_from",
                source_id="column:missing.y",
                target_id="column:a.x",
                label="derives_from",
            )
        ]
    )
    with pytest.raises(StructuralCheckError):
        enforce_structural_checks(artifact)
