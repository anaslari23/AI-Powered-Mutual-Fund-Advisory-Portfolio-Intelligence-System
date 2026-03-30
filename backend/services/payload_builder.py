from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from backend.database.models import Client, GoalLine, PortfolioSnapshot, ProposalDraft, RiskQuestionnaire
from backend.engines.advisory_language_engine import build_assumptions_block, generate_advisory_narrative
from backend.engines.affordability_engine import check_affordability
from backend.engines.allocation_engine import get_asset_allocation
from backend.engines.category_explainer import explain_category
from backend.engines.guidance_engine import generate_guidance
from backend.engines.portfolio_engine import analyze_portfolio
from backend.engines.rejection_engine import generate_rejection_logic
from backend.engines.risk_engine import calculate_risk_score
from backend.engines.sip_storyteller import generate_sip_story
from backend.scoring.assumption_box import AssumptionBox
from backend.engines.final_advisory_engine import generate_final_advisory

REQUIRED_KEYS = [
    "client_profile",
    "risk_output",
    "goal_output",
    "guidance_output",
    "allocation_output",
    "portfolio_analysis",
    "sip_output",
    "affordability",
    "fund_recommendations",
    "assumptions",
]


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _latest_risk(db_session: Session, client_id: int) -> Optional[RiskQuestionnaire]:
    return (
        db_session.query(RiskQuestionnaire)
        .filter(RiskQuestionnaire.client_id == client_id)
        .order_by(RiskQuestionnaire.created_at.desc())
        .first()
    )


def _goal_lines(db_session: Session, client_id: int) -> List[GoalLine]:
    return (
        db_session.query(GoalLine)
        .filter(GoalLine.client_id == client_id)
        .order_by(GoalLine.priority.asc(), GoalLine.id.asc())
        .all()
    )


def _latest_portfolio(db_session: Session, client_id: int) -> Optional[PortfolioSnapshot]:
    return (
        db_session.query(PortfolioSnapshot)
        .filter(PortfolioSnapshot.client_id == client_id)
        .order_by(PortfolioSnapshot.created_at.desc())
        .first()
    )


def _latest_draft(db_session: Session, client_id: int) -> Optional[ProposalDraft]:
    return (
        db_session.query(ProposalDraft)
        .filter(ProposalDraft.client_id == client_id)
        .order_by(ProposalDraft.created_at.desc())
        .first()
    )


def get_client_from_db(client_id: int, db_session: Session) -> Client:
    client = db_session.query(Client).filter(Client.id == client_id).first()
    if client is None:
        raise ValueError("Client not found")
    return client


def extract_client_profile(client: Client) -> Dict[str, Any]:
    profile = dict(client.profile_data or {})
    monthly_income = _safe_float(profile.get("monthly_income"))
    monthly_surplus = _safe_float(
        profile.get("monthly_surplus", profile.get("effective_monthly_savings", profile.get("investable_surplus")))
    )
    if monthly_surplus <= 0:
        monthly_surplus = _safe_float(client.investable_surplus)

    return {
        "client_id": client.id,
        "name": client.name,
        "age": client.age,
        "contact": client.contact,
        "city": client.city,
        "source_channel": client.source_channel,
        "occupation": client.occupation,
        "income_bracket": client.income_bracket,
        "monthly_income": monthly_income,
        "monthly_surplus": monthly_surplus,
        "investable_surplus": monthly_surplus,
        "effective_monthly_savings": monthly_surplus,
        "dependents": _safe_int(profile.get("dependents")),
        "marital_status": profile.get("marital_status"),
        "risk_appetite": profile.get("risk_appetite"),
        "behavior_traits": profile.get("behavior_traits", profile.get("behavior")),
        "existing_fd": _safe_float(profile.get("existing_fd")),
        "existing_savings": _safe_float(profile.get("existing_savings")),
        "existing_gold": _safe_float(profile.get("existing_gold")),
        "existing_mutual_funds": _safe_float(profile.get("existing_mutual_funds")),
        "outstanding_loans": profile.get("outstanding_loans") or [],
        "raw_profile": profile,
    }


def _build_risk_output(
    client_profile: Dict[str, Any], latest_risk: Optional[RiskQuestionnaire]
) -> Optional[Dict[str, Any]]:
    if latest_risk is not None:
        return {
            "score": float(latest_risk.score),
            "class": latest_risk.risk_class,
            "risk_class": latest_risk.risk_class,
            "source": "saved_analysis",
            "answers": latest_risk.answers or {},
            "created_at": latest_risk.created_at.isoformat() if latest_risk.created_at else None,
        }

    age = _safe_int(client_profile.get("age"))
    monthly_income = _safe_float(client_profile.get("monthly_income"))
    monthly_surplus = _safe_float(client_profile.get("monthly_surplus"))
    if age <= 0 or monthly_income <= 0 or monthly_surplus <= 0:
        return None

    computed = calculate_risk_score(
        age=age,
        dependents=_safe_int(client_profile.get("dependents")),
        monthly_income=monthly_income,
        monthly_savings=monthly_surplus,
        behavioral_trait=client_profile.get("behavior_traits"),
    )
    return {
        **computed,
        "class": computed.get("category", computed.get("risk_class", "Moderate")),
        "risk_class": computed.get("category", computed.get("risk_class", "Moderate")),
        "source": "engine",
    }


def _build_goal_output(goal_lines: List[GoalLine]) -> Optional[Dict[str, Any]]:
    if not goal_lines:
        return None

    goals = [
        {
            "goal_type": goal.goal_type,
            "target_amount": float(goal.target_amount),
            "horizon_years": int(goal.horizon_years),
            "priority": int(goal.priority),
        }
        for goal in goal_lines
    ]
    primary_goal = goals[0]
    return {
        "goals": goals,
        "primary_goal": primary_goal.get("goal_type"),
        "horizon": primary_goal.get("horizon_years"),
        "target_amount": primary_goal.get("target_amount"),
        "total_target_amount": round(sum(goal["target_amount"] for goal in goals), 2),
    }


def _extract_saved_allocation(latest_draft: Optional[ProposalDraft]) -> Optional[Dict[str, float]]:
    if latest_draft is None:
        return None

    for source in (latest_draft.advisor_final or {}, latest_draft.system_draft or {}):
        allocation = source.get("allocation")
        if isinstance(allocation, dict) and allocation:
            return {str(key): _safe_float(value) for key, value in allocation.items()}
        allocation = source.get("target_allocation")
        if isinstance(allocation, dict) and allocation:
            return {str(key): _safe_float(value) for key, value in allocation.items()}
    return None


def _build_allocation_output(
    risk_output: Optional[Dict[str, Any]],
    latest_draft: Optional[ProposalDraft],
) -> Optional[Dict[str, Any]]:
    saved_allocation = _extract_saved_allocation(latest_draft)
    if saved_allocation:
        return {
            "category": "Saved Advisory Allocation",
            "allocation": saved_allocation,
            "source": "saved_proposal",
        }

    if not risk_output:
        return None

    score = _safe_float(risk_output.get("score"))
    if score <= 0:
        return None

    allocation = get_asset_allocation(score)
    allocation["source"] = "engine"
    return allocation


def _build_portfolio_analysis(
    client_profile: Dict[str, Any],
    portfolio_snapshot: Optional[PortfolioSnapshot],
    risk_output: Optional[Dict[str, Any]],
    goal_output: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    existing_fd = _safe_float(client_profile.get("existing_fd"))
    existing_savings = _safe_float(client_profile.get("existing_savings"))
    existing_gold = _safe_float(client_profile.get("existing_gold"))
    existing_mutual_funds = _safe_float(client_profile.get("existing_mutual_funds"))

    if portfolio_snapshot is not None:
        existing_fd = _safe_float(portfolio_snapshot.fd_bonds, existing_fd)
        existing_savings = _safe_float(portfolio_snapshot.cash, existing_savings)
        existing_gold = _safe_float(portfolio_snapshot.gold, existing_gold)
        existing_mutual_funds = _safe_float(portfolio_snapshot.equity, existing_mutual_funds)

    return analyze_portfolio(
        existing_fd=existing_fd,
        existing_savings=existing_savings,
        existing_gold=existing_gold,
        existing_mutual_funds=existing_mutual_funds,
        risk_score=_safe_float((risk_output or {}).get("score"), 5.0),
        monthly_income=_safe_float(client_profile.get("monthly_income")),
        goal_years=_safe_int((goal_output or {}).get("horizon"), 10),
        term_life_cover=_safe_float(client_profile.get("raw_profile", {}).get("term_life_cover")),
        outstanding_loans=client_profile.get("outstanding_loans") or [],
    )


def _build_sip_output(
    goal_output: Optional[Dict[str, Any]],
    portfolio_analysis: Dict[str, Any],
    risk_output: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    if not goal_output:
        return None

    target_amount = _safe_float(goal_output.get("target_amount"))
    horizon_years = _safe_int(goal_output.get("horizon"))
    if target_amount <= 0 or horizon_years <= 0:
        return None

    assumption_box = AssumptionBox(risk_score=_safe_float((risk_output or {}).get("score"), 5.0))
    sip_plan = assumption_box.calculate_sip_for_goal(
        target_corpus=target_amount,
        years=horizon_years,
        current_investment=_safe_float(portfolio_analysis.get("total_corpus")),
    )
    story = generate_sip_story(
        monthly=_safe_float(sip_plan.get("required_sip")),
        years=horizon_years,
        rate=_safe_float(sip_plan.get("return_rate")) * 100.0,
        future_value=target_amount,
    )
    return {
        **sip_plan,
        "horizon_years": horizon_years,
        "projection_story": story,
    }


def _category_from_asset(asset_name: str) -> Optional[str]:
    name = str(asset_name).lower()
    if "small cap" in name:
        return "Small Cap"
    if "mid cap" in name:
        return "Mid Cap"
    if "large cap" in name:
        return "Large Cap"
    if "flexi" in name:
        return "Flexi Cap"
    if "sector" in name:
        return "Sectoral"
    if "hybrid" in name:
        return "Hybrid"
    if "gold" in name:
        return "Gold"
    if "debt" in name or "bond" in name:
        return "Debt"
    if "equity" in name:
        return "Flexi Cap"
    return None


def _fallback_fund_recommendations(
    allocation_output: Dict[str, Any],
    client_profile: Dict[str, Any],
    goal_output: Optional[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    horizon = _safe_int((goal_output or {}).get("horizon"), 10)
    for asset_name, weight in (allocation_output.get("allocation") or {}).items():
        category = _category_from_asset(asset_name)
        if category is None or _safe_float(weight) <= 0:
            continue
        category_meta = explain_category(
            category,
            profile={
                "risk_class": client_profile.get("risk_appetite") or client_profile.get("behavior_traits") or "Moderate",
                "age": client_profile.get("age"),
                "horizon_years": horizon,
            },
        )
        results.append(
            {
                "category": category,
                "allocation_weight": _safe_float(weight),
                "reason": category_meta.get("narrative"),
                "risk_note": category_meta.get("risk_level"),
                "source": "category_fallback",
            }
        )
    return results


def _build_fund_recommendations(
    allocation_output: Optional[Dict[str, Any]],
    risk_output: Optional[Dict[str, Any]],
    client_profile: Dict[str, Any],
    goal_output: Optional[Dict[str, Any]],
) -> Optional[List[Dict[str, Any]]]:
    if not allocation_output:
        return None

    allocation = allocation_output.get("allocation") or {}
    risk_class = str((risk_output or {}).get("class") or (risk_output or {}).get("risk_class") or "Moderate")

    try:
        from backend.engines.recommendation_engine import suggest_mutual_funds

        if suggest_mutual_funds is not None:
            recommendations, _ = suggest_mutual_funds(allocation, risk_class)
            if recommendations:
                return recommendations
    except Exception:
        pass

    fallback = _fallback_fund_recommendations(allocation_output, client_profile, goal_output)
    return fallback or None


def load_system_assumptions(
    risk_output: Optional[Dict[str, Any]],
    sip_output: Optional[Dict[str, Any]],
    goal_output: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    if not risk_output:
        return None

    assumption_box = AssumptionBox(risk_score=_safe_float(risk_output.get("score"), 5.0))
    return_rate_pct = _safe_float((sip_output or {}).get("return_rate")) * 100.0
    if return_rate_pct <= 0:
        return_rate_pct = assumption_box.get_expected_return(_safe_int((goal_output or {}).get("horizon"), 10)) * 100.0
    inflation_pct = assumption_box.get_inflation_rate("india") * 100.0
    horizon = _safe_int((goal_output or {}).get("horizon"), 10)

    return {
        "risk_assumptions": assumption_box.get_all_assumptions(),
        "display_block": build_assumptions_block(
            return_rate=return_rate_pct,
            inflation_rate=inflation_pct,
            horizon_years=horizon,
        ),
    }


def build_advisory_payload(client_id: int, db_session: Session) -> Dict[str, Any]:
    client = get_client_from_db(client_id, db_session)
    latest_risk = _latest_risk(db_session, client_id)
    goal_lines = _goal_lines(db_session, client_id)
    latest_portfolio = _latest_portfolio(db_session, client_id)
    latest_draft = _latest_draft(db_session, client_id)

    client_profile = extract_client_profile(client)
    risk_output = _build_risk_output(client_profile, latest_risk)
    goal_output = _build_goal_output(goal_lines)

    guidance_output = None
    if risk_output and goal_output:
        guidance_output = generate_guidance(
            age=_safe_int(client_profile.get("age")),
            risk_class=str(risk_output.get("class") or risk_output.get("risk_class") or "Moderate"),
            horizon_years=_safe_int(goal_output.get("horizon")),
        )

    allocation_output = _build_allocation_output(risk_output, latest_draft)
    portfolio_analysis = _build_portfolio_analysis(client_profile, latest_portfolio, risk_output, goal_output)
    sip_output = _build_sip_output(goal_output, portfolio_analysis, risk_output)

    affordability = None
    if sip_output is not None:
        affordability = check_affordability(
            monthly_sip=_safe_float(sip_output.get("required_sip")),
            monthly_surplus=_safe_float(client_profile.get("monthly_surplus")),
        )

    fund_recommendations = _build_fund_recommendations(
        allocation_output,
        risk_output,
        client_profile,
        goal_output,
    )
    assumptions = load_system_assumptions(risk_output, sip_output, goal_output)

    payload = {
        "client_profile": client_profile,
        "risk_output": risk_output,
        "goal_output": goal_output,
        "guidance_output": guidance_output,
        "allocation_output": allocation_output,
        "portfolio_analysis": portfolio_analysis,
        "sip_output": sip_output,
        "affordability": affordability,
        "fund_recommendations": fund_recommendations,
        "assumptions": assumptions,
    }

    payload["system_recommendation"] = allocation_output
    payload["advisor_override"] = {
        "equity": (allocation_output or {}).get("equity", 0),
        "debt": (allocation_output or {}).get("debt", 0),
        "gold": (allocation_output or {}).get("gold", 0),
        "override_reason": "No override applied",
    }

    if latest_draft and (latest_draft.advisor_final or latest_draft.override_reason):
        payload["advisor_override"] = {
            "advisor_final": latest_draft.advisor_final or {},
            "reason": latest_draft.override_reason,
        }

    advisory = generate_final_advisory(payload)
    payload.update(advisory)

    return payload


def validate_payload(payload: Dict[str, Any]) -> List[str]:
    return [key for key in REQUIRED_KEYS if key not in payload or payload[key] is None]


def _normalise_status(status: str) -> str:
    mapping = {
        "feasible": "FEASIBLE",
        "stretch": "STRETCH",
        "not_advisable": "NOT_ADVISABLE",
    }
    return mapping.get(str(status or "").lower(), "NOT_ADVISABLE")


def _allocation_mix(allocation: Dict[str, Any]) -> Dict[str, float]:
    mix = {"equity": 0.0, "debt": 0.0, "gold": 0.0}
    for key, value in (allocation or {}).items():
        name = str(key).lower()
        weight = _safe_float(value)
        if "gold" in name:
            mix["gold"] += weight
        elif "debt" in name or "bond" in name:
            mix["debt"] += weight
        else:
            mix["equity"] += weight
    return {k: round(v, 2) for k, v in mix.items()}


def _build_standard_baseline(guidance_output: Dict[str, Any]) -> str:
    equity_band = guidance_output.get("equity_band") or (0, 0)
    debt_band = guidance_output.get("debt_band") or (0, 0)
    return (
        f"The rule-based advisory baseline places equity between {equity_band[0]}% and {equity_band[1]}% "
        f"and debt between {debt_band[0]}% and {debt_band[1]}%. This is the default allocation guardrail "
        f"before any portfolio-level optimisation or advisor review."
    )


def _build_advisory_interpretation(
    client_profile: Dict[str, Any],
    goal_output: Dict[str, Any],
    risk_class: str,
) -> str:
    return (
        f"For a client aged {client_profile.get('age')} with a {risk_class.lower()} risk orientation and a "
        f"{goal_output.get('horizon')}-year goal horizon, this baseline supports long-term investing discipline "
        f"without taking risk beyond the client's financial capacity."
    )


def _build_portfolio_diagnosis(portfolio_analysis: Dict[str, Any]) -> str:
    insights = portfolio_analysis.get("insights") or []
    if insights:
        return " ".join(str(item) for item in insights[:3])
    return "The current portfolio does not show major concentration issues under the present rule set."


def _build_guidance_vs_final(guidance_output: Dict[str, Any], allocation_output: Dict[str, Any]) -> str:
    baseline_equity = guidance_output.get("equity_band") or (0, 0)
    baseline_debt = guidance_output.get("debt_band") or (0, 0)
    final_mix = _allocation_mix(allocation_output.get("allocation") or {})
    return (
        f"While the standard baseline suggests equity in the {baseline_equity[0]}%–{baseline_equity[1]}% range and "
        f"debt in the {baseline_debt[0]}%–{baseline_debt[1]}% range, the optimized allocation settles at "
        f"{final_mix['equity']:.2f}% equity, {final_mix['debt']:.2f}% debt, and {final_mix['gold']:.2f}% gold "
        f"based on the current portfolio structure and the funding requirement of the primary goal."
    )


def _build_why_this(
    narrative: Dict[str, str],
    goal_output: Dict[str, Any],
    portfolio_analysis: Dict[str, Any],
) -> str:
    goal_name = goal_output.get("primary_goal", "the primary financial goal")
    goal_horizon = goal_output.get("horizon")
    portfolio_note = (portfolio_analysis.get("insights") or ["The current portfolio requires a disciplined allocation update."])[0]
    return (
        f"{narrative.get('allocation_explanation', '')} This approach is aligned to {goal_name} over a "
        f"{goal_horizon}-year horizon and addresses the current portfolio diagnosis. {portfolio_note}"
    ).strip()


def _build_why_not(risk_class: str, horizon: int) -> List[Dict[str, str]]:
    items: List[Dict[str, str]] = []
    if risk_class in ("Moderate", "Conservative"):
        items.append(
            {
                "rejected_option": "Small-cap heavy allocation",
                "reason": f"A {risk_class.lower()} profile should not rely on high-volatility small-cap concentration.",
            }
        )
    if horizon < 5:
        items.append(
            {
                "rejected_option": "Equity-heavy allocation",
                "reason": f"A {horizon}-year horizon is too short to absorb equity drawdowns comfortably.",
            }
        )
    else:
        items.append(
            {
                "rejected_option": "Fully debt-based allocation",
                "reason": "A pure debt mix would weaken long-term wealth creation and reduce goal funding efficiency.",
            }
        )
    if risk_class == "Conservative":
        items.append(
            {
                "rejected_option": "Pure equity funds",
                "reason": "Capital preservation is more important than maximizing return volatility for this profile.",
            }
        )
    if len(items) < 2:
        generated = generate_rejection_logic(risk_class, horizon)
        for reason in generated:
            items.append({"rejected_option": "Alternative strategy", "reason": reason})
            if len(items) >= 2:
                break
    return items[: max(2, len(items))]


def _build_fund_rationale(
    fund_recommendations: List[Dict[str, Any]],
    client_profile: Dict[str, Any],
    goal_output: Dict[str, Any],
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for recommendation in fund_recommendations:
        category = recommendation.get("category") or _category_from_asset(recommendation.get("name", "")) or "Mutual Fund"
        meta = explain_category(
            category,
            profile={
                "risk_class": client_profile.get("risk_appetite") or "Moderate",
                "age": client_profile.get("age"),
                "horizon_years": goal_output.get("horizon"),
            },
        )
        results.append(
            {
                "category": category,
                "weight": _safe_float(recommendation.get("allocation_weight")),
                "why_selected": recommendation.get("reason") or meta.get("suitability") or meta.get("narrative"),
                "why_now": recommendation.get("market_reason") or meta.get("description"),
                "risk_note": recommendation.get("risk_note") or meta.get("risk_level"),
            }
        )
    return results


def _build_goal_confidence(goal_output: Dict[str, Any], sip_output: Dict[str, Any]) -> str:
    return (
        f"The primary goal requires a target corpus of ₹{_safe_float(goal_output.get('target_amount')):,.0f} over "
        f"{goal_output.get('horizon')} years. At the current assumption set, this translates to a required SIP of "
        f"approximately ₹{_safe_float(sip_output.get('required_sip')):,.0f} per month. Confidence improves when "
        f"the SIP is started early and increased as income grows."
    )


def _build_comparison(payload: Dict[str, Any]) -> Dict[str, Any]:
    system_allocation = (payload.get("allocation_output") or {}).get("allocation") or {}
    advisor_override = payload.get("advisor_override") or {}
    advisor_final = advisor_override.get("advisor_final") or {}
    advisor_allocation = advisor_final.get("allocation") or advisor_final.get("target_allocation") or {}
    if not advisor_allocation:
        return {
            "system": {"allocation": system_allocation},
            "message": "No deviation from system recommendation",
        }

    difference = {}
    for key in sorted(set(system_allocation) | set(advisor_allocation)):
        system_value = _safe_float(system_allocation.get(key))
        advisor_value = _safe_float(advisor_allocation.get(key))
        if round(system_value, 2) != round(advisor_value, 2):
            difference[key] = {
                "system": round(system_value, 2),
                "advisor": round(advisor_value, 2),
            }

    return {
        "system": {"allocation": system_allocation},
        "advisor": {"allocation": advisor_allocation},
        "difference": difference,
        "reason": advisor_override.get("reason") or "Advisor override recorded.",
    }


def generate_advisory_response(payload: Dict[str, Any]) -> Dict[str, Any]:
    missing_fields = validate_payload(payload)
    if missing_fields:
        return {"error": "Missing required input", "missing_fields": missing_fields}

    client_profile = payload["client_profile"]
    risk_output = payload["risk_output"]
    goal_output = payload["goal_output"]
    guidance_output = payload["guidance_output"]
    allocation_output = payload["allocation_output"]
    portfolio_analysis = payload["portfolio_analysis"]
    sip_output = payload["sip_output"]
    affordability = payload["affordability"]
    fund_recommendations = payload["fund_recommendations"] or []
    assumptions = payload["assumptions"] or {}

    risk_class = str(risk_output.get("class") or risk_output.get("risk_class") or "Moderate")
    narrative = generate_advisory_narrative(
        profile=client_profile,
        risk={"score": risk_output.get("score"), "category": risk_class},
        goals=goal_output.get("goals") or [],
        guidance={"allocation": allocation_output.get("allocation") or {}},
        portfolio=portfolio_analysis,
    )

    sip_story = (sip_output.get("projection_story") or {}).get("narrative") if isinstance(sip_output, dict) else ""
    if not sip_story:
        sip_story = (
            f"A SIP of approximately ₹{_safe_float(sip_output.get('required_sip')):,.0f} per month is required to "
            f"target the primary goal within the available horizon."
        )

    return {
        "client_summary": narrative.get("client_summary", ""),
        "standard_baseline": _build_standard_baseline(guidance_output),
        "advisory_interpretation": _build_advisory_interpretation(client_profile, goal_output, risk_class),
        "portfolio_diagnosis": _build_portfolio_diagnosis(portfolio_analysis),
        "guidance_vs_final": _build_guidance_vs_final(guidance_output, allocation_output),
        "why_this": _build_why_this(narrative, goal_output, portfolio_analysis),
        "why_not": _build_why_not(risk_class, _safe_int(goal_output.get("horizon"), 10)),
        "final_allocation": allocation_output.get("allocation") or {},
        "fund_rationale": _build_fund_rationale(fund_recommendations, client_profile, goal_output),
        "sip_interpretation": sip_story,
        "affordability_analysis": {
            "status": _normalise_status(affordability.get("status")),
            "ratio": _safe_float(affordability.get("ratio")),
            "explanation": affordability.get("message", ""),
        },
        "assumptions": assumptions.get("display_block") or assumptions,
        "goal_confidence": _build_goal_confidence(goal_output, sip_output),
        "comparison": _build_comparison(payload),
        "final_recommendation": narrative.get("final_recommendation", ""),
        "action_plan": [
            f"Start a SIP of approximately ₹{_safe_float(sip_output.get('required_sip')):,.0f} per month.",
            "Review the current portfolio and rebalance toward the recommended allocation.",
            "Revisit the plan at least annually or after any major income or goal change.",
        ],
        "disclaimer": (
            "All projections are illustrative, based on current assumptions, and subject to market risk. "
            "Actual returns are not guaranteed."
        ),
    }
