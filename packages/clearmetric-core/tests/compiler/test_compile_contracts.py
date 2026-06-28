"""Atomic compile_query_contracts tests."""

from __future__ import annotations

import copy

import pytest
from clearmetric.compiler.compile_contracts import compile_query_contracts
from clearmetric.core.errors import CompilerError
from clearmetric.core.models import CatalogArtifact, Node


def _artifact(*nodes: Node) -> CatalogArtifact:
    return CatalogArtifact(nodes=list(nodes))


def _query_node(
    node_id: str,
    *,
    sql: str = "SELECT 1",
    aspects: dict | None = None,
) -> Node:
    if aspects is None:
        aspects = {"query": {"sql": sql, "depends_on": []}}
    return Node(id=node_id, kind="query", name=node_id, aspects=aspects)


def test_compile_query_contracts_attaches_compiled_sql():
    artifact = _artifact(_query_node("query:ok", sql="SELECT amount FROM orders"))
    result = compile_query_contracts(artifact, dialect="postgres")
    query_aspect = (result.nodes[0].aspects or {})["query"]
    assert "compiled_sql" in query_aspect
    assert "SELECT" in query_aspect["compiled_sql"]


def test_compile_query_contracts_lists_all_sql_errors():
    artifact = _artifact(
        _query_node("query:bad1", sql="SELECT FROM"),
        _query_node("query:bad2", sql="SELECT FROM"),
    )
    with pytest.raises(CompilerError) as exc:
        compile_query_contracts(artifact, dialect="postgres")
    message = str(exc.value)
    assert "query:bad1" in message
    assert "query:bad2" in message


def test_compile_query_contracts_batches_invalid_aspect_and_sql_errors():
    artifact = _artifact(
        Node(
            id="query:bad_aspect",
            kind="query",
            name="bad_aspect",
            aspects={"query": {"sql": 123, "depends_on": []}},
        ),
        _query_node("query:bad_sql", sql="SELECT FROM"),
    )
    with pytest.raises(CompilerError) as exc:
        compile_query_contracts(artifact, dialect="postgres")
    message = str(exc.value)
    assert "query:bad_aspect" in message
    assert "invalid aspects.query" in message
    assert "query:bad_sql" in message


def test_compile_query_contracts_missing_aspect_fails_pass1():
    artifact = _artifact(
        Node(id="query:missing", kind="query", name="missing", aspects={})
    )
    with pytest.raises(CompilerError, match="missing aspects.query"):
        compile_query_contracts(artifact, dialect="postgres")


def test_compile_query_contracts_does_not_mutate_input_on_failure():
    artifact = _artifact(
        _query_node("query:bad", sql="SELECT FROM"),
    )
    before = copy.deepcopy(artifact.model_dump(mode="json"))
    with pytest.raises(CompilerError):
        compile_query_contracts(artifact, dialect="postgres")
    after = artifact.model_dump(mode="json")
    assert before == after


def test_compile_query_contracts_does_not_mutate_input_on_success():
    artifact = _artifact(_query_node("query:ok", sql="SELECT amount FROM orders"))
    before = copy.deepcopy(artifact.model_dump(mode="json"))
    result = compile_query_contracts(artifact, dialect="postgres")
    after = artifact.model_dump(mode="json")
    assert before == after
    assert result is not artifact
    query_aspect = (result.nodes[0].aspects or {})["query"]
    assert query_aspect["compiled_sql"]
