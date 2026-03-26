from typing import Dict, Any, List, Set, Optional
import numpy as np


def parse_holdings(holdings_str: str) -> Set[str]:
    if not holdings_str:
        return set()
    return set([h.strip().lower() for h in holdings_str.split(",") if h.strip()])


def calculate_jaccard_similarity(set_a: Set[str], set_b: Set[str]) -> float:
    if not set_a and not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


def calculate_overlap_percentage(set_a: Set[str], set_b: Set[str]) -> Dict[str, Any]:
    if not set_a and not set_b:
        return {
            "overlap_percentage": 0.0,
            "common_holdings": [],
            "unique_to_a": [],
            "unique_to_b": [],
        }

    intersection = set_a & set_b
    union = set_a | set_b

    overlap_pct = (len(intersection) / len(union)) * 100 if union else 0
    weight_a = (len(intersection) / len(set_a)) * 100 if set_a else 0
    weight_b = (len(intersection) / len(set_b)) * 100 if set_b else 0

    return {
        "overlap_percentage": round(overlap_pct, 2),
        "weight_in_fund_a": round(weight_a, 2),
        "weight_in_fund_b": round(weight_b, 2),
        "common_holdings": list(intersection),
        "unique_to_a": list(set_a - intersection),
        "unique_to_b": list(set_b - intersection),
        "common_count": len(intersection),
        "total_unique": len(union),
    }


def check_fund_overlap(
    fund_a_holdings: str, fund_b_holdings: str, threshold: float = 0.30
) -> Dict[str, Any]:
    set_a = parse_holdings(fund_a_holdings)
    set_b = parse_holdings(fund_b_holdings)

    jaccard = calculate_jaccard_similarity(set_a, set_b)
    overlap_details = calculate_overlap_percentage(set_a, set_b)

    is_duplicate = jaccard > threshold

    if jaccard > 0.5:
        risk_level = "High"
        recommendation = "Consider keeping only one fund"
    elif jaccard > 0.3:
        risk_level = "Medium"
        recommendation = "Monitor for potential consolidation"
    elif jaccard > 0.15:
        risk_level = "Low"
        recommendation = "Acceptable overlap for diversification"
    else:
        risk_level = "Minimal"
        recommendation = "Good diversification"

    return {
        "is_duplicate": is_duplicate,
        "jaccard_similarity": round(jaccard, 4),
        "overlap_percentage": overlap_details["overlap_percentage"],
        "risk_level": risk_level,
        "recommendation": recommendation,
        "details": overlap_details,
    }


def calculate_portfolio_overlap(
    portfolio_funds: List[Dict[str, Any]], holdings_field: str = "top_holdings"
) -> Dict[str, Any]:
    if len(portfolio_funds) < 2:
        return {"valid": False, "error": "Need at least 2 funds to calculate overlap"}

    overlap_matrix = []
    fund_names = [
        f.get("fund_name", f"Fund_{i}") for i, f in enumerate(portfolio_funds)
    ]

    for i, fund_a in enumerate(portfolio_funds):
        row = []
        for j, fund_b in enumerate(portfolio_funds):
            if i == j:
                row.append(1.0)
            else:
                holdings_a = fund_a.get(holdings_field, "")
                holdings_b = fund_b.get(holdings_field, "")
                set_a = parse_holdings(holdings_a)
                set_b = parse_holdings(holdings_b)
                similarity = calculate_jaccard_similarity(set_a, set_b)
                row.append(round(similarity, 4))
        overlap_matrix.append(row)

    avg_overlap = np.mean(
        [
            overlap_matrix[i][j]
            for i in range(len(portfolio_funds))
            for j in range(i + 1, len(portfolio_funds))
        ]
    )

    high_overlap_pairs = []
    for i in range(len(portfolio_funds)):
        for j in range(i + 1, len(portfolio_funds)):
            if overlap_matrix[i][j] > 0.3:
                high_overlap_pairs.append(
                    {
                        "fund_a": fund_names[i],
                        "fund_b": fund_names[j],
                        "overlap": overlap_matrix[i][j],
                    }
                )

    high_overlap_pairs.sort(key=lambda x: x["overlap"], reverse=True)

    diversification_score = 100 - (avg_overlap * 100)
    diversification_score = max(0, min(100, diversification_score))

    if diversification_score >= 80:
        category = "Well Diversified"
    elif diversification_score >= 60:
        category = "Adequately Diversified"
    elif diversification_score >= 40:
        category = "Moderate Overlap"
    else:
        category = "High Overlap - Review Recommended"

    return {
        "valid": True,
        "diversification_score": round(diversification_score, 2),
        "category": category,
        "average_overlap": round(avg_overlap * 100, 2),
        "overlap_matrix": overlap_matrix,
        "fund_names": fund_names,
        "high_overlap_pairs": high_overlap_pairs,
        "recommendations": _generate_overlap_recommendations(
            high_overlap_pairs, diversification_score
        ),
    }


def _generate_overlap_recommendations(
    high_overlap_pairs: List[Dict], score: float
) -> List[str]:
    recommendations = []

    if score < 40:
        recommendations.append(
            "Critical: Portfolio has very high overlap. Consider consolidating funds."
        )

    if score < 60:
        recommendations.append(
            "Consider replacing one of each high-overlap pair with a different investment style."
        )

    for pair in high_overlap_pairs[:3]:
        recommendations.append(
            f"Review overlap between {pair['fund_a']} and {pair['fund_b']} ({pair['overlap'] * 100:.1f}%)"
        )

    if not recommendations:
        recommendations.append("Portfolio shows good diversification across holdings.")

    return recommendations


def suggest_diversification(
    current_funds: List[Dict[str, Any]],
    available_funds: List[Dict[str, Any]],
    holdings_field: str = "top_holdings",
    max_overlap: float = 0.25,
) -> List[Dict[str, Any]]:
    if not current_funds or not available_funds:
        return []

    current_holdings = []
    for fund in current_funds:
        holdings = fund.get(holdings_field, "")
        current_holdings.append(parse_holdings(holdings))

    combined_current = set()
    for h in current_holdings:
        combined_current |= h

    suggestions = []
    for fund in available_funds:
        fund_name = fund.get("fund_name", "")
        if any(f.get("fund_name") == fund_name for f in current_funds):
            continue

        fund_holdings = parse_holdings(fund.get(holdings_field, ""))
        if not fund_holdings:
            continue

        overlap_with_portfolio = calculate_jaccard_similarity(
            combined_current, fund_holdings
        )

        if overlap_with_portfolio < max_overlap:
            suggestions.append(
                {
                    "fund_name": fund_name,
                    "category": fund.get("category", "Unknown"),
                    "overlap_with_portfolio": round(overlap_with_portfolio * 100, 2),
                    "new_holdings_count": len(fund_holdings - combined_current),
                    "recommendation_score": round(
                        (1 - overlap_with_portfolio) * 100, 2
                    ),
                }
            )

    suggestions.sort(key=lambda x: x["recommendation_score"], reverse=True)

    return suggestions[:10]


if __name__ == "__main__":
    fund_a = (
        "TCS, Infosys, HDFC Bank, ICICI Bank, Reliance, SBIN, Bajaj Finance, Axis Bank"
    )
    fund_b = "TCS, Infosys, HDFC Bank, Wipro, HCL Tech, Tech Mahindra, ICICI Bank"

    result = check_fund_overlap(fund_a, fund_b, threshold=0.30)
    print(result)
