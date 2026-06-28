"""Output emitters."""

from .impact import emit_impact
from .registry import emit_compile

__all__ = ["emit_compile", "emit_impact"]
