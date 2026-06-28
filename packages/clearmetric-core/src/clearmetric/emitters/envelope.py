"""Consumer-lane emit envelope."""

from __future__ import annotations

import json
from typing import Any

from clearmetric.core.models import CatalogArtifact


def wrap_envelope(
    format_name: str,
    identity: str,
    artifact: CatalogArtifact,
    payload: dict[str, Any],
) -> str:
    """Wrap consumer JSON output with consistent provenance metadata."""
    body = {
        "format": format_name,
        "version": "1",
        "identity": identity,
        "node_count": len(artifact.nodes),
        "edge_count": len(artifact.edges),
        "payload": payload,
    }
    return json.dumps(body, indent=2, sort_keys=False)


__all__ = ["wrap_envelope"]
