from typing import List, Dict, Any
import numpy as np

CATEGORY_WEIGHTS = {
    "Large Cap": 0.30,
    "Mid Cap": 0.20,
    "Small Cap": 0.15,
    "Multi Cap": 0.20,
    "ELSS": 0.10,
    "Debt": 0.25,
    "Liquid": 0.10,
    "Gold": 0.10,
    "Index": 0.15,
    "Sectoral": 0.10,
    "International": 0.10,
}

CATEGORY_PENALTY_THRESHOLDS = {
    "Large Cap": {"min": 15, "max": 45},
    "Mid Cap": {"min": 10, "max": 35},
    "Small Cap": {"min": 5, "max": 25},
    "Multi Cap": {"min": 10, "max": 40},
    "ELSS": {"min": 0, "max": 20},
    "Debt": {"min": 10, "max": 50},
    "Liquid": {"min": 0, "max": 20},
    "Gold": {"min": 0, "max": 15},
    "Index": {"min": 0, "max": 30},
    "Sectoral": {"min": 0, "max": 20},
    "International": {"min": 0, "max": 15},
}

RISK_BASED_CAPS = {
    1: {"Small Cap": 10, "Sectoral": 5, "Mid Cap": 15},
    2: {"Small Cap": 15, "Sectoral": 10, "Mid Cap": 20},
    3: {"Small Cap": 25, "Sectoral": 15, "Mid Cap": 25},
    4: {"Small Cap": 30, "Sectoral": 20, "Mid Cap": 30},
    5: {"Small Cap": 35, "Sectoral": 25, "Mid Cap": 35},
}


def calculate_diversification_score(allocation: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not allocation:
        return {
            "diversification_score": 0.0,
            "category": "No Allocation",
            "violations": ["Empty allocation"],
            "penalty": 0.0,
            "weights": {},
        }

    cat_weights = {}
    for item in allocation:
        cat = item.get("category", "Other")
        cat_weights[cat] = cat_weights.get(cat, 0) + item.get("weight", 0)

    total_weight = sum(cat_weights.values())
    if total_weight == 0:
        return {
            "diversification_score": 0.0,
            "category": "No Allocation",
            "violations": ["Total weight is zero"],
            "penalty": 0.0,
            "weights": cat_weights,
        }

    violations = []
    penalty = 0.0

    for cat, weight in cat_weights.items():
        if cat in CATEGORY_PENALTY_THRESHOLDS:
            thresh = CATEGORY_PENALTY_THRESHOLDS[cat]
            if weight < thresh["min"]:
                deficit = thresh["min"] - weight
                penalty += deficit * 0.5
                violations.append(f"{cat} under-allocated by {deficit:.1f}%")
            elif weight > thresh["max"]:
                excess = weight - thresh["max"]
                penalty += excess * 1.0
                violations.append(f"{cat} over-allocated by {excess:.1f}%")

    score = 100 - penalty
    score = max(0.0, min(100.0, score))

    if score >= 80:
        category = "Well Diversified"
    elif score >= 60:
        category = "Moderately Diversified"
    elif score >= 40:
        category = "Low Diversification"
    else:
        category = "Poorly Diversified"

    return {
        "diversification_score": round(score, 2),
        "category": category,
        "violations": violations,
        "penalty": round(penalty, 2),
        "weights": {k: round(v, 2) for k, v in cat_weights.items()},
    }


def apply_diversification_penalties(
    funds: List[Dict[str, Any]], risk_profile: int = 3
) -> List[Dict[str, Any]]:
    if not funds:
        return funds

    cat_weights = {}
    for fund in funds:
        cat = fund.get("category", "Other")
        cat_weights[cat] = cat_weights.get(cat, 0) + fund.get("weight", 0)

    adjusted = []
    caps = RISK_BASED_CAPS.get(risk_profile, RISK_BASED_CAPS[3])

    for fund in funds:
        fund_copy = fund.copy()
        cat = fund.get("category", "Other")

        if cat in caps:
            max_cap = caps[cat]
            if cat_weights.get(cat, 0) > max_cap:
                fund_copy["penalty_applied"] = True
                fund_copy["original_weight"] = fund_copy["weight"]
                fund_copy["weight"] = min(fund_copy["weight"], max_cap * 0.5)
                fund_copy["penalty_reason"] = f"Risk-based cap exceeded for {cat}"
        else:
            fund_copy["penalty_applied"] = False

        adjusted.append(fund_copy)

    total = sum(f["weight"] for f in adjusted)
    if total > 0:
        for f in adjusted:
            f["weight"] = round((f["weight"] / total) * 100, 2)

    return adjusted


def generate_diversification_comments(score_result: Dict[str, Any]) -> List[str]:
    comments = []
    score = score_result.get("diversification_score", 0)
    violations = score_result.get("violations", [])
    weights = score_result.get("weights", {})

    if score >= 80:
        comments.append(
            "Portfolio demonstrates excellent diversification across asset classes."
        )
    elif score >= 60:
        comments.append(
            "Portfolio shows reasonable diversification with room for improvement."
        )
    else:
        comments.append("Portfolio concentration risk detected. Consider rebalancing.")

    for cat, weight in weights.items():
        if cat in CATEGORY_PENALTY_THRESHOLDS:
            thresh = CATEGORY_PENALTY_THRESHOLDS[cat]
            if weight > thresh["max"]:
                comments.append(
                    f"Heavy exposure to {cat} ({weight:.1f}%) may increase volatility."
                )
            elif weight < thresh["min"]:
                comments.append(
                    f"Low exposure to {cat} ({weight:.1f}%). Consider increasing for better diversification."
                )

    for v in violations[:3]:
        comments.append(f"Alert: {v}")

    return comments


def optimize_allocation_for_diversification(
    funds: List[Dict[str, Any]], risk_profile: int = 3
) -> Dict[str, Any]:
    adjusted = apply_diversification_penalties(funds, risk_profile)
    score_result = calculate_diversification_score(adjusted)
    comments = generate_diversification_comments(score_result)

    return {
        "adjusted_allocation": adjusted,
        "diversification_score": score_result["diversification_score"],
        "diversification_category": score_result["category"],
        "comments": comments,
    }


if __name__ == "__main__":
    test_allocation = [
        {"fund_name": "HDFC Top 100", "category": "Large Cap", "weight": 35.0},
        {"fund_name": "Mirae Asset Midcap", "category": "Mid Cap", "weight": 25.0},
        {"fund_name": "Small Cap Fund", "category": "Small Cap", "weight": 20.0},
        {"fund_name": "Axis Bluechip", "category": "Large Cap", "weight": 10.0},
        {"fund_name": "Debt Fund", "category": "Debt", "weight": 10.0},
    ]
    result = optimize_allocation_for_diversification(test_allocation, risk_profile=3)
    print(result)
