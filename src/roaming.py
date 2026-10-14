"""An abstract decision model, not an IEEE 802.11 or packet simulator.

All traffic, radio, and delay equations are assumed. They do not reproduce a
particular device. The controller API exposes only present/past observations.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import random
from typing import Sequence


POLICIES = ("rssi", "load_aware", "app_myopic", "proposed", "no_cost", "no_age_penalty")
SCENARIOS = ("balanced", "hotspots", "overloaded", "abrupt", "reversal", "short_dwell")


def clip(value: float, low: float, high: float) -> float:
    return min(high, max(low, value))


@dataclass(frozen=True)
class Link:
    quality: float
    delivery_fraction: float
    residual_mbps: float
    rtt_ms: float
    radio_loss: float


def link_service(rssi: float, load: float, profile: dict, radio: dict) -> Link:
    """An assumed mapping, used identically for prediction and true service.

    This perfect knowledge of the mapping favors all model-based controllers.
    Stale reports, rather than model estimation error, are the main uncertainty.
    """
    phy = min(radio["maximum_rate_mbps"], radio["maximum_rate_mbps"] *
              10.0 ** ((rssi - radio["rate_reference_rssi_dbm"]) / radio["rate_drop_scale_db"]))
    residual = phy * (1.0 - load)
    radio_loss = clip(0.002 + 0.20 / (1.0 + math.exp((rssi + 76.0) / 3.0)) +
                      0.10 * (max(0.0, load - 0.8) / 0.2) ** 2, 0.0, 1.0)
    delivery = min(1.0, residual / profile["demand_mbps"]) * (1.0 - radio_loss)
    rtt = min(5000.0, 5.0 + 4.0 / (1.0 - load) ** 2 + 120.0 / max(phy, 0.05))
    latency_adequacy = clip(2.0 - rtt / profile["rtt_budget_ms"], 0.0, 1.0)
    loss_adequacy = clip(2.0 - radio_loss / profile["radio_loss_budget"], 0.0, 1.0)
    lw, pw = profile["latency_weight"], profile["loss_weight"]
    quality = delivery * (1.0 - lw - pw + lw * latency_adequacy + pw * loss_adequacy)
    return Link(quality, delivery, residual, rtt, radio_loss)


def position(scenario: str, t: float, duration: float) -> float:
    f = clip(t / duration, 0.0, 1.0)
    if scenario == "reversal":
        # Three changes of direction over the same corridor.
        phase = (f * 4.0) % 2.0
        return -8.0 + 136.0 * (phase if phase <= 1.0 else 2.0 - phase)
    if scenario == "short_dwell":
        # A deliberately fast shuttle: a stressful, non-pedestrian control.
        return 60.0 + 54.0 * math.sin(2.0 * math.pi * t / 28.0)
    return -8.0 + 136.0 * f


def base_load(scenario: str, ap: int, t: float, phase: float) -> float:
    if scenario == "balanced":
        return 0.18
    if scenario == "overloaded":
        return 0.87 + 0.06 * math.sin(t / 13.0 + phase + ap)
    if scenario == "abrupt":
        epoch = math.floor(t / 12.0)
        return 0.88 if (ap + epoch) % 3 == 0 else 0.28
    if scenario == "short_dwell":
        return 0.25 + (0.38 if ap % 2 else 0.0)
    # Alternating busy and quiet APs; drift is independent of the focal client.
    return (0.62 if ap % 2 else 0.24) + 0.10 * math.sin(t / 17.0 + phase + ap)


@dataclass(frozen=True)
class Trace:
    scenario: str
    seed: int
    dt: float
    start: int
    steps: int
    rssi: tuple[tuple[float, ...], ...]
    load: tuple[tuple[float, ...], ...]


def make_trace(config: dict, scenario: str, seed: int) -> Trace:
    # Do not use Python's process-randomized hash for reproducibility.
    rng = random.Random(seed * 100003 + SCENARIOS.index(scenario) * 7919)
    dt = config["step_seconds"]
    steps = round(config["duration_seconds"] / dt)
    start = math.ceil((max(config["telemetry_delays_seconds"]) +
                       config["report_period_seconds"]) / dt)
    radio = config["radio_parameters"]
    count = len(config["ap_positions_m"])
    signal_noise, load_noise = [0.0] * count, [0.0] * count
    phases = [rng.uniform(0.0, 2.0 * math.pi) for _ in range(count)]
    signals, loads = [], []
    for index in range(start + steps):
        t = (index - start) * dt
        x = position(scenario, t, config["duration_seconds"])
        sr, lr = [], []
        for ap, ap_x in enumerate(config["ap_positions_m"]):
            signal_noise[ap] = (radio["signal_ar_coefficient"] * signal_noise[ap] +
                                rng.gauss(0.0, radio["signal_innovation_std_db"]))
            load_noise[ap] = (radio["load_ar_coefficient"] * load_noise[ap] +
                              rng.gauss(0.0, radio["load_innovation_std"]))
            distance = math.hypot(x - ap_x, config["corridor_offset_m"])
            sr.append(radio["reference_rssi_dbm"] - 10.0 * radio["path_loss_exponent"] *
                      math.log10(max(distance, 1.0)) + signal_noise[ap])
            lr.append(clip(base_load(scenario, ap, t, phases[ap]) + load_noise[ap], 0.03, 0.97))
        signals.append(tuple(sr))
        loads.append(tuple(lr))
    return Trace(scenario, seed, dt, start, steps, tuple(signals), tuple(loads))


@dataclass(frozen=True)
class Observation:
    """No future trace, client position, or future traffic enters this interface."""
    time: float
    current_ap: int
    rssi: Sequence[float]
    quality: Sequence[float]
    residual_mbps: Sequence[float]
    age_seconds: Sequence[float]
    blackout_seconds: float


@dataclass(frozen=True)
class Parameters:
    rssi_hysteresis_db: float = 4.0
    load_relative_margin: float = 0.15
    horizon_seconds: float = 3.0
    age_penalty: float = 0.15


class Controller:
    def __init__(self, policy: str, config: dict, params: Parameters):
        if policy not in POLICIES:
            raise ValueError(policy)
        self.policy, self.config, self.params = policy, config, params
        self.last_switch = -math.inf

    def choose(self, obs: Observation) -> int:
        current = obs.current_ap
        emergency = obs.rssi[current] < self.config["emergency_rssi_dbm"]
        if not emergency and obs.time - self.last_switch < self.config["minimum_residence_seconds"]:
            return current
        if self.policy == "rssi":
            target = max(range(len(obs.rssi)), key=obs.rssi.__getitem__)
            threshold = 0.0 if emergency else self.params.rssi_hysteresis_db
            change = obs.rssi[target] > obs.rssi[current] + threshold
        elif self.policy == "load_aware":
            target = max(range(len(obs.rssi)), key=obs.residual_mbps.__getitem__)
            margin = 0.0 if emergency else self.params.load_relative_margin
            change = obs.residual_mbps[target] > obs.residual_mbps[current] * (1.0 + margin)
        else:
            scores = list(obs.quality)
            if self.policy != "app_myopic":
                for ap in range(len(scores)):
                    if ap == current:
                        continue
                    if self.policy != "no_cost":
                        # Average quality over a fixed, assumed holding interval.
                        scores[ap] *= max(0.0, 1.0 - obs.blackout_seconds / self.params.horizon_seconds)
                    if self.policy != "no_age_penalty":
                        age = obs.age_seconds[ap]
                        scores[ap] -= self.params.age_penalty * age / (age + self.config["age_penalty_scale_seconds"])
            target = max(range(len(scores)), key=scores.__getitem__)
            margin = 0.0 if emergency else self.config["quality_margin"]
            change = scores[target] > scores[current] + margin
        if change and target != current:
            self.last_switch = obs.time
            return target
        return current


@dataclass(frozen=True)
class Prepared:
    trace: Trace
    profile: dict
    signal: tuple[tuple[float, ...], ...]
    truth: tuple[tuple[Link, ...], ...]
    reported: tuple[tuple[Link, ...], ...]
    report_ages: tuple[float, ...]
    report_indices: tuple[int, ...]


def prepare(config: dict, trace: Trace, profile_name: str, telemetry_delay: float) -> Prepared:
    """Cache computations; controllers cannot access the containing trace object."""
    profile, radio = config["profiles_parameters"][profile_name], config["radio_parameters"]
    period_steps = round(config["report_period_seconds"] / trace.dt)
    delay_steps = round(telemetry_delay / trace.dt)
    truth, reported, ages, indices, signal = [], [], [], [], []
    for step in range(trace.steps):
        index = trace.start + step
        report_index = trace.start + (step // period_steps) * period_steps - delay_steps
        if report_index > index or report_index < 0:
            raise ValueError("A report must refer to an available past or present sample")
        sr = trace.rssi[index]
        signal.append(sr)
        truth.append(tuple(link_service(s, load, profile, radio) for s, load in zip(sr, trace.load[index])))
        reported.append(tuple(link_service(s, load, profile, radio) for s, load in zip(sr, trace.load[report_index])))
        ages.append((index - report_index) * trace.dt)
        indices.append(report_index)
    return Prepared(trace, profile, tuple(signal), tuple(truth), tuple(reported), tuple(ages), tuple(indices))


def run(prepared: Prepared, config: dict, policy: str, params: Parameters,
        blackout_seconds: float, keep_decisions: bool = False) -> dict:
    trace, dt = prepared.trace, prepared.trace.dt
    controller = Controller(policy, config, params)
    current = max(range(len(prepared.signal[0])), key=prepared.signal[0].__getitem__)
    remaining = 0.0
    quality_integral = delivered_integral = rtt_integral = blackout_total = 0.0
    handoffs = pingpong = 0
    previous_origin, previous_switch = None, -math.inf
    decisions = []
    for step in range(trace.steps):
        t = step * dt
        if remaining <= 1e-12:
            # All controllers receive the same information rule. Serving-AP
            # quality is fresh; alternative load reports may be stale.
            quality = [link.quality for link in prepared.reported[step]]
            capacity = [link.residual_mbps for link in prepared.reported[step]]
            ages = [prepared.report_ages[step]] * len(quality)
            quality[current] = prepared.truth[step][current].quality
            capacity[current] = prepared.truth[step][current].residual_mbps
            ages[current] = 0.0
            obs = Observation(t, current, prepared.signal[step], quality, capacity, ages, blackout_seconds)
            target = controller.choose(obs)
            if target != current:
                if target == previous_origin and t - previous_switch <= 5.0:
                    pingpong += 1
                previous_origin, previous_switch = current, t
                current = target
                handoffs += 1
                remaining = blackout_seconds
        if keep_decisions:
            decisions.append(current)
        blocked = min(dt, remaining)
        remaining = max(0.0, remaining - blocked)
        active = dt - blocked
        link = prepared.truth[step][current]
        blackout_total += blocked
        quality_integral += active * link.quality
        delivered_integral += active * link.delivery_fraction
        rtt_integral += active * link.delivery_fraction * link.rtt_ms
    elapsed = trace.steps * dt
    result = {
        "service_deficit": 1.0 - quality_integral / elapsed,
        "unserved_fraction": 1.0 - delivered_integral / elapsed,
        "delivered_mbps": prepared.profile["demand_mbps"] * delivered_integral / elapsed,
        "handoffs": handoffs,
        "pingpong": pingpong,
        "blackout_seconds_total": blackout_total,
        "blackout_fraction": blackout_total / elapsed,
        "delivered_weighted_rtt_ms": rtt_integral / delivered_integral if delivered_integral else math.nan,
    }
    if keep_decisions:
        result["decisions"] = decisions
    return result
