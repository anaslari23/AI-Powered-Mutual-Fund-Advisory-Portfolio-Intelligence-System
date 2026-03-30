"""
Deterministic advisory baseline engine.
Produces equity/debt allocation bands from age, risk class, and horizon.
No AI usage — all logic is rule-based and fully explainable.
"""


def generate_guidance(age: int, risk_class: str, horizon_years: int) -> dict:
    """
    Returns deterministic allocation bands based on client profile.
    These bands serve as the advisory baseline that the allocation engine
    must respect; AI signals may tilt within bands but cannot override them.
    """
    if age >= 55:
        equity_band = (20, 40)
        debt_band = (50, 70)
    elif risk_class == "Aggressive":
        equity_band = (70, 85)
        debt_band = (10, 25)
    elif risk_class == "Moderate":
        equity_band = (50, 70)
        debt_band = (30, 50)
    else:
        # Conservative or any unrecognised class defaults to conservative band
        equity_band = (30, 50)
        debt_band = (50, 70)

    return {
        "equity_band": equity_band,
        "debt_band": debt_band,
        "reason": (
            f"Derived from age={age}, risk_class={risk_class}, "
            f"horizon_years={horizon_years}"
        ),
    }
