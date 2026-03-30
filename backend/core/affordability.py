"""
backend/core/affordability.py
──────────────────────────────
Affordability & Feasibility Engine.

Validates user constraints against investment recommendations and produces
explicit Feasible / Stretch / Not Advisable flags — with fallback strategies
when targets are unrealistic.

Design principles
─────────────────
• Pure functions — no I/O, no randomness.
• Every flag comes with a quantitative rationale.
• Fallback strategies are concrete: revised SIP, revised horizon, or split approach.
• All monetary values in INR (₹).
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

from backend.core.utils import safe_round

# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

# Share of investable surplus that can be comfortably directed to SIPs
_COMFORTABLE_SIP_RATIO = 0.80   # 80 % of surplus is comfortable
_STRETCH_SIP_RATIO     = 0.95   # 95 % of surplus is a stretch
# Below the comfortable ratio → FEASIBLE; above stretch → NOT_ADVISABLE

_MIN_SIP_AMOUNT = 500.0          # ₹500 absolute minimum SIP
_EMERGENCY_RESERVE_MONTHS = 6.0  # recommended emergency buffer in months

# Annual return assumptions by risk profile (pre-inflation)
_RETURN_ASSUMPTIONS: Dict[str, float] = {
    "conservative": 0.07,   # 7 %
    "moderate":     0.10,   # 10 %
    "growth":       0.12,   # 12 %
    "aggressive":   0.14,   # 14 %
}

_INFLATION_RATE = 0.06   # 6 % long-run Indian inflation assumption


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _normalise_risk_category(raw: str) -> str:
    r = raw.lower().split("(")[0].strip()
    if "conserv" in r: return "conservative"
    if "aggress" in r: return "aggressive"
    if "growth" in r or "high" in r: return "growth"
    return "moderate"


def _future_value_of_sip(monthly_sip: float, annual_rate: float, years: float) -> float:
    """Standard SIP future value: FV = SIP × [(1+r)^n − 1] / r × (1+r)"""
    if years <= 0 or monthly_sip <= 0:
        return 0.0
    r = annual_rate / 12.0
    n = years * 12.0
    if r == 0:
        return monthly_sip * n
    return monthly_sip * (((1 + r) ** n - 1) / r) * (1 + r)


def _required_sip_for_target(
    target_corpus: float, annual_rate: float, years: float
) -> float:
    """Reverse SIP formula: monthly SIP needed to reach target."""
    if years <= 0 or target_corpus <= 0:
        return 0.0
    r = annual_rate / 12.0
    n = years * 12.0
    if r == 0:
        return target_corpus / n if n > 0 else 0.0
    denominator = (((1 + r) ** n - 1) / r) * (1 + r)
    if denominator <= 0:
        return 0.0
    return target_corpus / denominator


def _inflation_adjusted_target(nominal_target: float, years: float) -> float:
    """Inflate a today's-value target to its future nominal equivalent."""
    return nominal_target * ((1 + _INFLATION_RATE) ** years)


# ──────────────────────────────────────────────────────────────────────────────
# Core Assessments
# ──────────────────────────────────────────────────────────────────────────────

def compute_sip_capacity(profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate how much the client can realistically invest monthly.

    Returns
    -------
    dict
        ``max_comfortable_sip``  – SIP that leaves breathing room
        ``max_stretch_sip``      – absolute ceiling before it hurts
        ``investable_surplus``   – computed or provided surplus
        ``breakdown``            – line-item breakdown
        ``emergency_reserve_ok`` – whether emergency fund is adequate
    """
    monthly_income   = float(profile.get("monthly_income", 0.0) or 0.0)
    monthly_expenses = float(profile.get("monthly_expenses", 0.0) or 0.0)
    emi_total        = float(profile.get("emi_total", 0.0) or 0.0)
    existing_sips    = float(profile.get("existing_sip_total", 0.0) or 0.0)

    investable_surplus = float(
        profile.get("investable_surplus",
                    profile.get("effective_monthly_savings",
                                max(0.0, monthly_income - monthly_expenses - emi_total))) or 0.0
    )

    # Emergency reserve adequacy
    liquid_reserves  = float(profile.get("liquid_reserves", profile.get("cash_reserves", 0.0)) or 0.0)
    emergency_months = (liquid_reserves / monthly_expenses) if monthly_expenses > 0 else 0.0
    emergency_ok     = emergency_months >= _EMERGENCY_RESERVE_MONTHS

    # If emergency fund is insufficient, reserve a portion of surplus for it
    emergency_monthly_needed = 0.0
    if not emergency_ok and monthly_expenses > 0:
        shortfall_months = max(0.0, _EMERGENCY_RESERVE_MONTHS - emergency_months)
        # Aim to fill gap in 12 months
        emergency_monthly_needed = safe_round((shortfall_months * monthly_expenses) / 12.0, 2)

    available_for_investment = max(0.0, investable_surplus - existing_sips - emergency_monthly_needed)

    max_comfortable = safe_round(available_for_investment * _COMFORTABLE_SIP_RATIO, 0)
    max_stretch     = safe_round(available_for_investment * _STRETCH_SIP_RATIO, 0)

    return {
        "max_comfortable_sip":  max_comfortable,
        "max_stretch_sip":      max_stretch,
        "investable_surplus":   safe_round(investable_surplus, 2),
        "available_for_investment": safe_round(available_for_investment, 2),
        "emergency_reserve_ok": emergency_ok,
        "emergency_monthly_needed": emergency_monthly_needed,
        "breakdown": {
            "monthly_income":         safe_round(monthly_income, 2),
            "monthly_expenses":       safe_round(monthly_expenses, 2),
            "emi_obligations":        safe_round(emi_total, 2),
            "existing_sip_committed": safe_round(existing_sips, 2),
            "emergency_reserve_set_aside": safe_round(emergency_monthly_needed, 2),
            "net_available":          safe_round(available_for_investment, 2),
        },
    }


def assess_sip_feasibility(
    desired_sip: float, capacity: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Map a desired SIP against computed capacity.

    Returns
    -------
    dict
        ``flag``          – "FEASIBLE" | "STRETCH" | "NOT_ADVISABLE"
        ``desired_sip``
        ``max_comfortable``
        ``max_stretch``
        ``gap``           – amount by which desired exceeds comfortable (0 if feasible)
        ``narrative``     – plain-English verdict
    """
    comfortable = float(capacity.get("max_comfortable_sip", 0.0))
    stretch     = float(capacity.get("max_stretch_sip", 0.0))
    desired     = float(desired_sip or 0.0)

    if desired < _MIN_SIP_AMOUNT:
        flag = "NOT_ADVISABLE"
        narrative = (
            f"Desired SIP of ₹{desired:,.0f} is below the minimum viable amount (₹{_MIN_SIP_AMOUNT:,.0f}). "
            "Consider starting with ₹500/month and scaling up."
        )
    elif desired <= comfortable:
        flag = "FEASIBLE"
        narrative = (
            f"A monthly SIP of ₹{desired:,.0f} is comfortably within your capacity "
            f"(max comfortable: ₹{comfortable:,.0f}). This is a sustainable commitment."
        )
    elif desired <= stretch:
        flag = "STRETCH"
        narrative = (
            f"A monthly SIP of ₹{desired:,.0f} is achievable but leaves limited buffer "
            f"(comfortable ceiling: ₹{comfortable:,.0f}). "
            "Any income disruption may make this hard to sustain — ensure 3–6 months reserve first."
        )
    else:
        flag = "NOT_ADVISABLE"
        narrative = (
            f"A monthly SIP of ₹{desired:,.0f} exceeds your safe capacity "
            f"(max stretch: ₹{stretch:,.0f}). "
            "This level of commitment risks financial strain. See fallback strategies below."
        )

    return {
        "flag":            flag,
        "desired_sip":     safe_round(desired, 2),
        "max_comfortable": safe_round(comfortable, 2),
        "max_stretch":     safe_round(stretch, 2),
        "gap":             safe_round(max(0.0, desired - comfortable), 2),
        "narrative":       narrative,
    }


def assess_goal_feasibility(
    goal: Dict[str, Any],
    monthly_sip: float,
    risk_category: str = "moderate",
    existing_corpus: float = 0.0,
) -> Dict[str, Any]:
    """
    Evaluate whether a goal is achievable with the given SIP and risk profile.

    Parameters
    ----------
    goal :
        Dict with ``target_amount`` (today's value), ``horizon_years``, ``goal_type``.
    monthly_sip :
        Monthly SIP allocated to this goal.
    risk_category :
        Used to look up the expected annual return.
    existing_corpus :
        Already accumulated corpus that can be counted toward the goal.

    Returns
    -------
    dict
        ``flag``              – "FEASIBLE" | "STRETCH" | "NOT_ADVISABLE"
        ``target_nominal``    – inflation-adjusted future target
        ``projected_corpus``  – estimated corpus at horizon
        ``shortfall``         – gap (0 if feasible)
        ``required_sip``      – monthly SIP needed to fully meet target
        ``corpus_coverage``   – projected / target ratio
        ``narrative``
    """
    target_today   = float(goal.get("target_amount", 0.0) or 0.0)
    horizon        = float(goal.get("horizon_years", 10.0) or 10.0)
    goal_type      = str(goal.get("goal_type", "custom"))
    norm_category  = _normalise_risk_category(risk_category)
    annual_rate    = _RETURN_ASSUMPTIONS.get(norm_category, 0.10)

    # Inflate target to future value
    target_nominal = _inflation_adjusted_target(target_today, horizon)

    # Project SIP corpus
    sip_fv = _future_value_of_sip(monthly_sip, annual_rate, horizon)

    # Grow existing corpus
    existing_fv = existing_corpus * ((1 + annual_rate) ** horizon)

    projected_corpus = sip_fv + existing_fv
    corpus_coverage  = (projected_corpus / target_nominal) if target_nominal > 0 else 1.0
    shortfall        = max(0.0, target_nominal - projected_corpus)
    required_sip     = _required_sip_for_target(
        max(0.0, target_nominal - existing_fv), annual_rate, horizon
    )

    if corpus_coverage >= 1.0:
        flag = "FEASIBLE"
        narrative = (
            f"Goal '{goal_type.replace('_', ' ').title()}': projected corpus of "
            f"₹{projected_corpus:,.0f} meets the inflation-adjusted target of "
            f"₹{target_nominal:,.0f} over {horizon:.0f} years at {annual_rate*100:.0f}% p.a."
        )
    elif corpus_coverage >= 0.80:
        flag = "STRETCH"
        narrative = (
            f"Goal '{goal_type.replace('_', ' ').title()}': projected corpus of "
            f"₹{projected_corpus:,.0f} covers {corpus_coverage*100:.0f}% of the "
            f"inflation-adjusted target (₹{target_nominal:,.0f}). "
            f"A shortfall of ₹{shortfall:,.0f} remains — increase SIP to "
            f"₹{required_sip:,.0f}/month to fully fund this goal."
        )
    else:
        flag = "NOT_ADVISABLE"
        narrative = (
            f"Goal '{goal_type.replace('_', ' ').title()}': projected corpus of "
            f"₹{projected_corpus:,.0f} covers only {corpus_coverage*100:.0f}% of the "
            f"required ₹{target_nominal:,.0f}. "
            f"Shortfall of ₹{shortfall:,.0f}. Required monthly SIP: ₹{required_sip:,.0f}. "
            "Consider extending the horizon or revising the target."
        )

    return {
        "goal_type":        goal_type,
        "flag":             flag,
        "target_today":     safe_round(target_today, 2),
        "target_nominal":   safe_round(target_nominal, 2),
        "projected_corpus": safe_round(projected_corpus, 2),
        "existing_fv":      safe_round(existing_fv, 2),
        "sip_fv":           safe_round(sip_fv, 2),
        "shortfall":        safe_round(shortfall, 2),
        "required_sip":     safe_round(required_sip, 2),
        "corpus_coverage":  safe_round(corpus_coverage, 4),
        "annual_rate_used": annual_rate,
        "horizon_years":    horizon,
        "narrative":        narrative,
    }


def generate_fallback_strategy(
    goal: Dict[str, Any],
    profile: Dict[str, Any],
    feasibility: Dict[str, Any],
    risk_category: str = "moderate",
) -> Dict[str, Any]:
    """
    When a goal is STRETCH or NOT_ADVISABLE, generate concrete fallback options.

    Returns
    -------
    dict
        ``options``       – list of fallback strategy dicts
        ``recommended``   – index of the best option (0-based)
        ``summary``       – plain-English summary
    """
    flag         = feasibility.get("flag", "FEASIBLE")
    required_sip = float(feasibility.get("required_sip", 0.0))
    horizon      = float(feasibility.get("horizon_years", goal.get("horizon_years", 10.0)))
    target_today = float(goal.get("target_amount", 0.0) or 0.0)
    capacity     = compute_sip_capacity(profile)
    max_comfortable = float(capacity.get("max_comfortable_sip", 0.0))
    norm_category   = _normalise_risk_category(risk_category)
    annual_rate     = _RETURN_ASSUMPTIONS.get(norm_category, 0.10)
    existing_corpus = float(profile.get("existing_corpus", 0.0) or 0.0)

    options: List[Dict[str, Any]] = []

    if flag == "FEASIBLE":
        return {
            "options": [],
            "recommended": -1,
            "summary": "Goal is feasible with current SIP — no fallback required.",
        }

    # Option 1: Extend horizon to make current SIP work
    if max_comfortable > _MIN_SIP_AMOUNT and target_today > 0:
        # Solve for n: FV_target = SIP × [(1+r)^n − 1]/r × (1+r) + existing × (1+r)^n
        # Binary search for required years
        best_years = None
        for candidate_years in range(int(horizon) + 1, int(horizon) + 31):
            fv = _future_value_of_sip(max_comfortable, annual_rate, candidate_years)
            existing_fv = existing_corpus * ((1 + annual_rate) ** candidate_years)
            target_nom  = _inflation_adjusted_target(target_today, candidate_years)
            if fv + existing_fv >= target_nom:
                best_years = candidate_years
                break
        if best_years:
            options.append({
                "strategy":    "extend_horizon",
                "label":       f"Extend investment horizon to {best_years} years",
                "description": (
                    f"Maintain your current SIP of ₹{max_comfortable:,.0f}/month "
                    f"for {best_years} years instead of {horizon:.0f}. "
                    "This allows compounding to close the gap without increasing monthly outgo."
                ),
                "revised_sip":     safe_round(max_comfortable, 2),
                "revised_horizon": best_years,
            })

    # Option 2: Top up SIP to the required amount if it fits within stretch
    if required_sip <= float(capacity.get("max_stretch_sip", 0.0)):
        options.append({
            "strategy":    "increase_sip",
            "label":       f"Increase SIP to ₹{required_sip:,.0f}/month",
            "description": (
                f"Increasing your SIP by ₹{max(0, required_sip - max_comfortable):,.0f}/month "
                f"to ₹{required_sip:,.0f} makes the goal fully achievable within "
                f"{horizon:.0f} years. This is within your stretch capacity."
            ),
            "revised_sip":     safe_round(required_sip, 2),
            "revised_horizon": horizon,
        })

    # Option 3: Revise target downward to what's achievable with comfortable SIP
    achievable = _future_value_of_sip(max_comfortable, annual_rate, horizon)
    if achievable > 0 and target_today > 0:
        revised_target = achievable / ((1 + _INFLATION_RATE) ** horizon)  # back to today's value
        options.append({
            "strategy":    "revise_target",
            "label":       f"Revise goal target to ₹{revised_target:,.0f} (today's value)",
            "description": (
                f"With a SIP of ₹{max_comfortable:,.0f}/month over {horizon:.0f} years, "
                f"you can accumulate ₹{achievable:,.0f} in nominal terms "
                f"(≈ ₹{revised_target:,.0f} in today's value). "
                "Adjusting the target to this amount keeps the plan fully funded."
            ),
            "revised_target": safe_round(revised_target, 2),
            "revised_sip":    safe_round(max_comfortable, 2),
        })

    # Option 4: Split goal — partial lumpsum + SIP hybrid
    lumpsum_available = float(profile.get("existing_corpus", 0.0) or 0.0) * 0.20  # use 20 %
    if lumpsum_available > 0:
        lumpsum_fv  = lumpsum_available * ((1 + annual_rate) ** horizon)
        remaining   = max(0.0, _inflation_adjusted_target(target_today, horizon) - lumpsum_fv)
        hybrid_sip  = _required_sip_for_target(remaining, annual_rate, horizon)
        options.append({
            "strategy":    "lumpsum_plus_sip",
            "label":       f"Deploy ₹{lumpsum_available:,.0f} lumpsum + ₹{hybrid_sip:,.0f}/month SIP",
            "description": (
                f"A one-time deployment of ₹{lumpsum_available:,.0f} from existing corpus, "
                f"combined with a monthly SIP of ₹{hybrid_sip:,.0f}, fully funds the goal. "
                "This reduces the monthly burden significantly."
            ),
            "lumpsum_amount": safe_round(lumpsum_available, 2),
            "revised_sip":    safe_round(hybrid_sip, 2),
            "revised_horizon": horizon,
        })

    recommended = 0 if options else -1
    summary = (
        f"{len(options)} fallback option(s) generated. "
        "Review with client to select the most suitable approach."
    ) if options else "No feasible fallback found — goal may need to be deferred."

    return {
        "options":     options,
        "recommended": recommended,
        "summary":     summary,
    }


def run_affordability_assessment(
    profile: Dict[str, Any],
    goals: List[Dict[str, Any]],
    desired_sip: Optional[float],
    risk_category: str = "moderate",
) -> Dict[str, Any]:
    """
    Full affordability assessment for a client profile.

    Combines SIP capacity, per-goal feasibility, and fallback strategies
    into a single output block consumed by the advisory orchestrator.
    """
    capacity    = compute_sip_capacity(profile)
    desired     = float(desired_sip or capacity.get("max_comfortable_sip", 0.0))
    sip_check   = assess_sip_feasibility(desired, capacity)
    existing_corpus = float(profile.get("existing_corpus", 0.0) or 0.0)

    goal_assessments: List[Dict[str, Any]] = []
    for goal in (goals or []):
        feasibility = assess_goal_feasibility(
            goal, desired, risk_category, existing_corpus
        )
        fallback = generate_fallback_strategy(goal, profile, feasibility, risk_category)
        goal_assessments.append({
            "goal_type":   goal.get("goal_type", "custom"),
            "feasibility": feasibility,
            "fallback":    fallback,
        })

    # Overall feasibility flag: worst-case across all goals
    all_flags = [g["feasibility"]["flag"] for g in goal_assessments]
    if "NOT_ADVISABLE" in all_flags:
        overall_flag = "NOT_ADVISABLE"
    elif "STRETCH" in all_flags:
        overall_flag = "STRETCH"
    else:
        overall_flag = sip_check.get("flag", "FEASIBLE")

    return {
        "overall_flag":      overall_flag,
        "sip_capacity":      capacity,
        "sip_feasibility":   sip_check,
        "goal_assessments":  goal_assessments,
        "recommended_sip":   safe_round(desired, 2),
    }
