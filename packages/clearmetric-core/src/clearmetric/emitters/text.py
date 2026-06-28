"""Text emitter."""

from __future__ import annotations

from clearmetric.compiler.models import CompiledGraph


def emit_text(compiled: CompiledGraph) -> str:
    lines = [
        "clearmetric-core",
        f"dialect: {compiled.project.dialect}",
        f"sources: {', '.join(compiled.sources_run)}",
        f"nodes: {len(compiled.artifact.nodes)}",
        f"edges: {len(compiled.artifact.edges)}",
        f"warnings: {len(compiled.artifact.warnings)}",
    ]
    if compiled.artifact.warnings:
        lines.append("")
        lines.append("warnings:")
        for warning in compiled.artifact.warnings:
            location = f" [{warning.location}]" if warning.location else ""
            lines.append(f"  - {warning.code}: {warning.message}{location}")
    return "\n".join(lines)
