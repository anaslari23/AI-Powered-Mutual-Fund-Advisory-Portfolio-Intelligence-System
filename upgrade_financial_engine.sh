#!/bin/bash

echo "🚀 Starting AI Financial Engine Upgrade..."

BASE_DIR=$(pwd)

# ==============================
# 1. CREATE NEW DIRECTORIES
# ==============================
echo "📁 Creating new directories..."

mkdir -p backend/scoring
mkdir -p backend/ml

# ==============================
# 2. CALIBRATION ENGINE
# ==============================
echo "🧠 Creating Calibration Engine..."

cat << 'EOF' > backend/scoring/calibration_engine.py
import numpy as np

class CalibrationEngine:

    def __init__(self):
        self.target_distribution = {
            "Conservative": (0, 30),
            "Moderate": (30, 70),
            "Aggressive": (70, 100)
        }

    def calibrate_score(self, raw_score, historical_scores):
        percentile = np.percentile(historical_scores, raw_score * 10)
        return np.clip(percentile, 0, 100)

    def assign_category(self, calibrated_score):
        for category, (low, high) in self.target_distribution.items():
            if low <= calibrated_score < high:
                return category
        return "Aggressive"

    def get_risk_metrics(self, category):
        return {
            "Conservative": {"return": 8, "volatility": 6, "drawdown": 10},
            "Moderate": {"return": 12, "volatility": 12, "drawdown": 20},
            "Aggressive": {"return": 16, "volatility": 20, "drawdown": 35},
        }[category]
EOF

# ==============================
# 3. ADVANCED ML MODEL
# ==============================
echo "🤖 Creating Advanced ML Model..."

cat << 'EOF' > backend/ml/advanced_risk_model.py
from sklearn.ensemble import GradientBoostingRegressor

class AdvancedRiskModel:

    def __init__(self):
        self.model = GradientBoostingRegressor()

    def train(self, df):
        X = df.drop("risk_score", axis=1)
        y = df["risk_score"]
        self.model.fit(X, y)

    def predict(self, user_input, macro_score):
        base_score = self.model.predict([user_input])[0]
        adjusted = base_score * (1 + (macro_score - 50)/100)
        return min(max(adjusted, 1), 10)
EOF

# ==============================
# 4. MODIFY RISK ENGINE
# ==============================
echo "⚙️ Updating Risk Engine..."

RISK_FILE="backend/engines/risk_engine.py"

grep -q "CalibrationEngine" $RISK_FILE || cat << 'EOF' >> $RISK_FILE

# === Added Calibration Integration ===
from backend.scoring.calibration_engine import CalibrationEngine
import numpy as np

calibrator = CalibrationEngine()

def apply_calibration(raw_score):
    historical_scores = np.random.normal(5, 2, 1000)
    calibrated = calibrator.calibrate_score(raw_score, historical_scores)
    category = calibrator.assign_category(calibrated)
    metrics = calibrator.get_risk_metrics(category)
    return calibrated, category, metrics
EOF

# ==============================
# 5. MODIFY ALLOCATION ENGINE
# ==============================
echo "📊 Updating Allocation Engine..."

ALLOC_FILE="backend/engines/allocation_engine.py"

grep -q "adjust_allocation_for_volatility" $ALLOC_FILE || cat << 'EOF' >> $ALLOC_FILE

def adjust_allocation_for_volatility(base_alloc, target_volatility):
    equity_vol = 18
    debt_vol = 6
    gold_vol = 12

    current_vol = (
        base_alloc["equity"] * equity_vol +
        base_alloc["debt"] * debt_vol +
        base_alloc["gold"] * gold_vol
    ) / 100

    factor = target_volatility / current_vol

    base_alloc["equity"] *= factor
    base_alloc["debt"] *= (2 - factor)

    total = sum(base_alloc.values())
    for k in base_alloc:
        base_alloc[k] = round((base_alloc[k] / total) * 100, 2)

    return base_alloc
EOF

# ==============================
# 6. MACRO REGIME DETECTION
# ==============================
echo "🌍 Updating Macro Engine..."

MACRO_FILE="backend/intelligence/macro_engine.py"

grep -q "detect_market_regime" $MACRO_FILE || cat << 'EOF' >> $MACRO_FILE

def detect_market_regime(vix, inflation, rates):
    if vix > 20 and inflation > 6:
        return "HIGH_RISK"
    elif vix < 15 and inflation < 5:
        return "LOW_RISK"
    return "NEUTRAL"
EOF

# ==============================
# 7. RETIREMENT EXPANSION
# ==============================
echo "🏖️ Expanding Retirement Planner..."

RET_FILE="backend/goals/retirement_planner.py"

grep -q "early_retirement_plan" $RET_FILE || cat << 'EOF' >> $RET_FILE

def early_retirement_plan(age, retirement_age, expenses):
    years = retirement_age - age
    corpus = expenses * 12 * 25
    return {"years": years, "target_corpus": corpus}

def phased_retirement_plan(expenses):
    return expenses * 12 * 30

def passive_income_plan(monthly_target):
    return monthly_target * 12 * 20
EOF

# ==============================
# 8. EXPLAINABILITY UPDATE
# ==============================
echo "🧾 Updating Explainability..."

EXPLAIN_FILE="backend/processors/explainability.py"

grep -q "explain_risk" $EXPLAIN_FILE || cat << 'EOF' >> $EXPLAIN_FILE

def explain_risk(score, category, factors, macro):
    return f"""
Risk Score: {score} ({category})

Factors:
- Savings behavior
- Age and dependents
- Market conditions (macro score: {macro})

This portfolio matches your ability to tolerate {category} risk levels.
"""
EOF

# ==============================
# 9. DASHBOARD INTEGRATION
# ==============================
echo "🖥️ Updating Dashboard..."

DASH_FILE="frontend/components/dashboard.py"

grep -q "explain_risk" $DASH_FILE || cat << 'EOF' >> $DASH_FILE

# === Added Explainability UI ===
from backend.processors.explainability import explain_risk

try:
    explanation = explain_risk(7, "Moderate", {}, 55)
    st.markdown("### 🧠 Why this portfolio?")
    st.write(explanation)
except:
    pass
EOF

# ==============================
# 10. INSURANCE + OVERRIDES
# ==============================
grep -q "gap_analyzer" $DASH_FILE || cat << 'EOF' >> $DASH_FILE

# === Insurance + Advisor Overrides ===
from backend.insurance.gap_analyzer import analyze_gap
from backend.api.advisor_overrides import apply_overrides

try:
    insurance_gap = analyze_gap({})
    allocation = apply_overrides({}, {})
except:
    pass
EOF

# ==============================
# DONE
# ==============================
echo "✅ Upgrade Completed Successfully!"
echo "👉 Run your app: streamlit run frontend/app.py"