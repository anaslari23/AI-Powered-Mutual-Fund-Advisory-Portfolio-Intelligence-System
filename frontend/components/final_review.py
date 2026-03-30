"""
frontend/components/final_review.py
───────────────────────────────────
New Final Review screen. Displays full proposal preview with all
deterministic narratives, affordability checks, and assumptions.
Provides the ONLY path to PDF issuance, enforcing review.
"""
import streamlit as st
import pandas as pd
from typing import Any, Dict

from backend.engines.advisory_language_engine import build_assumptions_block, generate_advisory_narrative
from backend.engines.affordability_engine import check_affordability
from backend.engines.category_explainer import explain_category
from frontend.api_client import (
    APIClientError,
    approve_proposal,
    issue_proposal_report,
    list_issued_reports,
    list_proposals,
)

_STATUS_COLORS = {
    "draft": "🔵",
    "reviewed": "🟡",
    "overridden": "🟠",
    "approved": "🟢",
    "issued": "✅",
}


def render_final_review(token: str, client_id: int, client_record: Dict[str, Any]) -> None:
    st.subheader("Final Review & Report Issuance (Mandatory)")
    st.caption("Review the complete advisory narrative, validate affordability, and issue the final PDF report.")

    try:
        proposals = list_proposals(token, client_id)
    except APIClientError as exc:
        st.error(str(exc))
        return

    if not proposals:
        st.info("No proposals yet. Please build one in the Proposal Builder first.")
        return

    # Select the latest actionable proposal
    actionable = [p for p in proposals if p.get("status") in ("draft", "reviewed", "overridden", "approved")]
    if not actionable:
        st.info("No actionable proposals available for review.")
        return

    proposal = actionable[0]
    status = proposal.get("status", "draft")
    st.markdown(f"**Latest Proposal:** v{proposal.get('version_number', '?')} — {_STATUS_COLORS.get(status, '')} {status.title()}")

    # ── Gather data for narratives ──────────────────────────────────────────
    profile = client_record.get("profile_data") or {}
    analysis = client_record.get("analysis") or {}
    
    # 1. Proposal configuration
    sys_draft = proposal.get("system_draft") or {}
    adv_final = proposal.get("advisor_final") or {}
    eff_draft = adv_final if adv_final else sys_draft
    
    # Risk
    risk_q = analysis.get("risk_questionnaire") or {}
    risk_info = {"score": risk_q.get("score", 5.0), "category": eff_draft.get("client_snapshot", {}).get("risk_class", "Moderate")}
    
    # Goals
    goals = analysis.get("goal_lines") or []
    
    # Portfolio
    port_snap = analysis.get("portfolio_snapshot") or {}
    breakdown = {
        "Mutual Funds / Equity": port_snap.get("equity", 0),
        "Fixed Deposits / Bonds": port_snap.get("fd_bonds", 0),
        "Savings / Cash": port_snap.get("cash", 0),
        "Gold": port_snap.get("gold", 0),
    }
    
    # Guidance / Allocation
    guidance = {"allocation": eff_draft.get("allocation", sys_draft.get("allocation", {}))}
    
    # Category Rationale
    cat_name = eff_draft.get("fund_category", sys_draft.get("fund_category", "Mutual Fund"))
    human_rationale = proposal.get("category_rationale") or "No rationale provided."
    cat_expl = explain_category(cat_name, profile={"risk_class": risk_info["category"]})

    # SIP assumptions
    sip_data = (proposal.get("sip_assumptions") or {}).get("rows", [])
    primary_sip = sip_data[-1] if sip_data else {"monthly_sip": 0, "horizon_years": 10, "assumed_return_pct": 12}
    
    # Generate Core Narrative
    narrative = generate_advisory_narrative(
        profile=profile,
        risk=risk_info,
        goals=goals,
        guidance=guidance,
        portfolio={"breakdown": breakdown, "total_corpus": sum(breakdown.values())}
    )

    # Affordability check
    monthly_surplus = profile.get("investable_surplus") or profile.get("effective_monthly_savings") or 0
    affordability = check_affordability(primary_sip.get("monthly_sip", 0), monthly_surplus)

    # Assumptions block
    assumptions = build_assumptions_block(
        return_rate=primary_sip.get("assumed_return_pct", 12.0),
        horizon_years=primary_sip.get("horizon_years", 10),
    )

    # ── Render Preview ────────────────────────────────────────────────────────
    
    with st.expander("📝 1. Client Summary & Recommendation Logic", expanded=True):
        st.markdown("**Client Summary**")
        st.write(narrative["client_summary"])
        st.markdown("**Risk Explanation**")
        st.write(narrative["risk_explanation"])
        st.markdown("**Allocation Strategy**")
        st.write(narrative["allocation_explanation"])
        st.markdown("**Portfolio Commentary**")
        st.write(narrative["portfolio_commentary"])

    with st.expander("🎯 2. Product Category Justification", expanded=True):
        st.markdown(f"**WHY: {cat_name}**")
        st.write(human_rationale)
        st.write(cat_expl["narrative"])
        st.markdown("**WHY NOT (Alternatives)**")
        st.write(narrative["negative_justification"])

    with st.expander("📊 3. SIP & Affordability", expanded=True):
        if sip_data:
            st.dataframe(pd.DataFrame([{
                "Monthly SIP (₹)": f"₹{r.get('monthly_sip', 0):,.0f}",
                "Horizon": f"{r.get('horizon_years', 0)} yrs",
                "Assumed Return": f"{r.get('assumed_return_pct', 0)}%",
                "Projected Corpus": f"₹{r.get('projected_corpus', 0):,.0f}",
            } for r in sip_data]), use_container_width=True, hide_index=True)
        else:
            st.info("No SIP data configued in Proposal.")

        st.markdown("---")
        # Affordability Visual Indicator
        color_map = {"feasible": "green", "stretch": "orange", "not_advisable": "red"}
        status_color = color_map.get(affordability["status"], "gray")
        st.markdown(f"**Affordability Status:** :{status_color}[**{affordability['short_label']}**]")
        st.caption(affordability["message"])
        
        # Assumption Disclosure Box
        st.info(f"**Assumptions Used:**\n\n{assumptions['display_text']}")

    with st.expander("⚖️ 4. Final Conclusion", expanded=True):
        st.write(narrative["final_recommendation"])


    # ── Strict Validation (A7) ────────────────────────────────────────────────
    validation_passed = True
    errors = []
    
    if affordability["status"] == "not_advisable":
        validation_passed = False
        errors.append("Affordability is marked 'Not Advisable'. Please reduce SIP amount in Proposal Builder.")
    if not primary_sip.get("monthly_sip"):
        validation_passed = False
        errors.append("No valid SIP amounts found in proposal.")
    if not human_rationale or "No rationale provided" in human_rationale:
        validation_passed = False
        errors.append("Advisor category rationale is missing.")

    st.markdown("---")
    if not validation_passed:
        st.error("⚠️ **Validation Failed:** Cannot issue report until the following issues are resolved:")
        for err in errors:
            st.markdown(f"- {err}")
    else:
        st.success("✅ **Validation Passed:** Report is ready for issuance.")

    # ── Approval & Issue ──────────────────────────────────────────────────────
    action_col1, action_col2 = st.columns(2)
    with action_col1:
        if status in ("draft", "reviewed", "overridden"):
            if st.button("✅ Approve Proposal", key=f"fr_approve_{client_id}", use_container_width=True, disabled=not validation_passed):
                try:
                    approve_proposal(token, client_id, proposal["id"])
                    st.success("Proposal approved.")
                    st.rerun()
                except APIClientError as exc:
                    st.error(str(exc))
        else:
            st.success("Proposal is Approved.")

    with action_col2:
        if status == "approved":
            report_type = st.selectbox(
                "Report Type",
                ["proposal_deck", "vinsan_proposal"],
                format_func=lambda x: "Standard Proposal Deck" if x == "proposal_deck" else "Vinsan Presentation Deck",
                key=f"fr_report_type_{client_id}",
            )
            issue_btn_disabled = not validation_passed
            
            if st.button("📄 Issue Final Report (PDF)", key=f"fr_issue_{client_id}", use_container_width=True, disabled=issue_btn_disabled, type="primary"):
                # We also need to pass the narrative payload so backend PDF generator can inject it.
                payload = {
                    "report_type": report_type,
                    "advisory_narrative": narrative,
                    "affordability_indicator": affordability["short_label"],
                    "assumptions": assumptions,
                    "category_explanation": cat_expl["narrative"],
                }
                try:
                    with st.spinner("Generating Presentation-Grade PDF..."):
                        issued = issue_proposal_report(token, client_id, proposal["id"], payload)
                    st.success(f"Report issued. PDF: `{issued.get('pdf_path', 'N/A')}`")
                    if issued.get("pdf_path"):
                        try:
                            with open(issued["pdf_path"], "rb") as f:
                                st.download_button(
                                    "⬇️ Download PDF",
                                    data=f.read(),
                                    file_name=issued["pdf_path"].split("/")[-1],
                                    mime="application/pdf",
                                    key=f"fr_dl_new_{client_id}"
                                )
                        except Exception:
                            st.info("PDF generated on server. Check the reports/ directory.")
                    st.rerun()
                except APIClientError as exc:
                    st.error(str(exc))
