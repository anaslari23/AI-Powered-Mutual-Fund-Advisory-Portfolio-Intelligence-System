"""
frontend/components/demo_data.py
──────────────────────────────────
Quick-create demo client profiles for PoC demonstrations.
"""

import streamlit as st
from frontend.api_client import APIClientError, create_client_record

_DEMO_PROFILES = [
    {
        "label": "Young Growth Investor (Age 28, ₹10k SIP, 20yr horizon)",
        "payload": {
            "name": "Arjun Mehta (Demo)",
            "age": 28,
            "contact": "9800000001",
            "pan_placeholder": "DEMO1234A",
            "city": "Mumbai",
            "source_channel": "Demo",
        },
    },
    {
        "label": "Mid-Career Balanced Investor (Age 42, Retirement, 15yr horizon)",
        "payload": {
            "name": "Priya Sharma (Demo)",
            "age": 42,
            "contact": "9800000002",
            "pan_placeholder": "DEMO5678B",
            "city": "Bangalore",
            "source_channel": "Demo",
        },
    },
    {
        "label": "Senior Safety-First Investor (Age 58, Low Volatility)",
        "payload": {
            "name": "Ramesh Iyer (Demo)",
            "age": 58,
            "contact": "9800000003",
            "pan_placeholder": "DEMO9012C",
            "city": "Chennai",
            "source_channel": "Demo",
        },
    },
]


def render_demo_profile_selector(token: str) -> None:
    """Render a one-click demo profile picker."""
    st.markdown("### Quick-Start with a Demo Profile")
    cols = st.columns(len(_DEMO_PROFILES))
    for col, profile in zip(cols, _DEMO_PROFILES):
        with col:
            if st.button(profile["label"], use_container_width=True):
                try:
                    created = create_client_record(token, profile["payload"])
                    st.session_state["show_new_client_form"] = False
                    st.session_state["selected_client_id"] = created["id"]
                    st.session_state["loaded_client_id"] = None
                    st.session_state["_flash_success"] = (
                        f"Demo client '{created.get('name', '')}' created."
                    )
                    st.rerun()
                except APIClientError as exc:
                    st.error(str(exc))
