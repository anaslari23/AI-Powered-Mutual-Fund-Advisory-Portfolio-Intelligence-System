import json
from pathlib import Path
from typing import Any, Dict, List


_BOND_FIXTURE_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "fixtures" / "bonds_fixture.json"
)


def load_bond_fixture() -> List[Dict[str, Any]]:
    with open(_BOND_FIXTURE_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def recommend_bonds(target_weight: float = 0.0) -> List[Dict[str, Any]]:
    bonds = load_bond_fixture()
    if not bonds:
        return []

    selected = [
        next((b for b in bonds if b["bond_type"] == "G-Secs"), None),
        next((b for b in bonds if b["bond_type"] == "Corporate Bonds (AAA/AA)"), None),
        next((b for b in bonds if b["bond_type"] == "Tax-Free Bonds"), None),
        next((b for b in bonds if b["bond_type"] == "SGBs"), None),
    ]
    selected = [bond for bond in selected if bond is not None]
    per_bond_weight = round(target_weight / len(selected), 2) if selected and target_weight > 0 else 0.0

    recommendations = []
    for bond in selected:
        recommendations.append(
            {
                **bond,
                "allocation_weight": per_bond_weight,
            }
        )
    return recommendations


def get_advanced_product_eligibility(
    annual_income: float,
    net_worth: float,
) -> List[Dict[str, str]]:
    cards: List[Dict[str, str]] = []

    if net_worth > 5_000_000 or annual_income > 2_500_000:
        cards.append(
            {
                "title": "PMS Eligibility",
                "message": (
                    "You may qualify for PMS. These typically offer customized equity "
                    "strategies for ₹50L+. Contact your advisor."
                ),
            }
        )

    if net_worth > 10_000_000:
        cards.append(
            {
                "title": "AIF Eligibility",
                "message": (
                    "You may qualify for AIF opportunities. These are suited to higher-net-worth "
                    "investors seeking specialized private market or thematic exposure."
                ),
            }
        )

    return cards
