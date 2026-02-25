import streamlit as st
from backend.utils.sip_calculator import calculate_sip_future_value


def render_sip_calculator_widget():
    col1, col2, col3 = st.columns(3)
    with col1:
        sip_amount = st.slider(
            "Monthly SIP (₹)", min_value=1000, max_value=200000, value=10000, step=1000
        )
    with col2:
        return_rate = st.slider(
            "Expected Return (%)", min_value=5, max_value=20, value=12, step=1
        )
    with col3:
        years = st.slider(
            "Duration (Years)", min_value=1, max_value=40, value=10, step=1
        )

    fv = calculate_sip_future_value(sip_amount, return_rate / 100.0, years)
    invested = sip_amount * 12 * years
    wealth_gained = fv - invested

    st.info(
        f"**Total Invested:** ₹{invested:,.2f} | **Wealth Gained:** ₹{wealth_gained:,.2f} | **Total Value:** ₹{fv:,.2f}"
    )
