BENCHMARK_DATA = {
    "large_cap": {
        "index": "Nifty 50 TRI",
        "1y": 26.0,
        "3y": 18.0,
        "5y": 17.0,
        "sharpe_median": 0.85,
    },
    "mid_cap": {
        "index": "Nifty Midcap 150 TRI",
        "1y": 35.0,
        "3y": 22.0,
        "5y": 21.0,
        "sharpe_median": 0.75,
    },
    "small_cap": {
        "index": "Nifty Smallcap 250 TRI",
        "1y": 38.0,
        "3y": 24.0,
        "5y": 20.0,
        "sharpe_median": 0.65,
    },
    "flexi_cap": {
        "index": "Nifty 500 TRI",
        "1y": 28.0,
        "3y": 19.0,
        "5y": 18.0,
        "sharpe_median": 0.80,
    },
    "hybrid": {
        "index": "Nifty Hybrid 65:35",
        "1y": 18.0,
        "3y": 13.0,
        "5y": 12.0,
        "sharpe_median": 0.90,
    },
    "debt": {
        "index": "Debt Index",
        "1y": 7.5,
        "3y": 6.5,
        "5y": 6.8,
        "sharpe_median": 1.20,
    },
    "gold": {
        "index": "MCX Gold",
        "1y": 15.0,
        "3y": 12.0,
        "5y": 14.0,
        "sharpe_median": 0.50,
    },
}

CATEGORY_MAP = {
    "large cap": "large_cap",
    "mid cap": "mid_cap",
    "small cap": "small_cap",
    "flexi cap": "flexi_cap",
    "hybrid": "hybrid",
    "debt": "debt",
    "gold": "gold",
}


def get_benchmark(category):
    key = CATEGORY_MAP.get(category.lower(), "flexi_cap")
    return BENCHMARK_DATA[key]


def calculate_alpha(fund_return, benchmark_return):
    return round(fund_return - benchmark_return, 2)


def generate_benchmark_comparison(fund, category):
    bm = get_benchmark(category)

    return {
        "fund_name": fund["fund_name"],
        "benchmark": bm["index"],
        "alpha_1y": calculate_alpha(fund.get("1y_return", 0), bm["1y"]),
        "alpha_3y": calculate_alpha(fund.get("3y_return", 0), bm["3y"]),
        "alpha_5y": calculate_alpha(fund.get("5y_return", 0), bm["5y"]),
        "sharpe_above_median": fund.get("sharpe_ratio", 0) >= bm["sharpe_median"],
    }


def compare_fund_to_benchmark(fund, category):
    bm = get_benchmark(category)

    fund_1y = fund.get("1y_return", 0)
    fund_3y = fund.get("3y_return", 0)
    fund_5y = fund.get("5y_return", 0)
    fund_sharpe = fund.get("sharpe_ratio", 0)

    return {
        "benchmark_name": bm["index"],
        "fund_returns": {"1y": fund_1y, "3y": fund_3y, "5y": fund_5y},
        "benchmark_returns": {"1y": bm["1y"], "3y": bm["3y"], "5y": bm["5y"]},
        "alpha": {
            "1y": calculate_alpha(fund_1y, bm["1y"]),
            "3y": calculate_alpha(fund_3y, bm["3y"]),
            "5y": calculate_alpha(fund_5y, bm["5y"]),
        },
        "sharpe_ratio": fund_sharpe,
        "sharpe_median": bm["sharpe_median"],
        "outperforming": fund_sharpe >= bm["sharpe_median"],
    }
