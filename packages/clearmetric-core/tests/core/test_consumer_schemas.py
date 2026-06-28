"""Schema validation for consumer bundle contracts."""

from __future__ import annotations

import json

import pytest
from clearmetric.core.errors import ValidationError
from clearmetric.core.validate import (
    validate_bundle_manifest_dict,
    validate_consumer_envelope_dict,
    validate_impact_output_dict,
)

_VALID_MANIFEST = {
    "schema_version": "1",
    "scenario_id": "minimal",
    "label": "Test",
    "artifacts": {
        "graph": {
            "path": "graph.json",
            "kind": "catalog-artifact",
            "lane": "admin",
        },
        "catalog": {
            "path": "catalog.json",
            "kind": "catalog-artifact",
            "lane": "admin",
        },
        "impacts": {
            "orders.amount_upstream": {
                "path": "impacts/orders.amount_upstream.json",
                "selection": "orders.amount",
                "direction": "upstream",
            }
        },
    },
    "defaults": {"impact_key": "orders.amount_upstream"},
}

_VALID_IMPACT = {
    "selection": "orders.amount",
    "selection_id": "column:orders.amount",
    "related_ids": ["column:orders.amount", "column:raw.orders.amount"],
    "warnings": [],
    "derivation": [
        {
            "id": "column:orders.amount",
            "status": "complete",
            "confidence": "high",
        }
    ],
}

_VALID_ENVELOPE = {
    "format": "consumer-catalog",
    "version": "1",
    "identity": "analyst",
    "node_count": 1,
    "edge_count": 0,
    "payload": {"version": "1", "nodes": [], "edges": [], "warnings": []},
}


def test_valid_bundle_manifest():
    validate_bundle_manifest_dict(_VALID_MANIFEST)


def test_valid_impact_output():
    validate_impact_output_dict(_VALID_IMPACT)


def test_valid_consumer_envelope():
    validate_consumer_envelope_dict(_VALID_ENVELOPE)


def test_bundle_manifest_missing_required_field():
    payload = dict(_VALID_MANIFEST)
    del payload["scenario_id"]
    with pytest.raises(ValidationError, match="consumer-bundle.schema.json"):
        validate_bundle_manifest_dict(payload)


def test_impact_output_missing_derivation():
    payload = dict(_VALID_IMPACT)
    del payload["derivation"]
    with pytest.raises(ValidationError, match="impact-output.schema.json"):
        validate_impact_output_dict(payload)


def test_consumer_envelope_missing_identity():
    payload = dict(_VALID_ENVELOPE)
    del payload["identity"]
    with pytest.raises(ValidationError, match="consumer-envelope.schema.json"):
        validate_consumer_envelope_dict(payload)


def test_malformed_json_object_rejected_by_load_helpers(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not json", encoding="utf-8")
    from clearmetric.core.validate import load_bundle_manifest_file

    with pytest.raises(ValidationError, match="not valid JSON"):
        load_bundle_manifest_file(bad)


def test_non_object_json_rejected(tmp_path):
    bad = tmp_path / "array.json"
    bad.write_text(json.dumps([1, 2]), encoding="utf-8")
    from clearmetric.core.validate import load_impact_output_file

    with pytest.raises(ValidationError, match="JSON object"):
        load_impact_output_file(bad)
