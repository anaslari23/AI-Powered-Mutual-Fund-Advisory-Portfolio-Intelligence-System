"""
backend/engines/affordability_engine.py
────────────────────────────────────────
Validates whether a proposed SIP is affordable relative to the investor's
monthly surplus. Returns a structured status with advisory messaging.
"""
from typing import Any, Dict


_STATUS_MESSAGES = {
    "feasible": (
        "Your suggested monthly investment of ₹{sip:,.0f} is within comfortable limits, "
        "representing {ratio:.0f}% of your investible surplus. This level of commitment "
        "allows you to maintain your current lifestyle while building long-term wealth "
        "through disciplined investing."
    ),
    "stretch": (
        "Your suggested monthly investment of ₹{sip:,.0f} represents {ratio:.0f}% of "
        "your investible surplus, which is a stretch but achievable with disciplined "
        "budgeting. We recommend reviewing your monthly expenses to ensure this "
        "commitment does not create financial stress. Consider starting with a lower "
        "amount and increasing via annual step-ups."
    ),
    "not_advisable": (
        "Your suggested monthly investment of ₹{sip:,.0f} exceeds comfortable limits "
        "at {ratio:.0f}% of your investible surplus. Committing this amount may strain "
        "your monthly finances and lead to premature discontinuation. We strongly "
        "recommend reducing the SIP amount to ₹{recommended_sip:,.0f} (40% of surplus) "
        "or lower, and increasing gradually over time."
    ),
}

_STATUS_SHORT = {
    "feasible": "✓ Comfortable — within safe limits",
    "stretch": "⚠ Stretch — requires disciplined budgeting",
    "not_advisable": "✖ Not Advisable — exceeds comfortable limits",
}


def check_affordability(
    monthly_sip: float,
    monthly_surplus: float,
) -> Dict[str, Any]:
    """
    Validate whether the proposed SIP is affordable.

    Parameters
    ----------
    monthly_sip : float
        Proposed monthly SIP amount in ₹.
    monthly_surplus : float
        Monthly investible surplus (income - expenses - EMIs) in ₹.

    Returns
    -------
    dict
        Keys: status, message, short_label, ratio, recommended_sip,
              monthly_sip, monthly_surplus
    """
    if monthly_surplus <= 0:
        return {
            "status": "not_advisable",
            "message": (
                "Your current monthly surplus is zero or negative. Before committing "
                "to a SIP, we recommend reviewing your income and expenses to establish "
                "a positive investible surplus."
            ),
            "short_label": _STATUS_SHORT["not_advisable"],
            "ratio": 100.0,
            "recommended_sip": 0.0,
            "monthly_sip": monthly_sip,
            "monthly_surplus": monthly_surplus,
        }

    ratio = (monthly_sip / monthly_surplus) * 100.0
    recommended_sip = round(monthly_surplus * 0.4, -2)  # Round to nearest 100

    if monthly_sip <= monthly_surplus * 0.4:
        status = "feasible"
    elif monthly_sip <= monthly_surplus * 0.7:
        status = "stretch"
    else:
        status = "not_advisable"

    message = _STATUS_MESSAGES[status].format(
        sip=monthly_sip,
        ratio=ratio,
        recommended_sip=recommended_sip,
    )

    return {
        "status": status,
        "message": message,
        "short_label": _STATUS_SHORT[status],
        "ratio": round(ratio, 1),
        "recommended_sip": recommended_sip,
        "monthly_sip": monthly_sip,
        "monthly_surplus": monthly_surplus,
    }
