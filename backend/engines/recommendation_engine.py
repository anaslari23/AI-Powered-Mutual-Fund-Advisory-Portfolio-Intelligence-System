from typing import Dict, Any, List
import streamlit as st
from backend.engines.prediction_model import build_predictive_database


@st.cache_data(ttl=86400)  # Cache daily so we don't train at every button click
def get_cached_predictive_database():
    return build_predictive_database()


def suggest_mutual_funds(allocation: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Suggests specific mutual funds based on the target asset allocation.
    Returns dynamic predictions mapped to the requested allocation categories.
    """
    database = get_cached_predictive_database()
    recommendations = []

    for asset_class, weight in allocation.items():
        if weight > 0:
            # Find the best fund predicted for this category
            category_funds = [f for f in database if f["category"] == asset_class]
            if category_funds:
                # Pick the fund with the highest 5Y predicted return
                top_fund = sorted(category_funds, key=lambda x: x["5y"], reverse=True)[
                    0
                ].copy()
                top_fund["allocation_weight"] = weight
                recommendations.append(top_fund)

    return recommendations
