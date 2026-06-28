"""Experimental lab CLI helpers."""

from __future__ import annotations

import os

from clearmetric.core.errors import ClearMetricError
from clearmetric.emitters.registry import (
    GATED_COMPILE_FORMATS,
    LAB_COMPILE_FORMATS,
    WEDGE_COMPILE_FORMATS,
)


def is_experimental_enabled() -> bool:
    return os.environ.get("CM_EXPERIMENTAL", "").strip() == "1"


def require_experimental(feature: str) -> None:
    if not is_experimental_enabled():
        raise ClearMetricError(
            f"{feature} requires CM_EXPERIMENTAL=1 (experimental backbone lab; not a shipped capability)"
        )


def compile_format_choices() -> tuple[str, ...]:
    if is_experimental_enabled():
        return WEDGE_COMPILE_FORMATS + LAB_COMPILE_FORMATS
    return WEDGE_COMPILE_FORMATS


def is_lab_compile_format(format: str) -> bool:
    return format in GATED_COMPILE_FORMATS


__all__ = [
    "GATED_COMPILE_FORMATS",
    "LAB_COMPILE_FORMATS",
    "WEDGE_COMPILE_FORMATS",
    "compile_format_choices",
    "is_experimental_enabled",
    "is_lab_compile_format",
    "require_experimental",
]
