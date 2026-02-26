import streamlit as st
import pandas as pd
from typing import Dict, Any, List
from backend.data.mutual_fund_api import get_mutual_fund_universe
from backend.engines.fund_categorizer import categorize_funds
from backend.engines.fund_performance_engine import apply_performance_metrics


@st.cache_data(ttl=21600)  # Cache daily so we don't fetch/train at every button click
def get_processed_fund_universe() -> tuple[pd.DataFrame, bool]:
    df, is_live = get_mutual_fund_universe()
    if df is not None and not df.empty:
        df = categorize_funds(df)
        df = apply_performance_metrics(df)
    return df, is_live


def suggest_mutual_funds(
    allocation: Dict[str, Any], risk_profile: str
) -> tuple[List[Dict[str, Any]], bool]:
    """
    Suggests specific mutual funds dynamically using AMFI live NAVs and ETF proxy performance.
    Applies risk-based filtering and returns top 5 funds per requested category.
    Returns (Recommendations, is_live_data)
    """
    df, is_live = get_processed_fund_universe()
    recommendations = []

    if df is None or df.empty:
        return recommendations, False

    # Risk-Based Filtering logic
    # Assume Conservative, Moderate, Aggressive from Risk Meter
    # risk_profile usually comes as something like "Moderate" or "Aggressive Investor"
    # We will derive the broad category
    investor_type = risk_profile.lower()

    allowed_categories = set()
    if "conservative" in investor_type:
        allowed_categories = {"Debt", "Hybrid", "Large Cap"}
    elif "moderate" in investor_type:
        allowed_categories = {"Large Cap", "Flexi", "Hybrid", "Mid Cap"}
    elif "aggressive" in investor_type:
        allowed_categories = {"Small Cap", "Mid Cap", "Flexi", "Sectoral"}
    else:
        # Default safety net
        allowed_categories = {
            "Large Cap",
            "Flexi",
            "Debt",
            "Hybrid",
            "Mid Cap",
            "Small Cap",
            "Sectoral",
        }

    for asset_class, weight in allocation.items():
        if weight > 0:
            # The asset_class in allocation might be "Equity", "Debt", "Gold", etc.
            # We map the high-level asset class to specific fund categories based on Risk

            target_cats = set()
            if asset_class == "Equity":
                # Only include equity categories allowed by risk profile
                equity_cats = {"Large Cap", "Mid Cap", "Small Cap", "Flexi", "Sectoral"}
                target_cats = allowed_categories.intersection(equity_cats)
            elif asset_class == "Debt":
                target_cats = {"Debt"} if "Debt" in allowed_categories else set()
            elif asset_class == "Gold":
                target_cats = {"Gold"}

            if not target_cats:
                continue

            category_funds = df[df["category"].isin(target_cats)].copy()

            if not category_funds.empty:
                # Sort by the engine's pre-calculated ranking score descending
                category_funds = category_funds.sort_values(by="score", ascending=False)

                # Get Top 5 funds
                top_funds = category_funds.head(5).to_dict(orient="records")

                # We'll just append the #1 top fund to represent the slice in the UI,
                # or you can return all top 5. The previous code returned 1 fund per allocation.
                # Let's return the Absolute Top 1 for the specific asset class weight.
                top_fund = top_funds[0]

                # Format to match what UI expects
                recommendations.append(
                    {
                        "name": top_fund["scheme_name"],
                        "category": top_fund["category"],
                        "allocation_weight": weight,
                        "risk": risk_profile,  # Pass risk down
                        "1y": top_fund["1y"],
                        "3y": top_fund["3y"],
                        "5y": top_fund["5y"],
                        "sharpe": top_fund["sharpe"],
                        "volatility": top_fund["volatility"],
                        "nav": top_fund["nav"],
                        "date": top_fund["date"],
                    }
                )

    return recommendations, is_live
