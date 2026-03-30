"""
Rejection / "Why Not" engine.
Generates explicit, explainable reasons why certain strategies were excluded
from a client's proposal. Deterministic rule-based logic — no AI.
"""


def generate_rejection_logic(risk_class: str, horizon: int) -> list:
    """
    Returns a list of human-readable strings explaining which strategies
    were rejected and why.  Each reason maps to a verifiable rule so the
    output is fully auditable.
    """
    reasons = []

    if risk_class in ("Moderate", "Conservative"):
        reasons.append(
            "High-volatility small-cap strategies avoided due to "
            f"{risk_class} risk profile."
        )

    if horizon < 5:
        reasons.append(
            "Equity-heavy allocation avoided due to short investment "
            f"horizon of {horizon} year(s) — insufficient time to absorb "
            "market drawdowns."
        )

    if risk_class == "Conservative" and horizon >= 5:
        reasons.append(
            "Pure equity funds excluded; client profile requires capital "
            "preservation over growth."
        )

    if not reasons:
        reasons.append(
            "All standard category restrictions reviewed; none apply to "
            f"this {risk_class} profile with a {horizon}-year horizon."
        )

    return reasons
