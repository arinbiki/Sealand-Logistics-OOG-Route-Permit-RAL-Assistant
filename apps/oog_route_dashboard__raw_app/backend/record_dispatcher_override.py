"""
Backend runnable for Windmill Raw App: record_dispatcher_override
Allows a human dispatcher to grant an engineering waiver for a high-risk route survey.
"""
import uuid
from datetime import datetime, timezone

def main(
    survey_id: str,
    dispatcher_name: str,
    engineering_waiver_reason: str,
    current_risk_score: int = 75
) -> dict:
    override_id = f"OVR-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    adjusted_risk = max(15, current_risk_score - 25)
    
    return {
        "override_id": override_id,
        "survey_id": survey_id,
        "dispatcher_name": dispatcher_name,
        "waiver_reason": engineering_waiver_reason,
        "original_risk_score": current_risk_score,
        "adjusted_risk_score": adjusted_risk,
        "new_status": "OVERRIDDEN_DISPATCHER_WAIVER",
        "action_taken": "CLEARED_UNDER_ENGINEERING_SUPERVISION",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "clearance_pass_code": f"SEAL-ODC-{datetime.now().strftime('%Y%m%d')}-{override_id[-6:]}"
    }
