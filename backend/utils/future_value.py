def calculate_future_value(
    present_value: float, rate_of_return: float, years: int
) -> float:
    """
    Calculate Future Value of a lump sum amount.
    FV = PV * (1 + r)^years

    Args:
        present_value (float): The current value (or cost).
        rate_of_return (float): Expected annual inflation or return rate as a decimal (e.g., 0.06 for 6%).
        years (int): Number of years into the future.

    Returns:
        float: Future value.
    """
    if years < 0:
        raise ValueError("Years must be non-negative.")

    return present_value * ((1 + rate_of_return) ** years)
