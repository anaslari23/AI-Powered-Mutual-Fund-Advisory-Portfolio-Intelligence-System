def generate_final_advisory(payload: dict) -> dict:
    profile = payload["client_profile"]
    risk = payload["risk_output"]
    goal = payload["goal_output"]
    allocation = payload["allocation_output"]
    affordability = payload["affordability"]

    # -------------------------
    # 1. BASELINE
    # -------------------------
    baseline = f"""
STANDARD ADVISORY BASELINE

Given:
- Age: {profile.get('age')}
- Risk Profile: {risk.get('risk_class')}
- Investment Horizon: {goal.get('horizon_years')} years

A typical advisory allocation would be:
- Equity: 50–70%
- Debt: 30–50%
- Gold: 5–10%
"""

    # -------------------------
    # 2. BASELINE → FINAL
    # -------------------------
    transition = f"""
HOW THIS PLAN IS ADJUSTED

While a standard allocation follows the above ranges, this plan adjusts exposure based on:
- Goal horizon ({goal.get('horizon_years')} years)
- Market stability conditions
- Client-specific risk behavior

This results in a more optimized allocation tailored to the client rather than a generic framework.
"""

    # -------------------------
    # 3. WHY NOT
    # -------------------------
    why_not = [
        {
            "option": "Small-cap heavy allocation",
            "reason": "Higher volatility not suitable for current risk profile and time horizon"
        },
        {
            "option": "Pure equity strategy",
            "reason": "Short-term goal horizon increases downside risk"
        },
        {
            "option": "Sectoral funds",
            "reason": "Concentration risk reduces diversification benefits"
        }
    ]

    # -------------------------
    # 4. CATEGORY EXPLANATION
    # -------------------------
    category_explanation = f"""
CATEGORY EXPLANATION

The selected allocation balances growth and stability.

- Equity components provide long-term capital appreciation
- Debt instruments reduce volatility and provide stability
- Gold acts as a macro hedge against uncertainty

This combination aligns with a {risk.get('risk_class')} risk profile.
"""

    # -------------------------
    # 5. FINAL RECOMMENDATION
    # -------------------------
    final_recommendation = f"""
FINAL RECOMMENDATION

Based on the client’s financial profile, risk appetite, and goal timeline, a balanced portfolio with disciplined SIP deployment is recommended.

This strategy ensures:
- Goal achievement within the defined timeline
- Controlled exposure to market volatility
- Long-term capital efficiency through diversification

Affordability Status: {affordability.get('status')}
"""

    return {
        "baseline": baseline,
        "transition": transition,
        "why_not": why_not,
        "category_explanation": category_explanation,
        "final_recommendation": final_recommendation
    }