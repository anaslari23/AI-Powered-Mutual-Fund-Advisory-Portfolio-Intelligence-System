import pytest
from backend.utils.sip_calculator import (
    calculate_sip_future_value,
    calculate_required_sip,
)


def test_calculate_sip_future_value():
    """Test standard SIP formula correctness."""
    fv = calculate_sip_future_value(10000, 0.12, 10)
    assert round(fv, 2) > 1200000  # Basic sanity check


def test_calculate_required_sip():
    """Test standard reverse SIP calculation mapping directly back."""
    fv = calculate_sip_future_value(10000, 0.12, 10)
    required_sip = calculate_required_sip(fv, 0.12, 10)
    assert round(required_sip, 0) == 10000
