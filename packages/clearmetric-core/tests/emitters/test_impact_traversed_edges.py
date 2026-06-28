"""Impact JSON traversed-edge precision tests."""

from __future__ import annotations

import json
from pathlib import Path

from clearmetric.core.validate import validate_impact_output_dict

from tests.wedge.helpers import run_cm_subprocess


def test_impact_json_traversed_edges_match_traversal_only():
    repo_root = Path(__file__).resolve().parents[4]
    project_dir = repo_root / "examples" / "lineage-demo"
    result = run_cm_subprocess(
        project_dir,
        "impact",
        "orders_base.amount",
        "--downstream",
        "--format",
        "json",
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    validate_impact_output_dict(payload)

    traversed = payload["traversed_edges"]
    assert isinstance(traversed, list)
    assert traversed, "expected downstream traversal edges for orders_base.amount"
    for edge in traversed:
        assert edge["kind"] == "derives_from"
        assert edge["source_id"].startswith("column:")
        assert edge["target_id"].startswith("column:")

    related = set(payload["related_ids"])
    for edge in traversed:
        assert edge["source_id"] in related or edge["target_id"] in related
