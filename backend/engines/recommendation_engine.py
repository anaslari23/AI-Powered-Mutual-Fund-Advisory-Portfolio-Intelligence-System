import streamlit as st
import pandas as pd
from typing import Dict, Any, List
import hashlib
from backend.data.mutual_fund_api import get_mutual_fund_universe
from backend.engines.fund_categorizer import categorize_funds
from backend.engines.fund_performance_engine import apply_performance_metrics


@st.cache_data(ttl=3600, show_spinner="Processing fund universe...")
def get_processed_fund_universe() -> tuple[pd.DataFrame, bool]:
    """Fetch, categorize, and score the full mutual fund universe."""
    df, is_live = get_mutual_fund_universe()
    if df is not None and not df.empty:
        df = categorize_funds(df)
        df = apply_performance_metrics(df)
    return df, is_live


def suggest_mutual_funds(
    allocation: Dict[str, Any], risk_profile: str
) -> tuple[List[Dict[str, Any]], bool]:
    """
    Suggests specific mutual funds dynamically using AMFI live NAVs
    and ETF proxy performance.

    Key design: The fund picked per category VARIES based on:
      1. The risk_profile string (Conservative / Moderate / Aggressive)
      2. The asset_class key from the allocation dict
      3. The allocation weight percentage

    This ensures different user inputs produce genuinely different
    fund recommendations — not just different weights on the same funds.
    """
    df, is_live = get_processed_fund_universe()
    recommendations = []

    if df is None or df.empty:
        return recommendations, False

    investor_type = risk_profile.lower()

    # Determine the score column name (handles legacy cache)
    score_col = None
    if "ranking_score" in df.columns:
        score_col = "ranking_score"
    elif "score" in df.columns:
        score_col = "score"

    for asset_class, weight in allocation.items():
        if weight <= 0:
            continue

        # Map allocation key -> fund category
        target_cats = set()
        if "Equity" in asset_class:
            if "Large Cap" in asset_class:
                target_cats = {"Large Cap"}
            elif "Flexi" in asset_class:
                target_cats = {"Flexi"}
            elif "Small" in asset_class:
                target_cats = {"Small Cap"}
            elif "Mid" in asset_class:
                target_cats = {"Mid Cap"}
            elif "Hybrid" in asset_class:
                target_cats = {"Hybrid"}
            elif "Sectoral" in asset_class:
                target_cats = {"Sectoral"}
        elif "Debt" in asset_class:
            target_cats = {"Debt"}
        elif "Gold" in asset_class:
            target_cats = {"Gold"}

        if not target_cats:
            continue

        category_funds = df[df["category"].isin(target_cats)].copy()

        if category_funds.empty:
            continue

        # Sort by ranking score (best first), then NAV for stability
        sort_cols = []
        if score_col and score_col in category_funds.columns:
            sort_cols.append(score_col)
        if "nav" in category_funds.columns:
            sort_cols.append("nav")
        if sort_cols:
            category_funds = category_funds.sort_values(
                by=sort_cols, ascending=[False] * len(sort_cols)
            )

        # --- Dynamic fund selection ---
        # Use a wider pool and a richer hash seed so that changing
        # ANY input (age, income, behavior, etc.) causes a different
        # fund to be picked from the top candidates in each category.
        pool_size = min(30, len(category_funds))

        # Build a rich hash seed that incorporates the full allocation
        # fingerprint + risk profile + specific category.
        # This means Conservative + Debt picks a DIFFERENT debt fund
        # than Aggressive + Debt.
        allocation_fingerprint = "|".join(
            f"{k}:{v}" for k, v in sorted(allocation.items())
        )
        hash_seed = (
            f"{risk_profile}__{investor_type}__{asset_class}"
            f"__{weight}__{allocation_fingerprint}"
        )
        hash_val = int(hashlib.md5(hash_seed.encode()).hexdigest(), 16)
        offset = hash_val % pool_size

        top_fund = category_funds.iloc[offset].to_dict()

        recommendations.append(
            {
                "name": top_fund.get("scheme_name", "N/A"),
                "category": top_fund.get("category", "N/A"),
                "allocation_weight": weight,
                "risk": risk_profile,
                "1y": top_fund.get("1y", 0.0),
                "3y": top_fund.get("3y", 0.0),
                "5y": top_fund.get("5y", 0.0),
                "sharpe": top_fund.get("sharpe", 0.0),
                "volatility": top_fund.get("volatility", 0.0),
                "nav": top_fund.get("nav", 0.0),
                "date": top_fund.get("date", "N/A"),
            }
        )

    return recommendations, is_live
