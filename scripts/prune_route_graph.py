"""
Sealand Logistics - OOG Route & Permit RAG Assistant
Step 1: Graph Pruning and Corridor Routing Engine
Path: f/sealand_OOG/prune_route_graph
"""

import math
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from rapidfuzz import process, fuzz
import networkx as nx

NODES_DATA = {
    "PORT_CODE_INVTZ": {"node_id": "PORT_CODE_INVTZ", "node_name": "Visakhapatnam Port (Vizag)", "state_code": "AP", "latitude": 17.6868, "longitude": 83.2185, "aliases": ["Vizag", "Visakhapatnam", "Vizag Port", "INVTZ", "VPT"]},
    "PORT_CODE_INMAA": {"node_id": "PORT_CODE_INMAA", "node_name": "Chennai Port", "state_code": "TN", "latitude": 13.0827, "longitude": 80.2707, "aliases": ["Chennai", "Madras Port", "INMAA"]},
    "PORT_CODE_INBOM": {"node_id": "PORT_CODE_INBOM", "node_name": "Jawaharlal Nehru Port Trust (JNPT Mumbai)", "state_code": "MH", "latitude": 18.9499, "longitude": 72.9511, "aliases": ["JNPT", "Nhava Sheva", "Mumbai Port", "INBOM"]},
    "PORT_CODE_INCCU": {"node_id": "PORT_CODE_INCCU", "node_name": "Kolkata Syama Prasad Mookerjee Port", "state_code": "WB", "latitude": 22.5411, "longitude": 88.3142, "aliases": ["Kolkata Port", "Calcutta Port", "Haldia", "INCCU"]},
    "PORT_CODE_INPRT": {"node_id": "PORT_CODE_INPRT", "node_name": "Paradip Port", "state_code": "OD", "latitude": 20.2644, "longitude": 86.6953, "aliases": ["Paradip", "Paradeep", "INPRT"]},
    "PORT_CODE_INMUN": {"node_id": "PORT_CODE_INMUN", "node_name": "Mundra Port", "state_code": "GJ", "latitude": 22.7441, "longitude": 69.7042, "aliases": ["Mundra", "Adani Mundra", "INMUN"]},
    "HUB_RAIPUR": {"node_id": "HUB_RAIPUR", "node_name": "Raipur Logistics Park", "state_code": "CG", "latitude": 21.2514, "longitude": 81.6296, "aliases": ["Raipur", "Bhilai", "Naya Raipur"]},
    "HUB_NAGPUR": {"node_id": "HUB_NAGPUR", "node_name": "Nagpur Multimodal Logistics Hub", "state_code": "MH", "latitude": 21.1458, "longitude": 79.0882, "aliases": ["Nagpur", "MIHAN", "Butibori"]},
    "HUB_HYDERABAD": {"node_id": "HUB_HYDERABAD", "node_name": "Hyderabad Heavy Industrial Corridor", "state_code": "TS", "latitude": 17.3850, "longitude": 78.4867, "aliases": ["Hyderabad", "Secunderabad", "Patancheru"]},
    "HUB_JHARSUGUDA": {"node_id": "HUB_JHARSUGUDA", "node_name": "Jharsuguda Industrial Hub", "state_code": "OD", "latitude": 21.8554, "longitude": 84.0062, "aliases": ["Jharsuguda", "Rourkela"]},
    "HUB_JAMSHEDPUR": {"node_id": "HUB_JAMSHEDPUR", "node_name": "Jamshedpur Tata Steel Complex", "state_code": "JH", "latitude": 22.8046, "longitude": 86.2029, "aliases": ["Jamshedpur", "Tatanagar"]},
    "HUB_PUNE": {"node_id": "HUB_PUNE", "node_name": "Pune Chakan Auto Cluster", "state_code": "MH", "latitude": 18.5204, "longitude": 73.8567, "aliases": ["Pune", "Chakan", "Talegaon"]},
    "HUB_BANGALORE": {"node_id": "HUB_BANGALORE", "node_name": "Bangalore Nelamangala Freight Hub", "state_code": "KA", "latitude": 12.9716, "longitude": 77.5946, "aliases": ["Bangalore", "Bengaluru", "Peenya"]},
    "HUB_AHMEDABAD": {"node_id": "HUB_AHMEDABAD", "node_name": "Ahmedabad Sanand Auto Hub", "state_code": "GJ", "latitude": 23.0225, "longitude": 72.5714, "aliases": ["Ahmedabad", "Sanand"]},
    "JUNC_VIJAYAWADA": {"node_id": "JUNC_VIJAYAWADA", "node_name": "Vijayawada NH-16/NH-65 Junction", "state_code": "AP", "latitude": 16.5062, "longitude": 80.6480, "aliases": ["Vijayawada"]},
    "JUNC_SURYAPET": {"node_id": "JUNC_SURYAPET", "node_name": "Suryapet NH-65 Junction", "state_code": "TS", "latitude": 17.1439, "longitude": 79.6239, "aliases": ["Suryapet"]},
    "JUNC_SOLAPUR": {"node_id": "JUNC_SOLAPUR", "node_name": "Solapur NH-65/NH-52 Junction", "state_code": "MH", "latitude": 17.6599, "longitude": 75.9064, "aliases": ["Solapur"]},
    "JUNC_KOLHAPUR": {"node_id": "JUNC_KOLHAPUR", "node_name": "Kolhapur NH-48 Junction", "state_code": "MH", "latitude": 16.7050, "longitude": 74.2433, "aliases": ["Kolhapur"]},
    "JUNC_BELGAUM": {"node_id": "JUNC_BELGAUM", "node_name": "Belgaum NH-48 Hub", "state_code": "KA", "latitude": 15.8497, "longitude": 74.4977, "aliases": ["Belgaum"]},
    "JUNC_KHAMMAM": {"node_id": "JUNC_KHAMMAM", "node_name": "Khammam Bypass Junction", "state_code": "TS", "latitude": 17.2473, "longitude": 80.1514, "aliases": ["Khammam"]},
    "JUNC_JAGDALPUR": {"node_id": "JUNC_JAGDALPUR", "node_name": "Jagdalpur NH-30 Junction", "state_code": "CG", "latitude": 19.0748, "longitude": 82.0298, "aliases": ["Jagdalpur"]},
    "JUNC_SAMBALPUR": {"node_id": "JUNC_SAMBALPUR", "node_name": "Sambalpur NH-53 Junction", "state_code": "OD", "latitude": 21.4669, "longitude": 83.9812, "aliases": ["Sambalpur"]},
    "JUNC_BALASORE": {"node_id": "JUNC_BALASORE", "node_name": "Balasore NH-16 Junction", "state_code": "OD", "latitude": 21.4934, "longitude": 86.9135, "aliases": ["Balasore"]}
}

SEGMENTS_DATA = [
    {"segment_id": "SEG-VTZ-VJW-NH16", "source": "PORT_CODE_INVTZ", "target": "JUNC_VIJAYAWADA", "highway": "NH-16", "distance_km": 350.0, "max_weight_mt": 100.0, "max_height_m": 5.5, "max_width_m": 5.5, "ghat": False, "tolls": 5, "speed": 28.0, "states": ["AP"]},
    {"segment_id": "SEG-VTZ-JAG-NH30", "source": "PORT_CODE_INVTZ", "target": "JUNC_JAGDALPUR", "highway": "NH-30", "distance_km": 310.0, "max_weight_mt": 65.0, "max_height_m": 5.0, "max_width_m": 4.5, "ghat": True, "tolls": 3, "speed": 18.0, "states": ["AP", "CG"]},
    {"segment_id": "SEG-VTZ-SAM-NH26", "source": "PORT_CODE_INVTZ", "target": "JUNC_SAMBALPUR", "highway": "NH-26", "distance_km": 450.0, "max_weight_mt": 120.0, "max_height_m": 5.8, "max_width_m": 5.5, "ghat": False, "tolls": 6, "speed": 26.0, "states": ["AP", "OD"]},
    {"segment_id": "SEG-VJW-SUR-NH65", "source": "JUNC_VIJAYAWADA", "target": "JUNC_SURYAPET", "highway": "NH-65", "distance_km": 140.0, "max_weight_mt": 110.0, "max_height_m": 5.4, "max_width_m": 5.5, "ghat": False, "tolls": 2, "speed": 30.0, "states": ["AP", "TS"]},
    {"segment_id": "SEG-VJW-MAA-NH16", "source": "JUNC_VIJAYAWADA", "target": "PORT_CODE_INMAA", "highway": "NH-16", "distance_km": 430.0, "max_weight_mt": 120.0, "max_height_m": 5.6, "max_width_m": 5.5, "ghat": False, "tolls": 6, "speed": 30.0, "states": ["AP", "TN"]},
    {"segment_id": "SEG-VJW-KHM-NH365", "source": "JUNC_VIJAYAWADA", "target": "JUNC_KHAMMAM", "highway": "NH-365A", "distance_km": 115.0, "max_weight_mt": 90.0, "max_height_m": 5.2, "max_width_m": 4.8, "ghat": False, "tolls": 1, "speed": 25.0, "states": ["AP", "TS"]},
    {"segment_id": "SEG-SUR-HYD-NH65", "source": "JUNC_SURYAPET", "target": "HUB_HYDERABAD", "highway": "NH-65", "distance_km": 135.0, "max_weight_mt": 110.0, "max_height_m": 5.2, "max_width_m": 5.5, "ghat": False, "tolls": 2, "speed": 30.0, "states": ["TS"]},
    {"segment_id": "SEG-KHM-SUR-NH365", "source": "JUNC_KHAMMAM", "target": "JUNC_SURYAPET", "highway": "NH-365BB", "distance_km": 65.0, "max_weight_mt": 95.0, "max_height_m": 5.3, "max_width_m": 5.0, "ghat": False, "tolls": 1, "speed": 28.0, "states": ["TS"]},
    {"segment_id": "SEG-HYD-NGP-NH44", "source": "HUB_HYDERABAD", "target": "HUB_NAGPUR", "highway": "NH-44", "distance_km": 500.0, "max_weight_mt": 130.0, "max_height_m": 5.8, "max_width_m": 5.5, "ghat": False, "tolls": 7, "speed": 32.0, "states": ["TS", "MH"]},
    {"segment_id": "SEG-HYD-SOL-NH65", "source": "HUB_HYDERABAD", "target": "JUNC_SOLAPUR", "highway": "NH-65", "distance_km": 310.0, "max_weight_mt": 110.0, "max_height_m": 5.5, "max_width_m": 5.5, "ghat": False, "tolls": 4, "speed": 30.0, "states": ["TS", "KA", "MH"]},
    {"segment_id": "SEG-HYD-BLR-NH44", "source": "HUB_HYDERABAD", "target": "HUB_BANGALORE", "highway": "NH-44", "distance_km": 570.0, "max_weight_mt": 120.0, "max_height_m": 5.8, "max_width_m": 5.5, "ghat": False, "tolls": 8, "speed": 32.0, "states": ["TS", "AP", "KA"]},
    {"segment_id": "SEG-JAG-RPR-NH30", "source": "JUNC_JAGDALPUR", "target": "HUB_RAIPUR", "highway": "NH-30", "distance_km": 295.0, "max_weight_mt": 85.0, "max_height_m": 5.1, "max_width_m": 4.8, "ghat": True, "tolls": 3, "speed": 20.0, "states": ["CG"]},
    {"segment_id": "SEG-SAM-RPR-NH53", "source": "JUNC_SAMBALPUR", "target": "HUB_RAIPUR", "highway": "NH-53", "distance_km": 280.0, "max_weight_mt": 130.0, "max_height_m": 5.8, "max_width_m": 5.5, "ghat": False, "tolls": 4, "speed": 30.0, "states": ["OD", "CG"]},
    {"segment_id": "SEG-NGP-RPR-NH53", "source": "HUB_NAGPUR", "target": "HUB_RAIPUR", "highway": "NH-53", "distance_km": 290.0, "max_weight_mt": 130.0, "max_height_m": 5.8, "max_width_m": 5.5, "ghat": False, "tolls": 4, "speed": 30.0, "states": ["MH", "CG"]},
    {"segment_id": "SEG-SAM-JHS-NH49", "source": "JUNC_SAMBALPUR", "target": "HUB_JHARSUGUDA", "highway": "NH-49", "distance_km": 55.0, "max_weight_mt": 140.0, "max_height_m": 5.8, "max_width_m": 5.5, "ghat": False, "tolls": 1, "speed": 28.0, "states": ["OD"]},
    {"segment_id": "SEG-PRT-SAM-NH53", "source": "PORT_CODE_INPRT", "target": "JUNC_SAMBALPUR", "highway": "NH-53", "distance_km": 340.0, "max_weight_mt": 80.0, "max_height_m": 4.9, "max_width_m": 5.0, "ghat": False, "tolls": 4, "speed": 25.0, "states": ["OD"]},
    {"segment_id": "SEG-JHS-JAM-NH49", "source": "HUB_JHARSUGUDA", "target": "HUB_JAMSHEDPUR", "highway": "NH-49", "distance_km": 260.0, "max_weight_mt": 120.0, "max_height_m": 5.5, "max_width_m": 5.0, "ghat": False, "tolls": 3, "speed": 26.0, "states": ["OD", "JH"]},
    {"segment_id": "SEG-BLS-SAM-NH49", "source": "JUNC_BALASORE", "target": "JUNC_SAMBALPUR", "highway": "NH-49", "distance_km": 360.0, "max_weight_mt": 110.0, "max_height_m": 5.4, "max_width_m": 5.2, "ghat": False, "tolls": 4, "speed": 26.0, "states": ["OD"]},
    {"segment_id": "SEG-CCU-BLS-NH16", "source": "PORT_CODE_INCCU", "target": "JUNC_BALASORE", "highway": "NH-16", "distance_km": 240.0, "max_weight_mt": 75.0, "max_height_m": 4.95, "max_width_m": 5.2, "ghat": False, "tolls": 3, "speed": 26.0, "states": ["WB", "OD"]},
    {"segment_id": "SEG-CCU-JAM-NH18", "source": "PORT_CODE_INCCU", "target": "HUB_JAMSHEDPUR", "highway": "NH-18", "distance_km": 285.0, "max_weight_mt": 100.0, "max_height_m": 5.2, "max_width_m": 5.0, "ghat": False, "tolls": 3, "speed": 27.0, "states": ["WB", "JH"]},
    {"segment_id": "SEG-JNPT-PUN-NH48", "source": "PORT_CODE_INBOM", "target": "HUB_PUNE", "highway": "NH-48", "distance_km": 145.0, "max_weight_mt": 140.0, "max_height_m": 4.85, "max_width_m": 5.5, "ghat": True, "tolls": 2, "speed": 24.0, "states": ["MH"]},
    {"segment_id": "SEG-JNPT-NGP-NH160", "source": "PORT_CODE_INBOM", "target": "HUB_NAGPUR", "highway": "NH-160/NH-53", "distance_km": 780.0, "max_weight_mt": 90.0, "max_height_m": 4.8, "max_width_m": 4.8, "ghat": True, "tolls": 9, "speed": 22.0, "states": ["MH"]},
    {"segment_id": "SEG-PUN-SOL-NH65", "source": "HUB_PUNE", "target": "JUNC_SOLAPUR", "highway": "NH-65", "distance_km": 250.0, "max_weight_mt": 120.0, "max_height_m": 5.6, "max_width_m": 5.5, "ghat": False, "tolls": 3, "speed": 30.0, "states": ["MH"]},
    {"segment_id": "SEG-PUN-KOL-NH48", "source": "HUB_PUNE", "target": "JUNC_KOLHAPUR", "highway": "NH-48", "distance_km": 235.0, "max_weight_mt": 130.0, "max_height_m": 5.6, "max_width_m": 5.5, "ghat": False, "tolls": 3, "speed": 30.0, "states": ["MH"]},
    {"segment_id": "SEG-KOL-BLG-NH48", "source": "JUNC_KOLHAPUR", "target": "JUNC_BELGAUM", "highway": "NH-48", "distance_km": 105.0, "max_weight_mt": 130.0, "max_height_m": 5.6, "max_width_m": 5.5, "ghat": False, "tolls": 1, "speed": 30.0, "states": ["MH", "KA"]},
    {"segment_id": "SEG-BLG-BLR-NH48", "source": "JUNC_BELGAUM", "target": "HUB_BANGALORE", "highway": "NH-48", "distance_km": 505.0, "max_weight_mt": 120.0, "max_height_m": 5.5, "max_width_m": 5.5, "ghat": False, "tolls": 6, "speed": 32.0, "states": ["KA"]},
    {"segment_id": "SEG-MAA-BLR-NH48", "source": "PORT_CODE_INMAA", "target": "HUB_BANGALORE", "highway": "NH-48", "distance_km": 345.0, "max_weight_mt": 110.0, "max_height_m": 5.4, "max_width_m": 5.5, "ghat": False, "tolls": 4, "speed": 30.0, "states": ["TN", "KA"]},
    {"segment_id": "SEG-MUN-AMD-NH947", "source": "PORT_CODE_INMUN", "target": "HUB_AHMEDABAD", "highway": "NH-947", "distance_km": 360.0, "max_weight_mt": 140.0, "max_height_m": 5.8, "max_width_m": 5.5, "ghat": False, "tolls": 4, "speed": 32.0, "states": ["GJ"]},
    {"segment_id": "SEG-AMD-PUN-NH48", "source": "HUB_AHMEDABAD", "target": "HUB_PUNE", "highway": "NH-48", "distance_km": 660.0, "max_weight_mt": 120.0, "max_height_m": 5.5, "max_width_m": 5.5, "ghat": False, "tolls": 8, "speed": 30.0, "states": ["GJ", "MH"]},
    {"segment_id": "SEG-AMD-NGP-NH53", "source": "HUB_AHMEDABAD", "target": "HUB_NAGPUR", "highway": "NH-53", "distance_km": 820.0, "max_weight_mt": 120.0, "max_height_m": 5.6, "max_width_m": 5.5, "ghat": False, "tolls": 10, "speed": 28.0, "states": ["GJ", "MH"]}
]

BRIDGE_CONSTRAINTS = [
    {"bridge_id": "BRG-AP-NAGAVALI-01", "bridge_name": "Nagavali River Arch Bridge", "segment_id": "SEG-VTZ-JAG-NH30", "max_weight_mt": 65.0, "min_vertical_clearance_m": 5.2, "bypass_available": True, "bypass_route_id": "SEG-VTZ-SAM-NH26", "bypass_penalty_km": 140.0, "notes": "Arch limit 65MT. Detour via Sambalpur NH-26."},
    {"bridge_id": "BRG-AP-GODAVARI-04", "bridge_name": "Godavari Fourth Road Bridge", "segment_id": "SEG-VTZ-VJW-NH16", "max_weight_mt": 160.0, "min_vertical_clearance_m": 5.6, "bypass_available": True, "bypass_route_id": "BYPASS-RMY-OLD-NH16", "bypass_penalty_km": 25.0, "notes": "Up to 160MT capacity."},
    {"bridge_id": "BRG-MH-KASARA-ROB-01", "bridge_name": "Kasara Ghat Railway Overbridge", "segment_id": "SEG-JNPT-NGP-NH160", "max_weight_mt": 90.0, "min_vertical_clearance_m": 4.80, "bypass_available": True, "bypass_route_id": "SEG-JNPT-PUN-NH48", "bypass_penalty_km": 185.0, "notes": "Clearance 4.80m limit."},
    {"bridge_id": "BRG-MH-BHOR-TUNNEL-02", "bridge_name": "Bhor Ghat Khandala Tunnel", "segment_id": "SEG-JNPT-PUN-NH48", "max_weight_mt": 140.0, "min_vertical_clearance_m": 4.85, "bypass_available": True, "bypass_route_id": "BYPASS-OLD-MUM-PUN-NH48", "bypass_penalty_km": 38.0, "notes": "Crown clearance 4.85m."},
    {"bridge_id": "BRG-TS-SURYAPET-HT-01", "bridge_name": "Suryapet HT Transmission Crossing", "segment_id": "SEG-SUR-HYD-NH65", "max_weight_mt": 130.0, "min_vertical_clearance_m": 5.20, "bypass_available": True, "bypass_route_id": "BYPASS-SURYAPET-LOCAL", "bypass_penalty_km": 12.0, "notes": "400kV line SAG."},
    {"bridge_id": "BRG-OD-MAHANADI-02", "bridge_name": "Mahanadi Truss Bridge", "segment_id": "SEG-PRT-SAM-NH53", "max_weight_mt": 80.0, "min_vertical_clearance_m": 4.90, "bypass_available": True, "bypass_route_id": "BYPASS-SAMBALPUR-RING", "bypass_penalty_km": 45.0, "notes": "Weight capped at 80MT."},
    {"bridge_id": "BRG-CG-SHEONATH-01", "bridge_name": "Sheonath River Arch Bridge", "segment_id": "SEG-NGP-RPR-NH53", "max_weight_mt": 130.0, "min_vertical_clearance_m": 5.60, "bypass_available": True, "bypass_route_id": "BYPASS-DURG-NH53-NEW", "bypass_penalty_km": 18.0, "notes": "130MT capacity."},
    {"bridge_id": "BRG-TN-PALAR-01", "bridge_name": "Palar River Girder", "segment_id": "SEG-MAA-BLR-NH48", "max_weight_mt": 110.0, "min_vertical_clearance_m": 5.40, "bypass_available": True, "bypass_route_id": "BYPASS-VELLORE-NH48", "bypass_penalty_km": 15.0, "notes": "110MT capacity."},
    {"bridge_id": "BRG-KA-KALI-01", "bridge_name": "Kali River Estuary Span", "segment_id": "SEG-BLG-BLR-NH48", "max_weight_mt": 95.0, "min_vertical_clearance_m": 5.10, "bypass_available": True, "bypass_route_id": "BYPASS-DHARWAD-NH48", "bypass_penalty_km": 28.0, "notes": "Wind sway restrictions."},
    {"bridge_id": "BRG-WB-RUPNARAYAN-01", "bridge_name": "Rupnarayan River Kolaghat Truss", "segment_id": "SEG-CCU-BLS-NH16", "max_weight_mt": 75.0, "min_vertical_clearance_m": 4.95, "bypass_available": True, "bypass_route_id": "BYPASS-KHARAGPUR-NH16", "bypass_penalty_km": 52.0, "notes": "75MT limit."}
]

def fuzzy_match_node(query: str, nodes_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not query:
        return None
    cleaned = query.strip()
    if cleaned in nodes_dict:
        return nodes_dict[cleaned]
    candidate_lookup = {}
    for node_id, data in nodes_dict.items():
        candidate_lookup[data["node_name"].lower()] = data
        for alias in data.get("aliases", []):
            candidate_lookup[alias.lower()] = data
    candidates = list(candidate_lookup.keys())
    match_result = process.extractOne(cleaned.lower(), candidates, scorer=fuzz.WRatio)
    if match_result and match_result[1] >= 55:
        return candidate_lookup[match_result[0]]
    return None

def calculate_multiaxle_loading(cargo_weight_mt: float, axle_count: int) -> Dict[str, Any]:
    trailer_tare_mt = 3.5 * max(1, axle_count)
    puller_tare_mt = 12.0
    gvw_mt = cargo_weight_mt + trailer_tare_mt + puller_tare_mt
    axle_load_mt = gvw_mt / max(1, axle_count)
    max_permissible = 13.5
    is_overloaded = axle_load_mt > max_permissible
    return {
        "cargo_weight_mt": cargo_weight_mt,
        "puller_tare_mt": puller_tare_mt,
        "trailer_tare_mt": round(trailer_tare_mt, 2),
        "total_gvw_mt": round(gvw_mt, 2),
        "axle_count": axle_count,
        "axle_load_mt": round(axle_load_mt, 2),
        "permissible_axle_load_mt": max_permissible,
        "axle_overloaded": is_overloaded,
        "recommended_min_axle_count": math.ceil(gvw_mt / 12.5) if is_overloaded else axle_count,
        "axle_loading_safety_margin_pct": round(((max_permissible - axle_load_mt) / max_permissible) * 100, 2)
    }

def main(
    origin_query: str = "Visakhapatnam Port",
    destination_query: str = "Raipur Logistics Hub",
    cargo_weight_mt: float = 85.0,
    cargo_height_m: float = 5.1,
    cargo_width_m: float = 4.2,
    cargo_length_m: float = 24.5,
    axle_count: int = 10,
    allow_bypasses: bool = True
) -> dict:
    start_time = datetime.now(timezone.utc)
    origin_node = fuzzy_match_node(origin_query, NODES_DATA)
    dest_node = fuzzy_match_node(destination_query, NODES_DATA)
    if not origin_node or not dest_node:
        return {"success": False, "error": "NODE_RESOLUTION_FAILED", "message": "Could not resolve nodes"}
        
    axle_analysis = calculate_multiaxle_loading(cargo_weight_mt, axle_count)
    
    G = nx.Graph()
    for nid, n in NODES_DATA.items():
        G.add_node(nid, name=n["node_name"], state=n["state_code"])
        
    bottlenecks_map: Dict[str, List[Dict[str, Any]]] = {}
    for bridge in BRIDGE_CONSTRAINTS:
        bottlenecks_map.setdefault(bridge["segment_id"], []).append(bridge)
        
    pruned_segments = []
    bypasses_applied = []
    
    for seg in SEGMENTS_DATA:
        seg_id = seg["segment_id"]
        u, v = seg["source"], seg["target"]
        dist = seg["distance_km"]
        is_ghat = seg["ghat"]
        
        blocked = False
        block_reason = ""
        penalty_km = 0.0
        
        if is_ghat and cargo_width_m > seg["max_width_m"]:
            blocked = True
            block_reason = f"Ghat curve geometry violation: width {cargo_width_m}m > {seg['max_width_m']}m"
            
        for bridge in bottlenecks_map.get(seg_id, []):
            weight_breach = cargo_weight_mt > bridge["max_weight_mt"]
            height_breach = cargo_height_m > bridge["min_vertical_clearance_m"]
            if weight_breach or height_breach:
                desc = []
                if weight_breach: desc.append(f"Weight {cargo_weight_mt}MT > {bridge['max_weight_mt']}MT")
                if height_breach: desc.append(f"Height {cargo_height_m}m > {bridge['min_vertical_clearance_m']}m")
                desc_str = " & ".join(desc)
                if allow_bypasses and bridge["bypass_available"]:
                    penalty = bridge["bypass_penalty_km"]
                    penalty_km += penalty
                    bypasses_applied.append({
                        "bridge_id": bridge["bridge_id"],
                        "bridge_name": bridge["bridge_name"],
                        "segment_id": seg_id,
                        "breach": desc_str,
                        "bypass_route_id": bridge["bypass_route_id"],
                        "bypass_penalty_km": penalty,
                        "notes": bridge["notes"]
                    })
                else:
                    blocked = True
                    block_reason = f"Impassable bridge {bridge['bridge_name']}: {desc_str}"
                    break
                    
        if blocked:
            pruned_segments.append({"segment_id": seg_id, "reason": block_reason})
        else:
            eff_dist = dist + penalty_km
            weight = eff_dist + (35.0 if is_ghat else 0.0)
            G.add_edge(u, v, segment_id=seg_id, highway=seg["highway"], base_distance_km=dist, effective_distance_km=eff_dist, weight=weight, ghat=is_ghat, tolls=seg["tolls"], speed=seg["speed"], states=seg["states"])
            
    if not nx.has_path(G, origin_node["node_id"], dest_node["node_id"]):
        return {"success": False, "error": "NO_FEASIBLE_PATH", "pruned_segments": pruned_segments, "axle_analysis": axle_analysis}
        
    path_nodes = nx.shortest_path(G, origin_node["node_id"], dest_node["node_id"], weight="weight")
    total_km = 0.0
    total_tolls = 0
    total_hours = 0.0
    ghat_count = 0
    traversed_states = set()
    segments = []
    
    for i in range(len(path_nodes) - 1):
        u, v = path_nodes[i], path_nodes[i+1]
        edge = G[u][v]
        dist = edge["effective_distance_km"]
        total_km += dist
        total_tolls += edge["tolls"]
        if edge["ghat"]: ghat_count += 1
        for s in edge["states"]: traversed_states.add(s)
        total_hours += dist / edge["speed"]
        segments.append({"from_node": u, "to_node": v, "segment_id": edge["segment_id"], "highway": edge["highway"], "distance_km": dist, "ghat": edge["ghat"], "tolls": edge["tolls"]})
        
    route_coords = []
    for nid in path_nodes:
        n = NODES_DATA.get(nid)
        if n: route_coords.append({"node_id": nid, "node_name": n["node_name"], "lat": n["latitude"], "lon": n["longitude"], "state": n["state_code"]})
        
    exec_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
    
    return {
        "success": True,
        "origin": origin_node,
        "destination": dest_node,
        "cargo_specs": {"weight_mt": cargo_weight_mt, "height_m": cargo_height_m, "width_m": cargo_width_m, "length_m": cargo_length_m, "axle_count": axle_count},
        "axle_analysis": axle_analysis,
        "route_summary": {
            "path_nodes": path_nodes,
            "segments": segments,
            "total_distance_km": round(total_km, 2),
            "total_tolls": total_tolls,
            "estimated_travel_hours": round(total_hours, 2),
            "estimated_transit_days": round(total_km / 180.0, 1),
            "ghat_sections_count": ghat_count,
            "traversed_states": sorted(list(traversed_states))
        },
        "bypasses_applied": bypasses_applied,
        "pruned_segments_count": len(pruned_segments),
        "map_coordinates": route_coords,
        "execution_ms": round(exec_ms, 2)
    }
