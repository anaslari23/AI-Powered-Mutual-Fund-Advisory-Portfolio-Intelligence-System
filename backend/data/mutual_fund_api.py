import requests
import pandas as pd
from typing import Optional
import logging
import streamlit as st
import io
import time

logger = logging.getLogger(__name__)

AMFI_URL = "https://www.amfiindia.com/spages/NAVAll.txt"

# Browser-like headers to avoid being blocked by AMFI on cloud servers
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/plain,text/html,*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}


@st.cache_data(ttl=3600, show_spinner="Fetching live AMFI NAV data...")
def fetch_amfi_nav_data() -> Optional[pd.DataFrame]:
    """
    Fetches live NAV data from AMFI endpoint with retry logic.
    Parses the text response and converts it to a structured Pandas DataFrame.
    """
    logger.info("Fetching live AMFI NAV data")

    # Retry up to 3 times with increasing delay
    for attempt in range(3):
        try:
            response = requests.get(AMFI_URL, timeout=20, headers=REQUEST_HEADERS)
            response.raise_for_status()

            # Parse the text response
            lines = response.text.split("\n")

            data = []
            current_amc = ""

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                if ";" not in line:
                    if "Mutual Fund" in line:
                        current_amc = line
                    continue

                parts = line.split(";")
                if len(parts) >= 6 and parts[0] != "Scheme Code":
                    scheme_code = parts[0].strip()
                    isin_growth = parts[1].strip()
                    scheme_name = parts[3].strip()
                    nav_str = parts[4].strip()
                    date_str = parts[5].strip()

                    try:
                        nav = float(nav_str)
                        data.append(
                            {
                                "scheme_code": scheme_code,
                                "isin": isin_growth,
                                "scheme_name": scheme_name,
                                "nav": nav,
                                "date": date_str,
                                "amc": current_amc,
                            }
                        )
                    except ValueError:
                        continue

            df = pd.DataFrame(data)
            if df.empty:
                logger.warning("AMFI NAV data fetched but DataFrame is empty")
                return None

            logger.info(f"Successfully fetched {len(df)} funds from AMFI")
            return df

        except requests.exceptions.RequestException as e:
            logger.error(f"Attempt {attempt + 1}/3 failed to fetch AMFI data: {e}")
            if attempt < 2:
                time.sleep(2 * (attempt + 1))  # 2s, 4s backoff
            continue
        except Exception as e:
            logger.error(f"Error parsing AMFI data: {e}")
            return None

    logger.error("All 3 attempts to fetch AMFI NAV data failed")
    return None


def get_mutual_fund_universe() -> tuple[pd.DataFrame, bool]:
    """
    Returns the Mutual Fund universe dataframe and a boolean indicating
    if it's live data from AMFI.
    """
    df = fetch_amfi_nav_data()
    if df is not None and not df.empty:
        return df, True

    # Empty DataFrame as fallback; UI will show warning
    return pd.DataFrame(), False
