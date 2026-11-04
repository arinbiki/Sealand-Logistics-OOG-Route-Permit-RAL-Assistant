"""
Backend runnable for Windmill Raw App: get_preset_scenarios
Returns 6 industry-standard ODC/OOG heavy consignment scenarios.
"""

def main() -> list:
    return [
        {
            "id": "SCN-01-VIZAG-RAIPUR",
            "name": "Super-Heavy Power Turbine (120 MT)",
            "origin": "Visakhapatnam Port",
            "destination": "Raipur Logistics Hub",
            "cargo_weight_mt": 120.0,
            "cargo_length_m": 28.0,
            "cargo_width_m": 4.6,
            "cargo_height_m": 5.25,
            "axle_count": 14,
            "notes": "Triggers Nagavali bridge bypass via Sambalpur NH-53; requires multi-state night escort."
        },
        {
            "id": "SCN-02-CHENNAI-BANGALORE",
            "name": "High-Voltage Transformer (85 MT)",
            "origin": "Chennai Port",
            "destination": "Bangalore Nelamangala Hub",
            "cargo_weight_mt": 85.0,
            "cargo_length_m": 22.0,
            "cargo_width_m": 3.8,
            "cargo_height_m": 4.65,
            "axle_count": 10,
            "notes": "NH-48 Palar River bridge transit; standard multi-axle loading within safe margins."
        },
        {
            "id": "SCN-03-JNPT-NAGPUR",
            "name": "Petrochemical Distillation Column (95 MT)",
            "origin": "JNPT Mumbai",
            "destination": "Nagpur Multimodal Hub",
            "cargo_weight_mt": 95.0,
            "cargo_length_m": 34.0,
            "cargo_width_m": 4.4,
            "cargo_height_m": 5.15,
            "axle_count": 12,
            "notes": "Blocked by Kasara Ghat 4.80m ROB; automatically detours via Pune-Solapur-Nagpur."
        },
        {
            "id": "SCN-04-MUNDRA-AHMEDABAD",
            "name": "Wind Turbine Nacelle & Hub (140 MT)",
            "origin": "Mundra Port",
            "destination": "Ahmedabad Sanand Hub",
            "cargo_weight_mt": 140.0,
            "cargo_length_m": 32.0,
            "cargo_width_m": 4.8,
            "cargo_height_m": 5.4,
            "axle_count": 16,
            "notes": "NH-947 heavy freight corridor; requires wide-load lane closure and police patrol."
        },
        {
            "id": "SCN-05-KOLKATA-JAMSHEDPUR",
            "name": "Steel Rolling Mill Stand (70 MT)",
            "origin": "Kolkata Port",
            "destination": "Jamshedpur Tata Steel Complex",
            "cargo_weight_mt": 70.0,
            "cargo_length_m": 18.5,
            "cargo_width_m": 3.5,
            "cargo_height_m": 4.4,
            "axle_count": 8,
            "notes": "Crosses WB into Jharkhand; clean path with fast 3-day permit turnaround."
        },
        {
            "id": "SCN-06-PARADIP-JHARSUGUDA",
            "name": "Thermal Boiler Steam Drum (110 MT)",
            "origin": "Paradip Port",
            "destination": "Jharsuguda Industrial Hub",
            "cargo_weight_mt": 110.0,
            "cargo_length_m": 26.0,
            "cargo_width_m": 4.1,
            "cargo_height_m": 4.95,
            "axle_count": 12,
            "notes": "Bypasses Mahanadi 80MT rail-cum-road bridge via Sambalpur heavy ring road."
        }
    ]
