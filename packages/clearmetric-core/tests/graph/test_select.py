"""Graph select tests."""

from __future__ import annotations

from clearmetric.core.models import CatalogArtifact, Edge, Node, Warning
from clearmetric.graph import select, select_kinds, view_of


def test_select_kinds_filters_nodes_and_edges():
    artifact = CatalogArtifact(
        nodes=[
            Node(id="column:a.x", kind="column", name="x"),
            Node(id="column:b.y", kind="column", name="y"),
            Node(id="model:m", kind="model", name="m"),
        ],
        edges=[
            Edge(kind="derives_from", source_id="column:a.x", target_id="column:b.y"),
            Edge(kind="depends_on", source_id="model:m", target_id="column:a.x"),
        ],
    )
    view = view_of(artifact)
    sliced = select_kinds(view, frozenset({"column"}))
    assert {node.id for node in sliced.nodes} == {"column:a.x", "column:b.y"}
    assert len(sliced.edges) == 1
    assert sliced.edges[0].kind == "derives_from"


def test_select_id_prefix():
    artifact = CatalogArtifact(
        nodes=[
            Node(id="column:orders.amount", kind="column", name="amount"),
            Node(id="column:customers.id", kind="column", name="id"),
        ]
    )
    view = view_of(artifact)
    sliced = select(view, "id:column:orders")
    assert [node.id for node in sliced.nodes] == ["column:orders.amount"]


def test_select_empty_returns_valid_artifact():
    artifact = CatalogArtifact(
        nodes=[Node(id="column:a", kind="column", name="a")],
        warnings=[Warning(code="test", message="graph-level", subject_id=None)],
    )
    view = view_of(artifact)
    sliced = select(view, "id:missing")
    assert sliced.nodes == []
    assert sliced.edges == []
    assert len(sliced.warnings) == 1


def test_select_filters_warnings_to_visible_subjects():
    artifact = CatalogArtifact(
        nodes=[
            Node(id="column:visible", kind="column", name="visible"),
            Node(id="column:hidden", kind="column", name="hidden"),
        ],
        warnings=[
            Warning(code="visible", message="ok", subject_id="column:visible"),
            Warning(code="hidden", message="drop", subject_id="column:hidden"),
            Warning(code="global", message="keep", subject_id=None),
        ],
    )
    view = view_of(artifact)
    sliced = select(view, "id:column:visible")
    codes = {warning.code for warning in sliced.warnings}
    assert codes == {"visible", "global"}
    assert "hidden" not in codes


def test_select_kinds_clear_warnings():
    artifact = CatalogArtifact(
        nodes=[Node(id="column:a", kind="column", name="a")],
        warnings=[Warning(code="x", message="y", subject_id="column:a")],
    )
    view = view_of(artifact)
    sliced = select_kinds(view, frozenset({"column"}), clear_warnings=True)
    assert sliced.warnings == []
