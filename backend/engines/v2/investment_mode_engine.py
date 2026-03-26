from typing import Any, Dict


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _derive_market_stability_score(market_signals: Dict[str, Any]) -> float:
    if market_signals.get("market_stability_score") is not None:
        return _clamp(float(market_signals["market_stability_score"]), 0.0, 1.0)

    vix = float(market_signals.get("vix_level", market_signals.get("vix", 15.0)))
    trend = str(market_signals.get("market_trend", "neutral")).lower()
    sentiment = str(market_signals.get("global_sentiment", "neutral")).lower()
    inflation_trend = str(market_signals.get("inflation_trend", "stable")).lower()
    rate_trend = str(market_signals.get("interest_rate_trend", "stable")).lower()

    if vix >= 25:
        score = 0.35
    elif vix >= 20:
        score = 0.48
    elif vix >= 13:
        score = 0.68
    else:
        score = 0.86

    if trend == "bullish":
        score += 0.08
    elif trend == "bearish":
        score -= 0.12

    if sentiment == "positive":
        score += 0.05
    elif sentiment == "negative":
        score -= 0.08

    if inflation_trend == "rising":
        score -= 0.04
    if rate_trend == "rising":
        score -= 0.04

    return round(_clamp(score, 0.0, 1.0), 2)


def _estimate_advantage_vs_flat_sip(
    recommended_mode: str,
    available_capital: float,
    stability_score: float,
) -> str:
    capital = max(0.0, float(available_capital))
    if capital <= 0:
        return "No capital available for mode comparison."

    if recommended_mode == "Lumpsum":
        advantage = capital * 0.08 * max(stability_score, 0.5)
        return f"Estimated ₹{advantage:,.0f} better outcome versus flat SIP due to earlier market participation."
    if recommended_mode == "STP":
        advantage = capital * 0.03 * max(stability_score, 0.5)
        return f"Estimated ₹{advantage:,.0f} better outcome versus flat SIP through lower cash drag while controlling entry risk."
    if recommended_mode == "SIP + Lumpsum hybrid":
        advantage = capital * 0.05 * max(stability_score, 0.5)
        return f"Estimated ₹{advantage:,.0f} better outcome versus flat SIP from partial early deployment plus ongoing averaging."
    if recommended_mode == "SWP":
        advantage = capital * 0.02
        return f"Estimated ₹{advantage:,.0f} smoother cash-flow advantage versus ad hoc withdrawals."
    return "Likely smoother entry than lumpsum deployment in current conditions, with lower regret risk than market timing."


def recommend_investment_mode(
    market_signals: Dict[str, Any],
    available_capital: float,
) -> Dict[str, Any]:
    stability_score = _derive_market_stability_score(market_signals)
    nifty_pe = float(market_signals.get("nifty_pe", 22.5))
    idle_corpus = max(0.0, float(available_capital))
    stp_months = 6
    stp_monthly = idle_corpus / stp_months if stp_months > 0 else idle_corpus
    post_retirement_phase = bool(
        market_signals.get("post_retirement_phase")
        or market_signals.get("enable_swp")
        or market_signals.get("distribution_phase")
    )

    recommendation: Dict[str, Any]
    if post_retirement_phase:
        monthly_withdrawal = float(market_signals.get("target_monthly_withdrawal", 0.0))
        recommendation = {
            "recommended_mode": "SWP",
            "trigger_reason": "Distribution phase detected for post-retirement income needs.",
            "deployment_plan": (
                f"Move corpus into a retirement bucket and withdraw ₹{monthly_withdrawal:,.0f}/month via SWP."
                if monthly_withdrawal > 0
                else "Set up a monthly SWP from the retirement income corpus."
            ),
        }
    elif stability_score < 0.5:
        recommendation = {
            "recommended_mode": "SIP",
            "trigger_reason": "Market is uncertain. Use SIP to average your cost over 6–12 months.",
            "deployment_plan": (
                f"Deploy ₹{idle_corpus / 12:,.0f} per month for 12 months."
                if idle_corpus > 0
                else "Start a disciplined monthly SIP immediately."
            ),
        }
    elif stability_score > 0.8 and nifty_pe < 22:
        recommendation = {
            "recommended_mode": "Lumpsum",
            "trigger_reason": "Market at fair value with low volatility. Deploy lumpsum for maximum compounding.",
            "deployment_plan": f"Deploy ₹{idle_corpus:,.0f} as a lumpsum today."
            if idle_corpus > 0
            else "Deploy available capital as a lumpsum today.",
        }
    elif idle_corpus >= 250000 and 0.5 <= stability_score <= 0.8:
        recommendation = {
            "recommended_mode": "STP",
            "trigger_reason": (
                f"You have ₹{idle_corpus:,.0f} idle. Market is cautious, so phase equity entry through STP."
            ),
            "deployment_plan": (
                f"Park ₹{idle_corpus:,.0f} in a liquid fund and auto-transfer "
                f"₹{stp_monthly:,.0f}/month to equity over {stp_months} months."
            ),
            "stp_source_fund": "Liquid Fund",
            "stp_target_fund": "Equity Fund",
        }
    else:
        lumpsum_component = idle_corpus * 0.4
        sip_component = idle_corpus * 0.6 / 12 if idle_corpus > 0 else 0.0
        recommendation = {
            "recommended_mode": "SIP + Lumpsum hybrid",
            "trigger_reason": "Conditions are constructive but not ideal for full one-shot deployment.",
            "deployment_plan": (
                f"Invest ₹{lumpsum_component:,.0f} now and continue ₹{sip_component:,.0f}/month SIP for 12 months."
                if idle_corpus > 0
                else "Use a base SIP and add opportunistic lumpsums on market corrections."
            ),
        }

    recommendation.update(
        {
            "market_stability_score": stability_score,
            "nifty_pe": round(nifty_pe, 2),
            "available_capital": idle_corpus,
            "supported_modes": [
                "Lumpsum",
                "SIP",
                "STP",
                "SWP",
                "SIP + Lumpsum hybrid",
            ],
            "expected_advantage_vs_flat_sip": _estimate_advantage_vs_flat_sip(
                recommendation["recommended_mode"], idle_corpus, stability_score
            ),
        }
    )
    return recommendation
