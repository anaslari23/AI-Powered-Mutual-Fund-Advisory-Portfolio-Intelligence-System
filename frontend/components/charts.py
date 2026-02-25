import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from backend.engines.projection_engine import generate_projection_table


def render_allocation_chart(allocation_dict: dict):
    labels = list(allocation_dict.keys())
    values = list(allocation_dict.values())

    fig = px.pie(names=labels, values=values, hole=0.4, title="Asset Portfolio Layout")
    fig.update_traces(textinfo="percent+label", hoverinfo="label+percent")
    st.plotly_chart(fig, use_container_width=True)


def render_projection_chart(
    initial_investment: float, monthly_sip: float, annual_return_rate: float, years: int
):
    if years <= 0:
        st.warning("Projection years must be > 0.")
        return

    df = generate_projection_table(
        initial_investment, monthly_sip, annual_return_rate, years
    )

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["year"],
            y=df["invested"],
            mode="lines",
            fill="tozeroy",
            name="Amount Invested",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["year"],
            y=df["total_value"],
            mode="lines",
            fill="tonexty",
            name="Total Value",
        )
    )

    fig.update_layout(
        title="Wealth Projection Over Time",
        xaxis_title="Years",
        yaxis_title="Corpus Value (₹)",
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)
