from typing import Dict, Any


def calculate_risk_score(
    age: int,
    dependents: int,
    behavior: str,
    monthly_income: float,
    monthly_savings: float,
) -> Dict[str, Any]:
    """
    Compute an explainable risk score (0-10) and categorize it.
    """
    # 1. Age Factor (30%)
    if age < 35:
        age_factor = 8
    elif 35 <= age <= 45:
        age_factor = 7
    elif 45 < age <= 55:
        age_factor = 5
    else:
        age_factor = 3

    # 2. Dependents Factor (20%)
    if dependents == 0:
        dep_factor = 8
    elif dependents == 1:
        dep_factor = 6
    else:
        dep_factor = 4

    # 3. Behavioral Factor (30%)
    behavior_lower = behavior.lower()
    if "stability" in behavior_lower or "low" in behavior_lower:
        beh_factor = 5
    elif "moderate" in behavior_lower:
        beh_factor = 7
    elif "high" in behavior_lower or "aggressive" in behavior_lower:
        beh_factor = 9
    else:
        beh_factor = 7

    # 4. Income Stability Factor (20%)
    # Inferred from Savings Ratio
    savings_ratio = monthly_savings / monthly_income if monthly_income > 0 else 0
    if savings_ratio >= 0.3:
        inc_factor = 9
    elif savings_ratio >= 0.1:
        inc_factor = 7
    else:
        inc_factor = 5

    score = (
        (age_factor * 0.30)
        + (dep_factor * 0.20)
        + (inc_factor * 0.20)
        + (beh_factor * 0.30)
    )

    if score < 5:
        category = "Conservative"
    elif 5 <= score <= 7:
        category = "Moderate"
    else:
        category = "Aggressive"

    return {
        "score": round(score, 2),
        "category": category,
        "explanation": {
            "age_contribution": round(age_factor * 0.30, 2),
            "dependents_contribution": round(dep_factor * 0.20, 2),
            "income_stability_contribution": round(inc_factor * 0.20, 2),
            "behavioral_contribution": round(beh_factor * 0.30, 2),
            "total_score": round(score, 2),
        },
    }
