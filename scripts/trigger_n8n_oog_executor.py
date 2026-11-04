"""
Sealand Logistics - OOG Route & Permit RAG Assistant
Step 6: Trigger n8n Notification & Permit Filing Executor
Path: f/sealand_OOG/trigger_n8n_oog_executor
"""

import json
import urllib.request
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("trigger_n8n_oog_executor")

def main(
    survey_id: str = "SURVEY-2026-SEAL-8891",
    status: str = "APPROVED_AUTO_PERMIT",
    risk_score: int = 45,
    clearance_pass_code: str = "SEAL-ODC-20261104-CLEAR",
    total_distance_km: float = 730.0,
    total_statutory_fee_inr: float = 48500.0,
    client_id: str = "SEALAND_PROJECT_CARGO_DIV",
    n8n_webhook_url: str = "http://localhost:5678/webhook/oog-permit-notification",
    n8n_token: str = ""
) -> dict:
    """Dispatches webhook to n8n to send email clearance pass and trigger automated filing."""
    payload = {
        "event": "OOG_ROUTE_SURVEY_COMPLETED",
        "survey_id": survey_id,
        "status": status,
        "risk_score": risk_score,
        "clearance_pass_code": clearance_pass_code,
        "total_distance_km": total_distance_km,
        "total_statutory_fee_inr": total_statutory_fee_inr,
        "client_id": client_id,
        "timestamp": ""
    }
    
    headers = {"Content-Type": "application/json"}
    if n8n_token:
        headers["Authorization"] = f"Bearer {n8n_token}"
        
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(n8n_webhook_url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=4) as response:
            res_body = response.read().decode("utf-8")
            return {
                "n8n_notified": True,
                "status_code": response.status,
                "response": res_body,
                "payload_sent": payload
            }
    except Exception as e:
        logger.info(f"n8n webhook notification logged (standby/mock mode): {e}")
        return {
            "n8n_notified": False,
            "simulated": True,
            "message": f"Webhook dispatched in standby mode: {str(e)}",
            "payload_sent": payload
        }
