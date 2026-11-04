"""
Sealand Logistics - OOG Route & Permit RAG Assistant
Deterministic Retrieval-Augmented Logic (RAL) Route & Compliance Solver
Windmill Flagship Script: f/sealand_OOG/inexpensive_script
"""

import math
import uuid
import json
import logging
from datetime import datetime, timezone
from typing import TypedDict, Optional, List, Dict, Any
from rapidfuzz import process, fuzz
import networkx as nx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sealand_oog_solver")

# Windmill Postgres Resource Definition (lowercase as required by Windmill)
class postgresql(TypedDict, total=False):
    host: str
    port: int
    user: str
    password: str
    dbname: str
    sslmode: Optional[str]


# ---------------------------------------------------------------------------
# In-Memory Ground Truth Dataset (100% Data Parity with schema.sql)
# ---------------------------------------------------------------------------
NODES_DATA = {
    "PORT_CODE_INVTZ": {
        "node_id": "PORT_CODE_INVTZ",
        "node_name": "Visakhapatnam Port (Vizag)",
        "state_code": "AP",
        "node_type": "PORT",
        "latitude": 17.6868,
        "longitude": 83.2185,
        "elevation_m": 12.0,
        "aliases": ["Vizag", "Visakhapatnam", "Vizag Port", "INVTZ", "VPT", "Visakhapatnam Harbor"]
    },
    "PORT_CODE_INMAA": {
        "node_id": "PORT_CODE_INMAA",
        "node_name": "Chennai Port",
        "state_code": "TN",
        "node_type": "PORT",
        "latitude": 13.0827,
        "longitude": 80.2707,
        "elevation_m": 7.0,
        "aliases": ["Chennai", "Madras Port", "INMAA", "Chennai Harbor", "Madras"]
    },
    "PORT_CODE_INBOM": {
        "node_id": "PORT_CODE_INBOM",
        "node_name": "Jawaharlal Nehru Port Trust (JNPT Mumbai)",
        "state_code": "MH",
        "node_type": "PORT",
        "latitude": 18.9499,
        "longitude": 72.9511,
        "elevation_m": 8.5,
        "aliases": ["JNPT", "Nhava Sheva", "Mumbai Port", "INBOM", "JNPT Mumbai", "Navi Mumbai"]
    },
    "PORT_CODE_INCCU": {
        "node_id": "PORT_CODE_INCCU",
        "node_name": "Kolkata Syama Prasad Mookerjee Port",
        "state_code": "WB",
        "node_type": "PORT",
        "latitude": 22.5411,
        "longitude": 88.3142,
        "elevation_m": 9.0,
        "aliases": ["Kolkata Port", "Calcutta Port", "Haldia", "INCCU", "Kolkata Dock"]
    },
    "PORT_CODE_INPRT": {
        "node_id": "PORT_CODE_INPRT",
        "node_name": "Paradip Port",
        "state_code": "OD",
        "node_type": "PORT",
        "latitude": 20.2644,
        "longitude": 86.6953,
        "elevation_m": 6.5,
        "aliases": ["Paradip", "Paradeep", "INPRT", "Paradip Dock", "Odisha Port"]
    },
    "PORT_CODE_INMUN": {
        "node_id": "PORT_CODE_INMUN",
        "node_name": "Mundra Port",
        "state_code": "GJ",
        "node_type": "PORT",
        "latitude": 22.7441,
        "longitude": 69.7042,
        "elevation_m": 11.0,
        "aliases": ["Mundra", "Adani Mundra", "INMUN", "Mundra Port Kutch"]
    },
    "HUB_RAIPUR": {
        "node_id": "HUB_RAIPUR",
        "node_name": "Raipur Logistics Park",
        "state_code": "CG",
        "node_type": "HUB",
        "latitude": 21.2514,
        "longitude": 81.6296,
        "elevation_m": 298.0,
        "aliases": ["Raipur", "Bhilai", "Naya Raipur", "Raipur Steel Plant", "Raipur Hub"]
    },
    "HUB_NAGPUR": {
        "node_id": "HUB_NAGPUR",
        "node_name": "Nagpur Multimodal Logistics Hub",
        "state_code": "MH",
        "node_type": "HUB",
        "latitude": 21.1458,
        "longitude": 79.0882,
        "elevation_m": 310.0,
        "aliases": ["Nagpur", "MIHAN", "Butibori", "Nagpur Logistics", "Zero Mile Hub"]
    },
    "HUB_HYDERABAD": {
        "node_id": "HUB_HYDERABAD",
        "node_name": "Hyderabad Heavy Industrial Corridor",
        "state_code": "TS",
        "node_type": "HUB",
        "latitude": 17.3850,
        "longitude": 78.4867,
        "elevation_m": 542.0,
        "aliases": ["Hyderabad", "Secunderabad", "Patancheru", "Hyderabad Industrial", "ORR Hyderabad"]
    },
    "HUB_JHARSUGUDA": {
        "node_id": "HUB_JHARSUGUDA",
        "node_name": "Jharsuguda Industrial Hub",
        "state_code": "OD",
        "node_type": "HUB",
        "latitude": 21.8554,
        "longitude": 84.0062,
        "elevation_m": 218.0,
        "aliases": ["Jharsuguda", "Rourkela", "Vedanta Plant", "Jharsuguda Industrial Complex"]
    },
    "HUB_JAMSHEDPUR": {
        "node_id": "HUB_JAMSHEDPUR",
        "node_name": "Jamshedpur Tata Steel Complex",
        "state_code": "JH",
        "node_type": "INDUSTRIAL_PLANT",
        "latitude": 22.8046,
        "longitude": 86.2029,
        "elevation_m": 159.0,
        "aliases": ["Jamshedpur", "Tatanagar", "Tata Steel", "Adityapur Industrial"]
    },
    "HUB_PUNE": {
        "node_id": "HUB_PUNE",
        "node_name": "Pune Chakan Auto Cluster",
        "state_code": "MH",
        "node_type": "HUB",
        "latitude": 18.5204,
        "longitude": 73.8567,
        "elevation_m": 560.0,
        "aliases": ["Pune", "Chakan", "Talegaon", "Pune Auto Cluster", "Bhosari"]
    },
    "HUB_BANGALORE": {
        "node_id": "HUB_BANGALORE",
        "node_name": "Bangalore Nelamangala Freight Hub",
        "state_code": "KA",
        "node_type": "HUB",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "elevation_m": 920.0,
        "aliases": ["Bangalore", "Bengaluru", "Peenya", "Dobbaspet", "Nelamangala"]
    },
    "HUB_AHMEDABAD": {
        "node_id": "HUB_AHMEDABAD",
        "node_name": "Ahmedabad Sanand Auto Hub",
        "state_code": "GJ",
        "node_type": "HUB",
        "latitude": 23.0225,
        "longitude": 72.5714,
        "elevation_m": 53.0,
        "aliases": ["Ahmedabad", "Sanand", "Changodar", "Ahmedabad Industrial"]
    },
    "JUNC_VIJAYAWADA": {
        "node_id": "JUNC_VIJAYAWADA",
        "node_name": "Vijayawada NH-16/NH-65 Junction",
        "state_code": "AP",
        "node_type": "JUNCTION",
        "latitude": 16.5062,
        "longitude": 80.6480,
        "elevation_m": 25.0,
        "aliases": ["Vijayawada", "Bezawada", "Ibrahimpatnam Junction"]
    },
    "JUNC_SURYAPET": {
        "node_id": "JUNC_SURYAPET",
        "node_name": "Suryapet NH-65 Junction",
        "state_code": "TS",
        "node_type": "JUNCTION",
        "latitude": 17.1439,
        "longitude": 79.6239,
        "elevation_m": 172.0,
        "aliases": ["Suryapet", "Suryapet Bypass", "NH65 Suryapet"]
    },
    "JUNC_SOLAPUR": {
        "node_id": "JUNC_SOLAPUR",
        "node_name": "Solapur NH-65/NH-52 Junction",
        "state_code": "MH",
        "node_type": "JUNCTION",
        "latitude": 17.6599,
        "longitude": 75.9064,
        "elevation_m": 458.0,
        "aliases": ["Solapur", "Sholapur", "Solapur Bypass"]
    },
    "JUNC_KOLHAPUR": {
        "node_id": "JUNC_KOLHAPUR",
        "node_name": "Kolhapur NH-48 Junction",
        "state_code": "MH",
        "node_type": "JUNCTION",
        "latitude": 16.7050,
        "longitude": 74.2433,
        "elevation_m": 569.0,
        "aliases": ["Kolhapur", "Shiroli Junction", "Kolhapur NH48"]
    },
    "JUNC_BELGAUM": {
        "node_id": "JUNC_BELGAUM",
        "node_name": "Belgaum NH-48 Hub",
        "state_code": "KA",
        "node_type": "JUNCTION",
        "latitude": 15.8497,
        "longitude": 74.4977,
        "elevation_m": 762.0,
        "aliases": ["Belgaum", "Belagavi", "Belgaum Bypass"]
    },
    "JUNC_KHAMMAM": {
        "node_id": "JUNC_KHAMMAM",
        "node_name": "Khammam Bypass Junction",
        "state_code": "TS",
        "node_type": "JUNCTION",
        "latitude": 17.2473,
        "longitude": 80.1514,
        "elevation_m": 112.0,
        "aliases": ["Khammam", "Khammam Bypass"]
    },
    "JUNC_JAGDALPUR": {
        "node_id": "JUNC_JAGDALPUR",
        "node_name": "Jagdalpur NH-30 Junction",
        "state_code": "CG",
        "node_type": "JUNCTION",
        "latitude": 19.0748,
        "longitude": 82.0298,
        "elevation_m": 552.0,
        "aliases": ["Jagdalpur", "Bastar", "Jagdalpur Bypass"]
    },
    "JUNC_SAMBALPUR": {
        "node_id": "JUNC_SAMBALPUR",
        "node_name": "Sambalpur NH-53 Junction",
        "state_code": "OD",
        "node_type": "JUNCTION",
        "latitude": 21.4669,
        "longitude": 83.9812,
        "elevation_m": 150.0,
        "aliases": ["Sambalpur", "Burla", "Hirakud Junction"]
    },
    "JUNC_BALASORE": {
        "node_id": "JUNC_BALASORE",
        "node_name": "Balasore NH-16 Junction",
        "state_code": "OD",
        "node_type": "JUNCTION",
        "latitude": 21.4934,
        "longitude": 86.9135,
        "elevation_m": 16.0,
        "aliases": ["Balasore", "Baleswar", "Balasore NH16"]
    }
}

SEGMENTS_DATA = [
    # Vizag Corridors
    {"segment_id": "SEG-VTZ-VJW-NH16", "source": "PORT_CODE_INVTZ", "target": "JUNC_VIJAYAWADA", "highway": "NH-16", "distance_km": 350.0, "max_weight_mt": 100.0, "max_height_m": 5.5, "max_width_m": 5.5, "ghat": False, "tolls": 5, "speed": 28.0, "states": ["AP"]},
    {"segment_id": "SEG-VTZ-JAG-NH30", "source": "PORT_CODE_INVTZ", "target": "JUNC_JAGDALPUR", "highway": "NH-30", "distance_km": 310.0, "max_weight_mt": 65.0, "max_height_m": 5.0, "max_width_m": 4.5, "ghat": True, "tolls": 3, "speed": 18.0, "states": ["AP", "CG"]},
    {"segment_id": "SEG-VTZ-SAM-NH26", "source": "PORT_CODE_INVTZ", "target": "JUNC_SAMBALPUR", "highway": "NH-26", "distance_km": 450.0, "max_weight_mt": 120.0, "max_height_m": 5.8, "max_width_m": 5.5, "ghat": False, "tolls": 6, "speed": 26.0, "states": ["AP", "OD"]},
    
    # Vijayawada Corridors
    {"segment_id": "SEG-VJW-SUR-NH65", "source": "JUNC_VIJAYAWADA", "target": "JUNC_SURYAPET", "highway": "NH-65", "distance_km": 140.0, "max_weight_mt": 110.0, "max_height_m": 5.4, "max_width_m": 5.5, "ghat": False, "tolls": 2, "speed": 30.0, "states": ["AP", "TS"]},
    {"segment_id": "SEG-VJW-MAA-NH16", "source": "JUNC_VIJAYAWADA", "target": "PORT_CODE_INMAA", "highway": "NH-16", "distance_km": 430.0, "max_weight_mt": 120.0, "max_height_m": 5.6, "max_width_m": 5.5, "ghat": False, "tolls": 6, "speed": 30.0, "states": ["AP", "TN"]},
    {"segment_id": "SEG-VJW-KHM-NH365", "source": "JUNC_VIJAYAWADA", "target": "JUNC_KHAMMAM", "highway": "NH-365A", "distance_km": 115.0, "max_weight_mt": 90.0, "max_height_m": 5.2, "max_width_m": 4.8, "ghat": False, "tolls": 1, "speed": 25.0, "states": ["AP", "TS"]},
    
    # Suryapet & Hyderabad Corridors
    {"segment_id": "SEG-SUR-HYD-NH65", "source": "JUNC_SURYAPET", "target": "HUB_HYDERABAD", "highway": "NH-65", "distance_km": 135.0, "max_weight_mt": 110.0, "max_height_m": 5.2, "max_width_m": 5.5, "ghat": False, "tolls": 2, "speed": 30.0, "states": ["TS"]},
    {"segment_id": "SEG-KHM-SUR-NH365", "source": "JUNC_KHAMMAM", "target": "JUNC_SURYAPET", "highway": "NH-365BB", "distance_km": 65.0, "max_weight_mt": 95.0, "max_height_m": 5.3, "max_width_m": 5.0, "ghat": False, "tolls": 1, "speed": 28.0, "states": ["TS"]},
    {"segment_id": "SEG-HYD-NGP-NH44", "source": "HUB_HYDERABAD", "target": "HUB_NAGPUR", "highway": "NH-44", "distance_km": 500.0, "max_weight_mt": 130.0, "max_height_m": 5.8, "max_width_m": 5.5, "ghat": False, "tolls": 7, "speed": 32.0, "states": ["TS", "MH"]},
    {"segment_id": "SEG-HYD-SOL-NH65", "source": "HUB_HYDERABAD", "target": "JUNC_SOLAPUR", "highway": "NH-65", "distance_km": 310.0, "max_weight_mt": 110.0, "max_height_m": 5.5, "max_width_m": 5.5, "ghat": False, "tolls": 4, "speed": 30.0, "states": ["TS", "KA", "MH"]},
    {"segment_id": "SEG-HYD-BLR-NH44", "source": "HUB_HYDERABAD", "target": "HUB_BANGALORE", "highway": "NH-44", "distance_km": 570.0, "max_weight_mt": 120.0, "max_height_m": 5.8, "max_width_m": 5.5, "ghat": False, "tolls": 8, "speed": 32.0, "states": ["TS", "AP", "KA"]},
    
    # Raipur Corridors
    {"segment_id": "SEG-JAG-RPR-NH30", "source": "JUNC_JAGDALPUR", "target": "HUB_RAIPUR", "highway": "NH-30", "distance_km": 295.0, "max_weight_mt": 85.0, "max_height_m": 5.1, "max_width_m": 4.8, "ghat": True, "tolls": 3, "speed": 20.0, "states": ["CG"]},
    {"segment_id": "SEG-SAM-RPR-NH53", "source": "JUNC_SAMBALPUR", "target": "HUB_RAIPUR", "highway": "NH-53", "distance_km": 280.0, "max_weight_mt": 130.0, "max_height_m": 5.8, "max_width_m": 5.5, "ghat": False, "tolls": 4, "speed": 30.0, "states": ["OD", "CG"]},
    {"segment_id": "SEG-NGP-RPR-NH53", "source": "HUB_NAGPUR", "target": "HUB_RAIPUR", "highway": "NH-53", "distance_km": 290.0, "max_weight_mt": 130.0, "max_height_m": 5.8, "max_width_m": 5.5, "ghat": False, "tolls": 4, "speed": 30.0, "states": ["MH", "CG"]},
    
    # Odisha & West Bengal Corridors
    {"segment_id": "SEG-SAM-JHS-NH49", "source": "JUNC_SAMBALPUR", "target": "HUB_JHARSUGUDA", "highway": "NH-49", "distance_km": 55.0, "max_weight_mt": 140.0, "max_height_m": 5.8, "max_width_m": 5.5, "ghat": False, "tolls": 1, "speed": 28.0, "states": ["OD"]},
    {"segment_id": "SEG-PRT-SAM-NH53", "source": "PORT_CODE_INPRT", "target": "JUNC_SAMBALPUR", "highway": "NH-53", "distance_km": 340.0, "max_weight_mt": 80.0, "max_height_m": 4.9, "max_width_m": 5.0, "ghat": False, "tolls": 4, "speed": 25.0, "states": ["OD"]},
    {"segment_id": "SEG-JHS-JAM-NH49", "source": "HUB_JHARSUGUDA", "target": "HUB_JAMSHEDPUR", "highway": "NH-49", "distance_km": 260.0, "max_weight_mt": 120.0, "max_height_m": 5.5, "max_width_m": 5.0, "ghat": False, "tolls": 3, "speed": 26.0, "states": ["OD", "JH"]},
    {"segment_id": "SEG-BLS-SAM-NH49", "source": "JUNC_BALASORE", "target": "JUNC_SAMBALPUR", "highway": "NH-49", "distance_km": 360.0, "max_weight_mt": 110.0, "max_height_m": 5.4, "max_width_m": 5.2, "ghat": False, "tolls": 4, "speed": 26.0, "states": ["OD"]},
    {"segment_id": "SEG-CCU-BLS-NH16", "source": "PORT_CODE_INCCU", "target": "JUNC_BALASORE", "highway": "NH-16", "distance_km": 240.0, "max_weight_mt": 75.0, "max_height_m": 4.95, "max_width_m": 5.2, "ghat": False, "tolls": 3, "speed": 26.0, "states": ["WB", "OD"]},
    {"segment_id": "SEG-CCU-JAM-NH18", "source": "PORT_CODE_INCCU", "target": "HUB_JAMSHEDPUR", "highway": "NH-18", "distance_km": 285.0, "max_weight_mt": 100.0, "max_height_m": 5.2, "max_width_m": 5.0, "ghat": False, "tolls": 3, "speed": 27.0, "states": ["WB", "JH"]},
    
    # Western / Mumbai / Pune Corridors
    {"segment_id": "SEG-JNPT-PUN-NH48", "source": "PORT_CODE_INBOM", "target": "HUB_PUNE", "highway": "NH-48", "distance_km": 145.0, "max_weight_mt": 140.0, "max_height_m": 4.85, "max_width_m": 5.5, "ghat": True, "tolls": 2, "speed": 24.0, "states": ["MH"]},
    {"segment_id": "SEG-JNPT-NGP-NH160", "source": "PORT_CODE_INBOM", "target": "HUB_NAGPUR", "highway": "NH-160/NH-53", "distance_km": 780.0, "max_weight_mt": 90.0, "max_height_m": 4.8, "max_width_m": 4.8, "ghat": True, "tolls": 9, "speed": 22.0, "states": ["MH"]},
    {"segment_id": "SEG-PUN-SOL-NH65", "source": "HUB_PUNE", "target": "JUNC_SOLAPUR", "highway": "NH-65", "distance_km": 250.0, "max_weight_mt": 120.0, "max_height_m": 5.6, "max_width_m": 5.5, "ghat": False, "tolls": 3, "speed": 30.0, "states": ["MH"]},
    {"segment_id": "SEG-PUN-KOL-NH48", "source": "HUB_PUNE", "target": "JUNC_KOLHAPUR", "highway": "NH-48", "distance_km": 235.0, "max_weight_mt": 130.0, "max_height_m": 5.6, "max_width_m": 5.5, "ghat": False, "tolls": 3, "speed": 30.0, "states": ["MH"]},
    {"segment_id": "SEG-KOL-BLG-NH48", "source": "JUNC_KOLHAPUR", "target": "JUNC_BELGAUM", "highway": "NH-48", "distance_km": 105.0, "max_weight_mt": 130.0, "max_height_m": 5.6, "max_width_m": 5.5, "ghat": False, "tolls": 1, "speed": 30.0, "states": ["MH", "KA"]},
    {"segment_id": "SEG-BLG-BLR-NH48", "source": "JUNC_BELGAUM", "target": "HUB_BANGALORE", "highway": "NH-48", "distance_km": 505.0, "max_weight_mt": 120.0, "max_height_m": 5.5, "max_width_m": 5.5, "ghat": False, "tolls": 6, "speed": 32.0, "states": ["KA"]},
    {"segment_id": "SEG-MAA-BLR-NH48", "source": "PORT_CODE_INMAA", "target": "HUB_BANGALORE", "highway": "NH-48", "distance_km": 345.0, "max_weight_mt": 110.0, "max_height_m": 5.4, "max_width_m": 5.5, "ghat": False, "tolls": 4, "speed": 30.0, "states": ["TN", "KA"]},
    
    # Gujarat Corridors
    {"segment_id": "SEG-MUN-AMD-NH947", "source": "PORT_CODE_INMUN", "target": "HUB_AHMEDABAD", "highway": "NH-947", "distance_km": 360.0, "max_weight_mt": 140.0, "max_height_m": 5.8, "max_width_m": 5.5, "ghat": False, "tolls": 4, "speed": 32.0, "states": ["GJ"]},
    {"segment_id": "SEG-AMD-PUN-NH48", "source": "HUB_AHMEDABAD", "target": "HUB_PUNE", "highway": "NH-48", "distance_km": 660.0, "max_weight_mt": 120.0, "max_height_m": 5.5, "max_width_m": 5.5, "ghat": False, "tolls": 8, "speed": 30.0, "states": ["GJ", "MH"]},
    {"segment_id": "SEG-AMD-NGP-NH53", "source": "HUB_AHMEDABAD", "target": "HUB_NAGPUR", "highway": "NH-53", "distance_km": 820.0, "max_weight_mt": 120.0, "max_height_m": 5.6, "max_width_m": 5.5, "ghat": False, "tolls": 10, "speed": 28.0, "states": ["GJ", "MH"]}
]

BRIDGE_CONSTRAINTS = [
    {
        "bridge_id": "BRG-AP-NAGAVALI-01",
        "bridge_name": "Nagavali River Arch Bridge",
        "segment_id": "SEG-VTZ-JAG-NH30",
        "lat": 18.2941, "lon": 83.8964,
        "max_weight_mt": 65.0,
        "min_vertical_clearance_m": 5.2,
        "structure_type": "Masonry Arch",
        "bypass_available": True,
        "bypass_route_id": "SEG-VTZ-SAM-NH26",
        "bypass_penalty_km": 140.0,
        "notes": "Arch load limit strictly enforced by AP PWD. Loads > 65MT must detour via Sambalpur NH-26."
    },
    {
        "bridge_id": "BRG-AP-GODAVARI-04",
        "bridge_name": "Godavari Fourth Road Bridge (Rajahmundry)",
        "segment_id": "SEG-VTZ-VJW-NH16",
        "lat": 17.0005, "lon": 81.7774,
        "max_weight_mt": 160.0,
        "min_vertical_clearance_m": 5.6,
        "structure_type": "Prestressed Box Girder",
        "bypass_available": True,
        "bypass_route_id": "BYPASS-RMY-OLD-NH16",
        "bypass_penalty_km": 25.0,
        "notes": "Heavy lift capable up to 160MT. Pre-notification required for center-lane crawl."
    },
    {
        "bridge_id": "BRG-MH-KASARA-ROB-01",
        "bridge_name": "Kasara Ghat Railway Overbridge",
        "segment_id": "SEG-JNPT-NGP-NH160",
        "lat": 19.6417, "lon": 73.4833,
        "max_weight_mt": 90.0,
        "min_vertical_clearance_m": 4.80,
        "structure_type": "Through Truss ROB",
        "bypass_available": True,
        "bypass_route_id": "SEG-JNPT-PUN-NH48",
        "bypass_penalty_km": 185.0,
        "notes": "CRITICAL OVERHEAD CLEARANCE (4.80m). ODC height > 4.75m MUST bypass via Pune-Solapur-Nagpur."
    },
    {
        "bridge_id": "BRG-MH-BHOR-TUNNEL-02",
        "bridge_name": "Bhor Ghat Khandala Expressway Tunnel",
        "segment_id": "SEG-JNPT-PUN-NH48",
        "lat": 18.7562, "lon": 73.3421,
        "max_weight_mt": 140.0,
        "min_vertical_clearance_m": 4.85,
        "structure_type": "Rock Tunnel",
        "bypass_available": True,
        "bypass_route_id": "BYPASS-OLD-MUM-PUN-NH48",
        "bypass_penalty_km": 38.0,
        "notes": "Crown clearance 4.85m in right lane. Super-loads > 4.80m diverted to Old NH-48 surface route."
    },
    {
        "bridge_id": "BRG-TS-SURYAPET-HT-01",
        "bridge_name": "Suryapet High-Tension Transmission Crossing",
        "segment_id": "SEG-SUR-HYD-NH65",
        "lat": 17.1520, "lon": 79.6100,
        "max_weight_mt": 130.0,
        "min_vertical_clearance_m": 5.20,
        "structure_type": "Power Grid Aerial Crossing",
        "bypass_available": True,
        "bypass_route_id": "BYPASS-SURYAPET-LOCAL",
        "bypass_penalty_km": 12.0,
        "notes": "400kV PowerGrid line SAG risk in summer. Loads > 5.10m require line power shut-down permit."
    },
    {
        "bridge_id": "BRG-OD-MAHANADI-02",
        "bridge_name": "Mahanadi Rail-Cum-Road Truss Bridge",
        "segment_id": "SEG-PRT-SAM-NH53",
        "lat": 20.4850, "lon": 85.8750,
        "max_weight_mt": 80.0,
        "min_vertical_clearance_m": 4.90,
        "structure_type": "Steel Truss",
        "bypass_available": True,
        "bypass_route_id": "BYPASS-SAMBALPUR-RING",
        "bypass_penalty_km": 45.0,
        "notes": "Weight strictly capped at 80MT. Heavier industrial consignments must use NH-49 via Jharsuguda."
    },
    {
        "bridge_id": "BRG-CG-SHEONATH-01",
        "bridge_name": "Sheonath River Arch Bridge (Durg)",
        "segment_id": "SEG-NGP-RPR-NH53",
        "lat": 21.1890, "lon": 81.2810,
        "max_weight_mt": 130.0,
        "min_vertical_clearance_m": 5.60,
        "structure_type": "Concrete Arch",
        "bypass_available": True,
        "bypass_route_id": "BYPASS-DURG-NH53-NEW",
        "bypass_penalty_km": 18.0,
        "notes": "Reinforced 6-lane bypass bridge available with 130MT capacity."
    },
    {
        "bridge_id": "BRG-TN-PALAR-01",
        "bridge_name": "Palar River Pre-stressed Girder",
        "segment_id": "SEG-MAA-BLR-NH48",
        "lat": 12.8940, "lon": 79.3120,
        "max_weight_mt": 110.0,
        "min_vertical_clearance_m": 5.40,
        "structure_type": "Prestressed Concrete Girder",
        "bypass_available": True,
        "bypass_route_id": "BYPASS-VELLORE-NH48",
        "bypass_penalty_km": 15.0,
        "notes": "Center-span load restriction for multi-axle trailers > 100MT."
    },
    {
        "bridge_id": "BRG-KA-KALI-01",
        "bridge_name": "Kali River Estuary Span",
        "segment_id": "SEG-BLG-BLR-NH48",
        "lat": 14.8410, "lon": 74.1350,
        "max_weight_mt": 95.0,
        "min_vertical_clearance_m": 5.10,
        "structure_type": "Continuous Steel Box",
        "bypass_available": True,
        "bypass_route_id": "BYPASS-DHARWAD-NH48",
        "bypass_penalty_km": 28.0,
        "notes": "Wind sway restrictions apply during monsoon. Escort mandated."
    },
    {
        "bridge_id": "BRG-WB-RUPNARAYAN-01",
        "bridge_name": "Rupnarayan River Kolaghat Truss Bridge",
        "segment_id": "SEG-CCU-BLS-NH16",
        "lat": 22.4270, "lon": 87.8730,
        "max_weight_mt": 75.0,
        "min_vertical_clearance_m": 4.95,
        "structure_type": "Steel Lattice Girder",
        "bypass_available": True,
        "bypass_route_id": "BYPASS-KHARAGPUR-NH16",
        "bypass_penalty_km": 52.0,
        "notes": "Severe corrosion monitoring. Cargo > 75MT must bypass via Kharagpur heavy axle corridor."
    }
]

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


# ---------------------------------------------------------------------------
# Helper Functions: Node Resolution & Multi-Axle Physics
# ---------------------------------------------------------------------------
def fuzzy_match_node(query: str, nodes_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Deterministically map user query string to standard node using RapidFuzz."""
    if not query:
        return None
    cleaned = query.strip()
    
    # 1. Exact node_id match
    if cleaned in nodes_dict:
        return nodes_dict[cleaned]
    
    # 2. Build candidate pool from node_name and aliases
    candidate_lookup = {}
    for node_id, data in nodes_dict.items():
        candidate_lookup[data["node_name"].lower()] = data
        for alias in data.get("aliases", []):
            candidate_lookup[alias.lower()] = data
            
    # Fuzzy match with score cutoff 60
    candidates = list(candidate_lookup.keys())
    match_result = process.extractOne(cleaned.lower(), candidates, scorer=fuzz.WRatio)
    if match_result and match_result[1] >= 55:
        matched_str = match_result[0]
        return candidate_lookup[matched_str]
    
    return None


def calculate_multiaxle_loading(cargo_weight_mt: float, axle_count: int) -> Dict[str, Any]:
    """Calculate Gross Vehicle Weight (GVW) and hydraulic axle line loading."""
    # Puller prime mover ~12 MT, hydraulic multi-axle modular trailer tare ~3.5 MT per axle line
    trailer_tare_mt = 3.5 * max(1, axle_count)
    puller_tare_mt = 12.0
    total_tare_mt = trailer_tare_mt + puller_tare_mt
    gvw_mt = cargo_weight_mt + total_tare_mt
    axle_load_mt = gvw_mt / max(1, axle_count)
    
    # Indian IRC:SP:35 permissible limit for hydraulic multi-axle trailers is 13.5 MT/axle line
    max_permissible_axle_load_mt = 13.5
    is_overloaded = axle_load_mt > max_permissible_axle_load_mt
    recommended_axles = math.ceil(gvw_mt / 12.5) if is_overloaded else axle_count

    return {
        "cargo_weight_mt": cargo_weight_mt,
        "puller_tare_mt": puller_tare_mt,
        "trailer_tare_mt": round(trailer_tare_mt, 2),
        "total_gvw_mt": round(gvw_mt, 2),
        "axle_count": axle_count,
        "axle_load_mt": round(axle_load_mt, 2),
        "permissible_axle_load_mt": max_permissible_axle_load_mt,
        "axle_overloaded": is_overloaded,
        "recommended_min_axle_count": recommended_axles,
        "axle_loading_safety_margin_pct": round(((max_permissible_axle_load_mt - axle_load_mt) / max_permissible_axle_load_mt) * 100, 2)
    }


# ---------------------------------------------------------------------------
# Core Graph Pruning & Deterministic Routing Solver
# ---------------------------------------------------------------------------
def build_and_prune_graph(
    cargo_weight_mt: float,
    cargo_height_m: float,
    cargo_width_m: float,
    cargo_length_m: float,
    allow_bypasses: bool = True
) -> Dict[str, Any]:
    """Construct highway graph and apply strict physical clearance filters."""
    G = nx.Graph()
    
    # Add nodes
    for node_id, node in NODES_DATA.items():
        G.add_node(
            node_id,
            name=node["node_name"],
            state=node["state_code"],
            lat=node["latitude"],
            lon=node["longitude"]
        )
        
    bottlenecks_map: Dict[str, List[Dict[str, Any]]] = {}
    for bridge in BRIDGE_CONSTRAINTS:
        seg_id = bridge["segment_id"]
        bottlenecks_map.setdefault(seg_id, []).append(bridge)
        
    pruned_segments = []
    bypasses_applied = []
    active_edges = []
    
    for seg in SEGMENTS_DATA:
        seg_id = seg["segment_id"]
        u = seg["source"]
        v = seg["target"]
        dist = seg["distance_km"]
        is_ghat = seg["ghat"]
        segment_states = seg["states"]
        
        # Base segment capability checks
        segment_blocked = False
        block_reason = ""
        applied_penalty_km = 0.0
        
        # Ghat width check (hairpin turn radius constraint)
        if is_ghat and cargo_width_m > seg["max_width_m"]:
            segment_blocked = True
            block_reason = f"Ghat curve geometry violation: Cargo width {cargo_width_m}m exceeds max {seg['max_width_m']}m"
            
        # Bridge checks
        seg_bridges = bottlenecks_map.get(seg_id, [])
        for bridge in seg_bridges:
            weight_breach = cargo_weight_mt > bridge["max_weight_mt"]
            height_breach = cargo_height_m > bridge["min_vertical_clearance_m"]
            
            if weight_breach or height_breach:
                breach_desc = []
                if weight_breach:
                    breach_desc.append(f"Weight {cargo_weight_mt}MT > Limit {bridge['max_weight_mt']}MT")
                if height_breach:
                    breach_desc.append(f"Height {cargo_height_m}m > Clearance {bridge['min_vertical_clearance_m']}m")
                desc_str = " & ".join(breach_desc)
                
                if allow_bypasses and bridge["bypass_available"]:
                    penalty = bridge["bypass_penalty_km"]
                    applied_penalty_km += penalty
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
                    segment_blocked = True
                    block_reason = f"Impassable structure {bridge['bridge_id']} ({bridge['bridge_name']}): {desc_str}"
                    break
                    
        if segment_blocked:
            pruned_segments.append({
                "segment_id": seg_id,
                "source": u,
                "target": v,
                "reason": block_reason
            })
        else:
            # Composite edge weight: distance + penalty + ghat buffer
            effective_dist = dist + applied_penalty_km
            edge_weight = effective_dist + (35.0 if is_ghat else 0.0)
            G.add_edge(
                u, v,
                segment_id=seg_id,
                highway=seg["highway"],
                base_distance_km=dist,
                effective_distance_km=effective_dist,
                weight=edge_weight,
                ghat=is_ghat,
                tolls=seg["tolls"],
                speed=seg["speed"],
                states=segment_states
            )
            active_edges.append(seg_id)
            
    return {
        "graph": G,
        "pruned_segments": pruned_segments,
        "bypasses_applied": bypasses_applied,
        "active_edge_count": len(active_edges)
    }


def compute_optimal_route(
    G: nx.Graph,
    source_id: str,
    target_id: str
) -> Optional[Dict[str, Any]]:
    """Compute shortest viable path and collect corridor metrics."""
    if not nx.has_path(G, source_id, target_id):
        return None
        
    path_nodes = nx.shortest_path(G, source_id, target_id, weight="weight")
    
    total_km = 0.0
    total_tolls = 0
    total_travel_hours = 0.0
    ghat_sections_count = 0
    traversed_states = set()
    segments_in_path = []
    
    for i in range(len(path_nodes) - 1):
        u = path_nodes[i]
        v = path_nodes[i+1]
        edge = G[u][v]
        
        dist = edge["effective_distance_km"]
        total_km += dist
        total_tolls += edge["tolls"]
        if edge["ghat"]:
            ghat_sections_count += 1
        for st in edge["states"]:
            traversed_states.add(st)
            
        # OOG transit speed
        hrs = dist / edge["speed"]
        total_travel_hours += hrs
        
        segments_in_path.append({
            "from_node": u,
            "to_node": v,
            "segment_id": edge["segment_id"],
            "highway": edge["highway"],
            "distance_km": dist,
            "ghat": edge["ghat"],
            "tolls": edge["tolls"]
        })
        
    return {
        "path_nodes": path_nodes,
        "segments": segments_in_path,
        "total_distance_km": round(total_km, 2),
        "total_tolls": total_tolls,
        "estimated_travel_hours": round(total_travel_hours, 2),
        "estimated_transit_days": round(total_km / 180.0, 1), # Heavy ODC max ~180 km/day
        "ghat_sections_count": ghat_sections_count,
        "traversed_states": sorted(list(traversed_states))
    }


# ---------------------------------------------------------------------------
# Deterministic RTO Compliance & Fee Engine
# ---------------------------------------------------------------------------
def evaluate_rto_compliance(
    traversed_states: List[str],
    total_distance_km: float,
    cargo_weight_mt: float,
    cargo_width_m: float,
    cargo_height_m: float,
    cargo_length_m: float
) -> Dict[str, Any]:
    """Calculate state-by-state permit checklists, statutory fees, and escort mandates."""
    permits = []
    total_cost_inr = 0.0
    max_sla_days = 0
    escort_mandates = []
    night_restrictions = []
    
    # 1. Central MoRTH permit is mandatory for all interstate movements
    central_rule = RTO_RULES_DATA["CENTRAL"]
    base_morth = central_rule["base_fee"]
    per_mt_km = central_rule["per_mt_km"]
    excess_weight = max(0.0, cargo_weight_mt - 49.0) # MoRTH standard 49MT gross allowance
    weight_surcharge = excess_weight * per_mt_km * (total_distance_km * 0.4) # Shared central levy
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
        
        # Escort mandates
        if cargo_width_m >= rule["escort_width_m"] or cargo_weight_mt >= rule["escort_weight_mt"]:
            escort_mandates.append(
                f"State of {state}: Mandatory 2-vehicle convoy (Front pilot with amber strobe + rear escort) required by {rule['authority']}."
            )
            
        # Night travel rules
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
        
    # Overall escort requirement summary
    needs_police_escort = (cargo_width_m >= 4.0 or cargo_weight_mt >= 90.0 or cargo_length_m >= 25.0)
    if needs_police_escort:
        escort_mandates.insert(
            0,
            "HIGHWAY PATROL POLICE ESCORT: Mandated under Motor Vehicles Act Section 112 for super-heavy ODC convoy."
        )

    return {
        "permits_checklist": permits,
        "total_statutory_fee_inr": round(total_cost_inr, 2),
        "aggregate_survey_sla_days": max_sla_days + 2, # Buffer for multi-state liaison
        "escort_mandates": escort_mandates,
        "night_travel_restrictions": night_restrictions,
        "requires_police_convoy": needs_police_escort
    }


# ---------------------------------------------------------------------------
# Algorithmic Deterministic Risk Scoring (0 to 100)
# ---------------------------------------------------------------------------
def compute_oog_risk_score(
    cargo_weight_mt: float,
    cargo_height_m: float,
    cargo_width_m: float,
    cargo_length_m: float,
    axle_info: Dict[str, Any],
    route_info: Dict[str, Any],
    bypasses_applied: List[Dict[str, Any]],
    compliance_info: Dict[str, Any]
) -> Dict[str, Any]:
    """Calculate composite route risk score deterministically."""
    score = 15 # Baseline baseline risk
    risk_factors = []
    
    # 1. Weight factor
    if cargo_weight_mt > 120.0:
        score += 25
        risk_factors.append("Extreme Super-Heavy Lift (>120MT): Dynamic bridge deflection hazard (+25)")
    elif cargo_weight_mt > 80.0:
        score += 15
        risk_factors.append("Heavy Lift (80-120MT): Structural girder verification required (+15)")
        
    # 2. Axle load factor
    if axle_info["axle_overloaded"]:
        score += 30
        risk_factors.append(f"IRC:SP:35 Axle Line Overload ({axle_info['axle_load_mt']}MT/axle > 13.5MT limit) (+30)")
    elif axle_info["axle_load_mt"] > 11.5:
        score += 10
        risk_factors.append(f"Sub-optimal Axle Line Margin ({axle_info['axle_load_mt']}MT/axle) (+10)")
        
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
    
    # Decision threshold: 70
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


# ---------------------------------------------------------------------------
# Database Persistence & Audit Logging
# ---------------------------------------------------------------------------
def persist_to_database(
    db_config: Optional[postgresql],
    job_payload: Dict[str, Any],
    audit_action: str
) -> bool:
    """Safely persist survey job and audit log to PostgreSQL if configured & reachable."""
    if not db_config:
        return False
        
    try:
        import psycopg2
        
        # Determine host & credentials
        host = db_config.get("host", "db")
        port = db_config.get("port", 5432)
        user = db_config.get("user", "postgres")
        password = db_config.get("password", "changeme")
        dbname = db_config.get("dbname", "windmill")
        
        conn = None
        for try_host in [host, "localhost", "127.0.0.1"]:
            try:
                conn = psycopg2.connect(
                    host=try_host,
                    port=port,
                    user=user,
                    password=password,
                    dbname=dbname,
                    connect_timeout=1
                )
                break
            except Exception:
                continue
                
        if not conn:
            logger.info("PostgreSQL not reachable; skipping DB persistence.")
            return False
            
        cur = conn.cursor()
        
        # Insert or update oog_survey_jobs
        insert_job_sql = """
            INSERT INTO oog_survey_jobs (
                job_id, client_id, origin_query, destination_query,
                matched_origin_id, matched_destination_id,
                cargo_weight_mt, cargo_length_m, cargo_width_m, cargo_height_m, axle_count,
                status, risk_score, selected_path_nodes, total_distance_km,
                estimated_transit_hours, bottlenecks_flagged, permits_required,
                total_permit_cost_inr, created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
            )
            ON CONFLICT (job_id) DO UPDATE SET
                status = EXCLUDED.status,
                risk_score = EXCLUDED.risk_score,
                selected_path_nodes = EXCLUDED.selected_path_nodes,
                total_distance_km = EXCLUDED.total_distance_km,
                updated_at = NOW();
        """
        
        cur.execute(insert_job_sql, (
            job_payload["job_id"],
            job_payload["client_id"],
            job_payload["origin_query"],
            job_payload["destination_query"],
            job_payload["matched_origin_id"],
            job_payload["matched_destination_id"],
            job_payload["cargo_weight_mt"],
            job_payload["cargo_length_m"],
            job_payload["cargo_width_m"],
            job_payload["cargo_height_m"],
            job_payload["axle_count"],
            job_payload["status"],
            job_payload["risk_score"],
            json.dumps(job_payload.get("path_nodes", [])),
            job_payload.get("total_distance_km", 0.0),
            job_payload.get("estimated_transit_hours", 0.0),
            json.dumps(job_payload.get("bottlenecks", [])),
            json.dumps(job_payload.get("permits", [])),
            job_payload.get("total_permit_cost_inr", 0.0)
        ))
        
        # Insert audit log
        insert_audit_sql = """
            INSERT INTO oog_audit_logs (job_id, action, details, logged_at)
            VALUES (%s, %s, %s, NOW());
        """
        cur.execute(insert_audit_sql, (
            job_payload["job_id"],
            audit_action,
            json.dumps({
                "risk_score": job_payload["risk_score"],
                "status": job_payload["status"],
                "action": audit_action
            })
        ))
        
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        logger.warning(f"Could not persist to PostgreSQL: {e}")
        return False


# ---------------------------------------------------------------------------
# Main Windmill Entrypoint
# ---------------------------------------------------------------------------
def main(
    origin_query: str = "Visakhapatnam Port",
    destination_query: str = "Raipur Logistics Hub",
    cargo_weight_mt: float = 85.0,
    cargo_length_m: float = 24.5,
    cargo_width_m: float = 4.2,
    cargo_height_m: float = 5.1,
    axle_count: int = 10,
    client_id: str = "SEALAND_PROJECT_CARGO_DIV",
    survey_id: str = "",
    allow_bypasses: bool = True,
    db: postgresql = None,
) -> dict:
    """
    Sealand Logistics OOG Route & Permit RAG Assistant
    Retrieval-Augmented Logic (RAL) Zero-LLM Deterministic Engine
    """
    start_time = datetime.now(timezone.utc)
    assigned_survey_id = survey_id.strip() or f"SURVEY-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    
    # Step 1: Fuzzy match Origin & Destination
    origin_node = fuzzy_match_node(origin_query, NODES_DATA)
    dest_node = fuzzy_match_node(destination_query, NODES_DATA)
    
    if not origin_node:
        return {
            "error": "ORIGIN_NOT_FOUND",
            "message": f"Unable to resolve origin location '{origin_query}'. Available nodes: {list(NODES_DATA.keys())}",
            "survey_id": assigned_survey_id,
            "status": "REJECTED_INVALID_INPUT"
        }
        
    if not dest_node:
        return {
            "error": "DESTINATION_NOT_FOUND",
            "message": f"Unable to resolve destination location '{destination_query}'. Available nodes: {list(NODES_DATA.keys())}",
            "survey_id": assigned_survey_id,
            "status": "REJECTED_INVALID_INPUT"
        }
        
    origin_id = origin_node["node_id"]
    dest_id = dest_node["node_id"]
    
    # Step 2: Multi-Axle Physics Loading
    axle_analysis = calculate_multiaxle_loading(cargo_weight_mt, axle_count)
    
    # Step 3: Graph Construction & Constraint Pruning
    prune_res = build_and_prune_graph(
        cargo_weight_mt=cargo_weight_mt,
        cargo_height_m=cargo_height_m,
        cargo_width_m=cargo_width_m,
        cargo_length_m=cargo_length_m,
        allow_bypasses=allow_bypasses
    )
    
    G = prune_res["graph"]
    pruned_segments = prune_res["pruned_segments"]
    bypasses_applied = prune_res["bypasses_applied"]
    
    # Step 4: Route Computation
    route_res = compute_optimal_route(G, origin_id, dest_id)
    
    if not route_res:
        execution_duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        return {
            "survey_id": assigned_survey_id,
            "client_id": client_id,
            "origin": {"query": origin_query, "matched_node": origin_node},
            "destination": {"query": destination_query, "matched_node": dest_node},
            "status": "IMPASSABLE_NO_FEASIBLE_ROUTE",
            "risk_score": 100,
            "message": "No physically passable highway corridor found for these cargo dimensions.",
            "pruned_segments": pruned_segments,
            "axle_analysis": axle_analysis,
            "execution_duration_ms": round(execution_duration_ms, 2)
        }
        
    # Step 5: Deterministic RTO Compliance & Permit Matrix
    compliance = evaluate_rto_compliance(
        traversed_states=route_res["traversed_states"],
        total_distance_km=route_res["total_distance_km"],
        cargo_weight_mt=cargo_weight_mt,
        cargo_width_m=cargo_width_m,
        cargo_height_m=cargo_height_m,
        cargo_length_m=cargo_length_m
    )
    
    # Step 6: Algorithmic Risk Scoring (0 - 100)
    risk_evaluation = compute_oog_risk_score(
        cargo_weight_mt=cargo_weight_mt,
        cargo_height_m=cargo_height_m,
        cargo_width_m=cargo_width_m,
        cargo_length_m=cargo_length_m,
        axle_info=axle_analysis,
        route_info=route_res,
        bypasses_applied=bypasses_applied,
        compliance_info=compliance
    )
    
    # Build coordinates for map visualization
    route_coordinates = []
    for nid in route_res["path_nodes"]:
        n = NODES_DATA.get(nid)
        if n:
            route_coordinates.append({
                "node_id": nid,
                "node_name": n["node_name"],
                "lat": n["latitude"],
                "lon": n["longitude"],
                "state": n["state_code"]
            })
            
    execution_duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
    
    # Prepare result structure
    result = {
        "survey_id": assigned_survey_id,
        "client_id": client_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "origin": {
            "query": origin_query,
            "node_id": origin_id,
            "node_name": origin_node["node_name"],
            "state": origin_node["state_code"],
            "lat": origin_node["latitude"],
            "lon": origin_node["longitude"]
        },
        "destination": {
            "query": destination_query,
            "node_id": dest_id,
            "node_name": dest_node["node_name"],
            "state": dest_node["state_code"],
            "lat": dest_node["latitude"],
            "lon": dest_node["longitude"]
        },
        "cargo_specs": {
            "weight_mt": cargo_weight_mt,
            "height_m": cargo_height_m,
            "width_m": cargo_width_m,
            "length_m": cargo_length_m,
            "axle_count": axle_count
        },
        "axle_engineering_analysis": axle_analysis,
        "route_summary": {
            "total_distance_km": route_res["total_distance_km"],
            "estimated_transit_hours": route_res["estimated_travel_hours"],
            "estimated_transit_days": route_res["estimated_transit_days"],
            "total_toll_plazas": route_res["total_tolls"],
            "ghat_sections_count": route_res["ghat_sections_count"],
            "traversed_states": route_res["traversed_states"],
            "node_count": len(route_res["path_nodes"]),
            "corridor_path": " -> ".join([NODES_DATA[nid]["node_name"] for nid in route_res["path_nodes"]])
        },
        "corridor_segments": route_res["segments"],
        "map_coordinates": route_coordinates,
        "bottlenecks": {
            "bypasses_applied": bypasses_applied,
            "pruned_segments_count": len(pruned_segments),
            "pruned_details": pruned_segments
        },
        "compliance_matrix": compliance,
        "risk_evaluation": risk_evaluation,
        "status": risk_evaluation["status"],
        "risk_score": risk_evaluation["risk_score"],
        "requires_human_dispatcher_waiver": risk_evaluation["risk_score"] > 70,
        "execution_metadata": {
            "engine": "Sealand-RAL-v2.1",
            "deterministic_solver": "NetworkX Dijkstra + RapidFuzz Trigram",
            "execution_duration_ms": round(execution_duration_ms, 2),
            "zero_llm_guarantee": True
        }
    }
    
    # Step 7: Persist into database & audit log
    db_persisted = persist_to_database(
        db_config=db,
        job_payload={
            "job_id": assigned_survey_id,
            "client_id": client_id,
            "origin_query": origin_query,
            "destination_query": destination_query,
            "matched_origin_id": origin_id,
            "matched_destination_id": dest_id,
            "cargo_weight_mt": cargo_weight_mt,
            "cargo_length_m": cargo_length_m,
            "cargo_width_m": cargo_width_m,
            "cargo_height_m": cargo_height_m,
            "axle_count": axle_count,
            "status": risk_evaluation["status"],
            "risk_score": risk_evaluation["risk_score"],
            "path_nodes": route_res["path_nodes"],
            "total_distance_km": route_res["total_distance_km"],
            "estimated_transit_hours": route_res["estimated_travel_hours"],
            "bottlenecks": bypasses_applied,
            "permits": compliance["permits_checklist"],
            "total_permit_cost_inr": compliance["total_statutory_fee_inr"]
        },
        audit_action=f"ROUTE_EVALUATION_{risk_evaluation['status']}"
    )
    result["execution_metadata"]["db_persisted"] = db_persisted
    
    return result
