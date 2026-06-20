"""Text renderer for catalogkit-lineage."""

from __future__ import annotations

from ..models import LineageMap, TraversalResult


def render_text(lineage_map: LineageMap) -> str:
    """Render the public catalogkit-lineage artifact for human reading."""
    lines: list[str] = []
    summary = lineage_map.summary
    lines.append("catalogkit-lineage")
    lines.append(f"dialect: {summary.dialect}")
    lines.append(f"input_kind: {summary.input_kind}")
    lines.append(f"dataset_count: {summary.dataset_count}")
    lines.append(f"root_dataset_count: {summary.root_dataset_count}")
    lines.append(f"column_count: {summary.column_count}")
    lines.append("")
    lines.append("nodes:")
    for node in lineage_map.nodes:
        display_name = node.qualified_name or node.name
        lines.append(f"  - [{node.kind}] {display_name}")
    lines.append("")
    lines.append("edges:")
    for edge in lineage_map.edges:
        lines.append(f"  - [{edge.kind}] {edge.source_id} -> {edge.target_id}")
    if lineage_map.warnings:
        lines.append("")
        lines.append("warnings:")
        for warning in lineage_map.warnings:
            location = f" [{warning.location}]" if warning.location else ""
            lines.append(f"  - {warning.code}: {warning.message}{location}")
    return "\n".join(lines)


def render_traversal_text(result: TraversalResult, *, label: str) -> str:
    """Render an upstream or downstream traversal result."""
    lines = [
        "catalogkit-lineage",
        f"{label}: {result.selection}",
        f"selection_id: {result.selection_id}",
        "related_ids:",
    ]
    for item in result.related_ids:
        lines.append(f"  - {item}")
    return "\n".join(lines)
