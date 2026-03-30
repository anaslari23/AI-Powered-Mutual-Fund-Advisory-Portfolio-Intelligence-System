"""
backend/engines/demo_profiles.py
─────────────────────────────────
Three complete demo investor profiles for testing and demonstration.
Each produces different allocation, narrative, SIP story, and affordability.
"""
from typing import Any, Dict, List


DEMO_PROFILES: Dict[str, Dict[str, Any]] = {
    "young_aggressive": {
        "label": "Young Aggressive (Age 28)",
        "name": "Rahul Sharma",
        "age": 28,
        "contact": "+91 98765 00001",
        "city": "Bangalore",
        "source_channel": "Referral",
        "occupation": "Software Engineer",
        "monthly_income": 150000,
        "monthly_expenses": 55000,
        "monthly_emi": 15000,
        "effective_monthly_savings": 80000,
        "dependents": 0,
        "behavior_traits": "Aggressive",
        "income_bracket": "₹15L–₹30L",
        "existing_fd": 200000,
        "existing_savings": 150000,
        "existing_gold": 50000,
        "existing_mutual_funds": 600000,
        "term_life_cover": 10000000,
        "health_cover": 1000000,
        "outstanding_loans": [],
        "goals": [
            {
                "goal_type": "wealth_creation",
                "goal_name": "Wealth Creation",
                "target_amount": 50000000,
                "years_to_goal": 25,
                "priority": 1,
            },
            {
                "goal_type": "vehicle_purchase",
                "goal_name": "Car Purchase",
                "target_amount": 1500000,
                "years_to_goal": 3,
                "priority": 2,
            },
        ],
        "expected_risk_score": 8.2,
        "expected_risk_class": "Aggressive",
        "sip_target": 40000,
    },
    "mid_career_balanced": {
        "label": "Mid-Career Balanced (Age 40)",
        "name": "Priya Mehta",
        "age": 40,
        "contact": "+91 98765 00002",
        "city": "Mumbai",
        "source_channel": "Direct Walk-in",
        "occupation": "Corporate Manager",
        "monthly_income": 200000,
        "monthly_expenses": 90000,
        "monthly_emi": 35000,
        "effective_monthly_savings": 75000,
        "dependents": 2,
        "behavior_traits": "Moderate",
        "income_bracket": "Above ₹30L",
        "existing_fd": 1500000,
        "existing_savings": 500000,
        "existing_gold": 300000,
        "existing_mutual_funds": 2000000,
        "term_life_cover": 20000000,
        "health_cover": 2000000,
        "outstanding_loans": [
            {
                "loan_type": "Home Loan",
                "outstanding_principal": 3500000,
                "emi": 35000,
                "remaining_tenure_months": 120,
            }
        ],
        "goals": [
            {
                "goal_type": "retirement",
                "goal_name": "Retirement",
                "target_amount": 30000000,
                "years_to_goal": 20,
                "priority": 1,
                "current_monthly_expense": 90000,
                "retirement_age": 60,
            },
            {
                "goal_type": "child_education",
                "goal_name": "Child Higher Education",
                "target_amount": 5000000,
                "years_to_goal": 8,
                "priority": 2,
            },
            {
                "goal_type": "marriage",
                "goal_name": "Daughter Wedding",
                "target_amount": 3000000,
                "years_to_goal": 15,
                "priority": 3,
            },
        ],
        "expected_risk_score": 5.8,
        "expected_risk_class": "Moderate",
        "sip_target": 30000,
    },
    "senior_conservative": {
        "label": "Senior Conservative (Age 58)",
        "name": "Arun Iyer",
        "age": 58,
        "contact": "+91 98765 00003",
        "city": "Chennai",
        "source_channel": "Branch Visit",
        "occupation": "Retired Government Officer",
        "monthly_income": 80000,
        "monthly_expenses": 45000,
        "monthly_emi": 0,
        "effective_monthly_savings": 35000,
        "dependents": 1,
        "behavior_traits": "Conservative",
        "income_bracket": "₹7L–₹15L",
        "existing_fd": 5000000,
        "existing_savings": 1500000,
        "existing_gold": 800000,
        "existing_mutual_funds": 1200000,
        "term_life_cover": 5000000,
        "health_cover": 500000,
        "outstanding_loans": [],
        "goals": [
            {
                "goal_type": "retirement",
                "goal_name": "Post-Retirement Income",
                "target_amount": 10000000,
                "years_to_goal": 5,
                "priority": 1,
                "current_monthly_expense": 45000,
                "retirement_age": 60,
            },
            {
                "goal_type": "emergency_fund",
                "goal_name": "Emergency Fund",
                "target_amount": 500000,
                "years_to_goal": 1,
                "priority": 2,
            },
        ],
        "expected_risk_score": 3.2,
        "expected_risk_class": "Conservative",
        "sip_target": 15000,
    },
}


def get_demo_profile(profile_key: str) -> Dict[str, Any]:
    """Return a complete demo profile by key."""
    return dict(DEMO_PROFILES.get(profile_key, {}))


def list_demo_profiles() -> List[Dict[str, str]]:
    """Return list of {key, label} for all demo profiles."""
    return [
        {"key": key, "label": profile["label"]}
        for key, profile in DEMO_PROFILES.items()
    ]


def get_demo_client_create_payload(profile_key: str) -> Dict[str, Any]:
    """Extract the client creation payload from a demo profile."""
    profile = get_demo_profile(profile_key)
    if not profile:
        return {}
    return {
        "name": profile["name"],
        "age": profile["age"],
        "contact": profile.get("contact"),
        "city": profile.get("city"),
        "source_channel": profile.get("source_channel"),
        "occupation": profile.get("occupation"),
        "income_bracket": profile.get("income_bracket"),
    }


def get_demo_profile_data(profile_key: str) -> Dict[str, Any]:
    """Extract the full profile_data payload for profile update.

    Normalises field names to match what render_input_form expects:
    - behavior_traits  → behavior  (also normalises value)
    - effective_monthly_savings → monthly_savings
    - term_life_cover / health_cover / outstanding_loans → nested under insurance_inputs
    """
    profile = get_demo_profile(profile_key)
    if not profile:
        return {}

    _BEHAVIOR_MAP = {
        "Aggressive": "High risk",
        "Moderate": "Moderate",
        "Conservative": "Prefers stability",
    }
    _LOAN_TYPE_MAP = {
        "Home Loan": "Home",
        "Car Loan": "Car",
        "Personal Loan": "Personal",
        "Education Loan": "Education",
    }

    exclude_keys = {
        "label", "name", "contact", "city", "source_channel",
        "goals", "expected_risk_score", "expected_risk_class", "sip_target",
        # normalised below
        "behavior_traits", "effective_monthly_savings",
        "term_life_cover", "health_cover", "annual_insurance_premium", "outstanding_loans",
        "monthly_emi",
    }
    data = {k: v for k, v in profile.items() if k not in exclude_keys}

    # Normalize behavior
    raw_behavior = profile.get("behavior_traits", "Moderate")
    data["behavior"] = _BEHAVIOR_MAP.get(raw_behavior, "Moderate")

    # Normalize savings capacity key
    if "effective_monthly_savings" in profile:
        data["monthly_savings"] = profile["effective_monthly_savings"]

    # Normalize insurance fields into nested dict
    raw_loans = profile.get("outstanding_loans", [])
    normalized_loans = []
    for loan in raw_loans:
        raw_type = loan.get("loan_type") or loan.get("type", "Other")
        normalized_loans.append({
            "type": _LOAN_TYPE_MAP.get(raw_type, raw_type),
            "outstanding_principal": float(loan.get("outstanding_principal", 0.0)),
            "emi": float(loan.get("emi", 0.0)),
        })
    data["insurance_inputs"] = {
        "term_life_cover": float(profile.get("term_life_cover", 1000000.0)),
        "health_cover": float(profile.get("health_cover", 500000.0)),
        "annual_insurance_premium": float(profile.get("annual_insurance_premium", 0.0)),
        "outstanding_loans": normalized_loans,
    }

    return data
