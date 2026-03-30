"""
Advisory template engine.
Produces deterministic, rule-based explanatory text for client proposals.

AI MUST NOT be used for:
  - risk explanation
  - allocation reasoning
  - category logic

AI may only be used downstream to summarise meeting notes or
improve readability — never to drive advisory decisions.
"""


def generate_risk_explanation(age: int, risk: str) -> str:
    """Returns a plain-language risk explanation based on age and risk class."""
    return (
        f"Given your age of {age} and a {risk} risk profile, "
        "a balanced strategy is appropriate."
    )


def generate_allocation_explanation(equity_band: tuple, debt_band: tuple, risk: str) -> str:
    """Narrates the allocation band in plain language."""
    eq_lo, eq_hi = equity_band
    db_lo, db_hi = debt_band
    return (
        f"For a {risk} profile, equity exposure is targeted between "
        f"{eq_lo}%–{eq_hi}% and debt between {db_lo}%–{db_hi}%, "
        "ensuring the portfolio stays within prudent risk limits."
    )


def generate_horizon_note(horizon_years: int) -> str:
    """Returns a short note about the investment horizon."""
    if horizon_years >= 10:
        return (
            f"A {horizon_years}-year horizon provides sufficient time to "
            "benefit from equity compounding while riding out short-term volatility."
        )
    elif horizon_years >= 5:
        return (
            f"A {horizon_years}-year horizon allows moderate equity exposure "
            "with a gradual shift toward stability as the goal approaches."
        )
    else:
        return (
            f"A {horizon_years}-year horizon limits equity exposure; "
            "capital preservation takes precedence over growth."
        )
