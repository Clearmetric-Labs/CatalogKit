"""filter_warnings_for_ids tests."""

from __future__ import annotations

from clearmetric.core.models import Warning, filter_warnings_for_ids


def test_clear_warnings_returns_empty():
    warnings = [Warning(code="x", message="y", subject_id="column:a")]
    assert filter_warnings_for_ids(warnings, {"column:a"}, clear_warnings=True) == []


def test_keeps_subject_in_allowed_ids():
    warnings = [Warning(code="visible", message="ok", subject_id="column:a")]
    result = filter_warnings_for_ids(warnings, {"column:a"})
    assert len(result) == 1
    assert result[0].code == "visible"


def test_drops_subject_outside_allowed_ids():
    warnings = [
        Warning(code="hidden", message="drop", subject_id="column:b"),
        Warning(code="visible", message="keep", subject_id="column:a"),
    ]
    result = filter_warnings_for_ids(warnings, {"column:a"})
    assert [warning.code for warning in result] == ["visible"]


def test_keeps_graph_level_warnings():
    warnings = [
        Warning(code="global", message="keep", subject_id=None),
        Warning(code="hidden", message="drop", subject_id="column:b"),
    ]
    result = filter_warnings_for_ids(warnings, {"column:a"})
    assert [warning.code for warning in result] == ["global"]
