GOAL_CONFIGS = {
    "retirement": {
        "label": "Retirement",
        "inflation_pct": 7.0,
        "required_inputs": [
            "current_age",
            "retirement_age",
            "life_expectancy",
            "current_monthly_expense",
            "lifestyle_factor",
        ],
        "description": "Inflation-adjusted retirement corpus",
    },
    "child_education": {
        "label": "Child Education",
        "inflation_pct": 11.0,
        "required_inputs": [
            "child_current_age",
            "education_start_age",
            "target_amount",
        ],
        "description": "Education inflation applied",
    },
    "home_purchase": {
        "label": "Home Purchase",
        "inflation_pct": 9.0,
        "required_inputs": [
            "target_property_value",
            "down_payment_pct",
            "years_to_purchase",
        ],
    },
    "emergency_fund": {
        "label": "Emergency Fund",
        "inflation_pct": 0.0,
        "required_inputs": ["monthly_expenses", "months_of_coverage"],
    },
    "wealth_creation": {
        "label": "Wealth Creation",
        "inflation_pct": 0.0,
        "required_inputs": ["target_amount", "years_to_goal"],
    },
    "medical_corpus": {
        "label": "Medical Corpus",
        "inflation_pct": 13.0,
        "required_inputs": ["target_amount", "years_to_goal"],
    },
    "travel_lifestyle": {
        "label": "Travel Lifestyle",
        "inflation_pct": 6.0,
        "required_inputs": ["target_amount", "years_to_goal"],
    },
}


class GoalRegistry:
    @staticmethod
    def calculate_required_corpus(goal_type, inputs, annual_return_pct):
        cfg = GOAL_CONFIGS.get(goal_type)

        if not cfg:
            raise ValueError("Invalid goal type")

        missing = [k for k in cfg["required_inputs"] if k not in inputs]
        if missing:
            raise ValueError(f"Missing inputs: {missing}")

        inflation = cfg["inflation_pct"] / 100
        r = annual_return_pct / 100

        if goal_type == "retirement":
            years = inputs["retirement_age"] - inputs["current_age"]

            monthly_exp = inputs["current_monthly_expense"] * (1 + inflation) ** years

            corpus = (monthly_exp * 12) / 0.035

            sip = GoalRegistry._sip_formula(corpus, years, annual_return_pct)

            return {
                "required_corpus": round(corpus, 2),
                "monthly_sip": round(sip, 2),
                "years": years,
            }

        elif goal_type == "child_education":
            years = inputs["education_start_age"] - inputs["child_current_age"]

            corpus = inputs["target_amount"] * (1 + inflation) ** years

            sip = GoalRegistry._sip_formula(corpus, years, annual_return_pct)

            return {
                "required_corpus": round(corpus, 2),
                "monthly_sip": round(sip, 2),
                "years": years,
            }

        elif goal_type == "home_purchase":
            years = inputs.get("years_to_purchase", 10)
            target = inputs.get("target_property_value", inputs.get("target_amount", 0))
            corpus = target * (1 + inflation) ** years

            sip = GoalRegistry._sip_formula(corpus, years, annual_return_pct)

            return {
                "required_corpus": round(corpus, 2),
                "monthly_sip": round(sip, 2),
                "years": years,
            }

        elif goal_type == "emergency_fund":
            monthly_exp = inputs.get("monthly_expenses", 0)
            months = inputs.get("months_of_coverage", 6)
            corpus = monthly_exp * months

            return {
                "required_corpus": round(corpus, 2),
                "monthly_sip": round(corpus / 12, 2),
                "years": 1,
            }

        else:
            years = inputs.get("years_to_goal", 10)
            target = inputs.get("target_amount", 0)
            corpus = target * (1 + inflation) ** years

            sip = GoalRegistry._sip_formula(corpus, years, annual_return_pct)

            return {
                "required_corpus": round(corpus, 2),
                "monthly_sip": round(sip, 2),
                "years": years,
            }

    @staticmethod
    def _sip_formula(fv, years, annual_return_pct):
        r = annual_return_pct / 100 / 12
        n = years * 12

        if r == 0:
            return fv / n

        return fv * r / (((1 + r) ** n - 1) * (1 + r))

    @staticmethod
    def sip_topup_comparison(base_sip, topup_pct, years, annual_return_pct):
        r = annual_return_pct / 100 / 12

        flat = base_sip * (((1 + r) ** (years * 12) - 1) / r) * (1 + r)

        topup = flat * (1 + (topup_pct / 100) * years * 0.5)

        return {
            "flat_corpus": round(flat, 2),
            "topup_corpus": round(topup, 2),
            "extra_wealth": round(topup - flat, 2),
        }
