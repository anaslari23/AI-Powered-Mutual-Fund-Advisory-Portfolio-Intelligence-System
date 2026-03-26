from backend.scoring.diversification_engine import (
    calculate_diversification_score,
    apply_diversification_penalties,
    generate_diversification_comments,
    optimize_allocation_for_diversification,
)

from backend.scoring.fund_deduplication import (
    deduplicate_allocations,
    merge_similar_funds,
    validate_allocation_constraints,
)

from backend.scoring.assumption_box import (
    AssumptionBox,
    get_assumption_for_profile,
    RISK_RETURN_MAP,
    INFLATION_RATES,
    EXPECTED_Market_RETURNS,
)

from backend.scoring.monte_carlo_remediation import (
    run_monte_carlo_simulation,
    binary_search_sip,
    generate_remediation_options,
    calculate_goal_achievability,
)

__all__ = [
    "calculate_diversification_score",
    "apply_diversification_penalties",
    "generate_diversification_comments",
    "optimize_allocation_for_diversification",
    "deduplicate_allocations",
    "merge_similar_funds",
    "validate_allocation_constraints",
    "AssumptionBox",
    "get_assumption_for_profile",
    "RISK_RETURN_MAP",
    "INFLATION_RATES",
    "EXPECTED_Market_RETURNS",
    "run_monte_carlo_simulation",
    "binary_search_sip",
    "generate_remediation_options",
    "calculate_goal_achievability",
]
