import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from backend.engines.projection_engine import generate_projection_table


def render_allocation_chart(allocation_dict: dict):
    labels = list(allocation_dict.keys())
    values = list(allocation_dict.values())

    fig = px.pie(
        names=labels,
        values=values,
        hole=0.5,
        title="Optimized Asset Portfolio",
        template="plotly_dark",
        color_discrete_sequence=px.colors.sequential.Tealgrn,
    )
    fig.update_traces(
        textinfo="percent+label", hoverinfo="label+percent", textfont_size=14
    )
    fig.update_layout(margin=dict(t=40, b=0, l=0, r=0), showlegend=False)
    st.plotly_chart(fig, width="stretch")


def render_projection_chart(
    initial_investment: float,
    monthly_sip: float,
    annual_return_rate: float,
    years: int,
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
            hovertemplate="<b>Amount Invested:</b> ₹%{y:,.2f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["year"],
            y=df["total_value"],
            mode="lines",
            fill="tonexty",
            name="Total Value",
            hovertemplate="<b>Total Value:</b> ₹%{y:,.2f}<extra></extra>",
        )
    )

    fig.update_layout(
        template="plotly_dark",
        margin=dict(t=40, b=0, l=0, r=0),
        xaxis_title="Years",
        yaxis_title="Corpus Value (₹)",
        yaxis=dict(tickprefix="₹", tickformat=",.2f"),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig, width="stretch")
