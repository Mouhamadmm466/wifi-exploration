"""Packet-queue roaming abstraction. This is not an IEEE 802.11 MAC model."""
from __future__ import annotations
from dataclasses import dataclass
from collections import deque
import hashlib
import heapq
import json
import math
import random

POLICIES = ("rssi", "load_aware", "app_myopic", "cautious_v1", "session_stay",
            "predictive", "no_dwell", "no_guard", "no_cost", "no_age")
DEFAULT_PARAMETERS = dict(rssi_margin_db=3.0, load_margin=0.10, app_margin=0.05,
    minimum_residence_seconds=1.0, planning_horizon_seconds=3.0, cost_weight=1.0,
    age_weight=0.08, guard_miss_fraction=0.25, guard_rssi_dbm=-78.0, dwell_min_seconds=0.25)


def default_config():
    return dict(duration_seconds=60.0, dt_seconds=0.01, decision_period_seconds=0.1,
        drain_seconds=0.25, voice_interval_seconds=0.02, voice_packet_bytes=160,
        voice_deadline_seconds=0.06, video_fps=30.0, video_mbps=2.4,
        video_packet_bytes=1200, video_deadline_seconds=0.15,
        scan_period_seconds=1.0, scan_duration_seconds=0.012, signal_delay_seconds=0.04,
        report_period_seconds=0.5, report_delay_seconds=0.3, report_jitter_seconds=0.15,
        report_noise_std=0.05, handoff_mean_seconds=0.08, handoff_jitter_seconds=0.04,
        handoff_failure_probability=0.03, handoff_failure_extra_seconds=0.12,
        estimated_handoff_multiplier=1.0, background_packet_bytes=1200,
        background_queue_packets=256, mobile_queue_packets=256,
        background_rate_mbps=54.0, maximum_rate_mbps=54.0,
        packet_expiry=True, flush_queue_on_handoff=True,
        freeze_run_frames=6, exogenous_step_seconds=0.02)


def _scenario(name, mobility="linear", speed=1.0, load=0.35, pattern="flat", users=2):
    return dict(name=name, ap_positions_m=[0, 24, 48, 72, 96, 120], path_start_m=-4.0,
        path_end_m=124.0, mobility=mobility, speed_mps=speed, background_users_per_ap=users,
        base_load=load, load_pattern=pattern, burst_period_seconds=8.0,
        signal_noise_db=1.2, lateral_m=3.0)


SCENARIOS = {
    "corridor_slow": _scenario("corridor_slow"),
    "short_dwell": _scenario("short_dwell", "sine", 5.0, 0.55, "alternating"),
    "reversal": _scenario("reversal", "shuttle", 2.5, 0.55, "alternating"),
    "hotspot": _scenario("hotspot", "linear", 1.2, 0.65, "alternating"),
    "bursty": _scenario("bursty", "linear", 1.4, 0.55, "bursty"),
    "crowded": _scenario("crowded", "linear", 1.0, 0.95, "flat", 6),
}


def _clip(value, low, high):
    return max(low, min(high, value))


def _seed(seed, label):
    return int.from_bytes(hashlib.sha256(f"{seed}:{label}".encode()).digest()[:8], "big")


def _rate(signal, maximum):
    return 0.0 if signal < -85.0 else min(maximum, maximum * 10.0 ** ((signal + 55.0) / 20.0))


def _position(scenario, t):
    lo, hi = scenario["path_start_m"], scenario["path_end_m"]
    length = max(1e-9, hi - lo)
    distance = scenario["speed_mps"] * t
    if scenario["mobility"] == "shuttle":
        phase = distance % (2.0 * length)
        return lo + (phase if phase <= length else 2.0 * length - phase)
    if scenario["mobility"] == "sine":
        # speed_mps is the maximum speed of this sinusoidal route.
        return (lo + hi) / 2.0 + length / 2.0 * math.sin(2.0 * distance / length)
    return min(hi, lo + distance)


def _poisson(rng, mean):
    # Normal approximation for large packet batches; exact Poisson for small.
    if mean >= 10.0:
        return max(0, round(rng.gauss(mean, math.sqrt(mean))))
    threshold, product, count = math.exp(-mean), 1.0, 0
    while product > threshold:
        product *= rng.random()
        count += 1
    return max(0, count - 1)


@dataclass(frozen=True)
class World:
    config: dict
    scenario: dict
    seed: int
    fingerprint: str
    signals: tuple
    background_arrivals: tuple
    report_events: tuple
    handoff_uniforms: tuple
    handoff_durations: tuple
    frame_sizes: tuple


def make_world(config, scenario, seed):
    config = dict(default_config(), **config)
    scenario = dict(SCENARIOS[scenario] if isinstance(scenario, str) else scenario)
    if scenario["mobility"] not in ("linear", "shuttle", "sine"):
        raise ValueError("Unknown mobility")
    if config["dt_seconds"] <= 0 or config["dt_seconds"] > 0.05:
        raise ValueError("Use a positive simulation step no greater than 50 ms")
    for key in ("voice_deadline_seconds", "video_deadline_seconds", "decision_period_seconds",
                "report_period_seconds", "scan_period_seconds", "voice_interval_seconds", "video_fps"):
        if config[key] <= 0:
            raise ValueError(f"{key} must be positive")
    base = config["exogenous_step_seconds"]
    end = config["duration_seconds"] + max(config["drain_seconds"], config["voice_deadline_seconds"],
                                          config["video_deadline_seconds"]) + 0.1
    ap_count, users = len(scenario["ap_positions_m"]), scenario["background_users_per_ap"]
    radio_rng, arrivals_rng = random.Random(_seed(seed, "radio")), random.Random(_seed(seed, "arrivals"))
    report_rng, handoff_rng = random.Random(_seed(seed, "reports")), random.Random(_seed(seed, "handoffs"))
    frame_rng = random.Random(_seed(seed, "frames"))
    noise = [0.0] * ap_count
    alpha = math.exp(-base / 0.4)
    signals, arrivals = [], []
    for index in range(math.ceil(end / base) + 1):
        t, row, counts = index * base, [], []
        x = _position(scenario, t)
        for ap, ap_x in enumerate(scenario["ap_positions_m"]):
            noise[ap] = alpha * noise[ap] + radio_rng.gauss(0, scenario["signal_noise_db"] * math.sqrt(1 - alpha ** 2))
            distance = math.hypot(x - ap_x, scenario.get("lateral_m", 3.0))
            row.append(-36.0 - 30.0 * math.log10(max(1.0, distance)) + noise[ap])
            load = scenario.get("per_ap_load", [scenario["base_load"]] * ap_count)[ap]
            if scenario["load_pattern"] == "alternating":
                load *= 1.35 if ap % 2 else 0.45
            elif scenario["load_pattern"] == "bursty":
                epoch = math.floor(t / scenario["burst_period_seconds"])
                load *= 1.65 if (ap + epoch) % 3 == 0 else 0.45
            load = _clip(load, 0.0, 1.5)
            mean = load * config["background_rate_mbps"] * 1e6 * base / (8 * config["background_packet_bytes"] * max(users, 1))
            counts.extend(_poisson(arrivals_rng, mean) for _ in range(users))
        signals.append(tuple(row))
        arrivals.append(tuple(counts))
    report_events = []
    for ap in range(ap_count):
        t = report_rng.uniform(0.0, config["report_period_seconds"])
        while t < end:
            delay = max(0.0, config["report_delay_seconds"] + report_rng.uniform(-config["report_jitter_seconds"], config["report_jitter_seconds"]))
            report_events.append((t, ap, delay, report_rng.gauss(0.0, config["report_noise_std"])))
            t += config["report_period_seconds"]
    decisions = math.ceil(end / config["decision_period_seconds"]) + 2
    uniforms, durations = [], []
    for _ in range(decisions):
        uniforms.append(tuple(handoff_rng.random() for _ in range(ap_count)))
        durations.append(tuple(max(0.0, config["handoff_mean_seconds"] + handoff_rng.uniform(
            -config["handoff_jitter_seconds"], config["handoff_jitter_seconds"])) for _ in range(ap_count)))
    frame_count = math.ceil(config["duration_seconds"] * config["video_fps"] - 1e-10)
    mean_frame = config["video_mbps"] * 1e6 / (8.0 * config["video_fps"])
    frames = tuple(max(1, round(mean_frame * frame_rng.uniform(0.75, 1.25))) for _ in range(frame_count))
    identity = dict(config=config, scenario=scenario, seed=seed, model="packet-roaming-v2")
    fingerprint = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    return World(config, scenario, seed, fingerprint, tuple(signals), tuple(arrivals),
                 tuple(sorted(report_events)), tuple(uniforms), tuple(durations), frames)


@dataclass(frozen=True)
class Observation:
    time: float
    current_ap: int
    signals: tuple
    signal_ages: tuple
    signal_slopes: tuple
    loads: tuple
    report_ages: tuple
    active_users: tuple
    queue_delay_seconds: tuple
    own_miss_fraction: float
    own_miss_source_time: float


class Controller:
    def __init__(self, policy, config, params=None):
        if policy not in POLICIES:
            raise ValueError(policy)
        self.policy, self.config = policy, config
        self.params = dict(DEFAULT_PARAMETERS, **(params or {}))
        self.last_switch = -math.inf

    def choose(self, obs):
        p, c, current = self.params, self.config, obs.current_ap
        basic_emergency = obs.signals[current] < p["guard_rssi_dbm"]
        predictive = self.policy in ("predictive", "no_dwell", "no_guard", "no_cost", "no_age")
        guard = predictive and self.policy != "no_guard" and (
            basic_emergency or obs.own_miss_fraction > p["guard_miss_fraction"])
        if not basic_emergency and not guard and obs.time - self.last_switch < p["minimum_residence_seconds"]:
            return current
        capacities = [
            _rate(signal, c["maximum_rate_mbps"]) * max(1.0 - load, 1.0 / (active + 1.0))
            for signal, load, active in zip(obs.signals, obs.loads, obs.active_users)]
        demand = c["video_mbps"] + c["voice_packet_bytes"] * 8 / c["voice_interval_seconds"] / 1e6
        # Coarse expected service score; actual outcomes use complete packets
        # and complete video frames by their deadlines, not this formula.
        budget = min(c["voice_deadline_seconds"], c["video_deadline_seconds"])
        scores = [min(1.0, rate / max(demand, 1e-9)) * max(0.0, 1.0 - delay / (2.0 * budget))
                  for rate, delay in zip(capacities, obs.queue_delay_seconds)]
        if self.policy == "session_stay":
            if not basic_emergency:
                return current
            target = max(range(len(scores)), key=obs.signals.__getitem__)
            change = obs.signals[target] > obs.signals[current]
        elif self.policy == "rssi":
            target = max(range(len(scores)), key=obs.signals.__getitem__)
            change = obs.signals[target] > obs.signals[current] + (0.0 if basic_emergency else p["rssi_margin_db"])
        elif self.policy == "load_aware":
            target = max(range(len(scores)), key=capacities.__getitem__)
            change = capacities[target] > capacities[current] * (1.0 + (0.0 if basic_emergency else p["load_margin"]))
        else:
            if (predictive or self.policy == "cautious_v1") and not guard:
                for ap in range(len(scores)):
                    if ap == current:
                        continue
                    horizon = p["planning_horizon_seconds"]
                    if predictive and self.policy != "no_dwell" and obs.signal_slopes[ap] < -0.15:
                        horizon = _clip((obs.signals[ap] - p["guard_rssi_dbm"]) / -obs.signal_slopes[ap],
                                        p["dwell_min_seconds"], horizon)
                    if self.policy != "no_cost":
                        cost = c["handoff_mean_seconds"] * c["estimated_handoff_multiplier"]
                        cost += c["handoff_failure_probability"] * c["handoff_failure_extra_seconds"]
                        scores[ap] *= max(0.0, 1.0 - p["cost_weight"] * cost / horizon)
                    if self.policy != "no_age":
                        age = max(obs.report_ages[ap], obs.signal_ages[ap])
                        scores[ap] -= p["age_weight"] * age / (age + 1.0)
            target = max(range(len(scores)), key=scores.__getitem__)
            margin = 0.0 if basic_emergency or guard else p["app_margin"]
            change = scores[target] > scores[current] + margin
        if target != current and change:
            self.last_switch = obs.time
            return target
        return current


class BackgroundQueue:
    """FIFO of equal-sized packets, represented by count and partial head bytes."""
    __slots__ = ("size", "limit", "offered", "dropped", "delivered", "served_bytes", "bytes", "maximum")
    def __init__(self, size, limit):
        self.size, self.limit = size, limit
        self.offered = self.dropped = self.delivered = self.served_bytes = self.bytes = self.maximum = 0

    def arrive(self, count):
        self.offered += count
        outstanding = self.offered - count - self.dropped - self.delivered
        accepted = min(count, max(0, self.limit - outstanding))
        self.dropped += count - accepted
        self.bytes += accepted * self.size
        self.maximum = max(self.maximum, outstanding + accepted)

    def serve(self, amount):
        amount = min(self.bytes, max(0.0, amount))
        self.bytes -= amount
        self.served_bytes += amount
        # Count complete packets from remaining FIFO bytes. This avoids a
        # cumulative floating-point sum losing a packet at a large total.
        pending = math.ceil(max(0.0, self.bytes) / self.size - 1e-10)
        self.delivered = self.offered - self.dropped - pending
        return amount


def _airtime_allocations(demands, budget):
    """Equal-airtime processor sharing, redistributing unused allocations."""
    allocations = [0.0] * len(demands)
    active = [i for i, amount in enumerate(demands) if amount > 1e-12]
    while active and budget > 1e-12:
        share = budget / len(active)
        finished = [i for i in active if demands[i] <= share]
        if not finished:
            for i in active:
                allocations[i] = share
            break
        for i in finished:
            allocations[i] = demands[i]
            budget -= demands[i]
        active = [i for i in active if i not in finished]
    return allocations


def _runs(flags):
    lengths, current = [], 0
    for flag in flags:
        if flag:
            current += 1
        elif current:
            lengths.append(current)
            current = 0
    if current:
        lengths.append(current)
    return lengths


def run(world, policy, params=None, keep_trace=False):
    c, s = world.config, world.scenario
    controller = Controller(policy, c, params)
    dt, duration = c["dt_seconds"], c["duration_seconds"]
    end = duration + max(c["drain_seconds"], c["voice_deadline_seconds"], c["video_deadline_seconds"]) + dt
    ap_count, users = len(s["ap_positions_m"]), s["background_users_per_ap"]
    background = [[BackgroundQueue(c["background_packet_bytes"], c["background_queue_packets"]) for _ in range(users)] for _ in range(ap_count)]
    bg_rate = c["background_rate_mbps"] * 1e6 / 8.0
    current = max(range(ap_count), key=world.signals[0].__getitem__)
    signal = list(world.signals[0]); signal_time = [0.0] * ap_count; slope = [0.0] * ap_count
    loads, load_time = [0.5] * ap_count, [0.0] * ap_count
    active_users, queue_delays, busy_ema = [users] * ap_count, [0.0] * ap_count, [0.0] * ap_count
    mobile, deliveries, telemetry = [], [], []
    queued_bytes = 0.0
    serial = 0
    voice_count = math.ceil(duration / c["voice_interval_seconds"] - 1e-10)
    voice_ok = [False] * voice_count
    video_parts = [math.ceil(size / c["video_packet_bytes"]) for size in world.frame_sizes]
    video_ok_parts = [0] * len(video_parts)
    voice_next = frame_next = bg_next = report_next = 0
    next_scan, next_control = c["scan_period_seconds"], 0.0
    scan_until = 0.0
    pending_target, pending_failure, pending_until = None, False, 0.0
    switches = failures = successful_switches = delivered_packets = timely_packets = offered_packets = 0
    queue_drops = expiry_drops = handoff_drops = 0
    delivered_bytes = timely_bytes = 0.0
    max_mobile_queue = 0
    scan_blackout = handoff_blackout = radio_blackout_union = 0.0
    voice_deadline_index = frame_deadline_index = 0
    miss_history = deque()
    own_miss, own_miss_source = 0.0, 0.0
    history = []

    def send(arrival, kind, payload):
        nonlocal serial
        serial += 1
        heapq.heappush(telemetry, (arrival, serial, kind, payload))

    def arrive(kind, identity, created, size, deadline):
        nonlocal serial, offered_packets, queue_drops, queued_bytes, max_mobile_queue
        offered_packets += 1
        if len(mobile) >= c["mobile_queue_packets"]:
            queue_drops += 1
            return
        serial += 1
        # remaining bytes, original size, class, identity, creation timestamp
        packet = [float(size), size, kind, identity, created]
        heapq.heappush(mobile, (deadline, serial, packet))
        queued_bytes += size
        max_mobile_queue = max(max_mobile_queue, len(mobile))

    for step in range(math.ceil(end / dt)):
        t = step * dt
        base_index = min(int((t + 1e-10) / c["exogenous_step_seconds"]), len(world.signals) - 1)
        truth_signal = world.signals[base_index]
        while bg_next < len(world.background_arrivals) and bg_next * c["exogenous_step_seconds"] <= t + 1e-10:
            counts = world.background_arrivals[bg_next]
            for ap in range(ap_count):
                for user in range(users):
                    background[ap][user].arrive(counts[ap * users + user])
            bg_next += 1
        while voice_next < voice_count and voice_next * c["voice_interval_seconds"] <= t + 1e-10:
            created = voice_next * c["voice_interval_seconds"]
            arrive("voice", voice_next, created, c["voice_packet_bytes"], created + c["voice_deadline_seconds"])
            voice_next += 1
        while frame_next < len(video_parts) and frame_next / c["video_fps"] <= t + 1e-10:
            created, remaining = frame_next / c["video_fps"], world.frame_sizes[frame_next]
            while remaining:
                size = min(remaining, c["video_packet_bytes"])
                arrive("video", frame_next, created, size, created + c["video_deadline_seconds"])
                remaining -= size
            frame_next += 1
        if c["packet_expiry"]:
            while mobile and mobile[0][0] <= t + 1e-12:
                _, _, packet = heapq.heappop(mobile)
                queued_bytes -= packet[0]
                expiry_drops += 1
        while voice_deadline_index < voice_next and voice_deadline_index * c["voice_interval_seconds"] + c["voice_deadline_seconds"] <= t + 1e-10:
            deadline = voice_deadline_index * c["voice_interval_seconds"] + c["voice_deadline_seconds"]
            miss_history.append((deadline, not voice_ok[voice_deadline_index]))
            voice_deadline_index += 1
        while frame_deadline_index < frame_next and frame_deadline_index / c["video_fps"] + c["video_deadline_seconds"] <= t + 1e-10:
            deadline = frame_deadline_index / c["video_fps"] + c["video_deadline_seconds"]
            miss_history.append((deadline, video_ok_parts[frame_deadline_index] != video_parts[frame_deadline_index]))
            frame_deadline_index += 1
        # Histories can receive voice/video events interleaved; filter by age.
        miss_history = deque(item for item in miss_history if item[0] > t - 1.0)
        while report_next < len(world.report_events) and world.report_events[report_next][0] <= t + 1e-10:
            _, ap, delay, noise = world.report_events[report_next]
            backlog = sum(q.bytes for q in background[ap])
            active = sum(q.bytes > 1e-8 for q in background[ap])
            payload = (ap, t, _clip(busy_ema[ap] + noise, 0.0, 1.0), active, backlog / bg_rate)
            send(t + delay, "load", payload)
            report_next += 1
        while telemetry and telemetry[0][0] <= t + 1e-10:
            _, _, kind, payload = heapq.heappop(telemetry)
            if kind == "load":
                ap, source, load, active, delay = payload
                if source >= load_time[ap]:
                    loads[ap], load_time[ap], active_users[ap], queue_delays[ap] = load, source, active, delay
            elif kind == "signal":
                source, readings = payload
                for ap, value in readings:
                    if source > signal_time[ap]:
                        slope[ap] = (value - signal[ap]) / (source - signal_time[ap])
                        signal[ap], signal_time[ap] = value, source
            else:
                source, miss = payload
                if source >= own_miss_source:
                    own_miss_source, own_miss = source, miss
        if pending_target is not None and pending_until <= t + 1e-10:
            if not pending_failure:
                current = pending_target
                successful_switches += 1
            pending_target = None
        if t + 1e-10 >= next_scan and t < duration:
            scan_until = max(scan_until, t + c["scan_duration_seconds"])
            send(scan_until + c["signal_delay_seconds"], "signal", (t, tuple(enumerate(truth_signal))))
            next_scan += c["scan_period_seconds"]
        if t + 1e-10 >= next_control:
            send(t + c["signal_delay_seconds"], "signal", (t, ((current, truth_signal[current]),)))
            observed_miss = sum(item[1] for item in miss_history) / len(miss_history) if miss_history else 0.0
            send(t + c["report_delay_seconds"], "miss", (t, observed_miss))
            obs = Observation(t, current, tuple(signal), tuple(t - v for v in signal_time), tuple(slope),
                tuple(loads), tuple(t - v for v in load_time), tuple(active_users), tuple(queue_delays), own_miss, own_miss_source)
            if pending_target is None and t < duration:
                target = controller.choose(obs)
                if target != current:
                    decision_index = min(round(next_control / c["decision_period_seconds"]), len(world.handoff_uniforms) - 1)
                    pending_target = target
                    pending_failure = world.handoff_uniforms[decision_index][target] < c["handoff_failure_probability"]
                    latency = world.handoff_durations[decision_index][target]
                    if pending_failure:
                        latency += c["handoff_failure_extra_seconds"]
                        failures += 1
                    pending_until = t + latency
                    switches += 1
                    if c["flush_queue_on_handoff"]:
                        handoff_drops += len(mobile)
                        mobile.clear()
                        queued_bytes = 0.0
            if keep_trace:
                history.append(dict(time=t, current_ap=current, requested_ap=pending_target,
                    signal_sources=tuple(signal_time), load_sources=tuple(load_time),
                    own_miss_source=own_miss_source, observed_miss=own_miss))
            next_control += c["decision_period_seconds"]
        handoff_blocked = min(dt, max(0.0, pending_until - t)) if pending_target is not None else 0.0
        scan_blocked = min(dt, max(0.0, scan_until - t))
        blocked = max(handoff_blocked, scan_blocked)
        radio_blackout_union += blocked
        handoff_blackout += handoff_blocked
        scan_blackout += scan_blocked
        active_time = dt - blocked
        service_ap = current
        if pending_target is not None and pending_until < t + dt:
            service_ap = current if pending_failure else pending_target
        rate_bytes = _rate(truth_signal[service_ap], c["maximum_rate_mbps"]) * 1e6 / 8.0
        focal_demand = queued_bytes / rate_bytes if rate_bytes > 0 and active_time > 0 else 0.0
        allocations_focal = 0.0
        for ap in range(ap_count):
            demands = [q.bytes / bg_rate for q in background[ap]]
            if ap == service_ap and focal_demand > 0:
                # Background can use the time while the focal link is blocked.
                pre = _airtime_allocations(demands, blocked)
                for user, amount in enumerate(pre):
                    background[ap][user].serve(amount * bg_rate)
                demands = [q.bytes / bg_rate for q in background[ap]]
                allocations = _airtime_allocations(demands + [focal_demand], active_time)
                allocations_focal = allocations[-1]
                allocations = allocations[:-1]
                bg_airtime = sum(pre) + sum(allocations)
            else:
                allocations = _airtime_allocations(demands, dt)
                bg_airtime = sum(allocations)
            for user, amount in enumerate(allocations):
                background[ap][user].serve(amount * bg_rate)
            alpha = math.exp(-dt / 0.5)
            busy_ema[ap] = alpha * busy_ema[ap] + (1.0 - alpha) * min(1.0, bg_airtime / dt)
        capacity = allocations_focal * rate_bytes
        served_this_slot = 0.0
        while mobile and capacity > 1e-8:
            deadline, _, packet = mobile[0]
            consume = min(packet[0], capacity)
            packet[0] -= consume
            capacity -= consume
            queued_bytes -= consume
            served_this_slot += consume
            if packet[0] <= 1e-7:
                heapq.heappop(mobile)
                # Fluid sharing spreads allocated service over the active slot.
                completion = t + blocked + active_time * served_this_slot / max(allocations_focal * rate_bytes, 1e-20)
                delivered_packets += 1
                delivered_bytes += packet[1]
                deliveries.append(completion - packet[4])
                if completion <= deadline + 1e-10:
                    timely_packets += 1
                    timely_bytes += packet[1]
                    if packet[2] == "voice":
                        voice_ok[packet[3]] = True
                    else:
                        video_ok_parts[packet[3]] += 1
        queued_bytes = max(0.0, queued_bytes)
    video_ok = [done == required for done, required in zip(video_ok_parts, video_parts)]
    voice_runs = _runs([not flag for flag in voice_ok])
    video_runs = _runs([not flag for flag in video_ok])
    freezes = [length for length in video_runs if length >= c["freeze_run_frames"]]
    bg_flat = [q for queues in background for q in queues]
    bg_offered = sum(q.offered for q in bg_flat)
    bg_delivered = sum(q.delivered for q in bg_flat)
    bg_dropped = sum(q.dropped for q in bg_flat)
    bg_pending = sum(math.ceil(max(0.0, q.bytes) / q.size - 1e-10) for q in bg_flat)
    video_miss = 1.0 - sum(video_ok) / len(video_ok) if video_ok else 0.0
    voice_miss = 1.0 - sum(voice_ok) / len(voice_ok) if voice_ok else 0.0
    deliveries.sort()
    result = dict(world_fingerprint=world.fingerprint, policy=policy, seed=world.seed,
        scenario=s["name"], objective_miss_fraction=(voice_miss + video_miss) / 2.0,
        ontime_packet_fraction=timely_packets / offered_packets if offered_packets else 1.0,
        voice_missed_fraction=voice_miss, voice_missed_slots=len(voice_ok) - sum(voice_ok),
        voice_longest_outage_seconds=max(voice_runs, default=0) * c["voice_interval_seconds"],
        video_complete_fraction=1.0 - video_miss, video_missed_fraction=video_miss,
        video_freeze_fraction=sum(freezes) / len(video_ok) if video_ok else 0.0,
        video_freeze_count=len(freezes), video_longest_outage_seconds=max(video_runs, default=0) / c["video_fps"],
        delivered_mbps=delivered_bytes * 8 / (1e6 * duration),
        ontime_delivered_mbps=timely_bytes * 8 / (1e6 * duration),
        conditional_packet_delay_p95_ms=(deliveries[min(len(deliveries) - 1, math.ceil(.95 * len(deliveries)) - 1)] * 1000 if deliveries else 0.0),
        delivered_delay_sample_count=len(deliveries),
        handoffs=switches, failed_handoffs=failures, successful_handoffs=successful_switches,
        scan_blackout_seconds=scan_blackout,
        handoff_blackout_seconds=handoff_blackout, queue_drops=queue_drops,
        radio_blackout_union_seconds=radio_blackout_union,
        expiry_drops=expiry_drops, handoff_drops=handoff_drops,
        offered_packets=offered_packets, delivered_packets=delivered_packets,
        ontime_packets=timely_packets, late_packets=delivered_packets-timely_packets,
        final_pending_packets=len(mobile),
        packet_conservation_error=offered_packets-delivered_packets-queue_drops-expiry_drops-handoff_drops-len(mobile),
        generated_voice_packets=voice_count, generated_video_frames=len(video_ok),
        background_offered_packets=bg_offered, background_delivered_packets=bg_delivered,
        background_dropped_packets=bg_dropped, background_pending_packets=bg_pending,
        background_delivery_fraction=bg_delivered/bg_offered if bg_offered else 1.0,
        background_worst_delivery_fraction=min((q.delivered/q.offered for q in bg_flat if q.offered), default=1.0),
        background_conservation_error=bg_offered-bg_delivered-bg_dropped-bg_pending,
        max_mobile_queue_packets=max_mobile_queue,
        max_background_queue_packets=max((q.maximum for q in bg_flat), default=0))
    if keep_trace:
        result["decisions"] = history
        result["voice_ontime"] = voice_ok
        result["video_complete"] = video_ok
    return result
