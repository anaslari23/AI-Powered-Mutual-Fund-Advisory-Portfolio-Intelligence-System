def determine_market_regime(signals):
    vix = signals.get("vix", 15)
    nifty = signals.get("nifty_signal", "neutral")

    if vix > 25:
        return "VOLATILE"
    if nifty == "bearish":
        return "BEARISH"
    if nifty == "bullish":
        return "BULLISH"
    return "NEUTRAL"


def recommend_mode(fund, regime, surplus):
    amount = (fund.get("weight", 0) / 100) * surplus

    if regime == "BEARISH":
        return {"mode": "STP", "months": 6}

    if regime == "BULLISH":
        return {"mode": "LUMPSUM+SIP", "lumpsum": amount * 0.5}

    return {"mode": "SIP"}


def get_recommended_strategy(investor_profile, market_signals):
    regime = determine_market_regime(market_signals)
    risk_score = investor_profile.get("risk_score", 5)
    investment_amount = investor_profile.get("investment_amount", 0)
    horizon = investor_profile.get("horizon_years", 10)

    if regime == "VOLATILE":
        strategy = {
            "primary_mode": "SIP",
            "rationale": "Volatile markets - rupee cost averaging recommended",
            "allocation": {"sip": 100, "lumpsum": 0},
        }
    elif regime == "BEARISH":
        strategy = {
            "primary_mode": "STP",
            "rationale": "Bearish signals - gradual transfer from debt to equity",
            "allocation": {"debt_to_equity": 100, "duration_months": 12},
        }
    elif regime == "BULLISH":
        if horizon >= 5:
            strategy = {
                "primary_mode": "LUMPSUM",
                "rationale": "Bullish markets - full exposure recommended for long term",
                "allocation": {"lumpsum": 70, "sip": 30},
            }
        else:
            strategy = {
                "primary_mode": "SIP",
                "rationale": "Short horizon despite bullish signals - staggered entry",
                "allocation": {"lumpsum": 30, "sip": 70},
            }
    else:
        if risk_score >= 7:
            strategy = {
                "primary_mode": "LUMPSUM+SIP",
                "rationale": "Aggressive investor in neutral market - balanced approach",
                "allocation": {"lumpsum": 50, "sip": 50},
            }
        else:
            strategy = {
                "primary_mode": "SIP",
                "rationale": "Conservative investor - systematic investment recommended",
                "allocation": {"sip": 100},
            }

    strategy["regime"] = regime
    strategy["investment_amount"] = investment_amount

    if investment_amount > 0 and strategy["allocation"].get("sip", 0) > 0:
        strategy["monthly_sip"] = round(
            investment_amount * strategy["allocation"]["sip"] / 100
        )

    return strategy
