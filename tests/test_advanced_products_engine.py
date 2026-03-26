from backend.engines.advanced_products_engine import (
    get_advanced_product_eligibility,
    recommend_bonds,
)


def test_recommend_bonds_returns_curated_bond_set():
    bonds = recommend_bonds(target_weight=12.0)
    assert len(bonds) >= 3
    assert all("issuer" in bond for bond in bonds)
    assert all("ytm" in bond for bond in bonds)


def test_pms_eligibility_shows_when_income_or_net_worth_meets_threshold():
    cards = get_advanced_product_eligibility(
        annual_income=3_000_000,
        net_worth=6_000_000,
    )
    titles = [card["title"] for card in cards]
    assert "PMS Eligibility" in titles


def test_aif_eligibility_hidden_below_threshold():
    cards = get_advanced_product_eligibility(
        annual_income=2_000_000,
        net_worth=9_000_000,
    )
    titles = [card["title"] for card in cards]
    assert "AIF Eligibility" not in titles
