def calculate_ai_score(fund, market_signal="NEUTRAL"):
    ret1 = fund.get("1y_return", 0)
    ret3 = fund.get("3y_return", 0)
    vol = fund.get("volatility", 20)

    consistency = max(0, 100 - vol)

    comp1 = ret1 * 0.3
    comp2 = ret3 * 0.3
    comp3 = consistency * 0.2
    comp4 = 10 if market_signal == "BULLISH" else 0

    total = round(comp1 + comp2 + comp3 + comp4, 1)

    return {
        "ai_score": total,
        "components": {
            "1y_return_contribution": round(comp1, 2),
            "3y_return_contribution": round(comp2, 2),
            "consistency_contribution": round(comp3, 2),
            "market_fit_contribution": comp4,
        },
        "breakdown": {
            "1y_return": ret1,
            "3y_return": ret3,
            "volatility": vol,
            "consistency_score": consistency,
            "market_signal": market_signal,
        },
    }


def score_funds(funds, market_signal="NEUTRAL"):
    scored = []
    for fund in funds:
        score = calculate_ai_score(fund, market_signal)
        scored.append(
            {**fund, "ai_score": score["ai_score"], "ai_breakdown": score["components"]}
        )

    scored.sort(key=lambda x: x["ai_score"], reverse=True)
    return scored


def get_top_funds(funds, market_signal="NEUTRAL", limit=5):
    scored = score_funds(funds, market_signal)
    return scored[:limit]
