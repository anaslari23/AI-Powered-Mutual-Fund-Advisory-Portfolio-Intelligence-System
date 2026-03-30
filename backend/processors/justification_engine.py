"""
backend/processors/justification_engine.py
────────────────────────────────────────────
Deep Justification Engine — every recommendation must include a full
reasoning chain so the advisory output is audit-ready and explainable
to advisors and clients alike.

Each justification block contains:
    reasoning_chain        – ordered steps explaining how we arrived at the output
    factor_contributions   – percentage influence of each major factor
    trade_offs             – what was considered and why it was not chosen
    alternatives_considered – alternative strategies with rejection reasons
    edge_cases_applied     – special rules that fired due to unusual profile conditions

Design principles
─────────────────
• Pure functions — no I/O, no randomness.
• Fully decoupled from engines — receives plain dicts.
• Returns plain dicts — JSON-serialisable.
• Graceful: missing data yields minimal but valid justification.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from backend.core.utils import safe_round

# ──────────────────────────────────────────────────────────────────────────────
# Reasoning Chain
# ──────────────────────────────────────────────────────────────────────────────

def build_reasoning_chain(
    profile: Dict[str, Any],
    risk_output: Dict[str, Any],
    allocation: Dict[str, Any],
    confidence: Dict[str, Any],
    guardrails_trace: List[Dict[str, str]],
    affordability: Dict[str, Any],
) -> List[Dict[str, str]]:
    """
    Produce an ordered, numbered reasoning chain from raw inputs to final allocation.

    Each step has: ``step_number``, ``step_name``, ``input``, ``output``, ``rationale``.
    """
    chain: List[Dict[str, str]] = []

    # Step 1 — Profile Assessment
    age          = int(profile.get("age", 0) or 0)
    income       = float(profile.get("monthly_income", 0.0) or 0.0)
    dependents   = int(profile.get("dependents", 0) or 0)
    savings_rate = (
        float(profile.get("effective_monthly_savings", profile.get("monthly_savings", 0.0)) or 0.0)
        / income * 100.0
    ) if income > 0 else 0.0

    chain.append({
        "step_number": "1",
        "step_name":   "Client Profile Assessment",
        "input":       f"Age: {age}, Monthly Income: ₹{income:,.0f}, Dependents: {dependents}, Savings Rate: {savings_rate:.1f}%",
        "output":      "Profile captured and validated.",
        "rationale":   (
            f"Age {age} determines investment horizon and recovery capacity. "
            f"Income of ₹{income:,.0f}/month sets the investable surplus ceiling. "
            f"{dependents} dependent(s) increase financial responsibility, moderating risk capacity."
        ),
    })

    # Step 2 — Risk Scoring
    risk_score    = float(risk_output.get("score", 5.0) or 5.0)
    risk_category = str(risk_output.get("category", "Moderate")).split("(")[0].strip()
    risk_factors  = risk_output.get("explanation", {}).get("features", risk_output.get("factors", {}))

    top_factor_str = ""
    if isinstance(risk_factors, dict) and risk_factors:
        top = max(risk_factors, key=lambda k: abs(float(risk_factors[k])))
        top_factor_str = f" The dominant factor was '{top}' ({safe_round(float(risk_factors[top]) * 100, 1)}% weight)."

    chain.append({
        "step_number": "2",
        "step_name":   "Risk Profile Scoring",
        "input":       f"Questionnaire answers + profile signals",
        "output":      f"Risk Score: {risk_score}/10 → Category: {risk_category}",
        "rationale":   (
            f"A multi-factor model evaluated age, dependents, savings behaviour, "
            f"drawdown tolerance, and stated preference to produce a score of {risk_score}/10.{top_factor_str} "
            f"This maps to the '{risk_category}' category, defining the equity band for allocation."
        ),
    })

    # Step 3 — Allocation Optimisation
    if allocation and allocation.get("status") != "LOCKED":
        equity_pct = sum(
            float(v) for k, v in allocation.items()
            if isinstance(v, (int, float)) and "equity" in str(k).lower()
        )
        debt_pct = sum(
            float(v) for k, v in allocation.items()
            if isinstance(v, (int, float)) and "debt" in str(k).lower()
        )
        gold_pct = sum(
            float(v) for k, v in allocation.items()
            if isinstance(v, (int, float)) and "gold" in str(k).lower()
        )
        chain.append({
            "step_number": "3",
            "step_name":   "MPT-Based Allocation Optimisation",
            "input":       f"Risk category: {risk_category}, market return/volatility data",
            "output":      f"Equity: {safe_round(equity_pct, 1)}% | Debt: {safe_round(debt_pct, 1)}% | Gold: {safe_round(gold_pct, 1)}%",
            "rationale":   (
                "Mean-Variance Optimisation (Markowitz) maximised Sharpe ratio subject to "
                f"volatility constraints for a {risk_category} profile. "
                "Structural bounds (max 15% gold, max 35% debt) were enforced to prevent "
                "concentration risk."
            ),
        })
    else:
        chain.append({
            "step_number": "3",
            "step_name":   "Allocation — Locked",
            "input":       "Profile indicates investment not currently feasible",
            "output":      "Allocation: LOCKED",
            "rationale":   "Pre-conditions for investment (income, emergency fund, EMI ratio) were not met. Allocation has been locked pending profile improvement.",
        })

    # Step 4 — Guardrails Applied
    guardrail_messages = [
        t["message"] for t in guardrails_trace
        if t.get("step") == "guardrail_application" and t.get("level") in ("HIGH", "CRITICAL")
    ]
    if guardrail_messages:
        chain.append({
            "step_number": "4",
            "step_name":   "Safety Guardrails",
            "input":       "Allocation from Step 3 + profile risk flags",
            "output":      f"{len(guardrail_messages)} guardrail(s) applied",
            "rationale":   (
                "The following safety constraints modified the raw allocation: "
                + "; ".join(guardrail_messages)
                + ". Guardrails protect against over-allocation to risky assets given the client's current financial position."
            ),
        })
    else:
        chain.append({
            "step_number": "4",
            "step_name":   "Safety Guardrails",
            "input":       "Allocation from Step 3",
            "output":      "No guardrails triggered",
            "rationale":   "The optimised allocation already satisfies all safety constraints for this profile.",
        })

    # Step 5 — Confidence & Stress
    band    = str(confidence.get("band", "unknown")).upper()
    conf_pct = safe_round(float(confidence.get("display_confidence_pct", 0.0) or 0.0), 1)
    chain.append({
        "step_number": "5",
        "step_name":   "Goal Confidence Assessment",
        "input":       "Monte Carlo simulation (1,000 runs) × Market Stability × Income Stability",
        "output":      f"Confidence: {conf_pct}% — Band: {band}",
        "rationale":   (
            f"Monte Carlo GBM simulations estimated the probability of reaching the goal corpus. "
            f"This was adjusted by a macro stability multiplier and income stability score, "
            f"yielding a composite confidence of {conf_pct}%. "
            f"Band '{band}' indicates " + {
                "HIGH":    "strong probability of success with current plan.",
                "MEDIUM":  "moderate probability — plan should be monitored.",
                "LOW":     "uncertain success — consider increasing SIP or extending horizon.",
            }.get(band, "confidence level is being assessed.")
        ),
    })

    # Step 6 — Affordability Validation
    overall_flag = str(affordability.get("overall_flag", "FEASIBLE"))
    recommended_sip = float(affordability.get("recommended_sip", 0.0) or 0.0)
    chain.append({
        "step_number": "6",
        "step_name":   "Affordability & Feasibility Check",
        "input":       f"Desired SIP: ₹{recommended_sip:,.0f} vs monthly capacity",
        "output":      f"Flag: {overall_flag}",
        "rationale":   (
            affordability.get("sip_feasibility", {}).get("narrative", "Feasibility assessed against income and obligation data.")
        ),
    })

    return chain


# ──────────────────────────────────────────────────────────────────────────────
# Factor Contributions
# ──────────────────────────────────────────────────────────────────────────────

def build_factor_contributions(
    risk_output: Dict[str, Any],
    allocation: Dict[str, Any],
    confidence: Dict[str, Any],
    guardrails_count: int,
) -> Dict[str, Any]:
    """
    Express percentage contribution of each major factor to the final allocation.

    Returns a dict where values are contribution explanations (not raw %).
    """
    # Risk factors come directly from the risk engine if available
    risk_factors = risk_output.get("explanation", {}).get("features",
                   risk_output.get("factors", {}))

    # Normalise risk factor contributions to 100 %
    rf_contributions: Dict[str, str] = {}
    if isinstance(risk_factors, dict) and risk_factors:
        total_weight = sum(abs(float(v)) for v in risk_factors.values())
        for k, v in risk_factors.items():
            pct = (abs(float(v)) / total_weight * 100.0) if total_weight > 0 else 0.0
            direction = "increased" if float(v) > 0 else "decreased"
            rf_contributions[k] = f"{safe_round(pct, 1)}% influence — {direction} risk score"

    # Confidence breakdown
    mc_prob    = safe_round(float(confidence.get("normalized_probability", 0.0) or 0.0) * 100.0, 1)
    mkt_stab   = safe_round(float(confidence.get("market_stability", 0.0) or 0.0) * 100.0, 1)
    inc_stab   = safe_round(float(confidence.get("income_stability", 0.0) or 0.0) * 100.0, 1)

    # Allocation breakdown summary
    alloc_summary: Dict[str, str] = {}
    if allocation and allocation.get("status") != "LOCKED":
        for k, v in allocation.items():
            if isinstance(v, (int, float)):
                alloc_summary[k] = f"{safe_round(float(v), 1)}% of portfolio"

    return {
        "risk_score_drivers":       rf_contributions or {"note": "Detailed factor breakdown not available"},
        "allocation_breakdown":     alloc_summary,
        "confidence_components": {
            "monte_carlo_probability": f"{mc_prob}% base success probability from 1,000 simulations",
            "market_stability":        f"{mkt_stab}% — macro environment stability multiplier",
            "income_stability":        f"{inc_stab}% — client income reliability multiplier",
        },
        "guardrails_applied": (
            f"{guardrails_count} safety guardrail(s) adjusted the raw allocation"
            if guardrails_count > 0 else "No guardrails required — allocation is unconstrained"
        ),
    }


# ──────────────────────────────────────────────────────────────────────────────
# Trade-Offs
# ──────────────────────────────────────────────────────────────────────────────

def build_trade_offs(
    profile: Dict[str, Any],
    allocation: Dict[str, Any],
    risk_category: str,
    affordability: Dict[str, Any],
) -> List[Dict[str, str]]:
    """
    Document trade-offs that were consciously made in deriving this recommendation.
    """
    trade_offs: List[Dict[str, str]] = []
    norm_cat = risk_category.lower().split("(")[0].strip()

    # Trade-off 1: Growth vs Safety
    if "conserv" in norm_cat:
        trade_offs.append({
            "dimension":  "Return Potential vs Capital Safety",
            "chosen":     "Capital Safety (lower equity, higher debt/gold weight)",
            "rejected":   "Higher equity exposure for better long-term returns",
            "reason":     (
                "Given conservative risk tolerance, protecting capital takes precedence. "
                "Higher equity would offer better inflation-beating returns but introduces "
                "drawdown risk that conflicts with the client's stated tolerance."
            ),
        })
    elif "aggress" in norm_cat or "growth" in norm_cat:
        trade_offs.append({
            "dimension":  "Return Potential vs Capital Safety",
            "chosen":     "Higher equity exposure for long-term wealth creation",
            "rejected":   "Balanced or conservative allocation",
            "reason":     (
                "The client's aggressive risk tolerance and long horizon justify higher equity. "
                "A balanced approach would limit upside unnecessarily and underutilise "
                "the client's capacity to ride out volatility."
            ),
        })
    else:
        trade_offs.append({
            "dimension":  "Return Potential vs Capital Safety",
            "chosen":     "Balanced allocation (moderate equity + debt mix)",
            "rejected":   "All-equity or all-debt extremes",
            "reason":     (
                "A moderate profile calls for balanced growth — equity for inflation-beating "
                "returns, debt for stability. Extremes in either direction would create "
                "misalignment with the client's risk capacity."
            ),
        })

    # Trade-off 2: SIP vs Lumpsum
    overall_flag = str(affordability.get("overall_flag", "FEASIBLE"))
    if overall_flag in ("STRETCH", "NOT_ADVISABLE"):
        trade_offs.append({
            "dimension":  "SIP vs Lumpsum Deployment",
            "chosen":     "SIP (systematic monthly investment)",
            "rejected":   "Large lumpsum deployment",
            "reason":     (
                "Affordability constraints make a large lumpsum risky — it would deplete "
                "liquidity reserves. SIP averages purchase cost, reduces timing risk, and "
                "fits within the sustainable monthly budget."
            ),
        })
    else:
        trade_offs.append({
            "dimension":  "SIP vs Lumpsum Deployment",
            "chosen":     "SIP for ongoing allocation; lumpsum eligible for existing idle corpus",
            "rejected":   "Deferring all investment until a larger corpus is accumulated",
            "reason":     (
                "Starting SIP immediately captures market compounding and builds the "
                "investment habit. Idle corpus in savings accounts earns below-inflation "
                "returns — deploying it via lumpsum into debt/liquid funds is more efficient."
            ),
        })

    # Trade-off 3: Gold allocation
    if allocation and allocation.get("status") != "LOCKED":
        gold_pct = sum(
            float(v) for k, v in allocation.items()
            if isinstance(v, (int, float)) and "gold" in str(k).lower()
        )
        if gold_pct > 0:
            trade_offs.append({
                "dimension":  "Gold Allocation",
                "chosen":     f"{safe_round(gold_pct, 1)}% gold for inflation hedge",
                "rejected":   "Zero gold allocation",
                "reason":     (
                    f"A {safe_round(gold_pct, 1)}% gold allocation provides macro insurance "
                    "against inflation and geopolitical shocks. Gold has historically shown "
                    "low correlation to equities, improving portfolio Sharpe ratio. "
                    "Exceeding 15% was rejected as gold yields no dividends and can drag returns."
                ),
            })

    # Trade-off 4: Debt duration
    if "conserv" in norm_cat or "moderate" in norm_cat:
        trade_offs.append({
            "dimension":  "Debt Fund Duration",
            "chosen":     "Short-to-medium duration debt for capital stability",
            "rejected":   "Long-duration bonds for higher yield",
            "reason":     (
                "Long-duration bonds carry significant interest-rate risk — a 1% rate rise "
                "can erase 5–8% NAV. For this profile, capital stability matters more than "
                "chasing an extra 1–2% yield on debt."
            ),
        })

    return trade_offs


# ──────────────────────────────────────────────────────────────────────────────
# Alternatives Considered
# ──────────────────────────────────────────────────────────────────────────────

def build_alternatives_considered(
    risk_category: str,
    allocation: Dict[str, Any],
    profile: Dict[str, Any],
) -> List[Dict[str, str]]:
    """
    Document alternative strategies that were evaluated but not recommended.
    """
    norm_cat = risk_category.lower().split("(")[0].strip()
    age      = int(profile.get("age", 35) or 35)
    alternatives: List[Dict[str, str]] = []

    # Alternative 1: 100% equity
    alternatives.append({
        "strategy":     "100% Equity Portfolio",
        "description":  "Place all investable surplus into diversified equity funds.",
        "why_rejected": (
            "Maximum returns but maximum drawdown risk. A 30–40% market correction would "
            "severely impact corpus. Suitable only for investors who can withstand 5+ years "
            "of underperformance — not appropriate without explicit confirmation of "
            "very high risk tolerance and 10+ year horizon."
        ),
    })

    # Alternative 2: FD / traditional savings
    alternatives.append({
        "strategy":     "Fixed Deposits / Traditional Savings",
        "description":  "Park all surplus in bank FDs or savings accounts.",
        "why_rejected": (
            f"At the current inflation rate of ~6%, FD returns of 6.5–7.5% yield "
            "only 0.5–1.5% real return. Over {age < 45 and '10–20' or '5–10'} years, "
            "this approach cannot generate meaningful wealth — the capital is preserved "
            "in nominal terms but eroded in real terms."
        ),
    })

    # Alternative 3: Sector/Thematic concentration
    alternatives.append({
        "strategy":     "Thematic / Sectoral Concentration",
        "description":  "Invest entirely in a high-growth theme (e.g., technology, ESG).",
        "why_rejected": (
            "Thematic funds carry concentration risk — if the theme underperforms, "
            "the entire portfolio suffers. Diversified funds with tactical sector exposure "
            "offer better risk-adjusted returns without single-theme dependency."
        ),
    })

    # Alternative 4: Real estate (if high savings ratio)
    effective_savings = float(
        profile.get("effective_monthly_savings", profile.get("monthly_savings", 0.0)) or 0.0
    )
    monthly_income = float(profile.get("monthly_income", 1.0) or 1.0)
    if effective_savings / monthly_income > 0.30:
        alternatives.append({
            "strategy":     "Real Estate Investment",
            "description":  "Use surplus for property purchase or REITs.",
            "why_rejected": (
                "Direct real estate requires large capital outlay, has low liquidity, "
                "and generates rental yields of only 2–3%. REITs are viable but already "
                "implicitly captured through debt and hybrid allocation. "
                "Mutual funds offer better liquidity, transparency, and tax efficiency."
            ),
        })

    # Alternative 5: Only debt/hybrid (for aggressive profiles)
    if "aggress" in norm_cat or "growth" in norm_cat:
        alternatives.append({
            "strategy":     "Conservative Debt-Heavy Portfolio",
            "description":  "Allocate 70%+ to debt instruments for capital safety.",
            "why_rejected": (
                f"Given age {age} and aggressive risk profile, a debt-heavy portfolio "
                "would generate returns below inflation over the long run. "
                "The client has the time and stated risk capacity to ride equity cycles — "
                "a conservative allocation would significantly underutilise this advantage."
            ),
        })

    return alternatives


# ──────────────────────────────────────────────────────────────────────────────
# Edge Cases
# ──────────────────────────────────────────────────────────────────────────────

def identify_edge_cases(
    profile: Dict[str, Any],
    guardrails_trace: List[Dict[str, str]],
    affordability: Dict[str, Any],
    stress_test: Dict[str, Any],
) -> List[Dict[str, str]]:
    """
    Identify and document special conditions that modified standard recommendations.
    """
    edge_cases: List[Dict[str, str]] = []

    # No life cover
    if float(profile.get("life_cover", 0.0) or 0.0) == 0:
        edge_cases.append({
            "condition":    "No Life Insurance Coverage",
            "impact":       "Equity allocation capped at a reduced ceiling",
            "explanation":  (
                "Without life insurance, the family's financial security is at risk in an "
                "adverse event. Until adequate life cover is in place, equity exposure is "
                "moderated to ensure the investable corpus is not entirely at market risk."
            ),
            "recommendation": "Purchase term insurance of at least 10× annual income before increasing equity.",
        })

    # Low emergency fund
    emer_months = float(profile.get("emergency_fund_months", 0.0) or 0.0)
    if emer_months < 3.0:
        edge_cases.append({
            "condition":    f"Insufficient Emergency Fund ({safe_round(emer_months, 1)} months)",
            "impact":       "Investment amounts moderated; emergency reserve set-aside applied",
            "explanation":  (
                "An emergency fund below 3 months means the client may be forced to "
                "liquidate investments at a loss during a financial shock. "
                "A portion of monthly surplus is therefore directed to build this buffer first."
            ),
            "recommendation": "Build a 3–6 month emergency reserve in a liquid fund before increasing SIP.",
        })

    # High EMI ratio
    emi_ratio = float(profile.get("emi_ratio", 0.0) or 0.0)
    if emi_ratio > 0.40:
        edge_cases.append({
            "condition":    f"Elevated EMI-to-Income Ratio ({safe_round(emi_ratio * 100, 1)}%)",
            "impact":       "Investment SIP reduced; debt reduction prioritised",
            "explanation":  (
                f"With {safe_round(emi_ratio * 100, 1)}% of income committed to EMIs, "
                "the margin for investment is narrow. Defaults on EMI obligations are "
                "more damaging than investment underperformance."
            ),
            "recommendation": "Prioritise prepaying high-interest debt before scaling up investments.",
        })

    # Stress scenario HIGH severity
    crash = stress_test.get("market_crash", {})
    if str(crash.get("severity", "")).upper() == "HIGH":
        edge_cases.append({
            "condition":    "High-Severity Market Crash Stress Outcome",
            "impact":       "Composite confidence reduced; portfolio defensiveness increased",
            "explanation":  (
                "Stress testing revealed that a severe market correction scenario materially "
                "threatens goal achievement. Confidence has been adjusted downward and "
                "the allocation is tilted slightly more defensively than the raw MPT output."
            ),
            "recommendation": "Consider increasing debt allocation by 5–10% as an additional buffer.",
        })

    # NOT_ADVISABLE flag
    if str(affordability.get("overall_flag", "")).upper() == "NOT_ADVISABLE":
        edge_cases.append({
            "condition":    "Investment Not Currently Advisable",
            "impact":       "Allocation locked; fallback strategies provided",
            "explanation":  (
                "The combination of income, expenses, and obligations does not leave "
                "sufficient surplus for sustainable investment at the desired level. "
                "Proceeding would risk financial strain."
            ),
            "recommendation": "Review fallback strategies in the affordability section. Focus on income growth or expense reduction first.",
        })

    return edge_cases


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

def build_full_justification(
    profile: Dict[str, Any],
    risk_output: Dict[str, Any],
    allocation: Dict[str, Any],
    confidence: Dict[str, Any],
    guardrails_trace: List[Dict[str, str]],
    affordability: Dict[str, Any],
    stress_test: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Assemble the complete justification block for an advisory output.

    Returns
    -------
    dict with keys:
        ``reasoning_chain``         – ordered step-by-step decision log
        ``factor_contributions``    – quantified influence of each major factor
        ``trade_offs``              – trade-offs consciously made
        ``alternatives_considered`` – alternatives evaluated and rejected
        ``edge_cases_applied``      – special conditions that triggered
    """
    risk_category    = str(risk_output.get("category", "Moderate")).split("(")[0].strip()
    guardrails_count = sum(
        1 for t in guardrails_trace
        if t.get("step") == "guardrail_application" and t.get("level") in ("HIGH", "CRITICAL")
    )

    return {
        "reasoning_chain": build_reasoning_chain(
            profile, risk_output, allocation, confidence, guardrails_trace, affordability
        ),
        "factor_contributions": build_factor_contributions(
            risk_output, allocation, confidence, guardrails_count
        ),
        "trade_offs": build_trade_offs(
            profile, allocation, risk_category, affordability
        ),
        "alternatives_considered": build_alternatives_considered(
            risk_category, allocation, profile
        ),
        "edge_cases_applied": identify_edge_cases(
            profile, guardrails_trace, affordability, stress_test
        ),
    }
