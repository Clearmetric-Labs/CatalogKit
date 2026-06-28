"""AI context pack serializer."""

from __future__ import annotations

from clearmetric.core.models import CatalogArtifact
from clearmetric.policy.models import strip_sensitive_aspects


def serialize_ai_context(artifact: CatalogArtifact) -> dict:
    nodes = []
    for node in artifact.nodes:
        aspects = strip_sensitive_aspects(node.aspects or {})
        aspects.pop("_policy_masked", None)
        entry: dict = {
            "id": node.id,
            "kind": node.kind,
            "name": node.name,
        }
        if aspects:
            entry["aspects"] = aspects
        nodes.append(entry)
    return {"version": "1", "nodes": nodes}


__all__ = ["serialize_ai_context"]
