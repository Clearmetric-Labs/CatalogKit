"""Package-specific errors for sql-map."""

from __future__ import annotations


class SqlMapError(Exception):
    """Base class for sql-map failures."""


class SqlMapParseError(SqlMapError):
    """Raised when SQL cannot be parsed into a supported AST."""


class SqlMapContractError(SqlMapError):
    """Raised when parsed SQL cannot be represented by the current contract."""
