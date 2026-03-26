from backend.engines.monte_carlo_engine import run_monte_carlo_simulation
from backend.scoring.monte_carlo_remediation import (
    build_sensitivity_analysis,
    generate_fix_recommendation,
)


def test_monte_carlo_uses_initial_corpus_and_monthly_sip_inputs():
    probability = run_monte_carlo_simulation(
        initial_corpus=900000,
        monthly_sip=40000,
        years=5,
        target_corpus=3500000,
        expected_annual_return=0.12,
        annual_volatility=0.0,
        num_simulations=1000,
    )
    assert probability == 100.0


def test_monte_carlo_counts_unsuccessful_paths_against_target():
    probability = run_monte_carlo_simulation(
        initial_corpus=900000,
        monthly_sip=40000,
        years=5,
        target_corpus=5000000,
        expected_annual_return=0.12,
        annual_volatility=0.0,
        num_simulations=1000,
    )
    assert probability == 0.0


def test_generate_fix_recommendation_uses_current_sip_capacity():
    result = generate_fix_recommendation(
        current_sip=40000,
        required_sip=59294,
        required_corpus=3850000,
        current_age=30,
        retirement_age=40,
        current_monthly_expense=50000,
        existing_corpus=900000,
        expected_return=0.12,
        annual_volatility=0.15,
    )
    assert "₹40,000" in result["gap_analysis"]
    assert "₹59,294" in result["gap_analysis"]
    assert result["recommended"] == "option_2"


def test_sensitivity_analysis_extends_to_two_x_required_sip():
    result = build_sensitivity_analysis(
        current_sip=40000,
        required_sip=59294,
        initial_corpus=900000,
        target_corpus=3850000,
        years=10,
        expected_return=0.12,
        annual_volatility=0.15,
        points=10,
    )
    assert result["sips"][0] == 40000.0
    assert result["sips"][-1] == round(2.0 * 59294, 2)
