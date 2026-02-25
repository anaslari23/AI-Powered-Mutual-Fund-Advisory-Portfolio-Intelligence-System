import streamlit as st
from backend.engines.risk_engine import calculate_risk_score
from backend.engines.goal_engine import (
    calculate_retirement_goal,
    calculate_child_education_goal,
)
from backend.engines.allocation_engine import get_asset_allocation
from backend.engines.monte_carlo_engine import run_monte_carlo_simulation
from frontend.components.risk_meter import render_risk_meter
from frontend.components.charts import render_allocation_chart, render_projection_chart
from frontend.components.sip_calculator_widget import render_sip_calculator_widget


def render_dashboard(client_data: dict):
    # Calculations
    risk_profile = calculate_risk_score(
        age=client_data["age"],
        dependents=client_data["dependents"],
        behavior=client_data["behavior"],
        monthly_income=client_data["monthly_income"],
        monthly_savings=client_data["monthly_savings"],
    )

    st.subheader(
        f"Risk Profile: {risk_profile['category']} ({risk_profile['score']}/10)"
    )
    render_risk_meter(risk_profile["score"])

    # Asset Allocation
    allocation = get_asset_allocation(risk_profile["score"])
    st.markdown("### Recommended Asset Allocation")
    render_allocation_chart(allocation["allocation"])

    # Goals Analysis
    st.markdown("### Financial Goals Analysis")
    col1, col2 = st.columns(2)

    ret_data = client_data["goals"]["retirement"]
    ret_result = calculate_retirement_goal(
        client_data["age"], ret_data["expense"], expected_return_rate=0.12
    )

    with col1:
        st.info(
            f"**Retirement Goal**\n\nYears: {ret_result['years_to_goal']}\n\nRequired Corpus: ₹{ret_result['future_corpus']:,.2f}\n\nRequired Monthly SIP: ₹{ret_result['required_sip']:,.2f}"
        )

    edu_data = client_data["goals"]["education"]
    edu_result = calculate_child_education_goal(
        edu_data["cost"], edu_data["years"], expected_return_rate=0.12
    )

    with col2:
        st.info(
            f"**Child Education Goal**\n\nYears: {edu_result['years_to_goal']}\n\nRequired Corpus: ₹{edu_result['future_corpus']:,.2f}\n\nRequired Monthly SIP: ₹{edu_result['required_sip']:,.2f}"
        )

    # Projection Chart
    st.markdown("### Retirement Projection")
    render_projection_chart(
        0, client_data["monthly_savings"], 0.12, ret_result["years_to_goal"]
    )

    # Monte Carlo Simulation
    st.markdown("### Monte Carlo Simulation (Retirement Success Probability)")
    probability = run_monte_carlo_simulation(
        initial_corpus=0,
        monthly_sip=client_data["monthly_savings"],
        years=ret_result["years_to_goal"],
        target_corpus=ret_result["future_corpus"],
        expected_annual_return=0.12,
        annual_volatility=0.15,
    )
    st.progress(probability / 100.0)
    st.write(
        f"**{probability}%** probability of achieving your retirement corpus given current savings capacity."
    )

    # SIP Calculator Widget
    st.markdown("### Interactive SIP Calculator")
    render_sip_calculator_widget()
