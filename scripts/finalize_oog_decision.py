"""
Sealand Logistics - OOG Route & Permit RAG Assistant
Step 5: Finalize Clearance Decision & Generate Clearance Pass
Path: f/sealand_OOG/finalize_oog_decision
"""

import uuid
from datetime import datetime, timezone
from typing import TypedDict, Optional, Dict, Any

class postgresql(TypedDict, total=False):
    host: str
    port: int
    user: str
    password: str
    dbname: str
    sslmode: Optional[str]

def main(
    survey_id: str = "",
    client_id: str = "SEALAND_PROJECT_CARGO_DIV",
    risk_data: dict = None,
    route_data: dict = None,
    compliance_data: dict = None,
    dispatcher_override: bool = False,
    dispatcher_name: str = "Chief Route Surveyor",
    engineering_waiver_reason: str = "",
    db: postgresql = None
) -> dict:
    """Finalizes clearance status, incorporates any dispatcher waivers, and generates digital clearance certificate."""
    risk_data = risk_data or {}
    route_data = route_data or {}
    compliance_data = compliance_data or {}
    
    assigned_survey_id = survey_id or f"SURVEY-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    base_status = risk_data.get("status", "APPROVED_AUTO_PERMIT")
    risk_score = risk_data.get("risk_score", 45)
    
    if dispatcher_override:
        final_status = "OVERRIDDEN_DISPATCHER_WAIVER"
        decision = "CLEARED_UNDER_ENGINEERING_SUPERVISION"
        waiver_record = {
            "waiver_applied": True,
            "dispatcher": dispatcher_name,
            "reason": engineering_waiver_reason or "Route surveyed and confirmed physically passable with certified puller crawl speed.",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    elif risk_score <= 70:
        final_status = "APPROVED_AUTO_PERMIT"
        decision = "AUTOMATIC_PORT_CLEARANCE_ISSUED"
        waiver_record = {"waiver_applied": False}
    else:
        final_status = "SUSPENDED_AWAITING_PHYSICAL_SURVEY"
        decision = "PHYSICAL_SURVEY_MANDATED"
        waiver_record = {"waiver_applied": False}
        
    clearance_pass_code = f"SEAL-ODC-{datetime.now().strftime('%Y%m%d')}-{assigned_survey_id[-6:]}"
    
    # Try recording override if DB available and waiver applied
    if db and dispatcher_override:
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=db.get("host", "db"),
                port=db.get("port", 5432),
                user=db.get("user", "postgres"),
                password=db.get("password", "changeme"),
                dbname=db.get("dbname", "windmill"),
                connect_timeout=1
            )
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO oog_survey_overrides (override_id, job_id, dispatcher_name, engineering_waiver_reason, created_at)
                VALUES (%s, %s, %s, %s, NOW())
            """, (str(uuid.uuid4()), assigned_survey_id, dispatcher_name, engineering_waiver_reason))
            conn.commit()
            cur.close()
            conn.close()
        except Exception:
            pass

    return {
        "survey_id": assigned_survey_id,
        "clearance_pass_code": clearance_pass_code,
        "final_status": final_status,
        "decision": decision,
        "risk_score": risk_score,
        "waiver_record": waiver_record,
        "total_statutory_fee_inr": compliance_data.get("total_statutory_fee_inr", 0.0),
        "permits_count": len(compliance_data.get("permits_checklist", [])),
        "total_distance_km": route_data.get("total_distance_km", 0.0),
        "cleared_at": datetime.now(timezone.utc).isoformat()
    }
