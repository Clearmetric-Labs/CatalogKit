"""Experimental lab feature gates shared by CLI and adapters."""

from __future__ import annotations

import os

from .errors import AdapterError, ClearMetricError

LAB_SOURCE_KINDS = frozenset({"intent"})


def is_experimental_enabled() -> bool:
    return os.environ.get("CM_EXPERIMENTAL", "").strip() == "1"


def require_experimental(feature: str) -> None:
    if not is_experimental_enabled():
        raise ClearMetricError(
            f"{feature} requires CM_EXPERIMENTAL=1 (experimental backbone lab; not a shipped capability)"
        )


def require_experimental_source(kind: str) -> None:
    if kind in LAB_SOURCE_KINDS and not is_experimental_enabled():
        raise AdapterError(f"sources.{kind} requires CM_EXPERIMENTAL=1")
