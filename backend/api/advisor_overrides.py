try:
    from flask import Blueprint, request, jsonify

    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

import uuid
from datetime import datetime

override_log = []

if FLASK_AVAILABLE:
    advisor_bp = Blueprint("advisor", __name__)

    @advisor_bp.route("/override", methods=["POST"])
    def create_override():
        data = request.json

        entry = {
            "id": str(uuid.uuid4()),
            "client_id": data.get("client_id"),
            "original": data.get("original"),
            "replacement": data.get("replacement"),
            "reason": data.get("reason"),
            "advisor_id": data.get("advisor_id"),
            "created_at": datetime.now().isoformat(),
            "status": "pending",
        }

        override_log.append(entry)

        return jsonify(
            {
                "status": "ok",
                "override_id": entry["id"],
                "message": "Override request created",
            }
        )

    @advisor_bp.route("/override/<override_id>", methods=["GET"])
    def get_override(override_id):
        override = next((o for o in override_log if o["id"] == override_id), None)
        if override:
            return jsonify(override)
        return jsonify({"error": "Override not found"}), 404

    @advisor_bp.route("/override/<override_id>/approve", methods=["POST"])
    def approve_override(override_id):
        override = next((o for o in override_log if o["id"] == override_id), None)
        if override:
            override["status"] = "approved"
            override["approved_at"] = datetime.now().isoformat()
            return jsonify({"status": "approved", "override": override})
        return jsonify({"error": "Override not found"}), 404

    @advisor_bp.route("/override/<override_id>/reject", methods=["POST"])
    def reject_override(override_id):
        data = request.json
        override = next((o for o in override_log if o["id"] == override_id), None)
        if override:
            override["status"] = "rejected"
            override["rejected_at"] = datetime.now().isoformat()
            override["rejection_reason"] = data.get("reason", "")
            return jsonify({"status": "rejected", "override": override})
        return jsonify({"error": "Override not found"}), 404

    @advisor_bp.route("/overrides", methods=["GET"])
    def list_overrides():
        client_id = request.args.get("client_id")
        status = request.args.get("status")
        results = override_log
        if client_id:
            results = [o for o in results if o.get("client_id") == client_id]
        if status:
            results = [o for o in results if o.get("status") == status]
        return jsonify({"overrides": results, "count": len(results)})
else:
    advisor_bp = None


class AdvisorOverrideAPI:
    @staticmethod
    def create_override(client_id, original, replacement, reason, advisor_id):
        entry = {
            "id": str(uuid.uuid4()),
            "client_id": client_id,
            "original": original,
            "replacement": replacement,
            "reason": reason,
            "advisor_id": advisor_id,
            "created_at": datetime.now().isoformat(),
            "status": "pending",
        }
        override_log.append(entry)
        return entry

    @staticmethod
    def approve_override(override_id):
        override = next((o for o in override_log if o["id"] == override_id), None)
        if override:
            override["status"] = "approved"
            override["approved_at"] = datetime.now().isoformat()
            return override
        return None

    @staticmethod
    def reject_override(override_id, reason=""):
        override = next((o for o in override_log if o["id"] == override_id), None)
        if override:
            override["status"] = "rejected"
            override["rejected_at"] = datetime.now().isoformat()
            override["rejection_reason"] = reason
            return override
        return None

    @staticmethod
    def get_override(override_id):
        return next((o for o in override_log if o["id"] == override_id), None)

    @staticmethod
    def get_client_overrides(client_id):
        return [o for o in override_log if o.get("client_id") == client_id]


def apply_overrides(allocation: dict, user_data: dict) -> dict:
    """
    Apply rule-based advisor overrides to an allocation dict.

    Rules applied:
    - Clients over 55: minimum 40% debt allocation
    - Risk score below 4 (conservative): cap equity at 30%
    - Any key in allocation is preserved; only adjusted if rule triggers

    Parameters
    ----------
    allocation : dict
        Current allocation, e.g. {"equity": 60, "debt": 30, "gold": 10}
    user_data : dict
        Client profile dict from session state.

    Returns
    -------
    dict
        Adjusted allocation with override_applied flag and override_reason string.
    """
    if not allocation:
        return allocation

    result = dict(allocation)
    reasons = []

    try:
        age = user_data.get("age", 0)
        risk_score = user_data.get("risk_score", 5)

        # Rule 1: Age-based debt floor
        if age > 55 and result.get("debt", 100) < 40:
            excess = 40 - result.get("debt", 0)
            result["debt"] = 40
            result["equity"] = max(0, result.get("equity", 0) - excess)
            reasons.append(f"Age {age}: minimum 40% debt applied")

        # Rule 2: Conservative risk cap on equity
        if risk_score < 4 and result.get("equity", 0) > 30:
            excess = result["equity"] - 30
            result["equity"] = 30
            result["debt"] = result.get("debt", 0) + excess
            reasons.append(f"Risk score {risk_score}: equity capped at 30%")

        # Re-normalise to 100%
        total = sum(result.get(k, 0) for k in ["equity", "debt", "gold"])
        if total > 0 and abs(total - 100) > 0.5:
            for k in ["equity", "debt", "gold"]:
                if k in result:
                    result[k] = round(result[k] / total * 100, 2)

        result["override_applied"] = len(reasons) > 0
        result["override_reason"] = "; ".join(reasons) if reasons else ""

    except Exception as e:
        result["override_applied"] = False
        result["override_reason"] = f"Override skipped: {e}"

    return result
