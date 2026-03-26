from typing import Dict, Any, List
import numpy as np
from datetime import datetime

RISK_RETURN_MAP = {
    1: {"return": 0.06, "volatility": 0.05, "label": "Very Conservative"},
    2: {"return": 0.075, "volatility": 0.08, "label": "Conservative"},
    3: {"return": 0.09, "volatility": 0.10, "label": "Moderately Conservative"},
    4: {"return": 0.105, "volatility": 0.12, "label": "Moderate"},
    5: {"return": 0.12, "volatility": 0.15, "label": "Moderately Aggressive"},
    6: {"return": 0.135, "volatility": 0.18, "label": "Aggressive"},
    7: {"return": 0.15, "volatility": 0.22, "label": "Very Aggressive"},
    8: {"return": 0.16, "volatility": 0.25, "label": "Highly Aggressive"},
    9: {"return": 0.17, "volatility": 0.28, "label": "Very High Risk"},
    10: {"return": 0.18, "volatility": 0.32, "label": "Maximum Risk"},
}

INFLATION_RATES = {
    "india": 0.065,
    "education": 0.09,
    "healthcare": 0.08,
    "real_estate": 0.07,
    "lifestyle": 0.06,
}

EXPECTED_Market_RETURNS = {
    "large_cap": 0.11,
    "mid_cap": 0.14,
    "small_cap": 0.18,
    "debt": 0.07,
    "gold": 0.08,
    "index": 0.10,
    "hybrid": 0.10,
}


class AssumptionBox:
    def __init__(self, risk_score: float = 5.0):
        self.risk_score = max(1, min(10, risk_score))
        self.assumptions = self._load_default_assumptions()

    def _load_default_assumptions(self) -> Dict[str, Any]:
        risk_data = RISK_RETURN_MAP.get(int(round(self.risk_score)), RISK_RETURN_MAP[5])

        return {
            "expected_return": risk_data["return"],
            "volatility": risk_data["volatility"],
            "risk_label": risk_data["label"],
            "inflation_rate": INFLATION_RATES["india"],
            "safe_rate": 0.055,
            "equity_weight": max(0.1, min(0.9, (self.risk_score - 1) / 9)),
            "debt_weight": 0.0,
            "gold_weight": 0.0,
        }

    def get_expected_return(self, horizon_years: int = None) -> float:
        base_return = self.assumptions["expected_return"]
        if horizon_years and horizon_years > 15:
            return base_return * 1.1
        return base_return

    def get_volatility(self) -> float:
        return self.assumptions["volatility"]

    def get_inflation_rate(self, category: str = "india") -> float:
        return INFLATION_RATES.get(category, INFLATION_RATES["india"])

    def calculate_real_return(
        self, nominal_return: float = None, horizon_years: int = 10
    ) -> float:
        if nominal_return is None:
            nominal_return = self.get_expected_return(horizon_years)
        inflation = self.get_inflation_rate("india")
        real = ((1 + nominal_return) / (1 + inflation)) - 1
        return round(real, 4)

    def project_corpus(
        initial_corpus: float, monthly_sip: float, years: int, return_rate: float = None
    ) -> Dict[str, Any]:
        if return_rate is None:
            return_rate = AssumptionBox(self.risk_score).get_expected_return(years)

        monthly_rate = return_rate / 12
        months = years * 12

        if monthly_rate > 0:
            future_value_corpus = initial_corpus * ((1 + monthly_rate) ** months)
            future_value_sip = monthly_sip * (
                ((1 + monthly_rate) ** months - 1) / monthly_rate
            )
        else:
            future_value_corpus = initial_corpus
            future_value_sip = monthly_sip * months

        total_corpus = future_value_corpus + future_value_sip

        return {
            "initial_corpus": initial_corpus,
            "monthly_sip": monthly_sip,
            "years": years,
            "return_rate": return_rate,
            "future_value_corpus": round(future_value_corpus, 2),
            "future_value_sip": round(future_value_sip, 2),
            "total_corpus": round(total_corpus, 2),
            "inflation_adjusted": round(
                total_corpus / ((1 + INFLATION_RATES["india"]) ** years), 2
            ),
        }

    def calculate_sip_for_goal(
        target_corpus: float,
        years: int,
        current_investment: float = 0,
        return_rate: float = None,
    ) -> Dict[str, Any]:
        if return_rate is None:
            return_rate = self.get_expected_return(years)

        monthly_rate = return_rate / 12
        months = years * 12

        if monthly_rate > 0:
            future_value_current = current_investment * ((1 + monthly_rate) ** months)
        else:
            future_value_current = current_investment

        shortfall = max(0, target_corpus - future_value_current)

        if monthly_rate > 0:
            required_sip = shortfall * monthly_rate / ((1 + monthly_rate) ** months - 1)
        else:
            required_sip = shortfall / months

        return {
            "target_corpus": target_corpus,
            "years": years,
            "current_investment": current_investment,
            "future_value_current": round(future_value_current, 2),
            "shortfall": round(shortfall, 2),
            "required_sip": round(required_sip, 2),
            "return_rate": return_rate,
            "monthly_commitment_rate": round(
                (required_sip / max(current_investment, 1)) * 100, 2
            )
            if current_investment > 0
            else 0,
        }

    def get_all_assumptions(self) -> Dict[str, Any]:
        return {
            **self.assumptions,
            "risk_score": self.risk_score,
            "assumptions_date": datetime.now().isoformat(),
            "inflation_rates": INFLATION_RATES,
            "market_returns": EXPECTED_Market_RETURNS,
        }


def get_assumption_for_profile(profile_type: str) -> Dict[str, Any]:
    profiles = {
        "retirement": {
            "expected_return": 0.10,
            "volatility": 0.12,
            "inflation_rate": INFLATION_RATES["india"],
            "horizon_adjustment": "long_term",
        },
        "child_education": {
            "expected_return": 0.12,
            "volatility": 0.15,
            "inflation_rate": INFLATION_RATES["education"],
            "horizon_adjustment": "medium_term",
        },
        "house_purchase": {
            "expected_return": 0.08,
            "volatility": 0.08,
            "inflation_rate": INFLATION_RATES["real_estate"],
            "horizon_adjustment": "short_term",
        },
        "wealth_creation": {
            "expected_return": 0.14,
            "volatility": 0.18,
            "inflation_rate": INFLATION_RATES["lifestyle"],
            "horizon_adjustment": "long_term",
        },
    }
    return profiles.get(profile_type.lower(), profiles["wealth_creation"])


if __name__ == "__main__":
    box = AssumptionBox(risk_score=6.0)
    print(box.get_all_assumptions())

    projection = box.project_corpus(100000, 10000, 20)
    print(projection)

    sip = box.calculate_sip_for_goal(5000000, 15, 500000)
    print(sip)
