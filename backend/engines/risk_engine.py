from typing import Dict, Any
import numpy as np
import logging
import os

from backend.scoring.calibration_engine import CalibrationEngine
from backend.ml.advanced_risk_model import AdvancedRiskModel
from backend.intelligence.macro_engine import detect_market_regime

logger = logging.getLogger(__name__)

calibrator = CalibrationEngine()
ml_model = AdvancedRiskModel()


def load_real_or_cached_scores():
    try:
        return np.load("backend/data/risk_scores.npy")
    except:
        return np.random.normal(5, 2, 1000)


def compute_factor_contributions(user_input: Dict[str, Any]) -> Dict[str, Any]:
    behavior = user_input.get("behavior", 2)
    if isinstance(behavior, str):
        beh_map = {"conservative": 1, "moderate": 2, "aggressive": 3}
        behavior = beh_map.get(behavior.lower().strip(), 2)

    return {
        "age": user_input.get("age", 30) * 0.25,
        "savings": user_input.get("savings", 0) * 0.25,
        "behavior": behavior * 0.35,
        "dependents": user_input.get("dependents", 0) * 0.15,
    }


def compute_risk(
    user_input: Dict[str, Any], macro_data: Dict[str, Any]
) -> Dict[str, Any]:
    raw_score = ml_model.predict(user_input, macro_data.get("macro_score", 50))

    historical = load_real_or_cached_scores()
    calibrated = calibrator.calibrate_score(raw_score, historical)
    category = calibrator.assign_category(calibrated)

    regime = detect_market_regime(
        macro_data.get("vix", 15),
        macro_data.get("inflation", 5),
        macro_data.get("repo_rate", 6),
    )

    if regime == "HIGH_RISK":
        calibrated -= 1
    elif regime == "LOW_RISK":
        calibrated += 0.5

    factors = compute_factor_contributions(user_input)

    return {
        "score": round(max(1.0, min(10.0, calibrated)), 2),
        "raw_score": round(raw_score, 2),
        "category": category,
        "factors": factors,
        "macro_adjustment": regime,
    }


# === Backward Compatibility Wrapper for Tests ===
def calculate_risk_score(
    age: int,
    dependents: int,
    monthly_income: float,
    monthly_savings: float,
    behavioral_trait: str,
) -> Dict[str, Any]:
    beh_map = {"conservative": 1, "moderate": 2, "aggressive": 3}
    user_input = {
        "age": age,
        "dependents": dependents,
        "savings": monthly_savings / max(monthly_income, 1.0) * 100,
        "behavior": beh_map.get(behavioral_trait.lower().strip(), 2),
    }
    # Mock macro data for backwards-compatible test calls
    macro_data = {"macro_score": 50, "vix": 15, "inflation": 5, "repo_rate": 6.5}
    return compute_risk(user_input, macro_data)
