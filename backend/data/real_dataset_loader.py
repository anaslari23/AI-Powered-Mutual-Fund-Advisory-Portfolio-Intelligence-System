import pandas as pd
import os
from typing import Optional, Dict, Any


def load_real_data() -> Optional[pd.DataFrame]:
    try:
        data_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "data", "investor_profiles.csv"
        )
        if os.path.exists(data_path):
            return pd.read_csv(data_path)
    except Exception:
        pass
    return None


def load_market_data() -> Optional[pd.DataFrame]:
    try:
        data_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "data", "market_data.csv"
        )
        if os.path.exists(data_path):
            return pd.read_csv(data_path)
    except Exception:
        pass
    return None


def load_fund_performance() -> Optional[pd.DataFrame]:
    try:
        data_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "data", "fund_performance.csv"
        )
        if os.path.exists(data_path):
            return pd.read_csv(data_path)
    except Exception:
        pass
    return None


def get_data_status() -> Dict[str, Any]:
    status = {
        "investor_profiles": False,
        "market_data": False,
        "fund_performance": False,
        "source": "fallback",
    }

    if load_real_data() is not None:
        status["investor_profiles"] = True
        status["source"] = "live"

    if load_market_data() is not None:
        status["market_data"] = True
        status["source"] = "live"

    if load_fund_performance() is not None:
        status["fund_performance"] = True

    return status


if __name__ == "__main__":
    print("Data Status:", get_data_status())
    df = load_real_data()
    if df is not None:
        print("Loaded investor profiles:", len(df), "records")
    else:
        print("No real data available - using fallback")
