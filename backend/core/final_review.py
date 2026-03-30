"""
backend/core/final_review.py
─────────────────────────────
Mandatory Final Review System — runs before any advisory output is returned.

Every advisory output MUST pass through run_final_review() before being
sent to the caller. If validation fails the orchestrator regenerates with
conservative fallback guardrails; the result always carries a
``final_review_status`` and ``validation_notes`` block.

Design principles
─────────────────
• Pure function — no I/O, no randomness, deterministic for identical inputs.
• Fail-open: a review failure never crashes the system; it returns structured
  feedback and triggers regeneration.
• Three severity levels: PASS / WARN / FAIL.
  – PASS  → output is clean; emit as-is.
  – WARN  → output has advisory notes; emit with notes attached.
  – FAIL  → output has structural/logical problems; regeneration required.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from backend.core.utils import safe_round

# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

_RISK_CATEGORY_EQUITY_BANDS: Dict[str, Tuple[float, float]] = {
    "conservative": (0.0, 40.0),
    "moderate":     (25.0, 65.0),
    "growth":       (45.0, 80.0),
    "aggressive":   (55.0, 100.0),
}

_ALLOCATION_SUM_TOLERANCE: float = 2.0          # % deviation allowed
_MIN_CONFIDENCE_THRESHOLD: float = 0.05         # 5 % minimum composite confidence
_MAX_EMI_RATIO_WARN: float = 0.50               # warn if EMI > 50 % of income
_MAX_EMI_RATIO_FAIL: float = 0.70               # fail if EMI > 70 % of income
_MIN_EMERGENCY_MONTHS_WARN: float = 3.0
_STRESS_HIGH_SEVERITY_CONFIDENCE_CAP: float = 0.60


# ──────────────────────────────────────────────────────────────────────────────
# Individual check functions
# Each returns (passed: bool, severity: str, message: str)
# severity ∈ {"PASS", "WARN", "FAIL"}
# ──────────────────────────────────────────────────────────────────────────────

def _check_allocation_sum(allocation: Dict[str, Any]) -> Tuple[bool, str, str]:
    """Allocation weights must sum to ~100 %."""
    if not allocation or allocation.get("status") == "LOCKED":
        return True, "PASS", "Allocation is locked — sum check skipped."
    numeric = {k: float(v) for k, v in allocation.items() if isinstance(v, (int, float))}
    total = sum(numeric.values())
    if abs(total - 100.0) <= _ALLOCATION_SUM_TOLERANCE:
        return True, "PASS", f"Allocation sums to {safe_round(total, 2)} % — within tolerance."
    return False, "FAIL", (
        f"Allocation sum is {safe_round(total, 2)} % — expected 100 %. "
        "Output cannot be issued; recalibration required."
    )


def _check_risk_equity_alignment(
    allocation: Dict[str, Any], risk_category: str
) -> Tuple[bool, str, str]:
    """Equity exposure must sit within the band for the declared risk category."""
    if not allocation or allocation.get("status") == "LOCKED":
        return True, "PASS", "Allocation locked — equity alignment check skipped."

    equity_total = sum(
        float(v)
        for k, v in allocation.items()
        if isinstance(v, (int, float)) and "equity" in str(k).lower()
    )

    category_key = str(risk_category).lower().split("(")[0].strip()
    # Normalise common variants
    if "conserv" in category_key:
        category_key = "conservative"
    elif "aggress" in category_key:
        category_key = "aggressive"
    elif "growth" in category_key or "high" in category_key:
        category_key = "growth"
    else:
        category_key = "moderate"

    lo, hi = _RISK_CATEGORY_EQUITY_BANDS.get(category_key, (0.0, 100.0))

    if lo <= equity_total <= hi:
        return True, "PASS", (
            f"Equity exposure {safe_round(equity_total, 1)} % is within the "
            f"{category_key.title()} band [{lo}–{hi} %]."
        )
    severity = "WARN" if abs(equity_total - hi) <= 10 or abs(equity_total - lo) <= 10 else "FAIL"
    return False, severity, (
        f"Equity exposure {safe_round(equity_total, 1)} % is outside the "
        f"{category_key.title()} band [{lo}–{hi} %]. "
        "Allocation may not match declared risk tolerance."
    )


def _check_financial_feasibility(profile: Dict[str, Any]) -> Tuple[bool, str, str]:
    """Investable surplus must be positive for any investment to be recommended."""
    monthly_income = float(profile.get("monthly_income", 0.0) or 0.0)
    monthly_expenses = float(profile.get("monthly_expenses", 0.0) or 0.0)
    emi_total = float(profile.get("emi_total", 0.0) or 0.0)
    investable_surplus = float(
        profile.get("investable_surplus", profile.get("effective_monthly_savings", 0.0)) or 0.0
    )

    if investable_surplus <= 0:
        computed = monthly_income - monthly_expenses - emi_total
        if computed <= 0:
            return False, "FAIL", (
                "No investable surplus detected. Monthly income does not cover "
                "expenses and EMI obligations — investment is not feasible."
            )
        return True, "WARN", (
            f"Investable surplus not explicitly provided. "
            f"Estimated at ₹{safe_round(computed, 0):,.0f}/month from income minus expenses."
        )

    return True, "PASS", f"Investable surplus of ₹{safe_round(investable_surplus, 0):,.0f}/month confirmed."


def _check_emi_ratio(profile: Dict[str, Any]) -> Tuple[bool, str, str]:
    """EMI burden should not crowd out investment capacity."""
    emi_ratio = float(profile.get("emi_ratio", 0.0) or 0.0)
    if emi_ratio >= _MAX_EMI_RATIO_FAIL:
        return False, "FAIL", (
            f"EMI-to-income ratio is {safe_round(emi_ratio * 100, 1)} % — critically high. "
            "Investment recommendation blocked until debt is reduced."
        )
    if emi_ratio >= _MAX_EMI_RATIO_WARN:
        return False, "WARN", (
            f"EMI-to-income ratio is {safe_round(emi_ratio * 100, 1)} % — elevated. "
            "Investment amounts should be moderated; debt reduction is a priority."
        )
    return True, "PASS", f"EMI ratio {safe_round(emi_ratio * 100, 1)} % is within acceptable limits."


def _check_emergency_fund(profile: Dict[str, Any]) -> Tuple[bool, str, str]:
    """Warn if emergency fund coverage is insufficient."""
    months = float(profile.get("emergency_fund_months", 0.0) or 0.0)
    if months < _MIN_EMERGENCY_MONTHS_WARN:
        return False, "WARN", (
            f"Emergency fund covers only {safe_round(months, 1)} months of expenses. "
            "Recommend building 3–6 months reserve before large equity commitment."
        )
    return True, "PASS", f"Emergency fund covers {safe_round(months, 1)} months — adequate."


def _check_confidence_score(confidence_score: Dict[str, Any]) -> Tuple[bool, str, str]:
    """Composite confidence must exceed minimum threshold."""
    if not confidence_score:
        return True, "WARN", "Confidence score not computed — feasibility cannot be assessed."
    composite = float(confidence_score.get("composite_confidence", 0.0) or 0.0)
    band = str(confidence_score.get("band", "low"))
    if composite < _MIN_CONFIDENCE_THRESHOLD:
        return False, "FAIL", (
            f"Composite confidence is critically low at {safe_round(composite * 100, 1)} %. "
            "Goal achievement probability is near zero — review inputs and goals."
        )
    if band == "low":
        return False, "WARN", (
            f"Confidence band is LOW ({safe_round(composite * 100, 1)} %). "
            "Goal success is uncertain; consider extending horizon or increasing SIP."
        )
    return True, "PASS", (
        f"Confidence band is {band.upper()} at {safe_round(composite * 100, 1)} %."
    )


def _check_stress_consistency(
    stress_test: Dict[str, Any], confidence_score: Dict[str, Any]
) -> Tuple[bool, str, str]:
    """HIGH-severity stress outcome should depress confidence — warn if inconsistent."""
    if not stress_test or not confidence_score:
        return True, "PASS", "Stress/confidence cross-check skipped — data unavailable."

    crash = stress_test.get("market_crash", {})
    severity = str(crash.get("severity", "LOW")).upper()
    composite = float(confidence_score.get("composite_confidence", 1.0) or 1.0)

    if severity == "HIGH" and composite > _STRESS_HIGH_SEVERITY_CONFIDENCE_CAP:
        return False, "WARN", (
            f"High-severity stress scenario detected, but composite confidence "
            f"({safe_round(composite * 100, 1)} %) appears too high. "
            "Confidence may not fully reflect downside risk."
        )
    return True, "PASS", "Stress outcome and confidence level are consistent."


def _check_funds_present(
    investment_allowed: bool, funds: List[Any]
) -> Tuple[bool, str, str]:
    """If investment is allowed, at least one fund recommendation must exist."""
    if not investment_allowed:
        return True, "PASS", "Investment blocked — fund presence check skipped."
    if not funds:
        return False, "WARN", (
            "Investment is permitted but no fund recommendations were generated. "
            "Check fund universe availability and market signal pipeline."
        )
    return True, "PASS", f"{len(funds)} fund recommendation(s) present."


def _check_no_contradictions(
    investment_allowed: bool, allocation: Dict[str, Any]
) -> Tuple[bool, str, str]:
    """If investment is allowed, allocation must not be LOCKED."""
    if investment_allowed and isinstance(allocation, dict) and allocation.get("status") == "LOCKED":
        return False, "FAIL", (
            "Contradiction: investment is flagged as ALLOWED but allocation is LOCKED. "
            "This is a pipeline inconsistency — output must not be issued."
        )
    return True, "PASS", "Investment-allowed / allocation-locked state is consistent."


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

def run_final_review(
    output: Dict[str, Any],
    user_profile: Dict[str, Any],
    risk_category: str = "moderate",
) -> Dict[str, Any]:
    """
    Run all validation checks and return a ``final_review`` block.

    Parameters
    ----------
    output :
        The draft advisory output from the orchestrator.
    user_profile :
        Sanitised user profile dict (post ``_prepare_user_profile``).
    risk_category :
        Declared risk class (e.g. "Conservative", "Aggressive (ML Pred)").

    Returns
    -------
    dict with keys:
        ``status``                – "PASS" | "WARN" | "FAIL"
        ``regeneration_required`` – bool
        ``passed_checks``         – list[str]
        ``validation_notes``      – list[dict] with severity + message
        ``summary``               – one-line human-readable verdict
    """
    allocation = output.get("allocation", {})
    confidence = output.get("confidence_score", {})
    stress = output.get("stress_test", {})
    investment_allowed = bool(output.get("investment_allowed", False))
    funds = output.get("funds", [])

    checks = [
        _check_no_contradictions(investment_allowed, allocation),
        _check_allocation_sum(allocation),
        _check_risk_equity_alignment(allocation, risk_category),
        _check_financial_feasibility(user_profile),
        _check_emi_ratio(user_profile),
        _check_emergency_fund(user_profile),
        _check_confidence_score(confidence),
        _check_stress_consistency(stress, confidence),
        _check_funds_present(investment_allowed, funds),
    ]

    notes: List[Dict[str, str]] = []
    passed: List[str] = []
    has_fail = False
    has_warn = False

    check_names = [
        "no_contradictions",
        "allocation_sum",
        "risk_equity_alignment",
        "financial_feasibility",
        "emi_ratio",
        "emergency_fund",
        "confidence_score",
        "stress_consistency",
        "funds_present",
    ]

    for name, (ok, severity, message) in zip(check_names, checks):
        if ok:
            passed.append(name)
        else:
            notes.append({"check": name, "severity": severity, "message": message})
            if severity == "FAIL":
                has_fail = True
            elif severity == "WARN":
                has_warn = True

    if has_fail:
        overall_status = "FAIL"
        regeneration_required = True
        summary = (
            f"{len(notes)} validation issue(s) detected — {sum(1 for n in notes if n['severity'] == 'FAIL')} "
            "critical. Output regeneration required before issue."
        )
    elif has_warn:
        overall_status = "WARN"
        regeneration_required = False
        summary = (
            f"Advisory output passed with {len(notes)} warning(s). "
            "Review notes before sharing with client."
        )
    else:
        overall_status = "PASS"
        regeneration_required = False
        summary = f"All {len(passed)} validation checks passed. Output is ready to issue."

    return {
        "status": overall_status,
        "regeneration_required": regeneration_required,
        "passed_checks": passed,
        "validation_notes": notes,
        "summary": summary,
    }
