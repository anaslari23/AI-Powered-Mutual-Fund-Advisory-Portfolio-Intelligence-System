"""
backend/engines/sip_storyteller.py
───────────────────────────────────
Deterministic SIP narrative generator.
Converts raw SIP projection numbers into human-readable advisory stories
emphasising compounding and disciplined investing.
"""
from typing import Any, Dict, Optional


def _format_inr(amount: float) -> str:
    """Format amount in Indian ₹ notation with commas."""
    if amount >= 1_00_00_000:
        return f"₹{amount / 1_00_00_000:,.2f} Cr"
    if amount >= 1_00_000:
        return f"₹{amount / 1_00_000:,.2f} L"
    return f"₹{amount:,.0f}"


def generate_sip_story(
    monthly: float,
    years: int,
    rate: float,
    future_value: float,
    step_up_rate: Optional[float] = None,
) -> Dict[str, str]:
    """
    Generate a human-readable SIP story with compounding and discipline narratives.

    Parameters
    ----------
    monthly : float
        Monthly SIP amount in ₹.
    years : int
        Investment horizon in years.
    rate : float
        Expected annual return rate as percentage (e.g. 12.0 for 12%).
    future_value : float
        Projected corpus at the end of the horizon.
    step_up_rate : float, optional
        Annual SIP step-up percentage (e.g. 10.0 for 10%).

    Returns
    -------
    dict
        Keys: narrative, compounding_note, discipline_note, summary
    """
    total_invested = monthly * 12 * years
    wealth_gained = future_value - total_invested
    multiplier = future_value / total_invested if total_invested > 0 else 1.0

    monthly_fmt = _format_inr(monthly)
    fv_fmt = _format_inr(future_value)
    invested_fmt = _format_inr(total_invested)
    gained_fmt = _format_inr(wealth_gained)

    # ── Core narrative ─────────────────────────────────────────────────────
    narrative = (
        f"A monthly investment of {monthly_fmt} over {years} years, assuming an "
        f"annual return of {rate:.1f}%, can grow to approximately {fv_fmt}. "
        f"Your total investment of {invested_fmt} would generate an additional "
        f"{gained_fmt} in wealth — a {multiplier:.1f}x return on your committed capital."
    )

    if step_up_rate and step_up_rate > 0:
        narrative += (
            f" With an annual step-up of {step_up_rate:.0f}%, the effective corpus "
            f"could be significantly higher as your SIP contributions increase in "
            f"line with your income growth."
        )

    # ── Compounding explanation ────────────────────────────────────────────
    compounding_note = (
        "This projection demonstrates the power of compounding — where your returns "
        "generate further returns over time. In the early years, growth appears modest, "
        "but the acceleration in later years is where the real wealth multiplication occurs. "
        f"Over a {years}-year horizon, compounding transforms disciplined monthly "
        f"contributions of {monthly_fmt} into a corpus that is {multiplier:.1f}x your "
        f"total investment."
    )

    # ── Discipline messaging ───────────────────────────────────────────────
    if years >= 15:
        discipline_note = (
            "Long-term SIP investing rewards patience and consistency. Market corrections "
            "along the way actually benefit SIP investors through rupee-cost averaging — "
            "buying more units when prices are lower. Staying invested through market cycles "
            "is the most critical factor in achieving your projected wealth target."
        )
    elif years >= 7:
        discipline_note = (
            "A disciplined SIP approach over this medium-term horizon provides exposure to "
            "multiple market cycles, allowing your investments to benefit from both growth "
            "rallies and corrections through rupee-cost averaging. Consistency is the key "
            "to achieving your financial targets."
        )
    else:
        discipline_note = (
            "Even over a shorter horizon, disciplined monthly investing helps build a "
            "meaningful corpus. While short-term market movement can create volatility, "
            "the SIP approach reduces timing risk and builds a healthy investing habit. "
            "Consider extending your investment horizon if possible for enhanced compounding benefits."
        )

    # ── Condensed summary ──────────────────────────────────────────────────
    summary = (
        f"{monthly_fmt}/month × {years} years @ {rate:.1f}% → {fv_fmt} "
        f"(invested: {invested_fmt}, gained: {gained_fmt}, {multiplier:.1f}x)"
    )

    return {
        "narrative": narrative,
        "compounding_note": compounding_note,
        "discipline_note": discipline_note,
        "summary": summary,
    }


def generate_multi_sip_story(sip_rows: list) -> Dict[str, Any]:
    """
    Generate stories for multiple SIP scenarios and a comparative summary.

    Parameters
    ----------
    sip_rows : list[dict]
        Each dict has keys: monthly_sip, horizon_years, assumed_return_pct, projected_corpus

    Returns
    -------
    dict
        Keys: scenarios (list of story dicts), comparative_note
    """
    scenarios = []
    for row in sip_rows:
        monthly = float(row.get("monthly_sip", 0))
        years = int(row.get("horizon_years", 10))
        rate = float(row.get("assumed_return_pct", 12))
        corpus = float(row.get("projected_corpus", 0))
        if monthly > 0 and corpus > 0:
            story = generate_sip_story(monthly, years, rate, corpus)
            story["monthly_sip"] = monthly
            story["horizon_years"] = years
            story["assumed_return_pct"] = rate
            story["projected_corpus"] = corpus
            scenarios.append(story)

    if len(scenarios) >= 2:
        first = scenarios[0]
        last = scenarios[-1]
        comparative_note = (
            f"Comparing the scenarios, increasing your SIP from "
            f"{_format_inr(first['monthly_sip'])} to {_format_inr(last['monthly_sip'])} "
            f"over a longer horizon ({last['horizon_years']} vs {first['horizon_years']} years) "
            f"can multiply your projected corpus from {_format_inr(first['projected_corpus'])} "
            f"to {_format_inr(last['projected_corpus'])} — demonstrating how both increased "
            f"contributions and extended timelines amplify compounding effects."
        )
    elif scenarios:
        comparative_note = scenarios[0]["narrative"]
    else:
        comparative_note = "Please configure SIP scenarios to see projected outcomes."

    return {
        "scenarios": scenarios,
        "comparative_note": comparative_note,
    }
