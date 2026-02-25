import pytest
from backend.engines.goal_engine import (
    calculate_retirement_goal,
    calculate_child_education_goal,
)


def test_retirement_goal():
    """Test retirement planning baseline values."""
    res = calculate_retirement_goal(30, 50000, 0.12)
    assert res["years_to_goal"] == 30
    assert res["future_corpus"] > 0
    assert res["required_sip"] > 0


def test_child_education_goal():
    """Test child education goal calculation."""
    res = calculate_child_education_goal(2000000, 12, 0.12)
    assert res["years_to_goal"] == 12
    assert res["future_corpus"] > 2000000
