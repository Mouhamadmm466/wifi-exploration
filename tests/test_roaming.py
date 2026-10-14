"""Checks on accounting, information access, and policy counterfactuals."""
from dataclasses import replace
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from roaming import Controller, Link, Observation, Parameters, Prepared, Trace, make_trace, prepare, run


class RoamingTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT / "configs/study.json").read_text())
        self.config["duration_seconds"] = 12.0

    def test_identical_seeds_pair_traces_and_different_seeds_differ(self):
        first = make_trace(self.config, "abrupt", 1001)
        self.assertEqual(first, make_trace(self.config, "abrupt", 1001))
        self.assertNotEqual(first.load, make_trace(self.config, "abrupt", 1002).load)

    def test_reports_are_past_or_present_and_exact_age_is_recorded(self):
        trace = make_trace(self.config, "abrupt", 1001)
        prepared = prepare(self.config, trace, "realtime", 8.0)
        for step, index in enumerate(prepared.report_indices):
            self.assertLessEqual(index, trace.start + step)
            self.assertGreaterEqual(index, 0)
            self.assertEqual(prepared.report_ages[step], (trace.start + step - index) * trace.dt)
            self.assertGreaterEqual(prepared.report_ages[step], 8.0)
            self.assertLess(prepared.report_ages[step], 9.0)

    def test_changing_future_trace_cannot_change_past_decisions(self):
        trace = make_trace(self.config, "hotspots", 1001)
        cutoff = 24
        boundary = trace.start + cutoff
        changed = replace(trace,
                          rssi=trace.rssi[:boundary] + tuple(tuple(-50.0 if ap == 5 else -100.0 for ap in range(6))
                                                          for _ in trace.rssi[boundary:]),
                          load=trace.load[:boundary] + tuple((0.95, 0.95, 0.95, 0.95, 0.95, 0.03)
                                                          for _ in trace.load[boundary:]))
        for policy in ("rssi", "load_aware", "app_myopic", "proposed", "no_cost", "no_age_penalty"):
            original = run(prepare(self.config, trace, "realtime", 2.0), self.config, policy, Parameters(), 0.2, True)
            modified = run(prepare(self.config, changed, "realtime", 2.0), self.config, policy, Parameters(), 0.2, True)
            self.assertEqual(original["decisions"][:cutoff], modified["decisions"][:cutoff])

    def test_fractional_blackout_is_not_rounded_to_step(self):
        perfect = Link(1.0, 1.0, 100.0, 1.0, 0.0)
        trace = Trace("balanced", 0, 0.25, 0, 4, ((-40.0, -50.0),) * 4, ((0.0, 0.0),) * 4)
        prepared = Prepared(trace, {"demand_mbps": 4.0}, trace.rssi,
                            ((perfect, perfect),) * 4, ((perfect, perfect),) * 4, (0.0,) * 4, tuple(range(4)))
        # One forced transition at t=0; it may span several time steps.
        def choose(_, obs):
            return 1
        for blackout in (0.02, 0.2, 0.3, 0.8):
            with patch.object(Controller, "choose", choose):
                result = run(prepared, self.config, "proposed", Parameters(), blackout)
            self.assertAlmostEqual(result["service_deficit"], blackout)
            self.assertAlmostEqual(result["unserved_fraction"], blackout)
            self.assertAlmostEqual(result["blackout_seconds_total"], blackout)
            self.assertAlmostEqual(result["delivered_mbps"], 4.0 * (1.0 - blackout))
            self.assertEqual(result["handoffs"], 1)

    def test_emergency_bypasses_residence_rule(self):
        for policy in ("rssi", "load_aware", "app_myopic", "proposed", "no_cost", "no_age_penalty"):
            controller = Controller(policy, self.config, Parameters())
            controller.last_switch = 0.0
            obs = Observation(0.5, 0, (-70.0, -50.0), (0.2, 0.9), (1.0, 40.0), (0.0, 0.0), 0.02)
            self.assertEqual(controller.choose(obs), 0)
            self.assertEqual(controller.choose(replace(obs, rssi=(-80.0, -50.0))), 1)

    def test_cost_and_age_ablations_change_only_their_penalties(self):
        obs = Observation(3.0, 0, (-65.0, -60.0), (0.8, 0.85), (8.0, 10.0), (0.0, 0.0), 0.2)
        params = Parameters(horizon_seconds=1.0, age_penalty=0.15)
        self.assertEqual(Controller("proposed", self.config, params).choose(obs), 0)
        self.assertEqual(Controller("no_cost", self.config, params).choose(obs), 1)
        obs = replace(obs, quality=(0.8, 0.9), age_seconds=(0.0, 8.0), blackout_seconds=0.0)
        self.assertEqual(Controller("proposed", self.config, params).choose(obs), 0)
        self.assertEqual(Controller("no_age_penalty", self.config, params).choose(obs), 1)

    def test_emergency_is_not_a_guaranteed_rescue(self):
        # Emergency removes cooldown/margin, but leaves cost and age penalties.
        obs = Observation(0.5, 0, (-80.0, -50.0), (0.001, 0.02), (0.01, 0.08), (0.0, 8.0), 0.2)
        params = Parameters(horizon_seconds=8.0, age_penalty=0.05)
        controller = Controller("proposed", self.config, params)
        controller.last_switch = 0.0
        self.assertEqual(controller.choose(obs), 0)
        self.assertEqual(Controller("no_age_penalty", self.config, params).choose(obs), 1)

    def test_metric_bounds_and_bulk_service_equals_delivery(self):
        trace = make_trace(self.config, "overloaded", 1001)
        prepared = prepare(self.config, trace, "bulk", 8.0)
        for policy in ("rssi", "load_aware", "app_myopic", "proposed", "no_cost", "no_age_penalty"):
            result = run(prepared, self.config, policy, Parameters(), 0.2)
            self.assertGreaterEqual(result["service_deficit"], 0.0)
            self.assertLessEqual(result["service_deficit"], 1.0)
            self.assertAlmostEqual(result["service_deficit"], result["unserved_fraction"])
            self.assertAlmostEqual(result["delivered_mbps"], 20.0 * (1.0 - result["unserved_fraction"]))


if __name__ == "__main__":
    unittest.main()
