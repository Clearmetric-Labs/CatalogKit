"""Public package surface for sql-map."""

from __future__ import annotations

from ._version import __version__
from .api import build_query_map, render_json, render_text
from .errors import (
    SqlMapContractError,
    SqlMapError,
    SqlMapParseError,
)
from .models import (
    OutputColumn,
    OutputSourceHint,
    QueryMap,
    QuerySummary,
    Relation,
    RelationEdge,
    RelationUsage,
    WarningEntry,
)

__all__ = [
    "__version__",
    "build_query_map",
    "render_json",
    "render_text",
    "OutputColumn",
    "OutputSourceHint",
    "QueryMap",
    "QuerySummary",
    "Relation",
    "RelationEdge",
    "RelationUsage",
    "WarningEntry",
    "SqlMapContractError",
    "SqlMapError",
    "SqlMapParseError",
]
