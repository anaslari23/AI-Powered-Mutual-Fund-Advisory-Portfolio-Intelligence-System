import sys
import os

# Add root dir to sys.path
sys.path.append(os.path.abspath("."))

from backend.engines.recommendation_engine import suggest_mutual_funds

print("Testing suggest_mutual_funds()...")

try:
    allocation = {"Equity (Large Cap)": 60, "Debt": 40}
    risk_profile = "Moderate"
    recs, is_live = suggest_mutual_funds(allocation, risk_profile)
    print("Success! Recs:", recs)
except Exception as e:
    import traceback

    traceback.print_exc()
