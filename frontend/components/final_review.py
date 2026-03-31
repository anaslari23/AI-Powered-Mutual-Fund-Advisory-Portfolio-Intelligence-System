"""
frontend/components/final_review.py
─────────────────────────────────────
Final Review: pre-issuance advisor checklist, proposal summary, and compliance
sign-off screen. Sits between Proposal Builder and Periodic Review in the
advisor workflow.
"""
import streamlit as st
from typing import Any, Dict

from frontend.api_client import APIClientError, list_proposals, list_issued_reports


_CHECKLIST_ITEMS = [
    ("risk_profile_verified", "Risk profile verified and questionnaire completed"),
    ("goals_documented", "Client goals documented and acknowledged"),
    ("allocation_reviewed", "Proposed allocation reviewed and within mandate"),
    ("sip_illustration_checked", "SIP illustration reviewed for accuracy"),
    ("benchmark_data_verified", "Benchmark comparison data verified"),
    ("rationale_documented", "Fund category rationale documented"),
    ("override_noted", "Any advisor overrides are noted and justified"),
    ("client_consent", "Client verbal / written acknowledgement obtained"),
    ("regulatory_disclaimer", "Regulatory disclaimer shared with client"),
    ("kyc_confirmed", "KYC / PAN details confirmed and on record"),
]


def _render_proposal_summary(proposal: Dict[str, Any]) -> None:
    """Render a compact read-only summary of the selected proposal."""
    status = proposal.get("status", "draft")
    version = proposal.get("version_number", "?")
    created = (proposal.get("created_at") or "")[:10]

    status_colors = {
        "draft": "#60A5FA",
        "reviewed": "#FCD34D",
        "overridden": "#FB923C",
        "approved": "#34D399",
        "issued": "#A3E635",
    }
    color = status_colors.get(status, "#94A3B8")

    st.markdown(
        f'<div style="display:flex;align-items:center;gap:12px;margin-bottom:0.75rem">'
        f'<span style="font-size:1rem;font-weight:600;color:#CBD5E1">Proposal v{version}</span>'
        f'<span style="font-size:0.72rem;font-weight:700;padding:2px 10px;border-radius:20px;'
        f'background:rgba(255,255,255,0.06);color:{color};border:1px solid {color}40;'
        f'text-transform:uppercase;letter-spacing:0.07em">{status}</span>'
        f'<span style="font-size:0.72rem;color:#334E6E">{created}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    snap = (proposal.get("system_draft") or {}).get("client_snapshot", {})
    fund_cat = (proposal.get("system_draft") or {}).get("fund_category", "—")
    rationale = proposal.get("category_rationale") or "—"
    override = proposal.get("override_reason") or ""

    col1, col2, col3 = st.columns(3)
    col1.metric("Client", snap.get("name", "—"))
    col2.metric("Risk Class", snap.get("risk_class", "—"))
    col3.metric("Fund Category", fund_cat)

    sip_rows = (proposal.get("sip_assumptions") or {}).get("rows", [])
    if sip_rows:
        st.markdown(
            '<div style="font-size:0.7rem;color:#2D4A6A;text-transform:uppercase;'
            'letter-spacing:0.08em;font-weight:600;margin-top:0.75rem;margin-bottom:0.25rem">'
            "SIP Illustration Summary</div>",
            unsafe_allow_html=True,
        )
        for row in sip_rows:
            sip_amt = row.get("monthly_sip", 0)
            horizon = row.get("horizon_years", 0)
            ret = row.get("assumed_return_pct", 0)
            corpus = row.get("projected_corpus", 0)
            st.markdown(
                f'<div style="font-size:0.82rem;color:#64748B;padding:2px 0">'
                f'₹{sip_amt:,.0f}/mo · {horizon} yrs · {ret}% → '
                f'<strong style="color:#94A3B8">₹{corpus:,.0f}</strong>'
                f'</div>',
                unsafe_allow_html=True,
            )

    if rationale and rationale != "—":
        st.markdown("**Category Rationale**")
        st.markdown(
            f'<div style="font-size:0.84rem;color:#64748B;background:#0A1220;'
            f'border:1px solid #1A2E47;border-radius:7px;padding:10px 14px;'
            f'line-height:1.55">{rationale}</div>',
            unsafe_allow_html=True,
        )

    if override:
        st.markdown(
            f'<div style="margin-top:0.5rem;font-size:0.78rem;color:#FB923C;'
            f'background:rgba(251,146,60,0.07);border:1px solid rgba(251,146,60,0.2);'
            f'border-radius:6px;padding:8px 12px">⚠ Override noted: {override}</div>',
            unsafe_allow_html=True,
        )


def _render_checklist(client_id: int) -> bool:
    """Render the advisor pre-issuance checklist. Returns True if all items checked."""
    st.markdown("#### Pre-Issuance Compliance Checklist")
    st.caption(
        "Confirm each item before marking the proposal ready for issuance. "
        "All boxes must be checked to proceed."
    )

    all_checked = True
    for key, label in _CHECKLIST_ITEMS:
        session_key = f"fr_check_{client_id}_{key}"
        checked = st.checkbox(label, key=session_key)
        if not checked:
            all_checked = False

    return all_checked


def render_final_review(token: str, client_id: int, client_record: Dict[str, Any]) -> None:
    st.subheader("Final Review")
    st.caption(
        "Pre-issuance advisor sign-off. Review the active proposal, complete the "
        "compliance checklist, and confirm readiness before issuing to the client."
    )

    # ── Fetch proposals ──────────────────────────────────────────────────────
    try:
        proposals = list_proposals(token, client_id)
    except APIClientError as exc:
        st.error(f"Could not load proposals: {exc}")
        return

    if not proposals:
        st.info(
            "No proposals found for this client. "
            "Create and save a proposal in the **Proposal Builder** tab first."
        )
        return

    # ── Proposal selector ────────────────────────────────────────────────────
    proposal_options = list(range(len(proposals)))
    selected_idx = st.selectbox(
        "Select Proposal to Review",
        options=proposal_options,
        format_func=lambda i: (
            f"v{proposals[i].get('version_number', i + 1)} — "
            f"{proposals[i].get('status', 'draft').title()} — "
            f"{(proposals[i].get('created_at') or '')[:10]}"
        ),
        key=f"fr_proposal_select_{client_id}",
    )
    proposal = proposals[selected_idx]
    status = proposal.get("status", "draft")

    st.markdown("---")

    # ── Two-column layout: summary | checklist ───────────────────────────────
    left_col, right_col = st.columns([1.2, 1])

    with left_col:
        st.markdown("#### Proposal Summary")
        with st.container(border=True):
            _render_proposal_summary(proposal)

    with right_col:
        all_checked = _render_checklist(client_id)

        st.markdown("---")

        # ── Sign-off notes ─────────────────────────────────────────────────
        st.markdown("#### Advisor Sign-Off Notes")
        notes = st.text_area(
            "Final comments or caveats (optional)",
            height=100,
            key=f"fr_signoff_notes_{client_id}",
            placeholder=(
                "e.g. Client confirmed investment of ₹10,000/month via SIP. "
                "Agreed to review in 12 months."
            ),
        )

        # ── Status banner ──────────────────────────────────────────────────
        if status == "issued":
            st.success("✅ This proposal has already been issued to the client.")
        elif status == "approved":
            st.info("🟢 Proposal is approved — ready to issue from the **Proposal Builder** tab.")
        elif not all_checked:
            st.warning("Complete all checklist items above before marking as reviewed.")
        else:
            st.success("All checklist items confirmed. Ready to mark as reviewed.")

    st.markdown("---")

    # ── Issued reports history ───────────────────────────────────────────────
    st.markdown("#### Issued Reports for This Client")
    try:
        issued_reports = list_issued_reports(token, client_id)
    except APIClientError:
        issued_reports = []

    if not issued_reports:
        st.caption("No reports issued yet for this client.")
    else:
        for report in issued_reports:
            with st.container(border=True):
                rc1, rc2 = st.columns([3, 1])
                with rc1:
                    rtype = report.get("report_type", "").replace("_", " ").title()
                    issued_at = (report.get("issue_date") or "")[:16]
                    version = report.get("version_number", "?")
                    st.markdown(
                        f"**v{version}** — {rtype}  \n"
                        f'<span style="font-size:0.75rem;color:#334E6E">'
                        f"Issued: {issued_at} | Advisor #{report.get('issued_by')}"
                        f"</span>",
                        unsafe_allow_html=True,
                    )
                with rc2:
                    pdf_path = report.get("pdf_path")
                    if pdf_path:
                        try:
                            with open(pdf_path, "rb") as f:
                                st.download_button(
                                    "⬇️ PDF",
                                    data=f.read(),
                                    file_name=pdf_path.split("/")[-1],
                                    mime="application/pdf",
                                    key=f"fr_dl_{report['id']}",
                                    use_container_width=True,
                                )
                        except Exception:
                            st.caption(f"`{pdf_path}`")
