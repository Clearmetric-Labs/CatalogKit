"""Emitter registry tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from clearmetric.compiler.compile import compile as compile_project
from clearmetric.core.errors import PolicyError
from clearmetric.emitters.registry import emit_compile

from tests.backbone_lab.helpers import setup_backbone_lab_project
from tests.wedge.helpers import setup_wedge_project


def test_compile_returns_merged_graph(tmp_path: Path):
    compiled = compile_project(setup_wedge_project(tmp_path))
    assert compiled.sources_run == ["warehouse", "dbt"]
    assert any(node for node in compiled.artifact.nodes if node.bindings)


def test_emit_compile_json_raw_admin(tmp_path: Path):
    compiled = compile_project(setup_wedge_project(tmp_path))
    payload = json.loads(emit_compile("json", compiled))
    assert payload["version"] == "1"
    assert payload["nodes"]
    assert "payload" not in payload
    assert "envelope" not in payload


def test_emit_compile_catalog_raw_admin(tmp_path: Path):
    compiled = compile_project(setup_wedge_project(tmp_path))
    payload = json.loads(emit_compile("catalog", compiled))
    kinds = {node["kind"] for node in payload["nodes"]}
    assert kinds.issubset({"table", "column", "model"})
    assert "payload" not in payload


def test_emit_compile_gated_formats_require_identity(tmp_path: Path):
    compiled = compile_project(setup_backbone_lab_project(tmp_path / "lab"))
    with pytest.raises(PolicyError):
        emit_compile("consumer-catalog", compiled, identity=None)
    with pytest.raises(PolicyError):
        emit_compile("frontend-contract", compiled, identity=None)
    with pytest.raises(PolicyError):
        emit_compile("ai-context", compiled, identity=None)


def test_emit_compile_consumer_formats_use_envelope(tmp_path: Path):
    compiled = compile_project(setup_backbone_lab_project(tmp_path / "lab"))
    consumer = json.loads(
        emit_compile("consumer-catalog", compiled, identity="analyst")
    )
    assert consumer["format"] == "consumer-catalog"
    assert consumer["identity"] == "analyst"
    assert "payload" in consumer
    assert any(
        node["id"] == "query:executive_revenue" for node in consumer["payload"]["nodes"]
    )

    contracts = json.loads(
        emit_compile("frontend-contract", compiled, identity="analyst")
    )
    assert contracts["format"] == "frontend-contract"
    assert contracts["payload"]["queries"][0]["id"] == "query:executive_revenue"
    assert "SELECT" in contracts["payload"]["queries"][0]["sql"]

    ai_context = json.loads(emit_compile("ai-context", compiled, identity="analyst"))
    assert ai_context["format"] == "ai-context"
    assert any(
        node["id"] == "metric:executive_revenue"
        for node in ai_context["payload"]["nodes"]
    )
