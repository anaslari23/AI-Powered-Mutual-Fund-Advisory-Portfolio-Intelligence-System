# tests/run_all_phase_tests.py

import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ================================================================
# PHASE 1 TESTS
# ================================================================

def test_phase_1():

    print("\n=== PHASE 1 TESTS ===")

    # -----------------------------
    # T1.1 — Risk Score
    # -----------------------------
    from backend.engines.risk_engine import calculate_risk_score

    r = calculate_risk_score(45, 0, 150000, 40000, 'moderate')

    assert r['category'] != 'Aggressive', \
        f'FAIL T1.1a: got {r["category"]}'

    assert len(r['factor_contributions']) == 4, \
        'FAIL T1.1b: missing contributions'

    assert abs(sum(r['factor_contributions'].values()) - r['raw_score']) < 0.5, \
        'FAIL T1.1c: contributions dont sum to score'

    print("✅ T1.1 PASS: Risk score working correctly")

    # -----------------------------
    # T1.2 — Diversification Score
    # -----------------------------
    from backend.scoring.diversification_engine import calculate_diversification_score

    # Mapped from original dict parameters
    allocation = [
        {'category': 'Debt', 'weight': 55.5},
        {'category': 'Liquid', 'weight': 22.2},
        {'category': 'Gold', 'weight': 11.2},
        {'category': 'Multi Cap', 'weight': 11.1}
    ]

    d = calculate_diversification_score(allocation)

    assert d['diversification_score'] < 100.0, \
        f'FAIL T1.2: Score {d["diversification_score"]} too high'

    assert 'Optimal' not in d.get('category',''), \
        'FAIL T1.2: Incorrect Optimal label'

    print(f"✅ T1.2 PASS: Score {d['diversification_score']}")

    # -----------------------------
    # T1.3 — Fund Deduplication
    # -----------------------------
    from backend.scoring.fund_deduplication import deduplicate_allocations

    funds = [
        {'fund_name':'Baroda BNP Flexi','category':'flexi','weight':25,'ai_score':70},
        {'fund_name':'Baroda BNP Flexi','category':'flexi','weight':5,'ai_score':70},
        {'fund_name':'ICICI Bluechip','category':'large','weight':40,'ai_score':85},
        {'fund_name':'Nippon Liquid','category':'debt','weight':30,'ai_score':80},
    ]

    clean = deduplicate_allocations(funds)

    names = [f['fund_name'] for f in clean]

    assert len(names) == len(set(names)), \
        'FAIL T1.3: duplicates still exist'

    total_weight = sum(f.get('weight', 0) for f in clean)

    assert abs(total_weight - 100.0) < 0.6, \
        'FAIL T1.3: weights not normalized'

    print(f"✅ T1.3 PASS: {len(clean)} funds, total={total_weight}")

    # -----------------------------
    # T1.4 — Assumption Box
    # -----------------------------
    from backend.scoring.assumption_box import AssumptionBox

    ab = AssumptionBox(risk_score=5).get_all_assumptions()

    assert ab['expected_return'] == 0.12, \
        'FAIL T1.4: wrong return'

    print("✅ T1.4 PASS: Assumption box correct")

    # -----------------------------
    # T1.5 — Monte Carlo Remediation
    # -----------------------------
    from backend.scoring.monte_carlo_remediation import generate_remediation_options

    mc = generate_remediation_options(current_sip=100000, initial_corpus=10000, target_corpus=50000000, years=10, expected_return=0.11, volatility=0.15)

    if mc['baseline']['success_probability'] < 80:
        assert 'options' in mc, \
            'FAIL T1.5: remediation missing'

    print("✅ T1.5 PASS: Monte Carlo Remediation working")

    print("=== PHASE 1 ALL PASS ===\n")


# ================================================================
# PHASE 2 TESTS
# ================================================================

def test_phase_2():

    print("=== PHASE 2 TESTS ===")

    from backend.goals.goal_registry import GoalRegistry

    # Instantiating if GoalRegistry requires it, or using as class method
    edu = GoalRegistry().calculate_required_corpus(
        'child_education',
        {
            'child_current_age':5,
            'education_start_age':18,
            'target_amount':3000000
        },
        11.0
    )

    assert edu['required_corpus'] > 3000000, \
        'FAIL T2.1: inflation not applied'

    print(f"✅ T2.1 PASS: corpus ₹{edu['required_corpus']:,.0f}")

    ret = GoalRegistry().calculate_required_corpus(
        'retirement',
        {
            'current_age':30,
            'retirement_age':60,
            'life_expectancy':85,
            'current_monthly_expense':50000,
            'lifestyle_factor':1.0
        },
        11.0
    )

    assert 'required_corpus' in ret, \
        'FAIL T2.2: retirement missing output'

    print(f"✅ T2.2 PASS: retirement corpus ₹{ret['required_corpus']:,.0f}")

    print("=== PHASE 2 ALL PASS ===\n")


# ================================================================
# PHASE 3 TESTS
# ================================================================

def test_phase_3():

    print("=== PHASE 3 TESTS ===")

    from backend.funds.overlap_engine import eliminate_overlapping_funds

    funds = [
        {
            'fund_name':'Fund A',
            'ai_score':80,
            'top_holdings':['TCS','INFY','HDFC','RIL','WIPRO']
        },
        {
            'fund_name':'Fund B',
            'ai_score':70,
            'top_holdings':['TCS','INFY','HDFC','RIL','ITC']
        }
    ]

    clean = eliminate_overlapping_funds(funds, threshold=40)

    assert len(clean) == 1, \
        'FAIL T3.1: overlap not removed'

    print("✅ T3.1 PASS: overlap removed")

    from backend.intelligence.macro_engine import calculate_macro_stability

    m = calculate_macro_stability(6.0, 24.0)

    assert 0 <= m['stability_score'] <= 1, \
        'FAIL T3.2: invalid macro score'

    print("✅ T3.2 PASS: macro working")

    print("=== PHASE 3 ALL PASS ===\n")


# ================================================================
# MAIN RUNNER
# ================================================================

if __name__ == "__main__":

    test_phase_1()
    test_phase_2()
    test_phase_3()

    print("\n🎉 ALL PHASES PASS — SYSTEM READY")
