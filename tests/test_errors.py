from __future__ import annotations

import pytest

from sql_map import build_query_map
from sql_map.errors import SqlMapContractError, SqlMapParseError


def test_invalid_sql_fails_loudly():
    with pytest.raises(SqlMapParseError):
        build_query_map("NOT VALID SQL AT ALL !!!", dialect="postgres")


def test_multiple_statements_fail_loudly():
    sql = "SELECT * FROM customers; SELECT * FROM orders;"

    with pytest.raises(SqlMapContractError):
        build_query_map(sql, dialect="postgres")
