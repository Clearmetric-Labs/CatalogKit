"""JSON renderer for catalogkit-lineage."""

from __future__ import annotations

from ..models import LineageMap


def render_json(lineage_map: LineageMap) -> dict:
    """Return the canonical JSON-serializable catalogkit-lineage artifact."""
    return lineage_map.model_dump(mode="json", by_alias=True)
