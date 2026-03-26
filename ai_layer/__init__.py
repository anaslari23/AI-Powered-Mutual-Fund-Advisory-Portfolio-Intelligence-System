"""
ai_layer/__init__.py
─────────────────────
Public API for the AI Layer package.

This module exposes a single high-level function ``get_live_intelligence()``
that orchestrates all sub-modules and returns a complete intelligence bundle
for consumption by the dashboard and any other caller.

Quick start:
    from ai_layer import get_live_intelligence
    intel = get_live_intelligence(
        base_allocation={"Equity - Large Cap": 50.0, "Debt": 35.0, "Gold": 15.0},
        recommended_funds=[...],
        risk_category="Moderate (ML Pred)",
    )
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def get_live_intelligence(
    base_allocation: Dict[str, float],
    recommended_funds: List[Dict[str, Any]],
    risk_category: str,
    available_capital: float = 0.0,
    use_cache: bool = True,
) -> Dict[str, Any]:
    """
    Orchestrate all AI layer modules and return a unified intelligence bundle.

    Parameters
    ----------
    base_allocation : dict
        MPT base allocation from ``allocation_engine.get_asset_allocation()``.
    recommended_funds : list
        Fund list from ``recommendation_engine.suggest_mutual_funds()``.
    risk_category : str
        Investor risk category string (e.g. "Moderate (ML Pred)").
    use_cache : bool
        If True (default), reads live data from the scheduler cache.
        If False, forces a fresh synchronous fetch (slower, use for testing).

    Returns
    -------
    dict
        ``signals``              – market signal dict
        ``market_snapshot``      – raw market prices
        ``macro_indicators``     – macro data dict
        ``adaptive_allocation``  – market-aware adjusted allocation
        ``equity_delta``         – equity adjustment in pp
        ``debt_delta``           – debt adjustment in pp
        ``gold_delta``           – gold adjustment in pp
        ``adjustment_reasons``   – list of plain-English reason strings
        ``ranked_funds``         – funds re-scored for current market
        ``investment_mode_recommendation`` – smart deployment recommendation
        ``narratives``           – dict of market_summary, allocation_rationale, risk_narrative
        ``last_updated``         – ISO timestamp of underlying data
        ``data_source``          – "live" | "partial" | "fallback"
    """
    try:
        # ── Fetch or retrieve cached data ─────────────────────────────────────
        if use_cache:
            from ai_layer.scheduler.updater import get_cached_intelligence
            intel_cache = get_cached_intelligence()
            market_snapshot  = intel_cache.get("market_snapshot",  {})
            macro_indicators = intel_cache.get("macro_indicators", {})
            signals          = intel_cache.get("signals",          {})
            last_updated     = intel_cache.get("last_updated",     "unknown")
        else:
            from ai_layer.data_ingestion.market_data  import get_market_snapshot
            from ai_layer.data_ingestion.macro_data   import get_macro_indicators
            from ai_layer.signal_engine.market_signals import generate_signals

            market_snapshot  = get_market_snapshot()
            macro_indicators = get_macro_indicators()
            signals          = generate_signals(market_snapshot, macro_indicators)
            last_updated     = signals.get("fetched_at", "unknown")

        # ── Adaptive allocation ───────────────────────────────────────────────
        from ai_layer.decision_engine.adaptive_allocation import apply_adaptive_allocation
        adaptive_result = apply_adaptive_allocation(base_allocation, signals)

        # ── Fund scoring ──────────────────────────────────────────────────────
        from ai_layer.scoring_engine.fund_scoring import rank_funds
        ranked_funds = rank_funds(recommended_funds, signals)

        # ── Smart deployment mode ────────────────────────────────────────────
        from backend.engines.investment_mode_engine import recommend_investment_mode

        investment_mode_recommendation = recommend_investment_mode(
            market_signals={
                **signals,
                "market_stability_score": adaptive_result.get("market_stability_score"),
                "nifty_pe": market_snapshot.get("nifty", {}).get("pe", 22.5),
            },
            available_capital=available_capital,
        )

        # ── Narrative generation ──────────────────────────────────────────────
        from ai_layer.explanation_engine.narrative_builder import build_full_narrative
        narratives = build_full_narrative(
            signals, market_snapshot, macro_indicators,
            adaptive_result, risk_category,
        )

        # ── Data source quality ───────────────────────────────────────────────
        mkt_live   = market_snapshot.get("_meta", {}).get("is_fully_live", False)
        macro_src  = macro_indicators.get("source", "fallback")
        if mkt_live and macro_src == "live":
            data_source = "live"
        elif mkt_live or macro_src in ("live", "partial"):
            data_source = "partial"
        else:
            data_source = "fallback"

        return {
            "signals":             signals,
            "market_snapshot":     market_snapshot,
            "macro_indicators":    macro_indicators,
            "adaptive_allocation": adaptive_result.get("adaptive_allocation", {}),
            "base_allocation":     base_allocation,
            "equity_delta":        adaptive_result.get("equity_delta", 0.0),
            "debt_delta":          adaptive_result.get("debt_delta",   0.0),
            "gold_delta":          adaptive_result.get("gold_delta",   0.0),
            "adjustment_reasons":  adaptive_result.get("adjustment_reasons", []),
            "ranked_funds":        ranked_funds,
            "investment_mode_recommendation": investment_mode_recommendation,
            "narratives":          narratives,
            "last_updated":        last_updated,
            "data_source":         data_source,
        }

    except Exception as exc:
        logger.error("ai_layer: get_live_intelligence failed — %s", exc)
        # Return a minimal safe bundle so the dashboard never crashes
        return {
            "signals":             {},
            "market_snapshot":     {},
            "macro_indicators":    {},
            "adaptive_allocation": base_allocation,
            "base_allocation":     base_allocation,
            "equity_delta":        0.0,
            "debt_delta":          0.0,
            "gold_delta":          0.0,
            "adjustment_reasons":  ["AI layer data unavailable. Showing baseline allocation."],
            "ranked_funds":        recommended_funds,
            "investment_mode_recommendation": {
                "recommended_mode": "SIP",
                "trigger_reason": "AI layer data unavailable, defaulting to staggered deployment.",
                "deployment_plan": "Start a monthly SIP until live data recovers.",
                "expected_advantage_vs_flat_sip": "Fallback mode in use.",
                "market_stability_score": 0.5,
                "nifty_pe": 22.5,
                "available_capital": float(available_capital),
                "supported_modes": ["Lumpsum", "SIP", "STP", "SWP", "SIP + Lumpsum hybrid"],
            },
            "narratives":          {
                "market_summary":       "Real-time market data is temporarily unavailable.",
                "allocation_rationale": "Showing baseline allocation.",
                "risk_narrative":       "Please check back shortly.",
                "generated_at":        "unknown",
            },
            "last_updated":        "unknown",
            "data_source":         "fallback",
        }
