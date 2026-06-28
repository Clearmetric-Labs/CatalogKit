from __future__ import annotations

import pytest
from clearmetric.core.errors import CanonicalIdError
from clearmetric.core.ids import parse_column_selection


def test_wedge_form():
    assert parse_column_selection("orders.amount") == "column:orders.amount"


def test_column_prefix_form():
    assert parse_column_selection("column:orders.amount") == "column:orders.amount"


def test_logical_alias_form():
    assert parse_column_selection("column.orders.amount") == "column:orders.amount"


def test_dotted_parent():
    assert parse_column_selection("fct.orders.amount") == "column:fct.orders.amount"


@pytest.mark.parametrize(
    "selection",
    ["", "orders", "column:", "column.", "*", "orders.*"],
)
def test_rejects_invalid_selections(selection: str):
    with pytest.raises(CanonicalIdError):
        parse_column_selection(selection)
