"""
Sealand Logistics - OOG Route & Permit RAG Assistant
Step 3: Algorithmic Risk Scoring (0 to 100)
Path: f/sealand_OOG/calculate_oog_risk_score
"""

from typing import List, Dict, Any

def main(
    cargo_weight_mt: float = 85.0,
    cargo_height_m: float = 5.1,
    cargo_width_m: float = 4.2,
    cargo_length_m: float = 24.5,
    axle_info: dict = None,
    route_info: dict = None,
    bypasses_applied: list = None,
    compliance_info: dict = None
) -> dict:
    """Step 3 in OpenFlow DAG: Deterministically scores consignment risk across structural, legal, and terrain dimensions."""
    axle_info = axle_info or {"axle_overloaded": False, "axle_load_mt": 10.5}
    route_info = route_info or {"ghat_sections_count": 0}
    bypasses_applied = bypasses_applied or []
    compliance_info = compliance_info or {"night_travel_restrictions": []}
    
    score = 15
    risk_factors = []
    
    # 1. Weight factor
    if cargo_weight_mt > 120.0:
        score += 25
        risk_factors.append("Extreme Super-Heavy Lift (>120MT): Dynamic bridge deflection hazard (+25)")
    elif cargo_weight_mt > 80.0:
        score += 15
        risk_factors.append("Heavy Lift (80-120MT): Structural girder verification required (+15)")
        
    # 2. Axle load factor
    if axle_info.get("axle_overloaded", False):
        score += 30
        risk_factors.append(f"IRC:SP:35 Axle Line Overload ({axle_info.get('axle_load_mt')}MT/axle > 13.5MT limit) (+30)")
    elif axle_info.get("axle_load_mt", 0.0) > 11.5:
        score += 10
        risk_factors.append(f"Sub-optimal Axle Line Margin ({axle_info.get('axle_load_mt')}MT/axle) (+10)")
        
    # 3. Vertical Clearance factor
    if cargo_height_m > 5.2:
        score += 20
        risk_factors.append(f"Extreme Vertical Clearance ({cargo_height_m}m): High-tension wire & gantry hazard (+20)")
    elif cargo_height_m > 4.75:
        score += 12
        risk_factors.append(f"Tight Overhead Clearance ({cargo_height_m}m): Sub-5.0m toll canopies & ROBs (+12)")
        
    # 4. Width factor
    if cargo_width_m > 4.5:
        score += 20
        risk_factors.append(f"Super-Wide Consignment ({cargo_width_m}m): Complete opposite carriageway closure needed (+20)")
    elif cargo_width_m > 3.8:
        score += 10
        risk_factors.append(f"Wide Load ({cargo_width_m}m): Toll plaza lane splitter width constraint (+10)")
        
    # 5. Ghat sections
    ghat_count = route_info.get("ghat_sections_count", 0)
    if ghat_count > 0:
        pts = min(25, ghat_count * 12)
        score += pts
        risk_factors.append(f"Ghat Terrain Traversal ({ghat_count} sections): Hairpin turn & brake fade hazard (+{pts})")
        
    # 6. Bypasses applied
    bypass_count = len(bypasses_applied)
    if bypass_count > 0:
        pts = min(20, bypass_count * 8)
        score += pts
        risk_factors.append(f"Structural Bottleneck Detours ({bypass_count} bridges bypassed) (+{pts})")
        
    # 7. Night travel restriction complexity
    if len(compliance_info.get("night_travel_restrictions", [])) >= 2:
        score += 8
        risk_factors.append("Multi-State Night Curfew: Extended layover parking & security escort needed (+8)")
        
    final_score = min(100, max(0, score))
    
    if final_score > 70:
        status = "FLAGGED_FOR_DISPATCHER_SURVEY"
        action = "HUMAN_SURVEY_REQUIRED"
        summary = "Consignment exceeds automated clearance threshold. Human dispatcher route survey & engineering waiver mandatory."
    else:
        status = "APPROVED_AUTO_PERMIT"
        action = "CLEARANCE_GRANTED"
        summary = "Deterministic constraints verified. Safe for automated permit filing and corridor dispatch."

    return {
        "risk_score": final_score,
        "status": status,
        "recommended_action": action,
        "summary": summary,
        "risk_factors": risk_factors
    }
