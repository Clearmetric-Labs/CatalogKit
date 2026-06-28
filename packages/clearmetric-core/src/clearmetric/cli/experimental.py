"""Experimental lab CLI helpers."""

from __future__ import annotations

import os

from clearmetric.core.errors import ClearMetricError, PolicyError
from clearmetric.emitters.registry import (
    COMPILE_FORMATS,
    LAB_COMPILE_FORMATS,
    WEDGE_COMPILE_FORMATS,
)
from clearmetric.policy import require_gated_identity


def is_experimental_enabled() -> bool:
    return os.environ.get("CM_EXPERIMENTAL", "").strip() == "1"


def require_experimental(feature: str) -> None:
    if not is_experimental_enabled():
        raise ClearMetricError(
            f"{feature} requires CM_EXPERIMENTAL=1 (experimental backbone lab; not a shipped capability)"
        )


def _cli_gated_identity(identity: str | None, *, error: str) -> str:
    try:
        return require_gated_identity(identity)
    except PolicyError as exc:
        raise ClearMetricError(error) from exc


def require_gated_compile(format: str, identity: str | None) -> str:
    require_experimental(f"compile --format {format}")
    return _cli_gated_identity(
        identity,
        error=f"--identity required for experimental format {format!r}",
    )


def require_query_identity(identity: str | None) -> str:
    return _cli_gated_identity(identity, error="cm query requires --identity")


def compile_format_choices() -> tuple[str, ...]:
    if is_experimental_enabled():
        return WEDGE_COMPILE_FORMATS + LAB_COMPILE_FORMATS
    return WEDGE_COMPILE_FORMATS


def is_lab_compile_format(format: str) -> bool:
    spec = COMPILE_FORMATS.get(format)
    return spec is not None and spec.lane == "consumer"


__all__ = [
    "compile_format_choices",
    "is_experimental_enabled",
    "is_lab_compile_format",
    "require_experimental",
    "require_gated_compile",
    "require_query_identity",
]
