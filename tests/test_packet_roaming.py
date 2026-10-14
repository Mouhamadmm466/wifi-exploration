"""Causal access, packet/frame accounting, and transition checks for v2."""
from dataclasses import replace
import math
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from packet_roaming import (BackgroundQueue, Controller, Observation, POLICIES,
                            SCENARIOS, _airtime_allocations, default_config, make_world, run)


class PacketModelTests(unittest.TestCase):
    def config(self, **updates):
        return dict(default_config(), duration_seconds=1.0, **updates)

    def clear_world(self, config):
        scenario = dict(SCENARIOS["corridor_slow"], background_users_per_ap=0,
                        path_start_m=0, path_end_m=0, ap_positions_m=[0, 1], signal_noise_db=0)
        return make_world(config, scenario, 20001)

    def test_background_packet_batches_conserve_partial_heads_and_overflow(self):
        queue = BackgroundQueue(1200, 3)
        queue.arrive(4)
        self.assertEqual(queue.dropped, 1)
        queue.serve(1300)
        self.assertEqual(queue.delivered, 1)
        self.assertEqual(queue.bytes, 2300)
        queue.arrive(2)
        self.assertEqual(queue.dropped, 2)
        queue.serve(1e9)
        self.assertEqual(queue.bytes, 0)
        self.assertEqual(queue.offered, queue.delivered + queue.dropped)

    def test_airtime_is_finite_and_unused_shares_are_redistributed(self):
        allocations = _airtime_allocations([0.001, 1.0, 1.0], 0.01)
        self.assertAlmostEqual(sum(allocations), 0.01)
        self.assertAlmostEqual(allocations[0], 0.001)
        self.assertAlmostEqual(allocations[1], 0.0045)
        self.assertAlmostEqual(allocations[2], 0.0045)

    def test_every_generated_packet_is_accounted_for_under_pressure(self):
        config = self.config(mobile_queue_packets=4, background_queue_packets=3,
                             handoff_failure_probability=0.5)
        world = make_world(config, "crowded", 20002)
        for policy in POLICIES:
            result = run(world, policy)
            self.assertEqual(result["packet_conservation_error"], 0)
            self.assertEqual(result["background_conservation_error"], 0)
            self.assertEqual(result["generated_voice_packets"], 50)
            self.assertEqual(result["generated_video_frames"], 30)
            self.assertGreater(result["queue_drops"], 0)
            self.assertLessEqual(result["ontime_packets"], result["delivered_packets"])

    def test_full_video_frame_requires_every_packet_by_deadline(self):
        config = self.config(video_deadline_seconds=0.01)
        world = self.clear_world(config)
        world = replace(world, frame_sizes=(200000,) * len(world.frame_sizes))
        result = run(world, "session_stay")
        self.assertEqual(result["video_complete_fraction"], 0.0)
        self.assertGreater(result["ontime_packets"], 0)
        self.assertEqual(result["generated_video_frames"], 30)
        self.assertEqual(result["video_freeze_count"], 1)
        self.assertEqual(result["video_freeze_fraction"], 1.0)

    def test_clear_service_and_drain_include_last_frames(self):
        config = self.config(video_deadline_seconds=0.25, drain_seconds=0.01,
                             scan_period_seconds=100)
        result = run(self.clear_world(config), "session_stay")
        self.assertEqual(result["video_complete_fraction"], 1.0)
        self.assertEqual(result["voice_missed_fraction"], 0.0)
        self.assertEqual(result["final_pending_packets"], 0)

    def test_handoff_fractional_time_and_failure_return_to_origin(self):
        def request_once(_, obs):
            return 1 if obs.time == 0 else obs.current_ap
        for fail in (0.0, 1.0):
            config = self.config(handoff_mean_seconds=0.025, handoff_jitter_seconds=0,
                handoff_failure_probability=fail, handoff_failure_extra_seconds=0.02,
                scan_period_seconds=100, flush_queue_on_handoff=False)
            with patch.object(Controller, "choose", request_once):
                result = run(self.clear_world(config), "predictive", keep_trace=True)
            self.assertEqual(result["handoffs"], 1)
            self.assertEqual(result["failed_handoffs"], int(fail))
            self.assertEqual(result["successful_handoffs"], 1-int(fail))
            self.assertAlmostEqual(result["handoff_blackout_seconds"], 0.025 + fail*0.02)
            self.assertEqual(result["decisions"][-1]["current_ap"], 0 if fail else 1)

    def test_fractional_completion_uses_target_link_not_old_link(self):
        config = self.config(handoff_mean_seconds=.025, handoff_jitter_seconds=0,
            handoff_failure_probability=0, flush_queue_on_handoff=False, scan_period_seconds=100)
        world = self.clear_world(config)
        world = replace(world, signals=((-40., -100.),) * len(world.signals))
        def request_once(_, obs):
            return 1 if obs.time == 0 else obs.current_ap
        with patch.object(Controller, "choose", request_once):
            result = run(world, "predictive")
        self.assertEqual(result["delivered_packets"], 0)
        self.assertEqual(result["successful_handoffs"], 1)

    def test_overlapping_scan_and_handoff_lose_union_not_sum(self):
        config = self.config(scan_period_seconds=.1, scan_duration_seconds=.025,
            handoff_mean_seconds=.025, handoff_jitter_seconds=0,
            handoff_failure_probability=0, flush_queue_on_handoff=False)
        world = self.clear_world(config)
        baseline = run(world, "session_stay", keep_trace=True)
        def request_once(_, obs):
            return 1 if abs(obs.time-.1) < 1e-8 else obs.current_ap
        with patch.object(Controller, "choose", request_once):
            result = run(world, "predictive", keep_trace=True)
        self.assertAlmostEqual(result["radio_blackout_union_seconds"], result["scan_blackout_seconds"])
        self.assertAlmostEqual(result["handoff_blackout_seconds"], .025)
        self.assertEqual(result["voice_ontime"], baseline["voice_ontime"])
        self.assertEqual(result["video_complete"], baseline["video_complete"])

    def test_packet_completed_exactly_at_deadline_is_on_time(self):
        config = self.config(voice_deadline_seconds=.01, scan_period_seconds=100)
        world = replace(self.clear_world(config), frame_sizes=())
        result = run(world, "session_stay")
        self.assertEqual(result["generated_voice_packets"], result["ontime_packets"])
        self.assertAlmostEqual(result["conditional_packet_delay_p95_ms"], 10.0)

    def test_no_current_truth_enters_later_delayed_observations(self):
        config = self.config(report_jitter_seconds=0, report_delay_seconds=0.2)
        result = run(make_world(config, "bursty", 20001), "predictive", keep_trace=True)
        for obs in result["decisions"]:
            t = obs["time"]
            self.assertTrue(all(source <= t for source in obs["signal_sources"]))
            self.assertTrue(all(source == 0 or source <= t - config["signal_delay_seconds"] + 1e-8
                                for source in obs["signal_sources"]))
            self.assertTrue(all(source == 0 or source <= t - 0.2 + 1e-8 for source in obs["load_sources"]))
            self.assertLessEqual(obs["own_miss_source"], max(0.0, t - 0.2) + 1e-8)

    def test_future_world_changes_cannot_change_earlier_decisions(self):
        world = make_world(self.config(), "bursty", 20001)
        cutoff = 25  # 0.5 seconds on the fixed 20 ms exogenous grid.
        changed = replace(world,
            signals=world.signals[:cutoff] + tuple((-100.0,)*5+(-40.0,) for _ in world.signals[cutoff:]),
            background_arrivals=world.background_arrivals[:cutoff] + tuple((1000,)*12 for _ in world.background_arrivals[cutoff:]))
        for policy in ("rssi", "app_myopic", "predictive"):
            original = run(world, policy, keep_trace=True)["decisions"]
            modified = run(changed, policy, keep_trace=True)["decisions"]
            self.assertEqual([r for r in original if r["time"] < .5], [r for r in modified if r["time"] < .5])

    def test_random_streams_are_paired_and_do_not_depend_on_policy_order(self):
        world = make_world(self.config(), "bursty", 20001)
        first = run(world, "predictive")
        run(world, "rssi")
        self.assertEqual(first, run(world, "predictive"))
        self.assertEqual(world, make_world(self.config(), "bursty", 20001))

    def test_time_step_refinement_preserves_external_processes(self):
        coarse = make_world(self.config(dt_seconds=0.01), "bursty", 20001)
        fine = make_world(self.config(dt_seconds=0.005), "bursty", 20001)
        for attribute in ("signals", "background_arrivals", "report_events", "handoff_uniforms", "handoff_durations", "frame_sizes"):
            self.assertEqual(getattr(coarse, attribute), getattr(fine, attribute))

    def test_guard_uses_delayed_risk_and_has_an_isolated_ablation(self):
        obs = Observation(.2, 0, (-75., -55.), (.1, .2), (0., 0.), (.95, .5),
                          (.3, .4), (5, 1), (0., 0.), .8, .0)
        guarded = Controller("predictive", self.config())
        guarded.last_switch = 0
        unguarded = Controller("no_guard", self.config())
        unguarded.last_switch = 0
        self.assertEqual(guarded.choose(obs), 1)
        self.assertEqual(unguarded.choose(obs), 0)

    def test_dwell_ablation_removes_only_the_trend_based_horizon(self):
        obs = Observation(2., 0, (-65., -60.), (0., 0.), (0., -50.), (.5, .5),
                          (0., 0.), (1, 1), (0., 0.), 0., 1.)
        config = self.config(video_mbps=20)
        params = dict(cost_weight=2.0, age_weight=0)
        self.assertEqual(Controller("predictive", config, params).choose(obs), 0)
        self.assertEqual(Controller("no_dwell", config, params).choose(obs), 1)


if __name__ == "__main__":
    unittest.main()
