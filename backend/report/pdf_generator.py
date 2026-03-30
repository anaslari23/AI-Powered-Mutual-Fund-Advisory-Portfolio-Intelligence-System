import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from backend.report.charts import (
    generate_risk_factor_chart,
    generate_sensitivity_chart,
    generate_score_gauges
)
from backend.engines.explanation_standards import _STANDARDS

def generate_financial_report(
    client_data: dict,
    risk_data: dict,
    goals: list,
    allocation_data: dict,
    portfolio_data: dict,
    portfolio_rebalancing: dict,
    insurance_data: dict,
    macro_data: dict,
    funds: list,
    monte_carlo: dict,
    scenarios: dict,
    investment_mode: dict,
    executive_summary: dict | None = None,
    output_path: str = "report_v2.pdf",
):
    """
    Generates a professional PDF report with 13 key sections and embedded AI insights.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    env = Environment(loader=FileSystemLoader(current_dir))
    template = env.get_template("template.html")

    # 1. Generate Charts
    charts = {
        "risk_factors": generate_risk_factor_chart(risk_data.get("explanation", {})),
        "sensitivity": generate_sensitivity_chart(
            monte_carlo.get("sensitivity_analysis") or monte_carlo.get("prob", 0)
        ),
        "score_dashboard": generate_score_gauges({
            "Risk": risk_data.get("score", 0),
            "Diversification": portfolio_data.get("diversification_score", 0),
            "AI Market": macro_data.get("ai_market_score", 85),
            "Market Stability": macro_data.get("stability", 80),
            "Goal Confidence": monte_carlo.get("prob", 0)
        })
    }

    # 2. Prepare Standards Appendix
    standards_list = list(_STANDARDS.values())

    # 3. Load disclaimer
    disclaimer_path = os.path.join(current_dir, "..", "..", "DISCLAIMER.txt")
    try:
        with open(disclaimer_path, "r", encoding="utf-8") as f:
            disclaimer_text = f.read()
    except FileNotFoundError:
        disclaimer_text = "Market performance is not guaranteed. Please consult a qualified advisor."

    # 4. Render HTML
    html_out = template.render(
        today=datetime.now().strftime("%d %b %Y"),
        executive_summary=executive_summary or {},
        client=client_data,
        risk=risk_data,
        goals=goals,
        allocation=allocation_data,
        portfolio=portfolio_data,
        portfolio_rebalancing=portfolio_rebalancing,
        insurance=insurance_data,
        macro=macro_data,
        funds=funds,
        monte_carlo=monte_carlo,
        scenarios=scenarios,
        investment_mode=investment_mode,
        charts=charts,
        standards=standards_list,
        disclaimer=disclaimer_text,
    )

    # 5. Generate PDF
    HTML(string=html_out).write_pdf(output_path)
    return output_path


def generate_vinsan_proposal_pdf(
    deck_data: dict,
    output_path: str = "vinsan_proposal.pdf",
):
    """
    Generates the Vinsan-branded advisor presentation PDF.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    env = Environment(loader=FileSystemLoader(current_dir))
    template = env.get_template("vinsan_proposal.html")

    disclaimer_path = os.path.join(current_dir, "..", "..", "DISCLAIMER.txt")
    try:
        with open(disclaimer_path, "r", encoding="utf-8") as f:
            disclaimer_text = f.read()
    except FileNotFoundError:
        disclaimer_text = "Market performance is not guaranteed. Please consult a qualified advisor."

    html_out = template.render(
        today=datetime.now().strftime("%d %b %Y"),
        deck=deck_data,
        disclaimer=disclaimer_text,
    )

    HTML(string=html_out).write_pdf(output_path)
    return output_path


def generate_review_report_pdf(
    review_data: dict,
    output_path: str = "review_report.pdf",
):
    """
    Generates a periodic portfolio review PDF.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    env = Environment(loader=FileSystemLoader(current_dir))
    template = env.get_template("review_report.html")

    disclaimer_path = os.path.join(current_dir, "..", "..", "DISCLAIMER.txt")
    try:
        with open(disclaimer_path, "r", encoding="utf-8") as f:
            disclaimer_text = f.read()
    except FileNotFoundError:
        disclaimer_text = "Market performance is not guaranteed. Please consult a qualified advisor."

    html_out = template.render(
        today=datetime.now().strftime("%d %b %Y"),
        data=review_data,
        disclaimer=disclaimer_text,
    )

    HTML(string=html_out).write_pdf(output_path)
    return output_path


def generate_proposal_deck_pdf(
    deck_data: dict,
    output_path: str = "proposal_deck.pdf",
):
    """
    Generates a presentation-style advisor deck PDF using a dedicated Jinja template.
    """
    if "cover" not in deck_data and "client_snapshot" in deck_data:
        client_snapshot = deck_data.get("client_snapshot", {})
        why_this_category = deck_data.get("why_this_category", {})
        sip_illustration = deck_data.get("sip_illustration", {})
        benchmark_comparison = deck_data.get("benchmark_comparison", [])
        advisor_contact = deck_data.get("advisor_contact", {})

        monthly_sip = 0.0
        sip_rows = []
        for row in sip_illustration.get("rows", []):
            monthly_sip = float(row.get("monthly_sip", monthly_sip or 0.0))
            horizon_label = str(row.get("horizon", "")).strip()
            horizon_years = 0
            if horizon_label:
                try:
                    horizon_years = int(horizon_label.split()[0])
                except (ValueError, IndexError):
                    horizon_years = 0
            sip_rows.append(
                {
                    "monthly_sip": float(row.get("monthly_sip", 0.0)),
                    "horizon_years": horizon_years,
                    "assumed_return_pct": 12,
                    "projected_corpus": float(row.get("projected_corpus", 0.0)),
                }
            )

        benchmark_rows = []
        for row in benchmark_comparison:
            benchmark_rows.append(
                {
                    "period": row.get("name", "Selected Fund"),
                    "scheme_pct": float(row.get("alpha_1y", 0.0)),
                    "benchmark_pct": float(row.get("benchmark_1y_return", 0.0)),
                    "category_avg_pct": float(row.get("benchmark_3y_return", 0.0)),
                }
            )

        deck_data = {
            "cover": {
                "client_name": client_snapshot.get("name", "Client"),
                "risk_class": client_snapshot.get("risk_category", "Moderate"),
                "advisor_name": advisor_contact.get("name", "Assigned Advisor"),
                "version_number": deck_data.get("version_number", 1),
            },
            "category_rationale": {
                "category_name": client_snapshot.get("primary_goal", "Investment Proposal"),
                "rationale_text": why_this_category.get("allocation_reasoning")
                or why_this_category.get("narrative")
                or "",
            },
            "sip_matrix": {
                "rows": sip_rows,
            },
            "benchmark_data": benchmark_rows,
            "advisor_contact": advisor_contact,
            "version_number": deck_data.get("version_number", 1),
            "issue_date": deck_data.get("issue_date", datetime.now().strftime("%d %b %Y")),
            "advisory_narrative": {
                "client_summary": (
                    f"{client_snapshot.get('name', 'Client')} is a "
                    f"{client_snapshot.get('risk_category', 'Moderate')} investor with "
                    f"an investible surplus of Rs {monthly_sip:,.0f} per month focused on "
                    f"{client_snapshot.get('primary_goal', 'long-term wealth creation')}."
                ),
                "risk_explanation": why_this_category.get("headline", ""),
                "allocation_explanation": why_this_category.get("allocation_reasoning", ""),
                "portfolio_commentary": why_this_category.get("market_context", ""),
                "negative_justification": (
                    "Alternative categories were deprioritized because they fit the client's "
                    "risk profile, goal horizon, and current market context less effectively."
                ),
                "final_recommendation": why_this_category.get("narrative")
                or why_this_category.get("allocation_reasoning")
                or "",
            },
            "affordability_indicator": deck_data.get("affordability_indicator", "Feasible"),
            "assumptions": {
                "display_text": (
                    f"SIP illustration assumes a 12% annualized return with a monthly investment "
                    f"of Rs {monthly_sip:,.0f}. Outputs are illustrative and based on current planning inputs."
                ),
            },
            "category_explanation": why_this_category.get("narrative", ""),
            "allocation": deck_data.get("allocation", {}),
        }

    current_dir = os.path.dirname(os.path.abspath(__file__))
    env = Environment(loader=FileSystemLoader(current_dir))
    template = env.get_template("proposal_deck.html")

    disclaimer_path = os.path.join(current_dir, "..", "..", "DISCLAIMER.txt")
    try:
        with open(disclaimer_path, "r", encoding="utf-8") as f:
            disclaimer_text = f.read()
    except FileNotFoundError:
        disclaimer_text = "Market performance is not guaranteed. Please consult a qualified advisor."

    html_out = template.render(
        today=datetime.now().strftime("%d %b %Y"),
        deck=deck_data,
        disclaimer=disclaimer_text,
    )

    HTML(string=html_out).write_pdf(output_path)
    return output_path
