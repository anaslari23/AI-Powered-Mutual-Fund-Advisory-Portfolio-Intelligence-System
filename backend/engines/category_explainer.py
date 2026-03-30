"""
backend/engines/category_explainer.py
──────────────────────────────────────
Predefined mutual fund category explanation library.
Returns structured "WHY this category" for a given fund category and investor profile.
Deterministic, template-based — NOT AI generated.
"""
from typing import Any, Dict, Optional


# ──────────────────────────────────────────────────────────────────────────────
# Category Knowledge Base
# ──────────────────────────────────────────────────────────────────────────────

_CATEGORY_LIBRARY: Dict[str, Dict[str, str]] = {
    "Large Cap": {
        "description": (
            "Large Cap funds invest predominantly in the top 100 companies by market "
            "capitalisation. These are established businesses with proven track records, "
            "strong governance, and relatively lower volatility compared to mid or small-cap peers."
        ),
        "risk_level": "Moderate",
        "growth_potential": "Steady, inflation-beating returns over the long term",
        "typical_return": "10–13% annualised over 7+ years",
        "suitability_conservative": (
            "Large Cap funds offer stability and predictable returns suitable for investors "
            "seeking capital preservation with modest growth. The lower volatility aligns "
            "well with a conservative risk appetite."
        ),
        "suitability_moderate": (
            "Large Cap funds provide a stable foundation for a balanced portfolio. Combined "
            "with mid-cap exposure, they offer consistent returns while limiting downside risk."
        ),
        "suitability_aggressive": (
            "While Large Cap funds alone may not deliver the growth aggressive investors seek, "
            "they serve as a stabilising anchor in a diversified portfolio that includes "
            "higher-volatility categories."
        ),
    },
    "Mid Cap": {
        "description": (
            "Mid Cap funds invest in companies ranked 101–250 by market capitalisation. These "
            "companies are in their growth phase and offer higher upside potential than large caps, "
            "but with proportionally higher volatility."
        ),
        "risk_level": "Moderately High",
        "growth_potential": "Higher growth potential than large caps with moderate risk",
        "typical_return": "12–16% annualised over 7+ years",
        "suitability_conservative": (
            "Mid Cap funds carry higher volatility and are generally not the primary choice "
            "for conservative investors. A small allocation (5–10%) may be considered for "
            "investors with a horizon of 10+ years."
        ),
        "suitability_moderate": (
            "Mid Cap funds complement a balanced portfolio by adding growth potential beyond "
            "what large caps offer. A moderate allocation (15–25%) can enhance returns while "
            "keeping overall portfolio volatility manageable."
        ),
        "suitability_aggressive": (
            "Mid Cap funds are well-suited for growth-oriented investors willing to tolerate "
            "short-term fluctuations for potentially superior long-term returns."
        ),
    },
    "Small Cap": {
        "description": (
            "Small Cap funds invest in companies ranked beyond 250 by market capitalisation. "
            "These companies are early in their growth trajectory and can deliver outsized "
            "returns, but come with significant volatility and liquidity risk."
        ),
        "risk_level": "High",
        "growth_potential": "Highest growth potential among equity categories",
        "typical_return": "14–20% annualised over 10+ years (with high variance)",
        "suitability_conservative": (
            "Small Cap funds are generally not recommended for conservative investors due to "
            "their high volatility and potential for extended drawdowns."
        ),
        "suitability_moderate": (
            "A limited allocation to Small Cap funds (5–10%) can enhance portfolio returns "
            "for moderate investors with a long investment horizon of 10+ years."
        ),
        "suitability_aggressive": (
            "Small Cap funds align well with an aggressive investment stance, offering the "
            "highest return potential. Investors should be prepared for significant "
            "short-term volatility and maintain a long-term perspective."
        ),
    },
    "Flexi Cap": {
        "description": (
            "Flexi Cap funds provide flexibility across large, mid, and small-cap stocks. "
            "This allows fund managers to dynamically adjust allocation based on market "
            "conditions, valuation cycles, and emerging opportunities across the entire "
            "market capitalisation spectrum."
        ),
        "risk_level": "Moderate to Moderately High",
        "growth_potential": "Diversified growth with dynamic allocation",
        "typical_return": "11–15% annualised over 5+ years",
        "suitability_conservative": (
            "Flexi Cap funds offer a diversified equity exposure that can suit conservative "
            "investors seeking the growth benefits of equity with the safety of diversified "
            "allocation. The fund manager's flexibility to increase large-cap exposure during "
            "market stress provides built-in risk management."
        ),
        "suitability_moderate": (
            "Flexi Cap funds are an ideal core holding for moderate investors. The dynamic "
            "allocation across market caps balances growth and stability effectively, making "
            "them suitable as a primary equity allocation for investors with a long-term horizon."
        ),
        "suitability_aggressive": (
            "For aggressive investors, Flexi Cap funds serve as a well-diversified equity "
            "foundation. While dedicated mid/small-cap funds may offer higher returns, Flexi Caps "
            "provide professional diversification with significant equity upside."
        ),
    },
    "Hybrid": {
        "description": (
            "Hybrid funds invest across both equity and debt instruments within a single fund. "
            "They offer built-in diversification and are designed to balance growth with "
            "stability, reducing the need for manual rebalancing."
        ),
        "risk_level": "Low to Moderate",
        "growth_potential": "Moderate, balanced between equity growth and debt stability",
        "typical_return": "8–12% annualised over 5+ years",
        "suitability_conservative": (
            "Hybrid funds are highly suitable for conservative investors who want some equity "
            "participation without full equity volatility. The built-in debt component provides "
            "downside protection and income stability."
        ),
        "suitability_moderate": (
            "Hybrid funds can complement a moderate portfolio as a single-fund solution for "
            "investors seeking simplicity, or as a stabilising component alongside pure equity funds."
        ),
        "suitability_aggressive": (
            "Hybrid funds are generally under-weighted in aggressive portfolios due to their "
            "limited equity upside. However, they can serve as a strategic allocation during "
            "periods of market uncertainty."
        ),
    },
    "Debt": {
        "description": (
            "Debt funds invest primarily in fixed-income securities such as government bonds, "
            "corporate bonds, and money market instruments. They aim to provide steady income "
            "and capital preservation with lower volatility than equity."
        ),
        "risk_level": "Low",
        "growth_potential": "Stable, inflation-proximate returns",
        "typical_return": "6–8% annualised",
        "suitability_conservative": (
            "Debt funds form the backbone of a conservative portfolio, offering predictable "
            "returns, low volatility, and better post-tax efficiency than fixed deposits "
            "for investors in higher tax brackets."
        ),
        "suitability_moderate": (
            "Debt funds provide essential stability in a balanced portfolio. An allocation "
            "of 20–35% to debt helps cushion the portfolio during equity market corrections."
        ),
        "suitability_aggressive": (
            "Even aggressive investors benefit from a small debt allocation (5–15%) for "
            "liquidity and to provide dry powder for equity rebalancing during market dips."
        ),
    },
    "Gold": {
        "description": (
            "Gold funds invest in gold-backed securities or physical gold ETFs. Gold serves "
            "as a traditional hedge against inflation, currency devaluation, and geopolitical "
            "uncertainty."
        ),
        "risk_level": "Low to Moderate",
        "growth_potential": "Inflation hedge with moderate long-term appreciation",
        "typical_return": "8–10% annualised over 10+ years",
        "suitability_conservative": (
            "Gold provides a safe-haven asset within a conservative portfolio, offering "
            "protection during periods of economic uncertainty and market stress."
        ),
        "suitability_moderate": (
            "A strategic gold allocation of 5–10% adds diversification to a balanced "
            "portfolio and historically shows low correlation with equity markets."
        ),
        "suitability_aggressive": (
            "For aggressive investors, gold serves as a tactical hedge (5–10%) to reduce "
            "overall portfolio correlation and provide stability during sharp equity corrections."
        ),
    },
    "Sectoral": {
        "description": (
            "Sectoral or Thematic funds concentrate investments in a specific industry or theme "
            "such as technology, banking, healthcare, or infrastructure. These funds offer "
            "outsized returns when the chosen sector outperforms, but carry concentration risk."
        ),
        "risk_level": "High",
        "growth_potential": "High during favourable sector cycles",
        "typical_return": "Highly variable — 5–25% depending on sector cycle",
        "suitability_conservative": (
            "Sectoral funds are generally not recommended for conservative investors due to "
            "their concentrated exposure and cyclical volatility."
        ),
        "suitability_moderate": (
            "A small allocation to sectoral funds (5–10%) may benefit moderate investors "
            "with specific conviction in a sector's long-term tailwinds."
        ),
        "suitability_aggressive": (
            "Aggressive investors can allocate 10–20% to sectoral themes they believe in, "
            "provided they maintain diversification across their overall portfolio."
        ),
    },
    "ELSS": {
        "description": (
            "Equity Linked Savings Schemes (ELSS) are tax-saving mutual funds that invest "
            "predominantly in equity markets. They come with a mandatory 3-year lock-in period "
            "and qualify for tax deduction under Section 80C of the Income Tax Act."
        ),
        "risk_level": "Moderate to High",
        "growth_potential": "Similar to diversified equity with tax benefits",
        "typical_return": "10–14% annualised over 5+ years",
        "suitability_conservative": (
            "ELSS funds offer dual benefits — tax savings and equity growth. The 3-year lock-in "
            "naturally enforces long-term investing, which can suit conservative investors "
            "seeking tax-efficient equity exposure."
        ),
        "suitability_moderate": (
            "ELSS is an excellent default choice for investors seeking Section 80C benefits. "
            "The lock-in period aligns with disciplined investing principles."
        ),
        "suitability_aggressive": (
            "For aggressive investors, ELSS provides tax-efficient equity exposure. The lock-in "
            "is shorter than most investment horizons of aggressive portfolios."
        ),
    },
    "Liquid": {
        "description": (
            "Liquid funds invest in very short-term debt instruments with maturities up to "
            "91 days. They are designed for parking surplus cash and offer marginally better "
            "returns than savings accounts with high liquidity."
        ),
        "risk_level": "Very Low",
        "growth_potential": "Capital preservation with marginal income",
        "typical_return": "4–6% annualised",
        "suitability_conservative": (
            "Liquid funds are ideal for parking emergency reserves or short-term surpluses. "
            "They offer superior returns to savings accounts with minimal risk."
        ),
        "suitability_moderate": (
            "Liquid funds serve as a cash management tool for parking surplus savings before "
            "systematic deployment into equity via STP."
        ),
        "suitability_aggressive": (
            "Liquid funds are useful as a tactical staging area for lumpsum amounts awaiting "
            "deployment into equity markets via STP during favourable conditions."
        ),
    },
}


def _normalise_category(category: str) -> str:
    """Fuzzy match category name to library key."""
    cat = category.strip().title()
    # Direct match
    if cat in _CATEGORY_LIBRARY:
        return cat
    # Common aliases
    aliases = {
        "Flexi": "Flexi Cap",
        "Flexicap": "Flexi Cap",
        "Largecap": "Large Cap",
        "Midcap": "Mid Cap",
        "Smallcap": "Small Cap",
        "Bond": "Debt",
        "Bonds": "Debt",
        "Fixed Income": "Debt",
        "Thematic": "Sectoral",
    }
    return aliases.get(cat, cat)


def _risk_to_suitability_key(risk_class: str) -> str:
    """Map risk class to suitability template key."""
    rc = risk_class.strip().lower()
    if rc in ("aggressive", "high"):
        return "suitability_aggressive"
    if rc in ("conservative", "low"):
        return "suitability_conservative"
    return "suitability_moderate"


def explain_category(
    category: str,
    profile: Optional[Dict[str, Any]] = None,
) -> Dict[str, str]:
    """
    Return a structured explanation for a mutual fund category,
    personalised to the investor profile.

    Returns
    -------
    dict
        Keys: description, suitability, risk_level, growth_potential,
        typical_return, narrative
    """
    profile = profile or {}
    cat_key = _normalise_category(category)
    entry = _CATEGORY_LIBRARY.get(cat_key)

    if entry is None:
        return {
            "description": f"{category} is a mutual fund category.",
            "suitability": "Suitability depends on your individual financial profile.",
            "risk_level": "Varies",
            "growth_potential": "Varies",
            "typical_return": "Varies",
            "narrative": f"{category} fund selected based on your financial profile.",
        }

    risk_class = str(
        profile.get("risk_class",
                     profile.get("category",
                                 profile.get("risk_profile", "Moderate")))
    )
    suitability_key = _risk_to_suitability_key(risk_class)
    suitability = entry.get(suitability_key, entry["suitability_moderate"])

    horizon = profile.get("horizon_years", profile.get("years_to_goal", 10))
    age = profile.get("age", 30)

    # Build composite narrative
    narrative = (
        f"{entry['description']} "
        f"{suitability} "
        f"For an investor aged {age} with a {horizon}-year horizon, "
        f"this category offers {entry['growth_potential'].lower()}."
    )

    return {
        "description": entry["description"],
        "suitability": suitability,
        "risk_level": entry["risk_level"],
        "growth_potential": entry["growth_potential"],
        "typical_return": entry["typical_return"],
        "narrative": narrative,
    }


def list_categories() -> list:
    """Return all available category keys."""
    return list(_CATEGORY_LIBRARY.keys())
