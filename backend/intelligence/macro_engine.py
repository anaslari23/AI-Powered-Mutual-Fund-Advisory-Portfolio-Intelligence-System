INFLATION_RISK = [
    (4.0, 0.0),
    (6.0, 0.2),
    (8.0, 0.45),
    (10.0, 0.65),
    (12.0, 0.80),
    (999, 1.0),
]

VIX_RISK = [
    (12, 0.0),
    (18, 0.2),
    (25, 0.5),
    (35, 0.75),
    (999, 1.0),
]

GEOPOLITICAL_PRESETS = {
    "low": 0.1,
    "medium": 0.4,
    "high": 0.7,
    "extreme": 0.95,
}


def _lookup(table, value):
    for max_v, risk in table:
        if value <= max_v:
            return risk
    return 1.0


def calculate_macro_stability(
    cpi, vix, geopolitical_level="medium", repo_rate=6.5, repo_trend="stable"
):
    inf_risk = _lookup(INFLATION_RISK, cpi)
    vix_risk = _lookup(VIX_RISK, vix)
    geo_risk = GEOPOLITICAL_PRESETS.get(geopolitical_level, 0.4)

    if repo_trend == "rising":
        inf_risk = min(1.0, inf_risk + 0.1)
    elif repo_trend == "falling":
        inf_risk = max(0.0, inf_risk - 0.05)

    composite = (inf_risk * 0.35) + (geo_risk * 0.35) + (vix_risk * 0.30)

    stability = round(1.0 - composite, 3)

    if stability >= 0.80:
        label = "STABLE"
    elif stability >= 0.55:
        label = "CAUTIOUS"
    else:
        label = "UNCERTAIN"

    return {
        "stability_score": stability,
        "label": label,
        "market_signal": "BULLISH" if stability > 0.75 else "BEARISH",
        "components": {
            "inflation_risk": inf_risk,
            "vix_risk": vix_risk,
            "geopolitical_risk": geo_risk,
        },
        "inputs": {
            "cpi": cpi,
            "vix": vix,
            "geopolitical_level": geopolitical_level,
            "repo_rate": repo_rate,
            "repo_trend": repo_trend,
        },
    }


def get_market_outlook(cpi=5.5, vix=15, geopolitical_level="medium"):
    result = calculate_macro_stability(cpi, vix, geopolitical_level)

    if result["market_signal"] == "BULLISH" and result["stability_score"] > 0.8:
        outlook = "FAVOURABLE"
        recommendation = "Increase equity allocation"
    elif result["label"] == "UNCERTAIN":
        outlook = "CAUTIOUS"
        recommendation = "Maintain defensive allocation"
    else:
        outlook = "NEUTRAL"
        recommendation = "Balanced approach recommended"

    return {**result, "outlook": outlook, "recommendation": recommendation}

def detect_market_regime(vix, inflation, rates):
    if vix > 20 and inflation > 6:
        return "HIGH_RISK"
    elif vix < 15 and inflation < 5:
        return "LOW_RISK"
    return "NEUTRAL"
