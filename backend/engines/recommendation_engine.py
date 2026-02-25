from typing import Dict, Any, List


def suggest_mutual_funds(allocation: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Suggests specific mutual funds based on the target asset allocation.
    Returns realistic but mock data for India 2026.
    """
    database = {
        "Equity - Large Cap": [
            {
                "name": "Nippon India Large Cap Fund",
                "category": "Equity - Large Cap",
                "risk": "High",
                "1y": 18.5,
                "3y": 15.2,
                "5y": 14.8,
            },
            {
                "name": "ICICI Prudential Bluechip Fund",
                "category": "Equity - Large Cap",
                "risk": "High",
                "1y": 17.2,
                "3y": 14.9,
                "5y": 14.5,
            },
        ],
        "Equity - Flexi Cap": [
            {
                "name": "Parag Parikh Flexi Cap Fund",
                "category": "Equity - Flexi Cap",
                "risk": "High",
                "1y": 21.4,
                "3y": 18.6,
                "5y": 19.1,
            },
            {
                "name": "HDFC Flexi Cap Fund",
                "category": "Equity - Flexi Cap",
                "risk": "High",
                "1y": 20.1,
                "3y": 17.8,
                "5y": 16.5,
            },
        ],
        "Equity - Hybrid": [
            {
                "name": "SBI Equity Hybrid Fund",
                "category": "Equity - Hybrid",
                "risk": "Moderate",
                "1y": 14.2,
                "3y": 12.5,
                "5y": 11.8,
            }
        ],
        "Debt": [
            {
                "name": "Aditya Birla Sun Life Liquid Fund",
                "category": "Debt",
                "risk": "Low",
                "1y": 7.2,
                "3y": 6.8,
                "5y": 6.5,
            },
            {
                "name": "Kotak Corporate Bond Fund",
                "category": "Debt",
                "risk": "Low to Moderate",
                "1y": 8.1,
                "3y": 7.5,
                "5y": 7.2,
            },
        ],
        "Gold": [
            {
                "name": "SBI Gold Fund",
                "category": "Gold",
                "risk": "Moderate",
                "1y": 11.2,
                "3y": 9.5,
                "5y": 8.8,
            }
        ],
    }

    recommendations = []

    for asset_class, weight in allocation.items():
        if weight > 0 and asset_class in database:
            # Pick the top fund from the category for the allocation
            fund = database[asset_class][0].copy()
            fund["allocation_weight"] = weight
            recommendations.append(fund)

    return recommendations
