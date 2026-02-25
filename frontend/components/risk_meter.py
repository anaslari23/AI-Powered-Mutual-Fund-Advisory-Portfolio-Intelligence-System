import plotly.graph_objects as go
import streamlit as st


def render_risk_meter(score: float):
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": "Risk Score (0-10)", "font": {"size": 24}},
            gauge={
                "axis": {"range": [None, 10], "tickwidth": 1, "tickcolor": "darkblue"},
                "bar": {"color": "black"},
                "bgcolor": "white",
                "borderwidth": 2,
                "bordercolor": "gray",
                "steps": [
                    {"range": [0, 4.9], "color": "green"},
                    {"range": [5, 7.1], "color": "yellow"},
                    {"range": [7.1, 10], "color": "red"},
                ],
            },
        )
    )

    fig.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
    st.plotly_chart(fig, use_container_width=True)
