from typing import Dict, Any, List, Optional
from enum import Enum
import numpy as np


class InvestmentMode(str, Enum):
    SYSTEMATIC_INVESTMENT = "sip"
    SYSTEMATIC_TRANSFER = "stp"
    SYSTEMATIC_WITHDRAWAL = "swp"
    LUMPSUM = "lumpsum"
    VALUE_AVERAGING = "value_averaging"
    DOLLAR_COST_AVERAGING = "dca"


RISK_MODE_MAPPING = {
    1: [InvestmentMode.SYSTEMATIC_INVESTMENT, InvestmentMode.DOLLAR_COST_AVERAGING],
    2: [InvestmentMode.SYSTEMATIC_INVESTMENT, InvestmentMode.VALUE_AVERAGING],
    3: [InvestmentMode.SYSTEMATIC_INVESTMENT, InvestmentMode.SYSTEMATIC_TRANSFER],
    4: [InvestmentMode.SYSTEMATIC_INVESTMENT, InvestmentMode.LUMPSUM],
    5: [
        InvestmentMode.SYSTEMATIC_INVESTMENT,
        InvestmentMode.SYSTEMATIC_TRANSFER,
        InvestmentMode.LUMPSUM,
    ],
    6: [InvestmentMode.LUMPSUM, InvestmentMode.SYSTEMATIC_INVESTMENT],
    7: [InvestmentMode.LUMPSUM, InvestmentMode.SYSTEMATIC_TRANSFER],
    8: [InvestmentMode.LUMPSUM, InvestmentMode.SYSTEMATIC_WITHDRAWAL],
    9: [InvestmentMode.LUMPSUM, InvestmentMode.SYSTEMATIC_WITHDRAWAL],
    10: [InvestmentMode.LUMPSUM],
}


MODE_CONFIGS = {
    InvestmentMode.SYSTEMATIC_INVESTMENT: {
        "name": "Systematic Investment Plan (SIP)",
        "description": "Invest a fixed amount regularly regardless of market conditions",
        "min_investment": 500,
        "frequency": ["monthly", "quarterly"],
        "benefits": [
            "Rupee cost averaging",
            "Disciplined investing",
            "Power of compounding",
        ],
        "best_for": ["Long-term wealth creation", "Regular income investors"],
        "risk_level": "Low to Medium",
    },
    InvestmentMode.SYSTEMATIC_TRANSFER: {
        "name": "Systematic Transfer Plan (STP)",
        "description": "Transfer fixed amounts between funds automatically",
        "min_investment": 5000,
        "frequency": ["monthly", "weekly"],
        "benefits": ["Automatic rebalancing", "Tax efficient", "Controlled risk"],
        "best_for": ["Moving from debt to equity", "Goal-based investing"],
        "risk_level": "Medium",
    },
    InvestmentMode.SYSTEMATIC_WITHDRAWAL: {
        "name": "Systematic Withdrawal Plan (SWP)",
        "description": "Withdraw fixed amounts from your investment regularly",
        "min_investment": 25000,
        "frequency": ["monthly", "quarterly", "annual"],
        "benefits": ["Regular income", "Capital preservation", "Tax efficiency"],
        "best_for": ["Retirees", "Income generating portfolios"],
        "risk_level": "Medium to High",
    },
    InvestmentMode.LUMPSUM: {
        "name": "Lumpsum Investment",
        "description": "Invest a large amount at once",
        "min_investment": 5000,
        "frequency": ["one-time"],
        "benefits": ["Full market exposure", "No timing risk (if held long)"],
        "best_for": [
            "Inheritance funds",
            "Bonus received",
            "Long-term investors with idle funds",
        ],
        "risk_level": "High (short-term), Low (long-term)",
    },
    InvestmentMode.VALUE_AVERAGING: {
        "name": "Value Averaging (VA)",
        "description": "Invest more when prices are low, less when high",
        "min_investment": 1000,
        "frequency": ["monthly"],
        "benefits": [
            "Better than SIP in volatile markets",
            "Automatic buy more when cheap",
        ],
        "best_for": ["Experienced investors", "Volatile market conditions"],
        "risk_level": "Medium",
    },
    InvestmentMode.DOLLAR_COST_AVERAGING: {
        "name": "Dollar Cost Averaging (DCA)",
        "description": "Invest fixed amount in foreign currency at regular intervals",
        "min_investment": 100,
        "frequency": ["monthly", "quarterly"],
        "benefits": ["Currency diversification", "Hedge against currency risk"],
        "best_for": ["International exposure", "NRIs", "Currency risk mitigation"],
        "risk_level": "Medium to High",
    },
}


class InvestmentModeAI:
    def __init__(self, risk_score: float = 5.0, investment_horizon: int = 10):
        self.risk_score = max(1, min(10, risk_score))
        self.investment_horizon = max(1, min(30, investment_horizon))

    def recommend_mode(self) -> Dict[str, Any]:
        recommended_modes = RISK_MODE_MAPPING.get(
            int(round(self.risk_score)), [InvestmentMode.SYSTEMATIC_INVESTMENT]
        )

        mode_details = []
        for mode in recommended_modes:
            config = MODE_CONFIGS.get(mode, {})
            mode_details.append({"mode": mode.value, **config})

        primary_mode = mode_details[0] if mode_details else None

        rationale = self._generate_rationale(recommended_modes)

        return {
            "risk_score": self.risk_score,
            "investment_horizon": self.investment_horizon,
            "recommended_modes": mode_details,
            "primary_mode": primary_mode,
            "rationale": rationale,
            "horizon_advice": self._get_horizon_advice(),
        }

    def _generate_rationale(self, modes: List[InvestmentMode]) -> str:
        if self.risk_score <= 3:
            return "Conservative approach recommended. Regular investments help average out market volatility and reduce timing risk."
        elif self.risk_score <= 6:
            return "Balanced approach recommended. A mix of systematic investments with occasional lump sums can capture market opportunities while managing risk."
        elif self.risk_score <= 8:
            return "Growth-oriented approach recommended. Lump sum investments can capture full market exposure, supported by systematic additions."
        else:
            return "Aggressive approach recommended. Full market exposure through lump sum investments with systematic withdrawal for income generation."

    def _get_horizon_advice(self) -> str:
        if self.investment_horizon < 3:
            return "Short-term horizon (<3 years): Focus on debt funds, liquid funds, or short-term SIPs. Avoid equity-heavy allocations."
        elif self.investment_horizon < 7:
            return "Medium-term horizon (3-7 years): Hybrid approach with balanced funds. SIP recommended for wealth accumulation."
        elif self.investment_horizon < 15:
            return "Long-term horizon (7-15 years): Equity-heavy portfolio with SIP. Consider STP from debt to equity as you approach goal."
        else:
            return "Very long-term horizon (>15 years): Aggressive equity allocation. Lump sum with periodic top-ups recommended for maximum compounding."

    def compare_modes(
        self, amount: float, expected_return: float = 0.12, volatility: float = 0.15
    ) -> Dict[str, Any]:
        monthly_rate = expected_return / 12
        months = self.investment_horizon * 12

        comparisons = []

        if InvestmentMode.SYSTEMATIC_INVESTMENT in RISK_MODE_MAPPING.get(
            int(round(self.risk_score)), []
        ):
            monthly_sip = amount / months
            fv_sip = monthly_sip * (((1 + monthly_rate) ** months - 1) / monthly_rate)
            comparisons.append(
                {
                    "mode": "SIP",
                    "investment_type": "Monthly",
                    "total_invested": round(monthly_sip * months, 2),
                    "projected_value": round(fv_sip, 2),
                    "absolute_return": round(fv_sip - (monthly_sip * months), 2),
                }
            )

        fv_lumpsum = amount * ((1 + monthly_rate) ** months)
        comparisons.append(
            {
                "mode": "Lumpsum",
                "investment_type": "One-time",
                "total_invested": amount,
                "projected_value": round(fv_lumpsum, 2),
                "absolute_return": round(fv_lumpsum - amount, 2),
            }
        )

        comparisons.sort(key=lambda x: x["projected_value"], reverse=True)

        return {
            "investment_amount": amount,
            "expected_return": expected_return,
            "investment_horizon_years": self.investment_horizon,
            "projections": comparisons,
            "recommendation": comparisons[0]["mode"] if comparisons else "SIP",
        }

    def optimize_investment_schedule(
        self, total_amount: float, mode: str = "auto"
    ) -> Dict[str, Any]:
        if mode == "auto":
            recommended = self.recommend_mode()
            mode = (
                recommended["primary_mode"]["mode"]
                if recommended["primary_mode"]
                else "sip"
            )

        if mode == "sip":
            monthly_amount = total_amount / (self.investment_horizon * 12)
            return {
                "strategy": "SIP",
                "schedule": {
                    "monthly_investment": round(monthly_amount, 2),
                    "frequency": "monthly",
                    "duration_months": self.investment_horizon * 12,
                },
                "total_investment": total_amount,
                "flexibility": "Can increase/decrease amount with 30 days notice",
            }
        elif mode == "lumpsum":
            return {
                "strategy": "Lumpsum",
                "schedule": {
                    "investment": total_amount,
                    "timing": "Immediate",
                    "suggested_split": None,
                },
                "total_investment": total_amount,
                "note": "Consider staggering if market is volatile",
            }
        elif mode == "stp":
            debt_amount = total_amount * 0.4
            equity_amount = total_amount * 0.6
            monthly_transfer = equity_amount / (self.investment_horizon * 6)
            return {
                "strategy": "STP",
                "schedule": {
                    "initial_debt_allocation": round(debt_amount, 2),
                    "equity_allocation": round(equity_amount, 2),
                    "monthly_transfer": round(monthly_transfer, 2),
                    "transfer_duration_months": min(self.investment_horizon * 6, 36),
                },
                "total_investment": total_amount,
                "recommendation": "Start with debt funds, gradually move to equity",
            }
        else:
            return {"error": f"Mode {mode} not supported"}


def get_mode_details(mode: str) -> Optional[Dict[str, Any]]:
    try:
        return MODE_CONFIGS.get(InvestmentMode(mode.lower()))
    except ValueError:
        return None


def get_modes_by_risk_score(risk_score: int) -> List[Dict[str, Any]]:
    risk_score = max(1, min(10, risk_score))
    modes = RISK_MODE_MAPPING.get(risk_score, [InvestmentMode.SYSTEMATIC_INVESTMENT])
    return [MODE_CONFIGS.get(m, {}) for m in modes]


if __name__ == "__main__":
    ai = InvestmentModeAI(risk_score=6.0, investment_horizon=10)
    print(ai.recommend_mode())
    print(ai.compare_modes(100000))


def suggest_investment_mode(market_trend, volatility):
    if market_trend == "down":
        return "Lumpsum (market dip opportunity)"
    elif volatility > 20:
        return "SIP / STP recommended"
    return "Balanced SIP + Lumpsum"
