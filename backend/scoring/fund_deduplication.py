from typing import List, Dict, Any


def deduplicate_allocations(
    fund_list: List[Dict[str, Any]], fund_universe: List[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    seen = {}
    result = []
    removed = []

    for fund in sorted(fund_list, key=lambda x: x.get("weight", 0), reverse=True):
        name = fund.get("fund_name", "").strip().lower()

        if name not in seen:
            seen[name] = True
            result.append(fund.copy())
        else:
            removed.append(fund)

    for rem in removed:
        for r in result:
            if (
                r.get("category") == rem.get("category")
                and r.get("weight", 0) + rem.get("weight", 0) <= 40
            ):
                r["weight"] = round(r.get("weight", 0) + rem.get("weight", 0), 1)
                break

    total = sum(f.get("weight", 0) for f in result)

    if abs(total - 100.0) > 0.1:
        diff = round(100.0 - total, 1)
        if result:
            result[0]["weight"] = round(result[0].get("weight", 0) + diff, 1)

    return result


def merge_similar_funds(
    funds: List[Dict[str, Any]], similarity_threshold: float = 0.8
) -> List[Dict[str, Any]]:
    if not funds:
        return funds

    merged = []
    processed = set()

    for i, fund in enumerate(funds):
        if i in processed:
            continue

        name1 = fund.get("fund_name", "").lower()
        similar_group = [fund]
        processed.add(i)

        for j, other in enumerate(funds[i + 1 :], start=i + 1):
            if j in processed:
                continue

            name2 = other.get("fund_name", "").lower()

            if name1[:10] == name2[:10] or fund.get("category") == other.get(
                "category"
            ):
                if fund.get("category") == other.get("category"):
                    similar_group.append(other)
                    processed.add(j)

        if len(similar_group) > 1:
            combined = {
                "fund_name": similar_group[0].get("fund_name", "Combined"),
                "category": similar_group[0].get("category", "Mixed"),
                "weight": round(sum(f.get("weight", 0) for f in similar_group), 2),
                "merged_from": [f.get("fund_name", "") for f in similar_group],
                "is_merged": True,
            }
            merged.append(combined)
        else:
            merged.append(fund.copy())

    return merged


def validate_allocation_constraints(allocation: List[Dict[str, Any]]) -> Dict[str, Any]:
    violations = []
    warnings = []

    total = sum(f.get("weight", 0) for f in allocation)
    if abs(total - 100.0) > 0.5:
        violations.append(f"Total allocation {total:.1f}% does not equal 100%")

    category_weights = {}
    for fund in allocation:
        cat = fund.get("category", "Other")
        category_weights[cat] = category_weights.get(cat, 0) + fund.get("weight", 0)

    for cat, weight in category_weights.items():
        if weight > 45:
            violations.append(f"Category {cat} exceeds 45% limit: {weight:.1f}%")
        elif weight > 35:
            warnings.append(f"Category {cat} has high concentration: {weight:.1f}%")

    fund_names = [f.get("fund_name", "").lower() for f in allocation]
    duplicates = set([name for name in fund_names if fund_names.count(name) > 1])
    if duplicates:
        warnings.append(f"Duplicate fund names detected: {', '.join(duplicates)}")

    return {
        "valid": len(violations) == 0,
        "violations": violations,
        "warnings": warnings,
        "total_allocation": round(total, 2),
        "category_weights": {k: round(v, 2) for k, v in category_weights.items()},
    }


if __name__ == "__main__":
    test_funds = [
        {"fund_name": "HDFC Top 100", "category": "Large Cap", "weight": 30.0},
        {"fund_name": "hdfc top 100", "category": "Large Cap", "weight": 20.0},
        {"fund_name": "Mirae Asset Midcap", "category": "Mid Cap", "weight": 25.0},
        {"fund_name": "Axis Bluechip", "category": "Large Cap", "weight": 25.0},
    ]
    result = deduplicate_allocations(test_funds)
    print("Deduplicated:", result)
