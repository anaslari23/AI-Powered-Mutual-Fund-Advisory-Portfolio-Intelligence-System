import numpy as np


def run_monte_carlo_simulation(
    initial_corpus: float,
    monthly_sip: float,
    years: int,
    target_corpus: float,
    expected_annual_return: float,
    annual_volatility: float = 0.12,
    num_simulations: int = 1000,
) -> float:
    """
    Run a Monte Carlo simulation to calculate the probability of achieving the target corpus.
    Simulates `num_simulations` scenarios using a normal distribution of returns.
    """
    if years <= 0 or target_corpus <= 0:
        return 0.0

    months = years * 12
    monthly_return_mean = expected_annual_return / 12.0
    monthly_volatility = annual_volatility / np.sqrt(12)

    success_count = 0
    np.random.seed(42)  # For reproducibility in testing

    random_returns = np.random.normal(
        monthly_return_mean, monthly_volatility, (num_simulations, months)
    )

    for i in range(num_simulations):
        current_corpus = initial_corpus
        for month in range(months):
            current_corpus += monthly_sip
            current_corpus *= 1 + random_returns[i, month]

        if current_corpus >= target_corpus:
            success_count += 1

    success_probability = (success_count / num_simulations) * 100.0

    return round(success_probability, 2)
