from typing import Dict, Any


def analyze_portfolio(
    existing_fd: float,
    existing_savings: float,
    existing_gold: float,
    existing_mutual_funds: float,
) -> Dict[str, Any]:
    """
    Analyzes the existing asset distribution
    and generates a diversification score.
    """
    total_corpus = (
        existing_fd + existing_savings + existing_gold + existing_mutual_funds
    )

    if total_corpus == 0:
        return {
            "total_corpus": 0.0,
            "diversification_score": 0,
            "insights": ["Start investing to build a portfolio."],
            "breakdown": {},
        }

    breakdown = {
        "Fixed Deposits / Bonds": round((existing_fd / total_corpus) * 100, 2),
        "Savings / Cash": round((existing_savings / total_corpus) * 100, 2),
        "Gold": round((existing_gold / total_corpus) * 100, 2),
        "Mutual Funds / Equity": round((existing_mutual_funds / total_corpus) * 100, 2),
    }

    # Calculate Diversification Score (0-10)
    # Penalize too much cash/FD or too little equity
    score = 10
    insights = []

    if breakdown["Savings / Cash"] > 20:
        score -= 2
        insights.append(
            "High cash drag. Consider moving excess savings"
            " to liquid funds or short-term debt."
        )

    if breakdown["Mutual Funds / Equity"] < 20:
        score -= 2
        insights.append(
            "Low equity exposure limits long-term wealth creation."
            " Increase SIPs in equity funds."
        )

    if breakdown["Gold"] > 15:
        score -= 1
        insights.append(
            "Gold allocation is slightly high. Limit to 5-10% for optimal hedging."
        )

    if breakdown["Fixed Deposits / Bonds"] > 60:
        score -= 2
        insights.append(
            "Heavy reliance on FDs. Tax-inefficient and may underperform inflation."
        )

    if score == 10:
        insights.append("Your existing portfolio is well-diversified!")

    # Calculate Risk Exposure (Low, Moderate, High)
    equity_exposure = breakdown["Mutual Funds / Equity"]
    if equity_exposure < 30:
        risk_exposure = "Conservative (Low Equity)"
    elif equity_exposure <= 60:
        risk_exposure = "Moderate (Balanced Equity)"
    else:
        risk_exposure = "Aggressive (High Equity)"

    return {
        "total_corpus": total_corpus,
        "diversification_score": max(0, score),
        "risk_exposure": risk_exposure,
        "insights": insights,
        "breakdown": breakdown,
    }
