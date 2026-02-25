from backend.utils.future_value import calculate_future_value
from backend.utils.sip_calculator import calculate_required_sip
from typing import Dict, Any


def calculate_retirement_goal(
    current_age: int, current_monthly_expense: float, expected_return_rate: float
) -> Dict[str, Any]:
    """
    Calculate Retirement Corpus and Required SIP.
    Assumes retirement age = 60, Inflation = 6%.
    Assumes corpus is 25x the first year's annual expense at retirement.
    """
    retirement_age = 60
    years_to_goal = retirement_age - current_age

    if years_to_goal <= 0:
        return {
            "goal_name": "Retirement",
            "years_to_goal": 0,
            "future_corpus": 0.0,
            "required_sip": 0.0,
        }

    inflation_rate = 0.06
    # Monthly expense at age 60
    future_monthly_expense = calculate_future_value(
        current_monthly_expense, inflation_rate, years_to_goal
    )

    # Corpus rule of thumb: 25 * Annual Expense at retirement
    future_corpus = future_monthly_expense * 12 * 25

    required_sip = calculate_required_sip(
        future_corpus, expected_return_rate, years_to_goal
    )

    return {
        "goal_name": "Retirement",
        "years_to_goal": years_to_goal,
        "future_corpus": round(future_corpus, 2),
        "required_sip": round(required_sip, 2),
    }


def calculate_child_education_goal(
    present_cost: float, years_to_goal: int, expected_return_rate: float
) -> Dict[str, Any]:
    """
    Calculate Child Education Corpus and Required SIP.
    Assumes Inflation = 8%.
    """
    if years_to_goal <= 0:
        return {
            "goal_name": "Child Education",
            "years_to_goal": 0,
            "future_corpus": 0.0,
            "required_sip": 0.0,
        }

    inflation_rate = 0.08
    future_corpus = calculate_future_value(present_cost, inflation_rate, years_to_goal)

    required_sip = calculate_required_sip(
        future_corpus, expected_return_rate, years_to_goal
    )

    return {
        "goal_name": "Child Education",
        "years_to_goal": years_to_goal,
        "future_corpus": round(future_corpus, 2),
        "required_sip": round(required_sip, 2),
    }
