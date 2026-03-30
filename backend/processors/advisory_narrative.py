"""
backend/processors/advisory_narrative.py
──────────────────────────────────────────
Human-Like Advisory Layer — converts raw engine outputs into a complete,
professional, advisor-style advisory report.

The report has four structured sections matching the client proposal:
    1. Summary        — client snapshot + overall verdict
    2. Rationale      — why this allocation, key macro/risk drivers
    3. Risks          — what could go wrong + stress outcomes
    4. Alternatives   — other approaches considered and why this is better

Plus supplementary sections:
    5. SIP Illustrations  — projection tables by monthly amount
    6. Disclaimer         — mandatory risk disclosure text

Design principles
─────────────────
• Tone: professional, client-facing, not robotic.
• Zero jargon — all financial terms explained in context.
• Pure functions — no I/O, no randomness, deterministic.
• Every section returns structured dicts AND a plain-text string.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from backend.core.utils import safe_round

# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

_DISCLAIMER_TEXT = (
    "Mutual Fund investments are subject to market risks. "
    "Past performance is not indicative of future results. "
    "Returns shown are illustrative and based on assumed rates — "
    "actual returns may vary. "
    "Please read all scheme-related documents carefully before investing. "
    "This advisory is generated for informational purposes only and does not "
    "constitute a registered investment advisory under SEBI regulations. "
    "Consult your financial advisor before making investment decisions."
)

_RISK_CATEGORY_DESCRIPTIONS: Dict[str, str] = {
    "conservative": (
        "capital preservation and steady income. You prefer lower volatility even if "
        "it means potentially lower long-term growth."
    ),
    "moderate": (
        "balanced growth — you are comfortable with moderate market fluctuations "
        "in exchange for inflation-beating returns over the medium term."
    ),
    "growth": (
        "above-average long-term wealth creation. You accept higher short-term "
        "volatility in exchange for stronger compounding over time."
    ),
    "aggressive": (
        "maximum long-term wealth creation. You are comfortable with significant "
        "short-term fluctuations, understanding that equity markets reward patience."
    ),
}

_SIP_ILLUSTRATION_RETURNS: Dict[str, float] = {
    "conservative": 0.07,
    "moderate":     0.10,
    "growth":       0.12,
    "aggressive":   0.14,
}


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _normalise_risk(raw: str) -> str:
    r = raw.lower().split("(")[0].strip()
    if "conserv" in r: return "conservative"
    if "aggress" in r: return "aggressive"
    if "growth" in r or "high" in r: return "growth"
    return "moderate"


def _sip_future_value(monthly_sip: float, annual_rate: float, years: float) -> float:
    if years <= 0 or monthly_sip <= 0:
        return 0.0
    r = annual_rate / 12.0
    n = years * 12.0
    if r == 0:
        return monthly_sip * n
    return monthly_sip * (((1 + r) ** n - 1) / r) * (1 + r)


def _format_inr(amount: float) -> str:
    """Format rupee amount with Indian comma convention."""
    if amount >= 1_00_00_000:
        return f"₹{amount / 1_00_00_000:.2f} Cr"
    elif amount >= 1_00_000:
        return f"₹{amount / 1_00_000:.2f} L"
    else:
        return f"₹{amount:,.0f}"


# ──────────────────────────────────────────────────────────────────────────────
# Section 1: Summary
# ──────────────────────────────────────────────────────────────────────────────

def generate_summary(
    profile: Dict[str, Any],
    risk_output: Dict[str, Any],
    goals: List[Dict[str, Any]],
    affordability: Dict[str, Any],
    financial_health: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Client snapshot + overall advisory verdict.
    """
    name        = str(profile.get("name", "the client"))
    age         = int(profile.get("age", 0) or 0)
    income      = float(profile.get("monthly_income", 0.0) or 0.0)
    city        = str(profile.get("city", ""))
    risk_raw    = str(risk_output.get("category", "Moderate"))
    risk_norm   = _normalise_risk(risk_raw)
    risk_score  = float(risk_output.get("score", 5.0) or 5.0)
    risk_cat    = risk_raw.split("(")[0].strip()

    overall_flag = str(affordability.get("overall_flag", "FEASIBLE"))
    health_band  = str(financial_health.get("band", "moderate"))
    health_score = float(financial_health.get("score", 0.0) or 0.0)

    # Goal summary
    goal_lines: List[str] = []
    for g in (goals or []):
        gtype   = str(g.get("goal_type", "Goal")).replace("_", " ").title()
        target  = float(g.get("target_amount", 0.0) or 0.0)
        horizon = float(g.get("horizon_years", 0.0) or 0.0)
        if target > 0:
            goal_lines.append(f"{gtype}: {_format_inr(target)} in {horizon:.0f} years")

    goals_str = "; ".join(goal_lines) if goal_lines else "Goals not specified"

    risk_purpose = _RISK_CATEGORY_DESCRIPTIONS.get(risk_norm, "growth aligned with your profile.")

    verdict_map = {
        "FEASIBLE":       "Your financial profile is well-positioned for investment. The recommended plan is fully sustainable within your income and obligations.",
        "STRETCH":        "Your investment goals are ambitious given current cash flows. The plan is achievable but will require disciplined budgeting and consistent SIP commitment.",
        "NOT_ADVISABLE":  "At this time, large new investment commitments are not advisable given current financial obligations. Priority actions have been identified to strengthen the foundation first.",
    }
    verdict = verdict_map.get(overall_flag, "Assessment complete.")

    client_snapshot = {
        "name":          name,
        "age":           age,
        "city":          city if city else "Not provided",
        "monthly_income": _format_inr(income),
        "risk_profile":  f"{risk_cat} (Score: {safe_round(risk_score, 1)}/10)",
        "financial_health": f"{health_band.title()} ({safe_round(health_score * 100, 0):.0f}/100)",
        "goals":         goals_str,
        "investable_surplus": _format_inr(
            float(affordability.get("sip_capacity", {}).get("investable_surplus", 0.0) or 0.0)
        ),
    }

    narrative = (
        f"{name}{', aged ' + str(age) if age else ''} is a **{risk_cat}** investor "
        f"focused on {risk_purpose} "
        f"Key goals: {goals_str}. "
        f"Monthly investable surplus: {_format_inr(float(affordability.get('sip_capacity', {}).get('investable_surplus', 0.0) or 0.0))}. "
        f"\n\n**Overall Assessment**: {verdict}"
    )

    return {
        "client_snapshot": client_snapshot,
        "verdict":         verdict,
        "overall_flag":    overall_flag,
        "narrative":       narrative,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Section 2: Rationale
# ──────────────────────────────────────────────────────────────────────────────

def generate_rationale(
    allocation: Dict[str, Any],
    risk_output: Dict[str, Any],
    market_signals: Dict[str, Any],
    guardrails_trace: List[Dict[str, str]],
    justification: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Why this allocation was recommended — key drivers explained in advisor language.
    """
    risk_cat   = str(risk_output.get("category", "Moderate")).split("(")[0].strip()
    risk_score = float(risk_output.get("score", 5.0) or 5.0)

    # Allocation breakdown
    alloc_lines: List[str] = []
    if allocation and allocation.get("status") != "LOCKED":
        for k, v in sorted(allocation.items()):
            if isinstance(v, (int, float)):
                alloc_lines.append(f"  • {k.replace('_', ' ').title()}: {safe_round(float(v), 1)}%")

    alloc_str = "\n".join(alloc_lines) if alloc_lines else "  • Allocation locked"

    # Market context
    trend      = str(market_signals.get("market_trend", "neutral")).lower()
    volatility = str(market_signals.get("volatility", "medium")).lower()
    inflation  = str(market_signals.get("inflation_trend", "stable")).lower()
    repo_dir   = str(market_signals.get("repo_rate_direction", "stable")).lower()

    market_context_parts: List[str] = []
    if trend == "bullish":
        market_context_parts.append("markets are trending upward (golden cross signal), supporting equity exposure")
    elif trend == "bearish":
        market_context_parts.append("markets are under pressure (death cross signal), warranting a slightly defensive tilt")
    if volatility == "high":
        market_context_parts.append("VIX is elevated, favouring large-cap stability over high-beta mid/small caps")
    if inflation == "rising":
        market_context_parts.append("rising inflation supports real-asset exposure (equity + gold)")
    if repo_dir == "falling":
        market_context_parts.append("falling repo rates are supportive of debt fund duration")

    market_context = (
        "Current macro context: " + "; ".join(market_context_parts) + "."
        if market_context_parts
        else "Market conditions are broadly neutral — allocation reflects pure risk-profile optimisation."
    )

    # Guardrails applied
    guardrail_notes: List[str] = [
        t["message"] for t in guardrails_trace
        if t.get("step") == "guardrail_application" and "normalized" not in t.get("message", "").lower()
    ]

    # Reasoning chain summary
    chain = justification.get("reasoning_chain", [])
    chain_summary = " → ".join(
        str(step.get("step_name", "")) for step in chain
    ) if chain else "Profile → Risk Scoring → MPT Optimisation → Guardrails → Confidence"

    narrative = (
        f"**Why this allocation?**\n\n"
        f"Your risk profile score of {safe_round(risk_score, 1)}/10 classifies you as **{risk_cat}**. "
        f"The Mean-Variance Optimisation engine then identified the asset mix that maximises "
        f"expected returns for your risk tolerance, subject to structural diversification bounds.\n\n"
        f"**Portfolio Allocation:**\n{alloc_str}\n\n"
        f"**Market Context:** {market_context}\n\n"
    )
    if guardrail_notes:
        narrative += (
            f"**Safety Adjustments Applied:**\n"
            + "\n".join(f"  • {n}" for n in guardrail_notes)
            + "\n\n"
        )
    narrative += f"**Decision Flow:** {chain_summary}"

    return {
        "risk_profile_summary":  f"{risk_cat} (Score: {safe_round(risk_score, 1)}/10)",
        "allocation_breakdown":  alloc_lines,
        "market_context":        market_context,
        "guardrails_applied":    guardrail_notes,
        "decision_flow":         chain_summary,
        "trade_offs":            justification.get("trade_offs", []),
        "narrative":             narrative,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Section 3: Risks
# ──────────────────────────────────────────────────────────────────────────────

def generate_risks(
    profile: Dict[str, Any],
    stress_test: Dict[str, Any],
    confidence: Dict[str, Any],
    justification: Dict[str, Any],
) -> Dict[str, Any]:
    """
    What could go wrong — stress scenarios + edge-case risks in plain language.
    """
    conf_pct = safe_round(float(confidence.get("display_confidence_pct", 0.0) or 0.0), 1)
    band     = str(confidence.get("band", "medium")).upper()

    # Stress test outcomes
    stress_narratives: List[Dict[str, str]] = []
    for scenario_key, scenario_data in stress_test.items():
        if not isinstance(scenario_data, dict):
            continue
        severity    = str(scenario_data.get("severity", "LOW")).upper()
        description = str(scenario_data.get("description", scenario_key.replace("_", " ").title()))
        impact      = scenario_data.get("corpus_impact_pct", scenario_data.get("impact_pct", None))

        impact_str = (
            f"Estimated corpus impact: {safe_round(float(impact) * 100, 1)}%"
            if impact is not None else "Impact: under assessment"
        )

        plain_name = scenario_key.replace("_", " ").title()
        stress_narratives.append({
            "scenario":  plain_name,
            "severity":  severity,
            "impact":    impact_str,
            "narrative": (
                f"**{plain_name}** ({severity} severity): {description}. {impact_str}. "
                + {
                    "HIGH":   "This scenario materially threatens goal achievement — maintain liquidity buffer.",
                    "MEDIUM": "Manageable with a longer horizon; avoid panic-selling during this phase.",
                    "LOW":    "Minor disruption; stay the course with your SIP.",
                }.get(severity, "Monitor and review if this scenario materialises.")
            ),
        })

    # Edge-case risks from justification
    edge_cases = justification.get("edge_cases_applied", [])

    # Overall risk narrative
    risk_intro = (
        f"Your plan has a composite success confidence of **{conf_pct}%** ({band} band). "
        "Below are the key risk factors and scenarios you should be aware of:"
    )

    if not stress_narratives and not edge_cases:
        risk_body = "No significant stress risks identified for the current profile and allocation."
    else:
        risk_body = risk_intro

    return {
        "confidence_summary":  f"{conf_pct}% ({band} band)",
        "stress_scenarios":    stress_narratives,
        "profile_risk_flags":  edge_cases,
        "narrative":           risk_body,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Section 4: Alternatives
# ──────────────────────────────────────────────────────────────────────────────

def generate_alternatives_section(
    justification: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Why this recommendation beats the alternatives — structured comparison.
    """
    alternatives = justification.get("alternatives_considered", [])
    trade_offs   = justification.get("trade_offs", [])

    if not alternatives:
        return {
            "alternatives": [],
            "trade_offs":   trade_offs,
            "narrative":    "No alternative strategies were evaluated — profile uniquely suited to current recommendation.",
        }

    alt_lines: List[str] = []
    for alt in alternatives:
        alt_lines.append(
            f"**{alt.get('strategy', 'Alternative')}**: "
            f"{alt.get('description', '')} — "
            f"Not selected because: {alt.get('why_rejected', 'did not fit profile.')}"
        )

    narrative = (
        "**Alternatives Considered:**\n\n"
        + "\n\n".join(alt_lines)
        + "\n\n**Conclusion:** The recommended strategy was selected because it optimally "
        "balances return potential, risk alignment, liquidity, and affordability for "
        "this specific client profile."
    )

    return {
        "alternatives": alternatives,
        "trade_offs":   trade_offs,
        "narrative":    narrative,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Section 5: SIP Illustrations
# ──────────────────────────────────────────────────────────────────────────────

def generate_sip_illustrations(
    risk_category: str,
    horizons: Optional[List[float]] = None,
    sip_amounts: Optional[List[float]] = None,
) -> Dict[str, Any]:
    """
    Build SIP projection table for multiple monthly amounts and horizons.

    Returns rows ready for tabular rendering or PDF export.
    """
    norm_cat = _normalise_risk(risk_category)
    rate     = _SIP_ILLUSTRATION_RETURNS.get(norm_cat, 0.10)

    default_horizons = horizons or [5.0, 10.0, 15.0, 20.0]
    default_amounts  = sip_amounts or [1000.0, 2500.0, 5000.0, 10000.0, 25000.0]

    rows: List[Dict[str, Any]] = []
    for sip in default_amounts:
        row: Dict[str, Any] = {
            "monthly_sip":    _format_inr(sip),
            "monthly_sip_raw": sip,
        }
        for h in default_horizons:
            fv            = _sip_future_value(sip, rate, h)
            invested      = sip * h * 12
            gain          = fv - invested
            row[f"{int(h)}yr_value"]    = _format_inr(fv)
            row[f"{int(h)}yr_invested"] = _format_inr(invested)
            row[f"{int(h)}yr_gain"]     = _format_inr(gain)
        rows.append(row)

    return {
        "assumed_annual_return": f"{rate * 100:.0f}%",
        "risk_category":         risk_category,
        "horizons_years":        default_horizons,
        "table":                 rows,
        "disclaimer":            (
            f"Returns assumed at {rate * 100:.0f}% p.a. compounded monthly. "
            "Actual returns are not guaranteed and will vary with market conditions."
        ),
    }


# ──────────────────────────────────────────────────────────────────────────────
# Fund-Level Scheme Rationale (Why This Category)
# ──────────────────────────────────────────────────────────────────────────────

def generate_scheme_rationale(
    funds: List[Dict[str, Any]],
    allocation: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    For each recommended fund/category, build a scheme rationale block
    similar to the "WHY – FLEXI CAP FUND" section in the client sample deck.
    """
    rationales: List[Dict[str, Any]] = []

    for fund in funds:
        name         = str(fund.get("name", "Fund"))
        category     = str(fund.get("category", ""))
        risk         = str(fund.get("risk", "Moderate")).split("(")[0].strip()
        weight       = float(fund.get("allocation_weight", 0.0))
        ret_1y       = float(fund.get("1y", 0.0))
        ret_3y       = float(fund.get("3y", 0.0))
        ret_5y       = float(fund.get("5y", 0.0))
        market_reason= str(fund.get("market_reason", fund.get("reason", "")))
        confidence   = str(fund.get("confidence", "Medium"))
        score        = float(fund.get("score", 0.0))

        # Performance table for this fund
        perf_table = {
            "1_year":  f"{safe_round(ret_1y, 2)}%",
            "3_year":  f"{safe_round(ret_3y, 2)}%",
            "5_year":  f"{safe_round(ret_5y, 2)}%" if ret_5y else "N/A",
        }

        # Why this category
        category_why_map = {
            "large cap": (
                "Large-cap funds invest in the top 100 companies by market capitalisation. "
                "They offer stability, liquidity, and lower drawdown — ideal as the core "
                "equity holding in a diversified portfolio."
            ),
            "flexi": (
                "Flexi-cap funds have the freedom to invest across all market capitalisations. "
                "The fund manager can shift dynamically between large, mid, and small caps "
                "based on market opportunities — delivering active alpha while managing downside."
            ),
            "mid cap": (
                "Mid-cap funds target companies ranked 101–250 by market cap — the sweet spot "
                "of growth potential. They offer higher upside than large caps with lower risk "
                "than small caps, suited for growth-oriented investors."
            ),
            "small cap": (
                "Small-cap funds invest in emerging businesses below the top 250 companies. "
                "They carry higher volatility but have historically generated the strongest "
                "long-term compounding — best held for 7+ years."
            ),
            "debt": (
                "Debt funds invest in government securities, corporate bonds, and money-market "
                "instruments. They provide stable, predictable returns with capital safety — "
                "the stabiliser in a balanced portfolio."
            ),
            "gold": (
                "Gold funds provide exposure to gold prices without physical storage. "
                "Gold historically moves inversely to equities, reducing portfolio volatility "
                "and acting as a hedge during inflationary or geopolitical stress."
            ),
            "hybrid": (
                "Hybrid funds combine equity and debt in a single vehicle. "
                "They offer built-in rebalancing, lower volatility than pure equity, "
                "and a simpler portfolio for moderate-risk investors."
            ),
        }

        cat_lower = category.lower()
        why_category = next(
            (v for k, v in category_why_map.items() if k in cat_lower),
            f"{category} exposure aligns with the portfolio's risk-return target for this profile."
        )

        rationales.append({
            "fund_name":        name,
            "category":         category,
            "allocation_pct":   safe_round(weight, 1),
            "ai_score":         safe_round(score, 1),
            "confidence":       confidence,
            "why_category":     why_category,
            "why_now":          market_reason,
            "performance":      perf_table,
            "risk_note":        (
                f"Risk level: {risk}. "
                "Past performance does not guarantee future returns. "
                "Stay invested through full market cycles for best outcomes."
            ),
        })

    return rationales


# ──────────────────────────────────────────────────────────────────────────────
# Full Advisory Report
# ──────────────────────────────────────────────────────────────────────────────

def generate_full_advisory_report(
    profile: Dict[str, Any],
    risk_output: Dict[str, Any],
    goals: List[Dict[str, Any]],
    allocation: Dict[str, Any],
    funds: List[Dict[str, Any]],
    confidence: Dict[str, Any],
    stress_test: Dict[str, Any],
    financial_health: Dict[str, Any],
    market_signals: Dict[str, Any],
    guardrails_trace: List[Dict[str, str]],
    affordability: Dict[str, Any],
    justification: Dict[str, Any],
    advisor_name: Optional[str] = None,
    firm_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Assemble the complete advisor-style advisory report.

    This is the top-level function consumed by the orchestrator.
    All sections are independently addressable for PDF/PPT rendering.
    """
    risk_cat = str(risk_output.get("category", "Moderate")).split("(")[0].strip()

    summary_section      = generate_summary(profile, risk_output, goals, affordability, financial_health)
    rationale_section    = generate_rationale(allocation, risk_output, market_signals, guardrails_trace, justification)
    risks_section        = generate_risks(profile, stress_test, confidence, justification)
    alternatives_section = generate_alternatives_section(justification)
    sip_illustrations    = generate_sip_illustrations(
        risk_cat,
        sip_amounts=[
            float(affordability.get("recommended_sip", 5000.0)),
            float(affordability.get("recommended_sip", 5000.0)) * 2,
            float(affordability.get("recommended_sip", 5000.0)) * 0.5,
        ],
    )
    scheme_rationales    = generate_scheme_rationale(funds, allocation)

    report = {
        "report_version":     "1.0",
        "sections": {
            "summary":          summary_section,
            "rationale":        rationale_section,
            "risks":            risks_section,
            "alternatives":     alternatives_section,
            "sip_illustrations": sip_illustrations,
            "scheme_rationales": scheme_rationales,
        },
        "disclaimer": _DISCLAIMER_TEXT,
        "contact": {
            "advisor":   advisor_name or "Your Financial Advisor",
            "firm":      firm_name or "",
        },
        "plain_text_report": _render_plain_text(
            summary_section, rationale_section, risks_section,
            alternatives_section, sip_illustrations, scheme_rationales,
            advisor_name, firm_name
        ),
    }

    return report


def _render_plain_text(
    summary: Dict[str, Any],
    rationale: Dict[str, Any],
    risks: Dict[str, Any],
    alternatives: Dict[str, Any],
    sip_illus: Dict[str, Any],
    scheme_rationales: List[Dict[str, Any]],
    advisor_name: Optional[str],
    firm_name: Optional[str],
) -> str:
    """
    Combine all sections into a single human-readable text report.
    """
    lines: List[str] = []

    lines.append("=" * 70)
    lines.append("                  INVESTMENT ADVISORY REPORT")
    if firm_name:
        lines.append(f"                  {firm_name}")
    lines.append("=" * 70)
    lines.append("")

    # Summary
    lines.append("1. CLIENT SUMMARY")
    lines.append("-" * 40)
    snapshot = summary.get("client_snapshot", {})
    for k, v in snapshot.items():
        lines.append(f"   {k.replace('_', ' ').title():<25}: {v}")
    lines.append("")
    lines.append(summary.get("narrative", ""))
    lines.append("")

    # Rationale
    lines.append("2. INVESTMENT RATIONALE")
    lines.append("-" * 40)
    lines.append(rationale.get("narrative", ""))
    lines.append("")

    # Scheme Rationales
    if scheme_rationales:
        lines.append("3. RECOMMENDED FUNDS — SCHEME RATIONALE")
        lines.append("-" * 40)
        for sr in scheme_rationales:
            lines.append(f"\n   {sr['fund_name']} ({sr['category']}) — {sr['allocation_pct']}% allocation")
            lines.append(f"   Why this category: {sr['why_category']}")
            lines.append(f"   Why now: {sr['why_now']}")
            perf = sr.get("performance", {})
            lines.append(
                f"   Performance: 1Y {perf.get('1_year','N/A')} | "
                f"3Y {perf.get('3_year','N/A')} | "
                f"5Y {perf.get('5_year','N/A')}"
            )
            lines.append(f"   {sr['risk_note']}")
        lines.append("")

    # SIP Illustrations
    lines.append("4. SIP ILLUSTRATIONS")
    lines.append("-" * 40)
    lines.append(f"   Assumed return: {sip_illus.get('assumed_annual_return','N/A')}")
    table = sip_illus.get("table", [])
    if table:
        horizons = sip_illus.get("horizons_years", [10, 20])
        header = f"   {'SIP/month':<14}" + "".join(f"  {int(h)}yr Value" for h in horizons)
        lines.append(header)
        lines.append("   " + "-" * (len(header) - 3))
        for row in table:
            row_str = f"   {row.get('monthly_sip',''):<14}"
            for h in horizons:
                row_str += f"  {row.get(f'{int(h)}yr_value','N/A'):<12}"
            lines.append(row_str)
    lines.append(f"   * {sip_illus.get('disclaimer','')}")
    lines.append("")

    # Risks
    lines.append("5. RISKS & STRESS SCENARIOS")
    lines.append("-" * 40)
    lines.append(risks.get("narrative", ""))
    for scenario in risks.get("stress_scenarios", []):
        lines.append(f"\n   {scenario.get('narrative','')}")
    for flag in risks.get("profile_risk_flags", []):
        lines.append(f"\n   ⚠ {flag.get('condition','')} — {flag.get('recommendation','')}")
    lines.append("")

    # Alternatives
    lines.append("6. ALTERNATIVES CONSIDERED")
    lines.append("-" * 40)
    lines.append(alternatives.get("narrative", ""))
    lines.append("")

    # Disclaimer
    lines.append("DISCLAIMER")
    lines.append("-" * 40)
    lines.append(_DISCLAIMER_TEXT)
    lines.append("")

    if advisor_name:
        lines.append(f"Prepared by: {advisor_name}" + (f", {firm_name}" if firm_name else ""))

    lines.append("=" * 70)
    return "\n".join(lines)
