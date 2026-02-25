import pytest
from backend.engines.allocation_engine import get_asset_allocation


def test_allocation_sum_validation():
    """Ensure all generated allocations strictly sum to 100%."""
    # Conservative
    res1 = get_asset_allocation(4.0)
    assert sum(res1["allocation"].values()) == 100

    # Moderate
    res2 = get_asset_allocation(6.0)
    assert sum(res2["allocation"].values()) == 100

    # Aggressive
    res3 = get_asset_allocation(8.5)
    assert sum(res3["allocation"].values()) == 100
