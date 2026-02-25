import plotly.graph_objects as go
import streamlit as st


def render_risk_meter(score: float):
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": "Risk Score", "font": {"size": 24, "color": "white"}},
            gauge={
                "axis": {"range": [None, 10], "tickwidth": 1, "tickcolor": "white"},
                "bar": {"color": "#4facfe"},
                "bgcolor": "rgba(0,0,0,0)",
                "borderwidth": 2,
                "bordercolor": "gray",
                "steps": [
                    {"range": [0, 4.9], "color": "rgba(0, 255, 128, 0.3)"},
                    {"range": [5, 7.1], "color": "rgba(255, 204, 0, 0.3)"},
                    {"range": [7.1, 10], "color": "rgba(255, 51, 102, 0.3)"},
                ],
            },
        )
    )

    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": "white"},
    )
    st.plotly_chart(fig, use_container_width=True)
