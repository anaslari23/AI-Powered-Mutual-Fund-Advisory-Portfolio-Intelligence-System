from typing import Dict, Any


def get_asset_allocation(risk_score: float) -> Dict[str, Any]:
    """
    Returns the asset allocation based on the calculated risk score.
    Allocation sums exactly to 100%.
    """
    if risk_score < 5:
        category = "Conservative"
        allocation = {
            "Equity - Large Cap": 15,
            "Equity - Flexi Cap": 5,
            "Equity - Hybrid": 0,
            "Debt": 70,
            "Gold": 10,
        }
    elif 5 <= risk_score <= 7:
        category = "Moderate"
        allocation = {
            "Equity - Large Cap": 30,
            "Equity - Flexi Cap": 20,
            "Equity - Hybrid": 10,
            "Debt": 30,
            "Gold": 10,
        }
    else:
        category = "Aggressive"
        allocation = {
            "Equity - Large Cap": 40,
            "Equity - Flexi Cap": 30,
            "Equity - Hybrid": 10,
            "Debt": 10,
            "Gold": 10,
        }

    return {"category": category, "allocation": allocation}
