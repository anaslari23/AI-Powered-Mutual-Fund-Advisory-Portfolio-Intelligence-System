from typing import Dict, Any, List, Optional
import numpy as np

BENCHMARKS = {
    "NIFTY 50": {"type": "index", "expected_return": 0.12, "volatility": 0.16},
    "NIFTY 100": {"type": "index", "expected_return": 0.13, "volatility": 0.18},
    "NIFTY 200": {"type": "index", "expected_return": 0.14, "volatility": 0.20},
    "NIFTY MIDCAP 100": {"type": "index", "expected_return": 0.16, "volatility": 0.22},
    "NIFTY SMALLCAP 100": {
        "type": "index",
        "expected_return": 0.18,
        "volatility": 0.28,
    },
    "NIFTY 50 VALUE 20": {"type": "index", "expected_return": 0.11, "volatility": 0.14},
    "NIFTY GROWTH SECTOR 15": {
        "type": "index",
        "expected_return": 0.14,
        "volatility": 0.19,
    },
    "CRISIL 10 Year Gilt": {
        "type": "debt",
        "expected_return": 0.07,
        "volatility": 0.05,
    },
    "CRISIL Composite Bond": {
        "type": "debt",
        "expected_return": 0.075,
        "volatility": 0.06,
    },
    "NIFTY 1D Rate": {"type": "debt", "expected_return": 0.055, "volatility": 0.01},
    "NIFTY Gold": {"type": "commodity", "expected_return": 0.08, "volatility": 0.15},
    "NIFTY Silver": {"type": "commodity", "expected_return": 0.10, "volatility": 0.22},
}


def get_benchmark(name: str) -> Optional[Dict[str, Any]]:
    return BENCHMARKS.get(name.upper())


def get_all_benchmarks() -> List[Dict[str, Any]]:
    return [{"name": name, **data} for name, data in BENCHMARKS.items()]


def get_benchmark_by_type(benchmark_type: str) -> List[Dict[str, Any]]:
    return [
        {"name": name, **data}
        for name, data in BENCHMARKS.items()
        if data.get("type") == benchmark_type.lower()
    ]


def compare_fund_to_benchmark(
    fund_return: float,
    fund_volatility: float,
    benchmark_name: str,
    risk_free_rate: float = 0.055,
) -> Dict[str, Any]:
    benchmark = get_benchmark(benchmark_name)
    if not benchmark:
        return {"valid": False, "error": f"Benchmark {benchmark_name} not found"}

    excess_return = fund_return - risk_free_rate
    benchmark_excess = benchmark["expected_return"] - risk_free_rate

    sharpe_ratio = (excess_return / fund_volatility) if fund_volatility > 0 else 0
    benchmark_sharpe = (
        (benchmark_excess / benchmark["volatility"])
        if benchmark["volatility"] > 0
        else 0
    )

    return_diff = fund_return - benchmark["expected_return"]
    volatility_diff = fund_volatility - benchmark["volatility"]

    if return_diff > 0.02 and volatility_diff < 0.02:
        performance = "Outperforming"
    elif return_diff > 0:
        performance = "Slightly Outperforming"
    elif return_diff > -0.02:
        performance = "In Line"
    elif return_diff > -0.05:
        performance = "Underperforming"
    else:
        performance = "Significantly Underperforming"

    return {
        "valid": True,
        "fund": {
            "return": round(fund_return, 4),
            "volatility": round(fund_volatility, 4),
            "sharpe_ratio": round(sharpe_ratio, 3),
        },
        "benchmark": {
            "name": benchmark_name,
            "return": round(benchmark["expected_return"], 4),
            "volatility": round(benchmark["volatility"], 4),
            "sharpe_ratio": round(benchmark_sharpe, 3),
        },
        "comparison": {
            "return_difference": round(return_diff, 4),
            "volatility_difference": round(volatility_diff, 4),
            "performance": performance,
            "alpha": round(return_diff, 4),
        },
    }


def select_appropriate_benchmark(fund_category: str) -> str:
    category_benchmarks = {
        "Large Cap": "NIFTY 50",
        "Mid Cap": "NIFTY MIDCAP 100",
        "Small Cap": "NIFTY SMALLCAP 100",
        "Multi Cap": "NIFTY 100",
        "Large & Mid Cap": "NIFTY 100",
        "Index": "NIFTY 50",
        "ELSS": "NIFTY 50",
        "Value": "NIFTY 50 VALUE 20",
        "Growth": "NIFTY GROWTH SECTOR 15",
        "Debt": "CRISIL Composite Bond",
        "Liquid": "NIFTY 1D Rate",
        "Gold": "NIFTY Gold",
        "Silver": "NIFTY Silver",
    }

    return category_benchmarks.get(fund_category, "NIFTY 50")


def calculate_fund_metrics(
    returns: List[float], risk_free_rate: float = 0.055
) -> Dict[str, Any]:
    if not returns:
        return {"valid": False, "error": "No returns data provided"}

    returns_array = np.array(returns)
    mean_return = np.mean(returns_array)
    std_return = np.std(returns_array, ddof=1)

    annual_return = mean_return * 12
    annual_volatility = std_return * np.sqrt(12)

    excess_return = annual_return - risk_free_rate
    sharpe_ratio = (excess_return / annual_volatility) if annual_volatility > 0 else 0

    cumulative_returns = (1 + returns_array).cumprod() - 1
    max_drawdown = 0
    peak = cumulative_returns[0]
    for ret in cumulative_returns:
        if ret > peak:
            peak = ret
        drawdown = peak - ret
        if drawdown > max_drawdown:
            max_drawdown = drawdown

    positive_months = np.sum(returns_array > 0)
    win_rate = positive_months / len(returns_array)

    return {
        "valid": True,
        "monthly_return": round(mean_return, 4),
        "monthly_volatility": round(std_return, 4),
        "annual_return": round(annual_return, 4),
        "annual_volatility": round(annual_volatility, 4),
        "sharpe_ratio": round(sharpe_ratio, 3),
        "max_drawdown": round(max_drawdown, 4),
        "win_rate": round(win_rate, 4),
        "total_return": round(cumulative_returns[-1], 4),
    }


if __name__ == "__main__":
    print(get_all_benchmarks())
    print(select_appropriate_benchmark("Large Cap"))
    print(compare_fund_to_benchmark(0.14, 0.16, "NIFTY 50"))
