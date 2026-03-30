"""
backend/engines/advisory_language_engine.py
────────────────────────────────────────────
Deterministic, template-driven advisory language generator.
Produces human-readable, professional advisory narratives
using variable interpolation — NO AI free-text generation.

Covers: client summary, risk explanation, allocation reasoning,
portfolio commentary, SIP story, category justification,
negative justification (WHY NOT), and closing recommendation.
"""
from typing import Any, Dict, Optional


# ──────────────────────────────────────────────────────────────────────────────
# Template Library
# ──────────────────────────────────────────────────────────────────────────────

_CLIENT_SUMMARY_TEMPLATES = {
    "young": (
        "Based on your age of {age}, your financial profile suggests a long investment "
        "runway that can accommodate growth-oriented strategies. With {dependents} dependent(s) "
        "and a monthly income of ₹{income:,.0f}, we have designed a structured investment "
        "approach aligned with your long-term wealth creation objectives."
    ),
    "mid_career": (
        "At age {age}, you are in a pivotal phase of your financial journey. With {dependents} "
        "dependent(s), a monthly income of ₹{income:,.0f}, and an investible surplus of "
        "₹{surplus:,.0f}, our recommendation balances growth potential with the stability "
        "needed for your medium-term goals."
    ),
    "senior": (
        "At age {age}, capital preservation and income stability become paramount. With "
        "{dependents} dependent(s) and a monthly income of ₹{income:,.0f}, our strategy "
        "prioritises protecting your accumulated wealth while generating consistent returns "
        "to support your near-term financial requirements."
    ),
}

_RISK_TEMPLATES = {
    "Aggressive": (
        "Your risk assessment yields a score of {score:.1f}/10, classifying you as an "
        "Aggressive investor. Given your {risk_class} risk profile and a time horizon of "
        "{horizon} years, a growth-oriented approach with significant equity exposure is "
        "suitable. Your capacity to absorb short-term volatility enables participation in "
        "higher-return asset classes."
    ),
    "Moderate": (
        "Your risk assessment yields a score of {score:.1f}/10, classifying you as a "
        "Moderate investor. Given your {risk_class} risk profile and a time horizon of "
        "{horizon} years, a balanced approach combining equity growth with debt stability "
        "is recommended. This strategy positions your portfolio for steady appreciation "
        "while cushioning against excessive market fluctuations."
    ),
    "Conservative": (
        "Your risk assessment yields a score of {score:.1f}/10, classifying you as a "
        "Conservative investor. Given your {risk_class} risk profile and a time horizon of "
        "{horizon} years, a capital-preservation approach with higher debt allocation and "
        "limited equity exposure is advisable. Stability of returns takes priority over "
        "aggressive growth in this strategy."
    ),
}

_ALLOCATION_TEMPLATES = {
    "equity_heavy": (
        "A higher allocation towards equity ({equity:.1f}%) is recommended to maximise "
        "long-term growth potential, while maintaining sufficient stability through "
        "debt exposure ({debt:.1f}%) and a strategic gold hedge ({gold:.1f}%). This mix "
        "is calibrated to your risk tolerance and investment horizon."
    ),
    "balanced": (
        "A balanced allocation between equity ({equity:.1f}%) and debt ({debt:.1f}%) is "
        "recommended, supplemented by a gold hedge ({gold:.1f}%). This diversified approach "
        "aims to deliver consistent risk-adjusted returns while protecting against "
        "concentrated exposure to any single asset class."
    ),
    "debt_heavy": (
        "A stability-focused allocation with higher debt exposure ({debt:.1f}%) is "
        "recommended, complemented by limited equity ({equity:.1f}%) for modest growth "
        "and gold ({gold:.1f}%) as an inflation hedge. This conservative mix prioritises "
        "capital protection and predictable income streams."
    ),
}

_PORTFOLIO_COMMENTARY_TEMPLATES = {
    "equity_overweight": (
        "Your current portfolio is heavily concentrated in equity ({equity_pct:.1f}%), "
        "which increases exposure to market volatility. A more balanced allocation can "
        "help stabilise returns while maintaining growth potential. Consider gradually "
        "rebalancing towards debt and gold to reduce concentration risk."
    ),
    "fd_heavy": (
        "Your portfolio has a significant allocation to fixed deposits and bonds "
        "({fd_pct:.1f}%), which may result in sub-optimal post-tax returns given the "
        "current interest rate environment. Diversifying a portion into debt mutual funds "
        "or equity can improve long-term wealth creation."
    ),
    "well_diversified": (
        "Your current portfolio reflects a well-diversified approach across asset classes. "
        "The existing allocation is broadly aligned with your risk profile. Minor "
        "adjustments may be recommended to optimise returns based on current market "
        "conditions and your evolving financial goals."
    ),
    "cash_heavy": (
        "A significant portion of your portfolio is held in cash or savings accounts "
        "({cash_pct:.1f}%), which earns below-inflation returns. Deploying excess cash "
        "into liquid or short-duration debt funds can improve real returns without "
        "materially increasing risk."
    ),
    "no_portfolio": (
        "You do not currently have an existing investment portfolio. This provides a "
        "clean slate to build a well-diversified portfolio from the ground up, "
        "structured around your risk profile and financial goals."
    ),
}

_NEGATIVE_JUSTIFICATION_TEMPLATES = {
    "Aggressive": (
        "While the current allocation favours growth, a fully speculative approach "
        "involving concentrated sectoral or thematic bets has been avoided. Such strategies "
        "carry disproportionate downside risk and may not align with disciplined long-term "
        "wealth creation, even for investors with high risk tolerance."
    ),
    "Moderate": (
        "While small-cap or thematic funds may offer higher short-term returns, they carry "
        "significantly higher volatility and may not align with your current risk profile. "
        "Similarly, a fully conservative approach would sacrifice growth potential that your "
        "investment horizon can accommodate. The recommended balance seeks to optimise "
        "risk-adjusted returns."
    ),
    "Conservative": (
        "A fully equity-oriented approach may expose your portfolio to unnecessary "
        "volatility, which is not suitable given your shorter investment horizon and "
        "conservative risk appetite. While equities can deliver higher returns over "
        "extended periods, the near-term drawdown risk outweighs the potential benefit "
        "for your financial situation."
    ),
}

_FINAL_RECOMMENDATION_TEMPLATE = (
    "Based on your financial profile, risk tolerance, and investment horizon, a "
    "disciplined and well-diversified investment strategy is recommended to help you "
    "achieve your long-term financial goals while managing risk effectively. We encourage "
    "periodic reviews — at least annually — to ensure your portfolio remains aligned "
    "with your evolving needs and market conditions."
)


# ──────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────────────────────────────────────

def _classify_age_band(age: int) -> str:
    if age <= 35:
        return "young"
    elif age <= 55:
        return "mid_career"
    return "senior"


def _classify_allocation_style(equity: float, debt: float) -> str:
    if equity >= 55:
        return "equity_heavy"
    elif debt >= 50:
        return "debt_heavy"
    return "balanced"


def _classify_portfolio_bias(breakdown: Dict[str, float]) -> str:
    if not breakdown:
        return "no_portfolio"
    equity_pct = breakdown.get("Mutual Funds / Equity", 0.0)
    fd_pct = breakdown.get("Fixed Deposits / Bonds", 0.0)
    cash_pct = breakdown.get("Savings / Cash", 0.0)
    total = sum(breakdown.values())
    if total <= 0:
        return "no_portfolio"
    if equity_pct > 60:
        return "equity_overweight"
    if fd_pct > 50:
        return "fd_heavy"
    if cash_pct > 30:
        return "cash_heavy"
    return "well_diversified"


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

def generate_advisory_narrative(
    profile: Dict[str, Any],
    risk: Dict[str, Any],
    goals: list,
    guidance: Optional[Dict[str, Any]] = None,
    portfolio: Optional[Dict[str, Any]] = None,
) -> Dict[str, str]:
    """
    Generate a complete advisory narrative using deterministic templates.

    Parameters
    ----------
    profile : dict
        Client profile with keys: age, monthly_income, dependents,
        effective_monthly_savings, etc.
    risk : dict
        Risk engine output with keys: score, category/risk_class.
    goals : list[dict]
        List of goal dicts with goal_type, years_to_goal, etc.
    guidance : dict, optional
        Allocation guidance with keys: equity, debt, gold.
    portfolio : dict, optional
        Portfolio analysis with keys: breakdown, total_corpus, etc.

    Returns
    -------
    dict
        Keys: client_summary, risk_explanation, allocation_explanation,
        portfolio_commentary, sip_story, category_why, negative_justification,
        final_recommendation, final_advice
    """
    guidance = guidance or {}
    portfolio = portfolio or {}
    breakdown = portfolio.get("breakdown", {})

    # ── Extract values ─────────────────────────────────────────────────────
    age = _safe_int(profile.get("age"), 30)
    income = _safe_float(profile.get("monthly_income"), 0)
    surplus = _safe_float(
        profile.get("effective_monthly_savings",
                     profile.get("investable_surplus")), 0
    )
    dependents = _safe_int(profile.get("dependents"), 0)

    risk_score = _safe_float(risk.get("score"), 5.0)
    risk_class = str(risk.get("category", risk.get("risk_class", "Moderate")))

    # Determine primary goal horizon
    horizon = 10  # default
    if goals:
        horizon = max(
            _safe_int(g.get("years_to_goal", g.get("horizon_years")), 10)
            for g in goals
        )

    equity = _safe_float(guidance.get("equity", guidance.get("Equity", 0)))
    debt = _safe_float(guidance.get("debt", guidance.get("Debt", 0)))
    gold = _safe_float(guidance.get("gold", guidance.get("Gold", 0)))

    # If allocation comes as nested dict
    if not equity and "allocation" in guidance:
        alloc = guidance["allocation"]
        equity = sum(v for k, v in alloc.items() if "equity" in k.lower() or "cap" in k.lower() or "flexi" in k.lower() or "sectoral" in k.lower())
        debt = sum(v for k, v in alloc.items() if "debt" in k.lower() or "bond" in k.lower() or "liquid" in k.lower())
        gold = sum(v for k, v in alloc.items() if "gold" in k.lower())

    # ── Generate each section ──────────────────────────────────────────────
    age_band = _classify_age_band(age)
    client_summary = _CLIENT_SUMMARY_TEMPLATES.get(age_band, _CLIENT_SUMMARY_TEMPLATES["mid_career"]).format(
        age=age, income=income, surplus=surplus, dependents=dependents
    )

    risk_key = risk_class if risk_class in _RISK_TEMPLATES else "Moderate"
    risk_explanation = _RISK_TEMPLATES[risk_key].format(
        score=risk_score, risk_class=risk_class, horizon=horizon
    )

    alloc_style = _classify_allocation_style(equity, debt)
    allocation_explanation = _ALLOCATION_TEMPLATES[alloc_style].format(
        equity=equity, debt=debt, gold=gold
    )

    portfolio_bias = _classify_portfolio_bias(breakdown)
    portfolio_vars = {
        "equity_pct": breakdown.get("Mutual Funds / Equity", 0.0),
        "fd_pct": breakdown.get("Fixed Deposits / Bonds", 0.0),
        "cash_pct": breakdown.get("Savings / Cash", 0.0),
        "gold_pct": breakdown.get("Gold", 0.0),
    }
    portfolio_commentary = _PORTFOLIO_COMMENTARY_TEMPLATES[portfolio_bias].format(**portfolio_vars)

    negative_justification = _NEGATIVE_JUSTIFICATION_TEMPLATES.get(
        risk_key, _NEGATIVE_JUSTIFICATION_TEMPLATES["Moderate"]
    )

    final_recommendation = _FINAL_RECOMMENDATION_TEMPLATE

    # SIP story and category_why are populated by their dedicated engines
    # and merged downstream — we return placeholders here
    sip_story = ""
    category_why = ""
    final_advice = final_recommendation

    return {
        "client_summary": client_summary,
        "risk_explanation": risk_explanation,
        "allocation_explanation": allocation_explanation,
        "portfolio_commentary": portfolio_commentary,
        "sip_story": sip_story,
        "category_why": category_why,
        "negative_justification": negative_justification,
        "final_recommendation": final_recommendation,
        "final_advice": final_advice,
    }


def build_assumptions_block(
    return_rate: float,
    inflation_rate: float = 6.0,
    horizon_years: int = 10,
    sip_frequency: str = "Monthly",
    market_condition: str = "Assumed normal (no extreme volatility)",
) -> Dict[str, Any]:
    """
    Build a structured assumptions disclosure block.
    Values come from calculation context — not editable by client.
    """
    return {
        "expected_annual_return_pct": round(return_rate, 2),
        "inflation_rate_pct": round(inflation_rate, 2),
        "investment_horizon_years": horizon_years,
        "sip_frequency": sip_frequency,
        "market_condition": market_condition,
        "display_text": (
            f"Expected annual return: {return_rate:.1f}%  •  "
            f"Inflation: {inflation_rate:.1f}%  •  "
            f"Investment horizon: {horizon_years} years  •  "
            f"SIP frequency: {sip_frequency}  •  "
            f"Market conditions: {market_condition}"
        ),
    }
