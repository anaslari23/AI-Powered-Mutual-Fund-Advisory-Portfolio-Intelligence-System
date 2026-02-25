def calculate_sip_future_value(
    monthly_investment: float, annual_return_rate: float, years: int
) -> float:
    """
    Calculate the Future Value of a Systematic Investment Plan (SIP).
    FV = P * [((1+r)^n - 1) / r] * (1+r)

    Args:
        monthly_investment (float): Monthly investment amount.
        annual_return_rate (float): Expected annual return rate as a decimal (e.g., 0.12 for 12%).
        years (int): Investment duration in years.

    Returns:
        float: Future value of the SIP.
    """
    if years <= 0:
        return 0.0

    monthly_rate = annual_return_rate / 12.0
    total_months = years * 12

    if monthly_rate == 0.0:
        return monthly_investment * total_months

    # Standard SIP Formula (Investment at the beginning of the month)
    fv = (
        monthly_investment
        * (((1 + monthly_rate) ** total_months - 1) / monthly_rate)
        * (1 + monthly_rate)
    )
    return fv


def calculate_required_sip(
    future_value: float, annual_return_rate: float, years: int
) -> float:
    """
    Calculate the required monthly SIP to reach a specific future value.
    """
    if years <= 0:
        return 0.0

    monthly_rate = annual_return_rate / 12.0
    total_months = years * 12

    if monthly_rate == 0.0:
        return future_value / total_months

    sip = future_value / (
        (((1 + monthly_rate) ** total_months - 1) / monthly_rate) * (1 + monthly_rate)
    )
    return sip
