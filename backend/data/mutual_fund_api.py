import requests
import pandas as pd
from typing import Optional
import logging
import streamlit as st
import io

logger = logging.getLogger(__name__)

AMFI_URL = "https://www.amfiindia.com/spages/NAVAll.txt"


@st.cache_data(ttl=21600)  # Cache for 6 hours
def fetch_amfi_nav_data() -> Optional[pd.DataFrame]:
    """
    Fetches live NAV data from AMFI endpoint.
    Parses the text response and converts it to a structured Pandas DataFrame.
    """
    logger.info("Fetching live AMFI NAV data")
    try:
        response = requests.get(AMFI_URL, timeout=15)
        response.raise_for_status()

        # Parse the text response
        lines = response.text.split("\n")

        data = []
        current_category = ""
        current_amc = ""

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # If the line doesn't have a semi-colon, it's either a Category or AMC header
            if ";" not in line:
                if "Mutual Fund" in line:
                    current_amc = line
                continue

            # Data row format: Scheme Code;ISIN Div Payout/ISIN Growth;ISIN Div Reinvestment;Scheme Name;Net Asset Value;Date
            parts = line.split(";")
            if len(parts) >= 6 and parts[0] != "Scheme Code":
                scheme_code = parts[0].strip()
                isin_growth = parts[1].strip()
                scheme_name = parts[3].strip()
                nav_str = parts[4].strip()
                date_str = parts[5].strip()

                # Only include valid numeric NAVs
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
                    continue  # Skip rows with 'N.A.' or invalid NAV

        df = pd.DataFrame(data)
        if df.empty:
            logger.warning("AMFI NAV data fetched but DataFrame is empty")
            return None

        return df

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch AMFI NAV data: {e}")
        return None
    except Exception as e:
        logger.error(f"Error parsing AMFI data: {e}")
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
