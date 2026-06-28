"""JSON artifact serializer."""

from __future__ import annotations

from clearmetric.core import render_json
from clearmetric.core.models import CatalogArtifact


def serialize_artifact(artifact: CatalogArtifact) -> dict:
    return render_json(artifact)


__all__ = ["serialize_artifact"]
