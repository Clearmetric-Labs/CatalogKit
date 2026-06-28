"""Runtime serve harness tests."""

from __future__ import annotations

import pytest
from clearmetric.core.errors import ClearMetricError
from clearmetric.runtime.serve import validate_loopback_host


def test_validate_loopback_host_accepts_localhost():
    assert validate_loopback_host("127.0.0.1") == "127.0.0.1"
    assert validate_loopback_host("localhost") == "localhost"


def test_validate_loopback_host_rejects_public_bind():
    with pytest.raises(ClearMetricError, match="non-loopback"):
        validate_loopback_host("0.0.0.0")
    with pytest.raises(ClearMetricError, match="non-loopback"):
        validate_loopback_host("192.168.1.1")
