def calculate_overlap(a, b):
    set_a = set(a)
    set_b = set(b)
    if not set_a or not set_b:
        return 0.0
    return round(len(set_a & set_b) / len(set_a | set_b) * 100, 1)


def eliminate_overlapping_funds(funds, threshold=40):
    if not funds:
        return []

    funds = sorted(funds, key=lambda x: x.get("ai_score", 0), reverse=True)

    result = []

    for fund in funds:
        keep = True
        for r in result:
            overlap = calculate_overlap(
                fund.get("top_holdings", []), r.get("top_holdings", [])
            )
            if overlap > threshold:
                keep = False
                break

        if keep:
            result.append(fund)

    return result


def analyze_portfolio_overlap(funds, threshold=30):
    if len(funds) < 2:
        return {"valid": False, "message": "Need at least 2 funds"}

    overlap_pairs = []

    for i, fund_a in enumerate(funds):
        for fund_b in funds[i + 1 :]:
            overlap = calculate_overlap(
                fund_a.get("top_holdings", []), fund_b.get("top_holdings", [])
            )
            if overlap > threshold:
                overlap_pairs.append(
                    {
                        "fund_a": fund_a.get("fund_name", "Unknown"),
                        "fund_b": fund_b.get("fund_name", "Unknown"),
                        "overlap_pct": overlap,
                    }
                )

    overlap_pairs.sort(key=lambda x: x["overlap_pct"], reverse=True)

    return {
        "valid": True,
        "high_overlap_pairs": overlap_pairs,
        "recommendation": "Consolidate funds"
        if overlap_pairs
        else "Portfolio well diversified",
    }


def get_diversification_score(funds):
    if not funds:
        return 0.0

    categories = set(f.get("category", "Unknown") for f in funds)
    unique_categories = len(categories)

    score = min(100, unique_categories * 20)

    return score
