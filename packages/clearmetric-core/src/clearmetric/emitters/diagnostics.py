"""Compile diagnostics for stderr output."""

from __future__ import annotations

from clearmetric.core.models import CatalogArtifact
from clearmetric.graph import edge_kind_counts


def format_compile_diagnostics(artifact: CatalogArtifact) -> str | None:
    """Return LINEAGE WARNING block when column lineage is empty."""
    edge_counts = edge_kind_counts(artifact)
    derives_from_count = edge_counts.get("derives_from", 0)
    if derives_from_count > 0:
        return None
    depends_on = edge_counts.get("depends_on", 0)
    lines = [
        "LINEAGE WARNING:",
        "0 derives_from edges were produced.",
        "",
        "The graph compiled, but column-level impact will be incomplete.",
        "Common causes:",
        "- dbt artifacts do not contain usable compiled SQL (run dbt compile)",
        "- SELECT * references sources with unknown schemas",
        "- warehouse metadata did not bind to dbt/source tables",
        "- SQL pattern is unsupported",
        "",
        f"Graph summary: {len(artifact.nodes)} nodes, {len(artifact.edges)} edges, "
        f"{depends_on} depends_on edges.",
        "Run cm clean for details.",
    ]
    return "\n".join(lines)
