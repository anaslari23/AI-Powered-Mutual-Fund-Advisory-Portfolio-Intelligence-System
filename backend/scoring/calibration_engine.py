import numpy as np
from typing import Dict, Any, List, Optional


class CalibrationEngine:
    def __init__(self):
        self.target_distribution = {
            "Conservative": (0, 30),
            "Moderate": (30, 70),
            "Aggressive": (70, 100),
        }
        self.score_bounds = (1.0, 10.0)
        self.category_thresholds = {
            "Highly Conservative": 3.0,
            "Conservative": 5.0,
            "Moderately Conservative": 6.5,
            "Moderate": 7.5,
            "Moderately Aggressive": 8.5,
            "Aggressive": 10.0,
        }

    def calibrate_score(self, raw_score, historical_scores=None):
        if historical_scores is not None and len(historical_scores) > 0:
            try:
                hist_mean = np.mean(historical_scores)
                hist_std = np.std(historical_scores)

                if hist_std > 0:
                    z_score = (raw_score - hist_mean) / hist_std
                    calibrated = 5.0 + z_score * 1.5
                else:
                    calibrated = raw_score
            except:
                calibrated = raw_score
        else:
            calibrated = raw_score

        return round(
            max(self.score_bounds[0], min(self.score_bounds[1], calibrated)), 2
        )

    def assign_category(self, calibrated_score):
        if calibrated_score < self.category_thresholds["Highly Conservative"]:
            return "Highly Conservative"
        elif calibrated_score < self.category_thresholds["Conservative"]:
            return "Conservative"
        elif calibrated_score < self.category_thresholds["Moderately Conservative"]:
            return "Moderately Conservative"
        elif calibrated_score < self.category_thresholds["Moderate"]:
            return "Moderate"
        elif calibrated_score < self.category_thresholds["Moderately Aggressive"]:
            return "Moderately Aggressive"
        else:
            return "Aggressive"

    def get_risk_metrics(self, category):
        return {
            "Conservative": {"return": 8, "volatility": 6, "drawdown": 10},
            "Moderate": {"return": 12, "volatility": 12, "drawdown": 20},
            "Aggressive": {"return": 16, "volatility": 20, "drawdown": 35},
        }.get(category, {"return": 10, "volatility": 10, "drawdown": 15})

    def get_confidence_interval(self, score, historical_scores=None):
        if historical_scores is not None and len(historical_scores) > 10:
            std = np.std(historical_scores)
            return {
                "lower": round(max(1.0, score - 1.96 * std), 2),
                "upper": round(min(10.0, score + 1.96 * std), 2),
                "confidence": "high" if std < 1.5 else "medium" if std < 2.5 else "low",
            }
        return {
            "lower": round(score - 1.0, 2),
            "upper": round(score + 1.0, 2),
            "confidence": "low",
        }

    def apply_user_feedback(self, current_score, user_adjuster, historical_scores=None):
        adjusted = current_score + (user_adjuster - 5.0) * 0.5
        return self.calibrate_score(adjusted, historical_scores)
