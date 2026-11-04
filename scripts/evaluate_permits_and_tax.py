"""
Sealand Logistics - OOG Route & Permit RAG Assistant
Step 2: Deterministic RTO Permit & Statutory Tax Engine
Path: f/sealand_OOG/evaluate_permits_and_tax
"""

from typing import List, Dict, Any

RTO_RULES_DATA = {
    "CENTRAL": {
        "rule_id": "RULE-MORTH-CENTRAL-01",
        "authority": "Ministry of Road Transport & Highways (MoRTH)",
        "permit_code": "MORTH-ONLINE-SPECIAL-PERMIT",
        "base_fee": 15000.0,
        "per_mt_km": 1.25,
        "dimension_multiplier": 1.20,
        "escort_width_m": 3.5,
        "escort_weight_mt": 80.0,
        "sla_days": 5,
        "portal": "https://morth-owdc.nic.in/",
        "night_travel": False
    },
    "AP": {
        "rule_id": "RULE-AP-RTO-01",
        "authority": "Andhra Pradesh Transport Department",
        "permit_code": "FORM-ODC-AP-1",
        "base_fee": 7500.0,
        "per_mt_km": 0.85,
        "dimension_multiplier": 1.15,
        "escort_width_m": 3.6,
        "escort_weight_mt": 75.0,
        "sla_days": 4,
        "portal": "https://aptransport.org/odc_permits",
        "night_travel": True
    },
    "TS": {
        "rule_id": "RULE-TS-RTA-01",
        "authority": "Telangana State Transport Authority",
        "permit_code": "FORM-TS-HT-7",
        "base_fee": 8000.0,
        "per_mt_km": 0.90,
        "dimension_multiplier": 1.18,
        "escort_width_m": 3.5,
        "escort_weight_mt": 80.0,
        "sla_days": 3,
        "portal": "https://transport.telangana.gov.in/special_haulage",
        "night_travel": False
    },
    "OD": {
        "rule_id": "RULE-OD-STA-01",
        "authority": "State Transport Authority Odisha",
        "permit_code": "OD-RTO-PERMIT-4",
        "base_fee": 6500.0,
        "per_mt_km": 0.80,
        "dimension_multiplier": 1.12,
        "escort_width_m": 3.4,
        "escort_weight_mt": 70.0,
        "sla_days": 5,
        "portal": "https://odishatransport.gov.in/odc",
        "night_travel": False
    },
    "WB": {
        "rule_id": "RULE-WB-TRANS-01",
        "authority": "West Bengal Transport Directorate",
        "permit_code": "WB-MOTOR-TRANS-OOG",
        "base_fee": 9000.0,
        "per_mt_km": 1.10,
        "dimension_multiplier": 1.25,
        "escort_width_m": 3.3,
        "escort_weight_mt": 70.0,
        "sla_days": 6,
        "portal": "https://wbtransport.gov.in/permits",
        "night_travel": False
    },
    "MH": {
        "rule_id": "RULE-MH-PWD-01",
        "authority": "Maharashtra PWD & Motor Vehicles Dept",
        "permit_code": "MH-PWD-SUPER-LOAD",
        "base_fee": 11000.0,
        "per_mt_km": 1.15,
        "dimension_multiplier": 1.22,
        "escort_width_m": 3.5,
        "escort_weight_mt": 85.0,
        "sla_days": 5,
        "portal": "https://transport.maharashtra.gov.in/superloads",
        "night_travel": False
    },
    "CG": {
        "rule_id": "RULE-CG-RTO-01",
        "authority": "Chhattisgarh Transport Department",
        "permit_code": "CG-TRANSPORT-ODC-PERMIT",
        "base_fee": 6000.0,
        "per_mt_km": 0.75,
        "dimension_multiplier": 1.10,
        "escort_width_m": 3.6,
        "escort_weight_mt": 80.0,
        "sla_days": 3,
        "portal": "https://cgtransport.gov.in/odc",
        "night_travel": True
    },
    "TN": {
        "rule_id": "RULE-TN-STA-01",
        "authority": "Tamil Nadu State Transport Authority",
        "permit_code": "TN-TRANSPORT-SPECIAL-PERMIT",
        "base_fee": 8500.0,
        "per_mt_km": 0.95,
        "dimension_multiplier": 1.15,
        "escort_width_m": 3.5,
        "escort_weight_mt": 80.0,
        "sla_days": 4,
        "portal": "https://tnsta.gov.in/odc",
        "night_travel": True
    },
    "KA": {
        "rule_id": "RULE-KA-TRANS-01",
        "authority": "Karnataka Transport Department",
        "permit_code": "KA-RTO-HEAVY-HAUL",
        "base_fee": 9500.0,
        "per_mt_km": 1.05,
        "dimension_multiplier": 1.20,
        "escort_width_m": 3.5,
        "escort_weight_mt": 80.0,
        "sla_days": 4,
        "portal": "https://transport.karnataka.gov.in/heavyloads",
        "night_travel": False
    },
    "GJ": {
        "rule_id": "RULE-GJ-RTO-01",
        "authority": "Gujarat Ports and Transport Department",
        "permit_code": "GJ-RTO-SUPER-CARGO",
        "base_fee": 10000.0,
        "per_mt_km": 0.90,
        "dimension_multiplier": 1.15,
        "escort_width_m": 3.8,
        "escort_weight_mt": 90.0,
        "sla_days": 3,
        "portal": "https://cot.gujarat.gov.in/supercargo",
        "night_travel": True
    }
}

def main(
    traversed_states: List[str] = ["AP", "OD", "CG"],
    total_distance_km: float = 730.0,
    cargo_weight_mt: float = 85.0,
    cargo_width_m: float = 4.2,
    cargo_height_m: float = 5.1,
    cargo_length_m: float = 24.5
) -> dict:
    """Step 2 in OpenFlow DAG: Deterministically queries RTO rules for each traversed state."""
    permits = []
    total_cost_inr = 0.0
    max_sla_days = 0
    escort_mandates = []
    night_restrictions = []
    
    # 1. Central MoRTH permit
    central_rule = RTO_RULES_DATA["CENTRAL"]
    base_morth = central_rule["base_fee"]
    per_mt_km = central_rule["per_mt_km"]
    excess_weight = max(0.0, cargo_weight_mt - 49.0)
    weight_surcharge = excess_weight * per_mt_km * (total_distance_km * 0.4)
    morth_total = base_morth + weight_surcharge
    total_cost_inr += morth_total
    max_sla_days = max(max_sla_days, central_rule["sla_days"])
    
    permits.append({
        "jurisdiction": "CENTRAL_MORTH",
        "authority": central_rule["authority"],
        "permit_code": central_rule["permit_code"],
        "statutory_fee_inr": round(morth_total, 2),
        "sla_days": central_rule["sla_days"],
        "portal_url": central_rule["portal"],
        "mandatory": True
    })
    
    # 2. State-specific permits
    state_distance_share = total_distance_km / max(1, len(traversed_states))
    for state in traversed_states:
        rule = RTO_RULES_DATA.get(state)
        if not rule:
            continue
            
        state_fee = rule["base_fee"] + (excess_weight * rule["per_mt_km"] * state_distance_share * 0.3)
        if cargo_width_m > 3.8 or cargo_height_m > 5.0:
            state_fee *= rule["dimension_multiplier"]
            
        total_cost_inr += state_fee
        max_sla_days = max(max_sla_days, rule["sla_days"])
        
        if cargo_width_m >= rule["escort_width_m"] or cargo_weight_mt >= rule["escort_weight_mt"]:
            escort_mandates.append(
                f"State of {state}: Mandatory 2-vehicle convoy (Front pilot with amber strobe + rear escort) required by {rule['authority']}."
            )
            
        if not rule["night_travel"]:
            night_restrictions.append(
                f"State of {state}: Movement STRICTLY PROHIBITED between 20:00 and 06:00 hrs on all corridors."
            )
            
        permits.append({
            "jurisdiction": f"STATE_{state}",
            "authority": rule["authority"],
            "permit_code": rule["permit_code"],
            "statutory_fee_inr": round(state_fee, 2),
            "sla_days": rule["sla_days"],
            "portal_url": rule["portal"],
            "mandatory": True
        })
        
    needs_police_escort = (cargo_width_m >= 4.0 or cargo_weight_mt >= 90.0 or cargo_length_m >= 25.0)
    if needs_police_escort:
        escort_mandates.insert(
            0,
            "HIGHWAY PATROL POLICE ESCORT: Mandated under Motor Vehicles Act Section 112 for super-heavy ODC convoy."
        )

    return {
        "permits_checklist": permits,
        "total_statutory_fee_inr": round(total_cost_inr, 2),
        "aggregate_survey_sla_days": max_sla_days + 2,
        "escort_mandates": escort_mandates,
        "night_travel_restrictions": night_restrictions,
        "requires_police_convoy": needs_police_escort
    }
