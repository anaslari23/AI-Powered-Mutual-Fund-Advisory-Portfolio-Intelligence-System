from pathlib import Path
from datetime import datetime
import os
import sys

from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parent.parent / ".env")

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from frontend.api_client import (
    APIClientError,
    API_BASE_URL,
    create_client_audit_log,
    get_advisor_profile,
    get_client_audit_trail,
    create_client_record,
    get_client_record,
    get_current_advisor,
    get_proposal_counts,
    list_clients,
    login_advisor,
    register_advisor,
    update_advisor_profile,
    update_client_record,
)
from frontend.components.audit_trail import render_audit_trail_screen as render_audit_trail
from frontend.components.client_portal import render_client_portal
from frontend.components.dashboard import render_dashboard
from frontend.components.input_form import render_input_form
from frontend.components.meeting_notes import render_meeting_notes
from frontend.components.portfolio_snapshot import render_portfolio_snapshot
from frontend.components.proposal_builder import render_proposal_builder
from frontend.components.review_report import render_review_report

st.set_page_config(
    page_title="Vinsan Advisory",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
/* ── BASE ──────────────────────────────────────────────────── */
.stApp {
    background: #080E1A !important;
    font-family: ‘Inter’, -apple-system, BlinkMacSystemFont, ‘Segoe UI’, sans-serif;
}
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] {
    display: none !important;
    visibility: hidden !important;
}
[data-testid="stHeader"] { background: #080E1A !important; border-bottom: 1px solid #16243A; }
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: #080E1A; }
::-webkit-scrollbar-thumb { background: #1E3050; border-radius: 4px; }

/* ── TYPOGRAPHY ─────────────────────────────────────────────── */
h1 { font-size: 1.45rem !important; font-weight: 700 !important; color: #EFF6FF !important;
     letter-spacing: -0.02em; border-bottom: none !important; padding-bottom: 0 !important; margin-bottom: 0.25rem !important; }
h2 { font-size: 1.1rem !important; font-weight: 600 !important; color: #CBD5E1 !important;
     letter-spacing: -0.01em; border-bottom: 1px solid #16243A !important; padding-bottom: 0.5rem !important; }
h3 { font-size: 0.95rem !important; font-weight: 600 !important; color: #94A3B8 !important;
     border-bottom: none !important; padding-bottom: 0 !important; }
h4 { font-size: 0.78rem !important; font-weight: 600 !important; color: #64748B !important;
     text-transform: uppercase; letter-spacing: 0.09em; border-bottom: none !important; }

/* ── METRICS ────────────────────────────────────────────────── */
[data-testid="stMetric"] {
    background: #0E1829 !important;
    border: 1px solid #16243A !important;
    border-radius: 10px !important;
    padding: 14px 18px !important;
}
[data-testid="stMetricValue"] {
    font-size: 1.65rem !important; font-weight: 600 !important;
    color: #EFF6FF !important; letter-spacing: -0.025em;
}
[data-testid="stMetricLabel"] {
    font-size: 0.68rem !important; font-weight: 600 !important;
    color: #334E6E !important; text-transform: uppercase; letter-spacing: 0.1em;
}

/* ── TABS ───────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid #16243A !important;
    gap: 0 !important; padding: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important; color: #3D5A78 !important;
    font-size: 0.78rem !important; font-weight: 600 !important;
    letter-spacing: 0.05em; text-transform: uppercase;
    padding: 10px 18px !important; border: none !important;
    border-bottom: 2px solid transparent !important; border-radius: 0 !important;
    transition: color 0.15s ease;
}
.stTabs [data-baseweb="tab"]:hover { color: #7EA8D1 !important; }
.stTabs [aria-selected="true"] {
    color: #60A5FA !important; background: transparent !important;
    border-bottom: 2px solid #3B82F6 !important;
}
.stTabs [data-baseweb="tab-panel"] { padding-top: 1.25rem !important; }

/* ── BUTTONS ────────────────────────────────────────────────── */
div.stButton > button {
    background: #0E1829 !important; color: #94A3B8 !important;
    border: 1px solid #1E3050 !important; border-radius: 7px !important;
    font-size: 0.8rem !important; font-weight: 500 !important;
    padding: 7px 15px !important; letter-spacing: 0.03em;
    transition: all 0.15s ease !important;
}
div.stButton > button:hover {
    background: #142035 !important; border-color: #2D64AF !important;
    color: #BFDBFE !important;
}
div.stButton > button[kind="primary"] {
    background: #1D4ED8 !important; color: #EFF6FF !important;
    border: 1px solid #2563EB !important;
}
div.stButton > button[kind="primary"]:hover {
    background: #1E40AF !important; border-color: #1D4ED8 !important;
    color: #FFFFFF !important;
}

/* ── FORM INPUTS ────────────────────────────────────────────── */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stTextArea"] textarea {
    background: #0A1220 !important; border: 1px solid #1A2E47 !important;
    border-radius: 7px !important; color: #CBD5E1 !important;
    font-size: 0.875rem !important; caret-color: #60A5FA;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: #3B82F6 !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.12) !important;
}
[data-testid="stTextInput"] input::placeholder,
[data-testid="stNumberInput"] input::placeholder,
[data-testid="stTextArea"] textarea::placeholder { color: #2D4A6A !important; }
[data-testid="stSelectbox"] > div > div,
[data-testid="stSelectbox"] > div { background: #0A1220 !important; border-color: #1A2E47 !important; }
[data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] label {
    color: #3D5A78 !important; font-size: 0.73rem !important;
    font-weight: 600 !important; text-transform: uppercase; letter-spacing: 0.07em;
}
[data-testid="stFormSubmitButton"] > button {
    background: #1D4ED8 !important; color: #EFF6FF !important;
    border: 1px solid #2563EB !important; border-radius: 7px !important;
    font-weight: 600 !important; width: 100% !important;
}

/* ── CONTAINERS ─────────────────────────────────────────────── */
[data-testid="stContainer"][data-border="true"] {
    background: #0E1829 !important;
    border: 1px solid #16243A !important;
    border-radius: 10px !important;
    padding: 14px !important;
}

/* ── DATAFRAMES ─────────────────────────────────────────────── */
[data-testid="stDataFrame"] { border: 1px solid #16243A !important; border-radius: 8px !important; }
[data-testid="stDataFrame"] table { background: #0A1220 !important; }
[data-testid="stDataFrame"] th { background: #0E1829 !important; color: #3D5A78 !important; }
[data-testid="stDataFrame"] td { color: #94A3B8 !important; border-color: #16243A !important; }

/* ── ALERTS ─────────────────────────────────────────────────── */
[data-testid="stAlert"] { border-radius: 7px !important; border-left-width: 3px !important; }
[data-testid="stNotification"] { background: #0A1220 !important; border-color: #16243A !important; }

/* ── EXPANDER ───────────────────────────────────────────────── */
[data-testid="stExpander"] {
    background: #0E1829 !important; border: 1px solid #16243A !important; border-radius: 10px !important;
}
[data-testid="stExpander"] summary { color: #64748B !important; }

/* ── CODE ───────────────────────────────────────────────────── */
code {
    background: #0A1220 !important; color: #60A5FA !important;
    border-radius: 4px !important; padding: 2px 6px !important;
    font-size: 0.78rem !important; border: 1px solid #1A2E47 !important;
}

/* ── CAPTION ────────────────────────────────────────────────── */
[data-testid="stCaptionContainer"] p { color: #2D4A6A !important; font-size: 0.76rem !important; }

/* ── DIVIDER ────────────────────────────────────────────────── */
hr { border-color: #16243A !important; margin: 1.25rem 0 !important; }

/* ── SIDEBAR ────────────────────────────────────────────────── */
[data-testid="stSidebar"] { background: #080E1A !important; border-right: 1px solid #16243A !important; }

/* ── RADIO / CHECKBOX ───────────────────────────────────────── */
[data-testid="stRadio"] label p, [data-testid="stCheckbox"] label p { color: #64748B !important; font-size: 0.85rem !important; }

/* ── INFO / SUCCESS / WARNING / ERROR ───────────────────────── */
.stInfo { background: rgba(59,130,246,0.07) !important; border-left-color: #3B82F6 !important; }
.stSuccess { background: rgba(16,185,129,0.07) !important; border-left-color: #10B981 !important; }
.stWarning { background: rgba(245,158,11,0.07) !important; border-left-color: #F59E0B !important; }
.stError { background: rgba(239,68,68,0.07) !important; border-left-color: #EF4444 !important; }

/* ── NAV BRAND HEADER ───────────────────────────────────────── */
.advisory-nav {
    display: flex; align-items: center; justify-content: space-between;
    padding: 12px 0 12px 0; border-bottom: 1px solid #16243A; margin-bottom: 1.5rem;
}
.advisory-nav-brand { display: flex; flex-direction: column; gap: 2px; }
.advisory-nav-brand-name {
    font-size: 1.1rem; font-weight: 700; color: #EFF6FF;
    letter-spacing: -0.02em; line-height: 1;
}
.advisory-nav-brand-sub {
    font-size: 0.68rem; color: #2D4A6A; text-transform: uppercase;
    letter-spacing: 0.12em; font-weight: 600;
}

/* ── CLIENT CARD ────────────────────────────────────────────── */
.client-card-name { font-size: 0.95rem; font-weight: 600; color: #CBD5E1; margin-bottom: 2px; }
.client-card-sub { font-size: 0.73rem; color: #2D4A6A; }
.risk-badge {
    display: inline-block; font-size: 0.65rem; font-weight: 700;
    padding: 2px 8px; border-radius: 20px; text-transform: uppercase; letter-spacing: 0.06em;
}
.risk-badge-set { background: rgba(59,130,246,0.12); color: #60A5FA; border: 1px solid rgba(59,130,246,0.2); }
.risk-badge-unset { background: rgba(245,158,11,0.1); color: #FCD34D; border: 1px solid rgba(245,158,11,0.2); }

/* ── CLIENT CONTEXT BAR ─────────────────────────────────────── */
.client-context-bar {
    background: #0E1829; border: 1px solid #16243A; border-radius: 8px;
    padding: 10px 16px; margin-bottom: 1rem;
    display: flex; align-items: center; gap: 12px;
}
.context-label { font-size: 0.68rem; color: #2D4A6A; text-transform: uppercase;
    letter-spacing: 0.08em; font-weight: 600; }
.context-value { font-size: 0.82rem; color: #64748B; }
.context-value strong { color: #94A3B8; }

/* ── LOGIN ──────────────────────────────────────────────────── */
.login-brand { text-align: center; margin-bottom: 2rem; padding: 1.5rem 0 0.5rem; }
.login-brand-name { font-size: 1.6rem; font-weight: 700; color: #EFF6FF; letter-spacing: -0.03em; }
.login-brand-sub { font-size: 0.72rem; color: #2D4A6A; text-transform: uppercase;
    letter-spacing: 0.14em; font-weight: 600; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)


def _clear_login_state() -> None:
    for key in (
        "advisor_token",
        "advisor_id",
        "advisor_name",
        "advisor_email",
        "advisor_role",
        "selected_client_id",
        "selected_client_record",
        "client_data",
        "loaded_client_id",
        "show_new_client_form",
    ):
        st.session_state.pop(key, None)


def _clear_selected_client() -> None:
    for key in ("selected_client_id", "selected_client_record", "client_data", "loaded_client_id"):
        st.session_state.pop(key, None)


def _build_client_profile(client_record: dict) -> dict:
    profile = dict(client_record.get("profile_data") or {})
    for field in (
        "name", "age", "contact", "pan_placeholder", "city", "source_channel",
        "occupation", "income_bracket", "investable_surplus",
    ):
        value = client_record.get(field)
        if value is not None and field not in profile:
            profile[field] = value
    return profile


def _render_login_screen() -> None:
    _, center, _ = st.columns([1, 1.1, 1])
    with center:
        st.markdown("""
        <div class="login-brand">
            <div class="login-brand-name">Vinsan Advisory</div>
            <div class="login-brand-sub">Institutional Portfolio Intelligence</div>
        </div>
        """, unsafe_allow_html=True)

        login_tab, register_tab = st.tabs(["Sign In", "Register"])

        with login_tab:
            if st.session_state.get("register_success_message"):
                st.success(st.session_state.pop("register_success_message"))
            with st.form("advisor_login_form", clear_on_submit=False):
                email = st.text_input("Email Address")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Sign In", use_container_width=True)

            if submitted:
                try:
                    auth_response = login_advisor(email=email, password=password)
                except APIClientError as exc:
                    st.error(str(exc))
                else:
                    advisor = auth_response.get("advisor", {})
                    st.session_state["advisor_token"] = auth_response["access_token"]
                    st.session_state["advisor_id"] = advisor.get("id")
                    st.session_state["advisor_name"] = advisor.get("name", "Advisor")
                    st.session_state["advisor_email"] = advisor.get("email")
                    st.session_state["advisor_role"] = advisor.get("role", "advisor")
                    st.rerun()

        with register_tab:
            with st.form("advisor_register_form", clear_on_submit=False):
                full_name = st.text_input("Full Name")
                register_email = st.text_input("Email Address")
                register_password = st.text_input("Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
                role = st.selectbox("Role", ["advisor", "admin"], index=0)
                register_submitted = st.form_submit_button("Create Account", use_container_width=True)

            if register_submitted:
                if not full_name.strip() or not register_email.strip() or not register_password or not confirm_password:
                    st.error("All fields are required.")
                elif len(register_password) < 8:
                    st.error("Password must be at least 8 characters.")
                elif register_password != confirm_password:
                    st.error("Passwords do not match.")
                elif "@" not in register_email or "." not in register_email.split("@")[-1]:
                    st.error("Enter a valid email address.")
                else:
                    try:
                        register_advisor(
                            email=register_email,
                            password=register_password,
                            name=full_name,
                            role=role,
                        )
                    except APIClientError as exc:
                        message = str(exc)
                        if "already exists" in message.lower():
                            st.error("An account with this email already exists.")
                        else:
                            st.error(message)
                    else:
                        st.session_state["register_success_message"] = "Account created. Please sign in."
                        st.rerun()


def _render_new_client_form(token: str) -> None:
    from frontend.components.demo_data import render_demo_profile_selector
    
    render_demo_profile_selector(token)
    st.markdown("---")
    
    with st.form("new_client_form", clear_on_submit=True):
        st.markdown("### Or Create Manually")
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Name")
            age = st.number_input("Age", min_value=18, max_value=100, value=30)
            contact = st.text_input("Contact")
        with col2:
            pan_placeholder = st.text_input("PAN Placeholder")
            city = st.text_input("City")
            source_channel = st.text_input("Source Channel")
        submitted = st.form_submit_button("Create Client", width="stretch")

    if not submitted:
        return

    if not name.strip():
        st.error("Client name is required.")
        return

    try:
        created = create_client_record(
            token,
            {
                "name": name.strip(),
                "age": int(age),
                "contact": contact.strip() or None,
                "pan_placeholder": pan_placeholder.strip() or None,
                "city": city.strip() or None,
                "source_channel": source_channel.strip() or None,
            },
        )
    except APIClientError as exc:
        st.error(str(exc))
        return

    st.session_state["show_new_client_form"] = False
    st.session_state["selected_client_id"] = created["id"]
    st.session_state["loaded_client_id"] = None
    st.session_state["_flash_success"] = f"Client '{created.get('name', '')}' created successfully."
    st.rerun()


def _render_client_selector(token: str) -> None:
    advisor_role = st.session_state.get("advisor_role", "advisor")
    advisor_name = st.session_state.get("advisor_name", "Advisor")

    # ── Top nav bar ──────────────────────────────────────────────────────────
    nav_l, nav_r = st.columns([5, 1])
    with nav_l:
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:16px;padding:4px 0">
            <div>
                <div style="font-size:1.1rem;font-weight:700;color:#EFF6FF;letter-spacing:-0.02em">Vinsan Advisory</div>
                <div style="font-size:0.7rem;color:#2D4A6A;text-transform:uppercase;letter-spacing:0.1em;font-weight:600">
                    {advisor_name} &nbsp;·&nbsp; {advisor_role.title()}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with nav_r:
        if st.button("Sign Out", key="cs_logout", use_container_width=True):
            _clear_login_state()
            st.rerun()

    st.markdown("<div style='margin-top:0.5rem'></div>", unsafe_allow_html=True)

    # ── New client toggle ────────────────────────────────────────────────────
    if st.button("＋ New Client", key="cs_new_client", type="primary"):
        st.session_state["show_new_client_form"] = not st.session_state.get("show_new_client_form", False)

    if st.session_state.get("show_new_client_form"):
        st.markdown("<div style='margin-top:0.75rem'></div>", unsafe_allow_html=True)
        _render_new_client_form(token)

    st.markdown("---")

    try:
        clients = list_clients(token)
    except APIClientError as exc:
        st.error(str(exc))
        if "authorization" in str(exc).lower() or "token" in str(exc).lower():
            _clear_login_state()
            st.rerun()
        return

    try:
        proposal_counts = get_proposal_counts(token)
    except APIClientError:
        proposal_counts = {}

    # ── KPI row ──────────────────────────────────────────────────────────────
    total_clients = len(clients)
    profiled = sum(1 for c in clients if c.get("risk_class"))
    total_proposals = sum(proposal_counts.values())
    clients_with_proposals = sum(1 for c in clients if str(c.get("id")) in proposal_counts)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Clients", total_clients)
    k2.metric("Risk Profiled", profiled)
    k3.metric("Total Proposals", total_proposals)
    k4.metric("Clients with Proposals", clients_with_proposals)

    st.markdown("---")

    if not clients:
        st.info("No clients yet. Click **＋ New Client** to get started.")
        return

    st.markdown(f"<div style='font-size:0.7rem;color:#2D4A6A;text-transform:uppercase;letter-spacing:0.1em;font-weight:600;margin-bottom:0.75rem'>{total_clients} Client{'s' if total_clients!=1 else ''}</div>", unsafe_allow_html=True)

    for client in clients:
        risk_class = client.get("risk_class")
        risk_score = client.get("risk_score")
        badge_class = "risk-badge-set" if risk_class else "risk-badge-unset"
        badge_text = risk_class if risk_class else "Pending"

        with st.container(border=True):
            col1, col2, col3, col4 = st.columns([3, 1.2, 1.2, 0.9])
            with col1:
                sub_parts = [f"Age {client.get('age', '—')}"]
                if client.get("contact"):
                    sub_parts.append(client["contact"])
                if client.get("city"):
                    sub_parts.append(client["city"])
                if advisor_role == "admin" and (client.get("advisor_name") or client.get("advisor_id")):
                    sub_parts.append(f"Owner: {client.get('advisor_name') or client.get('advisor_id')}")
                st.markdown(
                    f'<div class="client-card-name">{client.get("name", "Unnamed")}</div>'
                    f'<div class="client-card-sub">{" · ".join(sub_parts)}</div>',
                    unsafe_allow_html=True,
                )
            with col2:
                st.markdown(
                    f'<div style="margin-top:4px"><span class="risk-badge {badge_class}">{badge_text}</span></div>',
                    unsafe_allow_html=True,
                )
            with col3:
                st.markdown(
                    f'<div style="font-size:0.7rem;color:#2D4A6A;text-transform:uppercase;letter-spacing:0.08em;font-weight:600;margin-top:2px">Score</div>'
                    f'<div style="font-size:1.05rem;font-weight:600;color:#94A3B8">{f"{float(risk_score):.1f}" if risk_score is not None else "—"}</div>',
                    unsafe_allow_html=True,
                )
            with col4:
                if st.button("Open →", key=f"open_client_{client['id']}", use_container_width=True):
                    st.session_state["selected_client_id"] = client["id"]
                    st.session_state["loaded_client_id"] = None
                    st.rerun()


def _render_advisor_settings(token: str) -> None:
    st.subheader("Advisor Settings")
    st.caption("Update your branding details — these appear on all generated PDF reports.")

    try:
        profile = get_advisor_profile(token)
    except APIClientError as exc:
        st.error(f"Could not load profile: {exc}")
        return

    with st.form("advisor_settings_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Display Name", value=profile.get("name") or "")
            firm_name = st.text_input("Firm / Company Name", value=profile.get("firm_name") or "",
                                      placeholder="e.g. Vinsan Financial Services")
        with col2:
            phone = st.text_input("Phone Number", value=profile.get("phone") or "",
                                  placeholder="e.g. +91 98765 43210")
            logo_path = st.text_input("Logo File Path (server path)", value=profile.get("logo_path") or "",
                                      placeholder="e.g. /app/assets/logo.png")

        st.caption(f"Email: `{profile.get('email')}` (cannot be changed) | Role: `{profile.get('role')}`")
        save = st.form_submit_button("Save Settings", use_container_width=True)

    if save:
        try:
            updated = update_advisor_profile(token, {
                "name": name.strip() or None,
                "firm_name": firm_name.strip() or None,
                "phone": phone.strip() or None,
                "logo_path": logo_path.strip() or None,
            })
            st.session_state["advisor_name"] = updated.get("name", st.session_state.get("advisor_name"))
            st.success("Settings saved. Your details will appear on the next generated report.")
        except APIClientError as exc:
            st.error(f"Failed to save: {exc}")

    st.markdown("---")
    st.markdown("**Client Portal Link**")
    st.caption("Share this URL pattern with clients after issuing a proposal:")
    st.code("http://localhost:8501/?view=portal&client_id=<CLIENT_ID>", language="text")


def _render_audit_trail(token: str, client_id: int) -> None:
    st.subheader("Audit Trail")
    st.caption("Chronological history of profile edits, proposal actions, and report issues for this client.")
    try:
        audit_entries = get_client_audit_trail(token, client_id)
    except APIClientError as exc:
        st.error(str(exc))
        return

    if not audit_entries:
        st.info("No audit events recorded for this client yet.")
        return

    for entry in audit_entries:
        container = st.container(border=True)
        with container:
            st.markdown(
                f"**{entry.get('action', 'event').replace('_', ' ').title()}**  \n"
                f"`{entry.get('timestamp', '-')}` • Advisor `{entry.get('advisor_id', '-')}`"
            )
            if entry.get("notes"):
                st.caption(entry["notes"])
            before_value = entry.get("before_value")
            after_value = entry.get("after_value")
            if before_value is not None or after_value is not None:
                before_col, after_col = st.columns(2)
                with before_col:
                    st.markdown("**Before**")
                    st.json(before_value or {})
                with after_col:
                    st.markdown("**After**")
                    st.json(after_value or {})


def _load_selected_client(token: str, client_id: int) -> tuple[dict, dict] | tuple[None, None]:
    if st.session_state.get("loaded_client_id") == client_id:
        return st.session_state.get("selected_client_record"), st.session_state.get("client_data")

    try:
        client_record = get_client_record(token, client_id)
    except APIClientError as exc:
        st.error(str(exc))
        _clear_selected_client()
        return None, None

    try:
        create_client_audit_log(
            token,
            client_id,
            {
                "action": "analysis_viewed",
                "after_value": {
                    "viewed_at": datetime.now().isoformat(),
                    "viewed_by": st.session_state.get("advisor_name"),
                },
                "notes": "Client analysis workspace opened.",
            },
        )
    except APIClientError:
        pass

    client_profile = _build_client_profile(client_record)
    st.session_state["selected_client_record"] = client_record
    st.session_state["client_data"] = client_profile
    st.session_state["loaded_client_id"] = client_id
    return client_record, client_profile


# ── Client portal: ?view=portal&client_id=X ──────────────────────────────────
_qp = st.query_params
if _qp.get("view") == "portal":
    _portal_client_id = _qp.get("client_id")
    if _portal_client_id:
        render_client_portal(token="", report_id=int(_portal_client_id))
    else:
        st.error("Invalid portal link. No client_id provided.")
    st.stop()

if "advisor_token" not in st.session_state:
    _render_login_screen()
else:
    advisor_token = st.session_state["advisor_token"]

    try:
        advisor_profile = get_current_advisor(advisor_token)
        st.session_state["advisor_id"] = advisor_profile.get("id")
        st.session_state["advisor_name"] = advisor_profile.get("name", st.session_state.get("advisor_name", "Advisor"))
        st.session_state["advisor_email"] = advisor_profile.get("email", st.session_state.get("advisor_email"))
        st.session_state["advisor_role"] = advisor_profile.get("role", st.session_state.get("advisor_role", "advisor"))
    except APIClientError as exc:
        st.error(str(exc))
        _clear_login_state()
        st.rerun()

    if not st.session_state.get("selected_client_id"):
        dash_tab, settings_tab = st.tabs(["Clients", "Settings"])
        with dash_tab:
            _render_client_selector(advisor_token)
        with settings_tab:
            _render_advisor_settings(advisor_token)
    else:
        if st.session_state.get("_flash_success"):
            st.success(st.session_state.pop("_flash_success"))

        selected_client_id = int(st.session_state["selected_client_id"])
        client_record, client_profile = _load_selected_client(advisor_token, selected_client_id)
        if not client_record or not client_profile:
            st.stop()

        # ── Client context bar ───────────────────────────────────────────────
        bar_l, bar_r = st.columns([5, 1])
        with bar_l:
            meta = []
            if client_record.get("contact"):
                meta.append(client_record["contact"])
            if client_record.get("city"):
                meta.append(client_record["city"])
            if client_record.get("source_channel"):
                meta.append(client_record["source_channel"])
            meta_str = " · ".join(meta) if meta else "—"
            advisor_label = st.session_state.get("advisor_name", "—")
            st.markdown(
                f'<div class="client-context-bar">'
                f'<div><span class="context-label">Client</span><br>'
                f'<span class="context-value"><strong>{client_record.get("name", "—")}</strong></span></div>'
                f'<div style="width:1px;background:#16243A;align-self:stretch"></div>'
                f'<div><span class="context-label">Details</span><br>'
                f'<span class="context-value">{meta_str}</span></div>'
                f'<div style="width:1px;background:#16243A;align-self:stretch"></div>'
                f'<div><span class="context-label">Advisor</span><br>'
                f'<span class="context-value">{advisor_label}</span></div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with bar_r:
            bcol1, bcol2 = st.columns(2)
            with bcol1:
                if st.button("← Back", key="back_to_clients", use_container_width=True):
                    _clear_selected_client()
                    st.rerun()
            with bcol2:
                if st.button("Sign Out", key="client_logout", use_container_width=True):
                    _clear_login_state()
                    st.rerun()

        (
            analysis_tab,
            meeting_tab,
            snapshot_tab,
            proposal_tab,
            final_review_tab,
            periodic_review_tab,
            audit_tab,
        ) = st.tabs([
            "Analysis",
            "Meeting Notes",
            "Portfolio",
            "Proposal Builder",
            "Final Review",
            "Periodic Review",
            "Audit Trail",
        ])

        with analysis_tab:
            col1, col2 = st.columns([1, 2.5])

            with col1:
                st.header("Client Profile")
                updated_profile = render_input_form(initial_data=client_profile)
                if updated_profile:
                    try:
                        updated_client = update_client_record(
                            advisor_token,
                            selected_client_id,
                            {
                                "age": int(updated_profile["age"]),
                                "occupation": updated_profile.get("occupation"),
                                "income_bracket": updated_profile.get("income_bracket"),
                                "investable_surplus": updated_profile.get("effective_monthly_savings"),
                                "profile_data": updated_profile,
                            },
                        )
                    except APIClientError as exc:
                        st.error(str(exc))
                    else:
                        merged_profile = _build_client_profile(updated_client)
                        refreshed_record = dict(client_record)
                        refreshed_record.update(updated_client)
                        refreshed_record["profile_data"] = updated_client.get("profile_data", merged_profile)
                        st.session_state["selected_client_record"] = refreshed_record
                        st.session_state["client_data"] = merged_profile
                        client_record = refreshed_record
                        client_profile = merged_profile
                        st.success("Client profile saved.")

            with col2:
                st.header("Intelligence Dashboard")
                if client_profile.get("monthly_income") is not None:
                    render_dashboard(st.session_state.get("client_data", client_profile))
                else:
                    st.info("Complete and save the client profile to load the dashboard.")

        with meeting_tab:
            render_meeting_notes(advisor_token, selected_client_id)

        with snapshot_tab:
            render_portfolio_snapshot(advisor_token, selected_client_id, client_profile)

        with proposal_tab:
            render_proposal_builder(advisor_token, selected_client_id, client_record)

        with final_review_tab:
            from frontend.components.final_review import render_final_review
            render_final_review(advisor_token, selected_client_id, client_record)

        with periodic_review_tab:
            render_review_report(advisor_token, selected_client_id, client_record)

        with audit_tab:
            render_audit_trail(advisor_token, selected_client_id)

st.markdown("<br>", unsafe_allow_html=True)
try:
    with open(PROJECT_ROOT / "DISCLAIMER.txt", "r") as f:
        disclaimer = f.read()
    st.markdown(
        f'<div style="border-top:1px solid #16243A;padding-top:0.75rem;margin-top:1rem">'
        f'<span style="font-size:0.68rem;color:#1A2E47">{disclaimer}</span></div>',
        unsafe_allow_html=True,
    )
except FileNotFoundError:
    pass
