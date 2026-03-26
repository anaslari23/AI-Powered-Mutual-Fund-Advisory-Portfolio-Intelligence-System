from typing import Dict, Any, List, Tuple
import numpy as np
from scipy import stats

np.random.seed(42)


def run_monte_carlo_simulation(
    initial_corpus: float,
    monthly_sip: float,
    years: int,
    target_corpus: float,
    expected_annual_return: float,
    annual_volatility: float = 0.12,
    num_simulations: int = 1000,
    seed: int = 42,
) -> Dict[str, Any]:
    if years <= 0 or target_corpus <= 0:
        return {
            "success_probability": 0.0,
            "median_outcome": 0.0,
            "percentile_10": 0.0,
            "percentile_90": 0.0,
            "simulations": [],
        }

    np.random.seed(seed)
    months = years * 12
    dt = 1.0 / 12.0

    drift = (expected_annual_return - (annual_volatility**2) / 2) * dt
    diffusion = (
        annual_volatility
        * np.sqrt(dt)
        * np.random.normal(size=(num_simulations, months))
    )

    return_multipliers = np.exp(drift + diffusion)

    final_values = []
    success_count = 0

    for i in range(num_simulations):
        current_corpus = initial_corpus
        for month in range(months):
            current_corpus += monthly_sip
            current_corpus *= return_multipliers[i, month]

        final_values.append(current_corpus)
        if current_corpus >= target_corpus:
            success_count += 1

    final_values = np.array(final_values)
    success_probability = (success_count / num_simulations) * 100.0

    return {
        "success_probability": round(success_probability, 2),
        "median_outcome": round(float(np.median(final_values)), 2),
        "percentile_10": round(float(np.percentile(final_values, 10)), 2),
        "percentile_25": round(float(np.percentile(final_values, 25)), 2),
        "percentile_75": round(float(np.percentile(final_values, 75)), 2),
        "percentile_90": round(float(np.percentile(final_values, 90)), 2),
        "mean_outcome": round(float(np.mean(final_values)), 2),
        "std_deviation": round(float(np.std(final_values)), 2),
        "min_outcome": round(float(np.min(final_values)), 2),
        "max_outcome": round(float(np.max(final_values)), 2),
        "simulations": [],
    }


def binary_search_sip(
    initial_corpus: float,
    target_corpus: float,
    years: int,
    expected_return: float,
    volatility: float = 0.12,
    success_threshold: float = 75.0,
    max_sip: float = 1000000,
    min_sip: float = 0,
) -> float:
    best_sip = min_sip

    for _ in range(50):
        mid_sip = (best_sip + max_sip) / 2
        result = run_monte_carlo_simulation(
            initial_corpus=initial_corpus,
            monthly_sip=mid_sip,
            years=years,
            target_corpus=target_corpus,
            expected_annual_return=expected_return,
            annual_volatility=volatility,
            num_simulations=500,
        )

        if result["success_probability"] >= success_threshold:
            best_sip = mid_sip
            max_sip = mid_sip
        else:
            min_sip = mid_sip

    return round(best_sip, 2)


def generate_remediation_options(
    current_sip: float,
    initial_corpus: float,
    target_corpus: float,
    years: int,
    expected_return: float,
    volatility: float = 0.12,
) -> Dict[str, Any]:
    baseline = run_monte_carlo_simulation(
        initial_corpus, current_sip, years, target_corpus, expected_return, volatility
    )

    options = []

    if baseline["success_probability"] < 80:
        increased_sip = current_sip * 1.25
        option_a = run_monte_carlo_simulation(
            initial_corpus,
            increased_sip,
            years,
            target_corpus,
            expected_return,
            volatility,
        )
        options.append(
            {
                "option_id": "A",
                "description": "Increase SIP by 25%",
                "new_sip": round(increased_sip, 2),
                "success_probability": option_a["success_probability"],
                "median_outcome": option_a["median_outcome"],
                "additional_monthly": round(increased_sip - current_sip, 2),
            }
        )

        optimal_sip = binary_search_sip(
            initial_corpus, target_corpus, years, expected_return, volatility
        )
        if optimal_sip > current_sip:
            option_b = run_monte_carlo_simulation(
                initial_corpus,
                optimal_sip,
                years,
                target_corpus,
                expected_return,
                volatility,
            )
            options.append(
                {
                    "option_id": "B",
                    "description": "Optimize SIP to achieve 75% success probability",
                    "new_sip": optimal_sip,
                    "success_probability": option_b["success_probability"],
                    "median_outcome": option_b["median_outcome"],
                    "additional_monthly": round(optimal_sip - current_sip, 2),
                }
            )

    if years >= 5:
        extended_years = years + 3
        option_c = run_monte_carlo_simulation(
            initial_corpus,
            current_sip,
            extended_years,
            target_corpus,
            expected_return,
            volatility,
        )
        options.append(
            {
                "option_id": "C",
                "description": f"Extend timeline by 3 years ({extended_years} years total)",
                "new_sip": current_sip,
                "success_probability": option_c["success_probability"],
                "median_outcome": option_c["median_outcome"],
                "additional_monthly": 0,
                "new_years": extended_years,
            }
        )

    if baseline["success_probability"] < 60:
        lumpsum_additional = initial_corpus * 0.25
        option_d = run_monte_carlo_simulation(
            initial_corpus + lumpsum_additional,
            current_sip,
            years,
            target_corpus,
            expected_return,
            volatility,
        )
        options.append(
            {
                "option_id": "D",
                "description": f"Add lumpsum investment of {round(lumpsum_additional, 0)}",
                "new_sip": current_sip,
                "new_lumpsum": round(initial_corpus + lumpsum_additional, 2),
                "success_probability": option_d["success_probability"],
                "median_outcome": option_d["median_outcome"],
                "additional_monthly": 0,
                "additional_lumpsum": round(lumpsum_additional, 2),
            }
        )

    sorted_options = sorted(
        options, key=lambda x: x.get("success_probability", 0), reverse=True
    )

    return {
        "baseline": {
            "current_sip": current_sip,
            "success_probability": baseline["success_probability"],
            "median_outcome": baseline["median_outcome"],
        },
        "options": sorted_options,
        "recommended_option": sorted_options[0]["option_id"]
        if sorted_options
        else None,
    }


def calculate_goal_achievability(
    current_sip: float,
    initial_corpus: float,
    target_corpus: float,
    years: int,
    expected_return: float,
    volatility: float = 0.12,
) -> Dict[str, Any]:
    simulation = run_monte_carlo_simulation(
        initial_corpus, current_sip, years, target_corpus, expected_return, volatility
    )

    probability = simulation["success_probability"]

    if probability >= 80:
        status = "On Track"
        message = "Goal is likely achievable with current investment plan."
    elif probability >= 60:
        status = "At Risk"
        message = "Goal may be achievable with adjustments to investment plan."
    elif probability >= 40:
        status = "Needs Attention"
        message = "Significant changes needed to achieve goal."
    else:
        status = "Off Track"
        message = "Goal is unlikely achievable with current plan. Consider revising."

    return {
        "status": status,
        "message": message,
        "success_probability": probability,
        "median_outcome": simulation["median_outcome"],
        "worst_case_10": simulation["percentile_10"],
        "best_case_90": simulation["percentile_90"],
        "shortfall_at_median": max(0, target_corpus - simulation["median_outcome"]),
        "recommendations": _get_recommendations(
            probability, target_corpus, simulation["median_outcome"]
        ),
    }


def _get_recommendations(probability: float, target: float, median: float) -> List[str]:
    recommendations = []

    if probability < 80:
        shortfall = target - median
        recommendations.append(
            f"Consider increasing monthly investment by approximately {round(shortfall * 0.1 / 12, 0)} to improve success probability."
        )

    if probability < 60:
        recommendations.append(
            "Consider extending your investment horizon by 2-3 years if possible."
        )

    if probability < 50:
        recommendations.append(
            "Consider reducing target corpus or breaking into smaller milestone goals."
        )

    return recommendations


if __name__ == "__main__":
    result = run_monte_carlo_simulation(100000, 10000, 15, 5000000, 0.12, 0.15)
    print("Monte Carlo Result:", result)

    remediation = generate_remediation_options(10000, 100000, 5000000, 15, 0.12)
    print("Remediation Options:", remediation)
