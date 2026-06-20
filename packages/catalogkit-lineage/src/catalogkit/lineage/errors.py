"""Package-specific errors for catalogkit-lineage."""

from __future__ import annotations


class LineageError(Exception):
    """Base class for catalogkit-lineage failures."""


class LineageInputError(LineageError):
    """Raised when the top-level project input is invalid or unsupported."""


class LineageContractError(LineageError):
    """Raised when supported input cannot satisfy the current public contract."""
