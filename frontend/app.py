import streamlit as st
import sys
import os

# Add root directory to sys.path to allow backend imports if needed
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from frontend.components.input_form import render_input_form
from frontend.components.dashboard import render_dashboard

st.set_page_config(page_title="AI Financial Engine", layout="wide", page_icon="📈")

# Premium Custom CSS
st.markdown(
    """
<style>
    /* Dark Theme Optimization */
    .stApp {
        background-color: #0e1117;
        color: #e0e0e0;
    }
    /* Sleek Cards */
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
        color: #4facfe;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 1.1rem;
        color: #a0aab2;
    }
    /* Headers & Text */
    h1, h2, h3 {
        color: #ffffff;
        font-family: 'Inter', sans-serif;
    }
    /* Input Forms Styling */
    div[data-testid="stForm"] {
        background: rgba(30, 41, 59, 0.5);
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #334155;
    }
    /* Buttons */
    div.stButton > button:first-child {
        background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    div.stButton > button:first-child:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(79, 172, 254, 0.4);
        color: white;
    }
</style>
""",
    unsafe_allow_html=True,
)

st.title("⚡ AI-Powered Portfolio Intelligence Engine")

st.markdown("""
Welcome to the intelligent terminal. Define your profile on the left to activate the **Financial Quantum Engine** on the right.
""")

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
st.caption(f"⚠️ **Disclaimer:** {disclaimer}")
