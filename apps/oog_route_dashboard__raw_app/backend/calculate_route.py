"""
Backend runnable for Windmill Raw App: calculate_route
100% Self-contained deterministic route solver.
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

RTO_RULES_DATA = {
    "CENTRAL": {"authority": "Ministry of Road Transport & Highways (MoRTH)", "permit_code": "MORTH-ONLINE-SPECIAL-PERMIT", "base_fee": 15000.0, "per_mt_km": 1.25, "sla_days": 5, "portal": "https://morth-owdc.nic.in/"},
    "AP": {"authority": "Andhra Pradesh Transport Department", "permit_code": "FORM-ODC-AP-1", "base_fee": 7500.0, "per_mt_km": 0.85, "sla_days": 4, "portal": "https://aptransport.org/odc_permits"},
    "TS": {"authority": "Telangana State Transport Authority", "permit_code": "FORM-TS-HT-7", "base_fee": 8000.0, "per_mt_km": 0.90, "sla_days": 3, "portal": "https://transport.telangana.gov.in/special_haulage"},
    "OD": {"authority": "State Transport Authority Odisha", "permit_code": "OD-RTO-PERMIT-4", "base_fee": 6500.0, "per_mt_km": 0.80, "sla_days": 5, "portal": "https://odishatransport.gov.in/odc"},
    "WB": {"authority": "West Bengal Transport Directorate", "permit_code": "WB-MOTOR-TRANS-OOG", "base_fee": 9000.0, "per_mt_km": 1.10, "sla_days": 6, "portal": "https://wbtransport.gov.in/permits"},
    "MH": {"authority": "Maharashtra PWD & Motor Vehicles Dept", "permit_code": "MH-PWD-SUPER-LOAD", "base_fee": 11000.0, "per_mt_km": 1.15, "sla_days": 5, "portal": "https://transport.maharashtra.gov.in/superloads"},
    "CG": {"authority": "Chhattisgarh Transport Department", "permit_code": "CG-TRANSPORT-ODC-PERMIT", "base_fee": 6000.0, "per_mt_km": 0.75, "sla_days": 3, "portal": "https://cgtransport.gov.in/odc"},
    "TN": {"authority": "Tamil Nadu State Transport Authority", "permit_code": "TN-TRANSPORT-SPECIAL-PERMIT", "base_fee": 8500.0, "per_mt_km": 0.95, "sla_days": 4, "portal": "https://tnsta.gov.in/odc"},
    "KA": {"authority": "Karnataka Transport Department", "permit_code": "KA-RTO-HEAVY-HAUL", "base_fee": 9500.0, "per_mt_km": 1.05, "sla_days": 4, "portal": "https://transport.karnataka.gov.in/heavyloads"},
    "GJ": {"authority": "Gujarat Ports and Transport Department", "permit_code": "GJ-RTO-SUPER-CARGO", "base_fee": 10000.0, "per_mt_km": 0.90, "sla_days": 3, "portal": "https://cot.gujarat.gov.in/supercargo"}
}

def fuzzy_match(query: str) -> Optional[Dict[str, Any]]:
    if not query: return None
    q = query.strip()
    if q in NODES_DATA: return NODES_DATA[q]
    lookup = {}
    for nid, d in NODES_DATA.items():
        lookup[d["node_name"].lower()] = d
        for al in d.get("aliases", []): lookup[al.lower()] = d
    res = process.extractOne(q.lower(), list(lookup.keys()), scorer=fuzz.WRatio)
    return lookup[res[0]] if res and res[1] >= 55 else None

def main(
    origin_query: str = "Visakhapatnam Port",
    destination_query: str = "Raipur Logistics Hub",
    cargo_weight_mt: float = 85.0,
    cargo_height_m: float = 5.1,
    cargo_width_m: float = 4.2,
    cargo_length_m: float = 24.5,
    axle_count: int = 10,
    allow_bypasses: bool = True,
    client_id: str = "SEALAND_DISPATCH_PORTAL"
) -> dict:
    start_time = datetime.now(timezone.utc)
    orig = fuzzy_match(origin_query)
    dest = fuzzy_match(destination_query)
    if not orig or not dest:
        return {"status": "REJECTED_INVALID_INPUT", "risk_score": 100, "message": "Could not resolve origin or destination"}
        
    gvw = cargo_weight_mt + (3.5 * axle_count) + 12.0
    axle_load = gvw / max(1, axle_count)
    axle_overloaded = axle_load > 13.5
    
    G = nx.Graph()
    for nid, n in NODES_DATA.items(): G.add_node(nid, name=n["node_name"], state=n["state_code"])
    
    bottlenecks_map: Dict[str, List[Dict[str, Any]]] = {}
    for b in BRIDGE_CONSTRAINTS: bottlenecks_map.setdefault(b["segment_id"], []).append(b)
    
    bypasses = []
    pruned = []
    
    for seg in SEGMENTS_DATA:
        seg_id = seg["segment_id"]
        u, v = seg["source"], seg["target"]
        dist = seg["distance_km"]
        is_ghat = seg["ghat"]
        blocked = False
        penalty = 0.0
        
        if is_ghat and cargo_width_m > seg["max_width_m"]:
            blocked = True
            
        for b in bottlenecks_map.get(seg_id, []):
            if cargo_weight_mt > b["max_weight_mt"] or cargo_height_m > b["min_vertical_clearance_m"]:
                if allow_bypasses and b["bypass_available"]:
                    penalty += b["bypass_penalty_km"]
                    bypasses.append({"bridge_name": b["bridge_name"], "bypass_route_id": b["bypass_route_id"], "bypass_penalty_km": b["bypass_penalty_km"], "notes": b["notes"], "breach": f"Limit: {b['max_weight_mt']}MT / {b['min_vertical_clearance_m']}m"})
                else:
                    blocked = True
                    break
                    
        if blocked:
            pruned.append(seg_id)
        else:
            eff = dist + penalty
            G.add_edge(u, v, segment_id=seg_id, distance_km=eff, weight=eff + (35.0 if is_ghat else 0.0), ghat=is_ghat, tolls=seg["tolls"], speed=seg["speed"], states=seg["states"])
            
    if not nx.has_path(G, orig["node_id"], dest["node_id"]):
        return {"status": "IMPASSABLE_NO_FEASIBLE_ROUTE", "risk_score": 100, "message": "No feasible route for cargo dimensions"}
        
    path = nx.shortest_path(G, orig["node_id"], dest["node_id"], weight="weight")
    total_km = 0.0
    total_tolls = 0
    total_hrs = 0.0
    ghat_count = 0
    states = set()
    segments = []
    
    for i in range(len(path) - 1):
        edge = G[path[i]][path[i+1]]
        dist = edge["distance_km"]
        total_km += dist
        total_tolls += edge["tolls"]
        if edge["ghat"]: ghat_count += 1
        for s in edge["states"]: states.add(s)
        total_hrs += dist / edge["speed"]
        segments.append({"from_node": path[i], "to_node": path[i+1], "segment_id": edge["segment_id"], "distance_km": dist})
        
    # Permits
    permits = []
    total_fee = 15000.0 + max(0.0, cargo_weight_mt - 49.0) * 1.25 * (total_km * 0.4)
    permits.append({"jurisdiction": "CENTRAL_MORTH", "authority": RTO_RULES_DATA["CENTRAL"]["authority"], "permit_code": RTO_RULES_DATA["CENTRAL"]["permit_code"], "statutory_fee_inr": round(total_fee, 2), "sla_days": 5, "portal_url": RTO_RULES_DATA["CENTRAL"]["portal"]})
    
    for st in sorted(list(states)):
        r = RTO_RULES_DATA.get(st)
        if r:
            st_fee = r["base_fee"] + max(0.0, cargo_weight_mt - 49.0) * r["per_mt_km"] * (total_km / len(states)) * 0.3
            total_fee += st_fee
            permits.append({"jurisdiction": f"STATE_{st}", "authority": r["authority"], "permit_code": r["permit_code"], "statutory_fee_inr": round(st_fee, 2), "sla_days": r["sla_days"], "portal_url": r["portal"]})
            
    # Risk scoring
    score = 15
    if cargo_weight_mt > 120: score += 25
    elif cargo_weight_mt > 80: score += 15
    if axle_overloaded: score += 30
    if cargo_height_m > 5.2: score += 20
    elif cargo_height_m > 4.75: score += 12
    if cargo_width_m > 4.5: score += 20
    elif cargo_width_m > 3.8: score += 10
    score += min(25, ghat_count * 12)
    score += min(20, len(bypasses) * 8)
    final_score = min(100, max(0, score))
    status = "FLAGGED_FOR_DISPATCHER_SURVEY" if final_score > 70 else "APPROVED_AUTO_PERMIT"
    
    return {
        "survey_id": f"SURVEY-APP-{int(total_km)}-{int(cargo_weight_mt)}",
        "client_id": client_id,
        "origin": orig,
        "destination": dest,
        "cargo_specs": {"weight_mt": cargo_weight_mt, "height_m": cargo_height_m, "width_m": cargo_width_m, "length_m": cargo_length_m, "axle_count": axle_count},
        "axle_engineering_analysis": {"total_gvw_mt": round(gvw, 2), "axle_load_mt": round(axle_load, 2), "axle_overloaded": axle_overloaded, "axle_loading_safety_margin_pct": round(((13.5 - axle_load)/13.5)*100, 2)},
        "route_summary": {"total_distance_km": round(total_km, 2), "estimated_transit_days": round(total_km / 180.0, 1), "estimated_travel_hours": round(total_hrs, 2), "total_tolls": total_tolls, "ghat_sections_count": ghat_count, "traversed_states": sorted(list(states))},
        "corridor_segments": segments,
        "bottlenecks": {"bypasses_applied": bypasses, "pruned_segments_count": len(pruned)},
        "compliance_matrix": {"permits_checklist": permits, "total_statutory_fee_inr": round(total_fee, 2), "aggregate_survey_sla_days": 7, "escort_mandates": ["Front pilot vehicle with strobe required", "Rear safety escort required"]},
        "risk_evaluation": {"risk_score": final_score, "status": status, "summary": "Deterministic constraints evaluated."},
        "status": status,
        "risk_score": final_score,
        "requires_human_dispatcher_waiver": final_score > 70
    }
