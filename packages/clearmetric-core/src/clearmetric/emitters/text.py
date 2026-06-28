"""Text summary serializer."""

from __future__ import annotations

from clearmetric.compiler.models import CompiledGraph
from clearmetric.core.models import CatalogArtifact


def serialize_text(artifact: CatalogArtifact, compiled: CompiledGraph) -> str:
    lines = [
        "clearmetric-core",
        f"dialect: {compiled.project.dialect}",
        f"sources: {', '.join(compiled.sources_run)}",
        f"nodes: {len(artifact.nodes)}",
        f"edges: {len(artifact.edges)}",
        f"warnings: {len(artifact.warnings)}",
    ]
    if artifact.warnings:
        lines.append("")
        lines.append("warnings:")
        for warning in artifact.warnings:
            location = f" [{warning.location}]" if warning.location else ""
            lines.append(f"  - {warning.code}: {warning.message}{location}")
    return "\n".join(lines)


__all__ = ["serialize_text"]
