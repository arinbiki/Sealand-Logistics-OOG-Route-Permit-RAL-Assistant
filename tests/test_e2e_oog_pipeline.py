"""
Sealand Logistics - OOG Route & Permit RAG Assistant
End-to-End Pipeline & Deterministic Constraint Solver Test Suite
"""

import unittest
import sys
import os

# Add scripts directory
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

from inexpensive_script import (
    main as solve_oog,
    fuzzy_match_node,
    calculate_multiaxle_loading,
    build_and_prune_graph,
    compute_optimal_route,
    evaluate_rto_compliance,
    compute_oog_risk_score,
    NODES_DATA
)

class TestOOGPipeline(unittest.TestCase):

    def test_01_fuzzy_node_matching(self):
        """Test deterministic resolution of messy origin/destination queries."""
        # Seaports
        vtz = fuzzy_match_node("Vizag", NODES_DATA)
        self.assertIsNotNone(vtz)
        self.assertEqual(vtz["node_id"], "PORT_CODE_INVTZ")

        vtz2 = fuzzy_match_node("Visakhapatnam Harbor Dock", NODES_DATA)
        self.assertEqual(vtz2["node_id"], "PORT_CODE_INVTZ")

        maa = fuzzy_match_node("Madras Port", NODES_DATA)
        self.assertEqual(maa["node_id"], "PORT_CODE_INMAA")

        bom = fuzzy_match_node("Nhava Sheva JNPT", NODES_DATA)
        self.assertEqual(bom["node_id"], "PORT_CODE_INBOM")

        # Inland Hubs
        rpr = fuzzy_match_node("Bhilai Raipur", NODES_DATA)
        self.assertEqual(rpr["node_id"], "HUB_RAIPUR")

        ngp = fuzzy_match_node("MIHAN Logistics Nagpur", NODES_DATA)
        self.assertEqual(ngp["node_id"], "HUB_NAGPUR")

    def test_02_multiaxle_physics_loading(self):
        """Test Gross Vehicle Weight and hydraulic axle line loading under IRC:SP:35."""
        # Case A: 85MT cargo on 10 axles -> (85 + 35 + 12) / 10 = 13.2 MT/axle -> Permissible (<13.5)
        res_a = calculate_multiaxle_loading(cargo_weight_mt=85.0, axle_count=10)
        self.assertFalse(res_a["axle_overloaded"])
        self.assertLessEqual(res_a["axle_load_mt"], 13.5)
        self.assertGreater(res_a["axle_loading_safety_margin_pct"], 0)

        # Case B: 120MT cargo on 8 axles -> (120 + 28 + 12) / 8 = 20.0 MT/axle -> Overloaded (>13.5)
        res_b = calculate_multiaxle_loading(cargo_weight_mt=120.0, axle_count=8)
        self.assertTrue(res_b["axle_overloaded"])
        self.assertGreater(res_b["axle_load_mt"], 13.5)
        self.assertGreaterEqual(res_b["recommended_min_axle_count"], 12)

    def test_03_bridge_pruning_and_bypass_routing(self):
        """Test physical bridge constraint pruning and automatic bypass detour."""
        # 1. 50MT cargo can cross Nagavali bridge directly (limit 65MT)
        prune_light = build_and_prune_graph(
            cargo_weight_mt=50.0,
            cargo_height_m=4.5,
            cargo_width_m=3.5,
            cargo_length_m=20.0,
            allow_bypasses=True
        )
        route_light = compute_optimal_route(
            prune_light["graph"],
            "PORT_CODE_INVTZ",
            "HUB_RAIPUR"
        )
        self.assertIsNotNone(route_light)
        # Direct route via Jagdalpur is shorter (~605 km)
        self.assertLess(route_light["total_distance_km"], 650.0)

        # 2. 90MT cargo CANNOT cross Nagavali bridge (limit 65MT), must take detour via Sambalpur NH-26 / NH-53
        prune_heavy = build_and_prune_graph(
            cargo_weight_mt=90.0,
            cargo_height_m=4.5,
            cargo_width_m=3.5,
            cargo_length_m=20.0,
            allow_bypasses=True
        )
        route_heavy = compute_optimal_route(
            prune_heavy["graph"],
            "PORT_CODE_INVTZ",
            "HUB_RAIPUR"
        )
        self.assertIsNotNone(route_heavy)
        self.assertIn("JUNC_SAMBALPUR", route_heavy["path_nodes"])
        self.assertGreater(route_heavy["total_distance_km"], 700.0)

    def test_04_rto_compliance_and_escort_rules(self):
        """Test deterministic state transit fee schedule and escort mandates."""
        compliance = evaluate_rto_compliance(
            traversed_states=["AP", "OD", "CG"],
            total_distance_km=730.0,
            cargo_weight_mt=85.0,
            cargo_width_m=4.2,
            cargo_height_m=5.1,
            cargo_length_m=24.5
        )
        # Central MoRTH + 3 states = 4 permits
        self.assertEqual(len(compliance["permits_checklist"]), 4)
        self.assertGreater(compliance["total_statutory_fee_inr"], 30000.0)
        self.assertGreaterEqual(compliance["aggregate_survey_sla_days"], 5)
        # Width 4.2m >= 4.0m mandates police convoy
        self.assertTrue(compliance["requires_police_convoy"])
        self.assertGreater(len(compliance["escort_mandates"]), 0)

    def test_05_deterministic_risk_scoring(self):
        """Test risk score calculation thresholds."""
        # Safe consignment
        score_safe = compute_oog_risk_score(
            cargo_weight_mt=45.0,
            cargo_height_m=4.2,
            cargo_width_m=3.2,
            cargo_length_m=18.0,
            axle_info={"axle_overloaded": False, "axle_load_mt": 9.5},
            route_info={"ghat_sections_count": 0},
            bypasses_applied=[],
            compliance_info={"night_travel_restrictions": []}
        )
        self.assertLessEqual(score_safe["risk_score"], 70)
        self.assertEqual(score_safe["status"], "APPROVED_AUTO_PERMIT")

        # High-risk consignment (130MT, overloaded axles, ghat traversal, tight height)
        score_high = compute_oog_risk_score(
            cargo_weight_mt=130.0,
            cargo_height_m=5.3,
            cargo_width_m=4.6,
            cargo_length_m=32.0,
            axle_info={"axle_overloaded": True, "axle_load_mt": 14.8},
            route_info={"ghat_sections_count": 2},
            bypasses_applied=[{"bypass_penalty_km": 140.0}],
            compliance_info={"night_travel_restrictions": ["AP", "OD"]}
        )
        self.assertGreater(score_high["risk_score"], 70)
        self.assertEqual(score_high["status"], "FLAGGED_FOR_DISPATCHER_SURVEY")
        self.assertEqual(score_high["recommended_action"], "HUMAN_SURVEY_REQUIRED")

    def test_06_end_to_end_solver_execution(self):
        """Test full flagship main() solver execution from input to clearance pass."""
        res = solve_oog(
            origin_query="Visakhapatnam Port",
            destination_query="Raipur Logistics Hub",
            cargo_weight_mt=85.0,
            cargo_height_m=5.1,
            cargo_width_m=4.2,
            cargo_length_m=24.5,
            axle_count=10,
            allow_bypasses=True
        )

        self.assertIn("survey_id", res)
        self.assertEqual(res["origin"]["node_id"], "PORT_CODE_INVTZ")
        self.assertEqual(res["destination"]["node_id"], "HUB_RAIPUR")
        self.assertIn("route_summary", res)
        self.assertGreater(res["route_summary"]["total_distance_km"], 600)
        self.assertIn("compliance_matrix", res)
        self.assertIn("execution_metadata", res)
        self.assertTrue(res["execution_metadata"]["zero_llm_guarantee"])
        self.assertLess(res["execution_metadata"]["execution_duration_ms"], 100.0) # Sub-100ms guarantee

if __name__ == "__main__":
    unittest.main()
