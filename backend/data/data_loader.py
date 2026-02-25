import yfinance as yf
import pandas as pd
from typing import Dict, Optional
# Many Indian MFs have specific symbols on Yahoo Finance. Let's use a curated robust list for our categories.

FUNDS_DATABASE = {
    "Equity - Large Cap": [
        "0P00005V1U.BO",  # Nippon India Large Cap Fund
        "0P00005WZY.BO",  # ICICI Prudential Bluechip Fund
    ],
    "Equity - Flexi Cap": [
        "0P0000XVMA.BO",  # Parag Parikh Flexi Cap Fund
        "0P00005WVT.BO",  # HDFC Flexi Cap Fund
    ],
    "Equity - Hybrid": [
        "0P00005WZZ.BO",  # SBI Equity Hybrid Fund
    ],
    "Debt": [
        "LIQUIDBEES.NS",  # Nippon India ETF Liquid BeES (Proxy for Liquid Fund)
        "ICICILIQ.NS",  # ICICI Prudential Liquid ETF
    ],
    "Gold": [
        "GOLDBEES.NS",  # Nippon India ETF Gold BeES
    ],
}


def fetch_historical_data(
    ticker_symbol: str, period: str = "5y"
) -> Optional[pd.DataFrame]:
    """
    Fetches historical NAV (Close price) data for a given mutual fund ticker from Yahoo Finance.
    Returns a pandas DataFrame with 'Date' and 'Close' columns.
    """
    try:
        fund = yf.Ticker(ticker_symbol)
        df = fund.history(period=period)

        if df.empty:
            return None

        # We only need the Close price (NAV representation)
        df = df[["Close"]].reset_index()
        # Ensure Date column is timezone naive for easier handling
        df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)
        return df
    except Exception as e:
        print(f"Failed to fetch data for {ticker_symbol}: {e}")
        return None


def get_all_funds_data() -> Dict[str, pd.DataFrame]:
    """
    Fetches historical data for all predefined funds.
    """
    all_data = {}
    for category, tickers in FUNDS_DATABASE.items():
        for ticker in tickers:
            print(f"Fetching data for {ticker}...")
            df = fetch_historical_data(ticker)
            if df is not None:
                all_data[ticker] = {"category": category, "data": df}
            else:
                print(f"Warning: No data found for {ticker}")

    return all_data


if __name__ == "__main__":
    # Test script locally
    data = get_all_funds_data()
    for ticker, info in data.items():
        print(f"{ticker} ({info['category']}): {len(info['data'])} records")
