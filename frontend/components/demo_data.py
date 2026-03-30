"""
frontend/components/demo_data.py
─────────────────────────────────
UI component to select and load demo profiles into the system.
"""
import streamlit as st

from backend.engines.demo_profiles import (
    get_demo_client_create_payload,
    get_demo_profile_data,
    list_demo_profiles,
)
from frontend.api_client import (
    APIClientError,
    create_client_record,
    update_client_record,
)


def render_demo_profile_selector(token: str) -> None:
    """Render a dropdown to create a new client from a demo profile."""
    st.markdown("### Load Demo Profile")
    st.caption("Quickly populate a complete client record with pre-configured data for testing.")

    profiles = list_demo_profiles()
    if not profiles:
        st.info("No demo profiles are configured.")
        return

    options = {p["label"]: p["key"] for p in profiles}

    col1, col2 = st.columns([3, 1])
    with col1:
        selected_label = st.selectbox("Select Demo Profile", options=list(options.keys()), key="demo_profile_select")

    with col2:
        st.write("")  # Spacing to align with selectbox
        st.write("")
        if st.button("Load Profile", width="stretch", type="secondary"):
            profile_key = options[selected_label]

            # 1. Create base client
            base_payload = get_demo_client_create_payload(profile_key)
            try:
                with st.spinner(f"Creating profile for {base_payload['name']}..."):
                    created = create_client_record(token, base_payload)
                    client_id = created["id"]

                    # 2. Update with rich profile data
                    rich_data = get_demo_profile_data(profile_key)
                    update_client_record(token, client_id, {"profile_data": rich_data})

                    st.session_state["show_new_client_form"] = False
                    st.session_state["selected_client_id"] = client_id
                    st.session_state["loaded_client_id"] = None
                    st.success(f"Successfully loaded {base_payload['name']}!")
                    st.rerun()
            except APIClientError as exc:
                st.error(f"Failed to load demo profile: {exc}")
