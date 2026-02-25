import streamlit as st
import sys
import os

# Add root directory to sys.path to allow backend imports if needed
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from frontend.components.input_form import render_input_form
from frontend.components.dashboard import render_dashboard

st.set_page_config(page_title="AI Financial Engine", layout="wide", page_icon="📈")

st.title("AI-Powered Goal-Oriented Financial Planning Engine")

if "client_data" not in st.session_state:
    st.session_state.client_data = None

col1, col2 = st.columns([1, 2.5])

with col1:
    st.header("Client Profile")
    render_input_form()

with col2:
    st.header("Intelligence Dashboard")
    if st.session_state.client_data:
        render_dashboard(st.session_state.client_data)
    else:
        st.info("Please fill the Client Profile form to generate your financial plan.")

st.markdown("---")
with open(os.path.join(os.path.dirname(__file__), "..", "DISCLAIMER.txt"), "r") as f:
    disclaimer = f.read()
st.caption(disclaimer)
