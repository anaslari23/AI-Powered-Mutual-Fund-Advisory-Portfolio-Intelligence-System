from backend.utils.future_value import calculate_future_value
from backend.utils.sip_calculator import calculate_required_sip
from typing import Dict, Any


def calculate_retirement_goal(
    current_age: int,
    current_monthly_expense: float,
    expected_return_rate: float,
    retirement_age: int = 60,
    existing_corpus: float = 0.0,
) -> Dict[str, Any]:
    """
    Calculate Retirement Corpus and Required SIP.
    Assumes Indian Inflation (2026 Outlook) = 6.5%.
    Factors in existing investment corpus and target retirement age.
    """
    years_to_goal = retirement_age - current_age

    if years_to_goal <= 0:
        return {
            "goal_name": "Retirement",
            "years_to_goal": 0,
            "future_corpus": 0.0,
            "required_sip": 0.0,
        }

    inflation_rate = 0.065
    # Monthly expense at age 60
    future_monthly_expense = calculate_future_value(
        current_monthly_expense, inflation_rate, years_to_goal
    )

    # Corpus rule of thumb: 25 * Annual Expense at retirement
    total_future_corpus = future_monthly_expense * 12 * 25

    # Growth of existing corpus until retirement
    fv_existing_corpus = existing_corpus * ((1 + expected_return_rate) ** years_to_goal)

    # Calculate shortfall
    shortfall = max(0.0, total_future_corpus - fv_existing_corpus)

    required_sip = calculate_required_sip(
        shortfall, expected_return_rate, years_to_goal
    )

    return {
        "goal_name": "Retirement",
        "years_to_goal": years_to_goal,
        "total_future_corpus": round(total_future_corpus, 2),
        "fv_existing_corpus": round(fv_existing_corpus, 2),
        "shortfall_corpus": round(shortfall, 2),
        "future_corpus": round(total_future_corpus, 2),  # Legacy key mapping
        "required_sip": round(required_sip, 2),
    }


def calculate_child_education_goal(
    present_cost: float, years_to_goal: int, expected_return_rate: float
) -> Dict[str, Any]:
    """
    Calculate Child Education Corpus and Required SIP.
    Assumes Indian Education Inflation (2026 Outlook) = 9%.
    """
    if years_to_goal <= 0:
        return {
            "goal_name": "Child Education",
            "years_to_goal": 0,
            "future_corpus": float(present_cost),
            "required_sip": 0.0,
        }

    inflation_rate = 0.09
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
