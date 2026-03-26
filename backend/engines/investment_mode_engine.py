from typing import Any, Dict

from config import is_feature_enabled


def recommend_investment_mode(
    market_signals: Dict[str, Any],
    available_capital: float,
) -> Dict[str, Any]:
    if is_feature_enabled("investment_mode_recommendation", True):
        from backend.engines.v2.investment_mode_engine import (
            recommend_investment_mode as _recommend_v2,
        )

        return _recommend_v2(market_signals, available_capital)

    from backend.funds.investment_mode import get_recommended_strategy

    fallback = get_recommended_strategy(
        {"investment_amount": available_capital, "risk_score": 5, "horizon_years": 10},
        {
            "vix": market_signals.get("vix_level", market_signals.get("vix", 15.0)),
            "nifty_signal": market_signals.get("market_trend", "neutral"),
        },
    )
    return {
        "recommended_mode": fallback.get("primary_mode", "SIP"),
        "trigger_reason": fallback.get("rationale", "Systematic investing recommended."),
        "deployment_plan": fallback.get("rationale", "Start with SIP."),
        "expected_advantage_vs_flat_sip": "Fallback recommendation in use.",
        "market_stability_score": market_signals.get("market_stability_score", 0.6),
        "nifty_pe": market_signals.get("nifty_pe", 22.5),
        "available_capital": float(available_capital),
        "supported_modes": ["Lumpsum", "SIP", "STP", "SWP", "SIP + Lumpsum hybrid"],
    }
