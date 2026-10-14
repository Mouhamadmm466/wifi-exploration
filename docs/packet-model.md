# The packet-queue model: what it can and cannot test

Version 2 replaces the first model's service-quality outcome with packets, finite queues, deadlines, and complete video frames. It asks a more concrete question: when a device changes AP, which offered voice packets and video frames still arrive before their scheduled deadlines?

This is still a **packet-queue abstraction**, not an IEEE 802.11 stack. It does not simulate contention windows, collisions, retransmissions, encryption, authentication messages, channels, or RF interference between APs. Nearby AP geometry and competition within an AP represent selected parts of a dense network. They do not represent every effect of a dense Wi-Fi deployment.

The source is [packet_roaming.py](../src/packet_roaming.py). The prospective local study design is [packet-study-protocol.md](packet-study-protocol.md). All numerical parameters below are assumed research settings, not measurements from a real device. The original model and its unfavorable results remain unchanged.

## A moving call and competing users

One device carries a voice stream and a video stream at the same time. Several background users remain attached to each AP. Every user has a finite packet queue. The focal device and active background users share the AP's available airtime equally. If one queue needs less than its share, the remaining airtime is shared among the others.

This creates feedback that the first model did not have. When the device joins an AP, the background users there may get less service, their queues may grow, and later AP reports may change. Background users do not roam or change their sending rate in response. They are fixed-rate traffic sources, not TCP applications. There is only one adaptive mobile device; the experiment does not test several roaming policies competing with each other.

Each AP has its own one-second-per-second service budget. It shares that time between its users. There is no interference between different APs in this model. All APs are on the same subnet; there is no IP address change.

## Time and the external world

The default run generates call traffic for 60 seconds. Queue service is updated every 10 ms. After generation stops, the model continues for at least the longer voice/video deadline, plus one simulation step. The configured drain time can make this longer. Thus, the last generated frame remains in the denominator and gets its full opportunity to meet its deadline.

Radio noise and background packet arrivals use a **fixed 20 ms external time grid**. This grid stays the same when the service step changes to 5 or 20 ms. The fixed external process matters: a smaller service step must not silently create a different fading or traffic process.

Voice and frame creation times are defined on their own clocks. A packet scheduled between service steps enters the queue at the next step, but keeps its original creation timestamp and deadline. This introduces up to one step of timing error. The time-step sensitivity study measures part of this limitation.

The model has separate random streams for radio conditions, background arrivals, reports, handoffs, and video sizes. A `World` stores these external inputs before any policy runs. The same world can be reused across policies. Running one policy does not consume another policy's random stream. Handoff failure and duration draws are indexed by decision time and target AP, not by the order in which a policy asks for random numbers.

The world fingerprint identifies the model version, configuration, scenario, and seed. It is a reproducibility key for those inputs, not a claim that every internal queue trajectory is identical across policies. Queue trajectories should differ when association decisions differ.

## Layout, movement, and signal

A scenario specifies AP positions, the route's start and end, speed, movement type, background user count, traffic pattern, and signal-noise level. Movement can be a straight pass, a shuttle between endpoints, or a sine-shaped route. For the sine route, the stated speed is the maximum speed. A straight pass stops when it reaches the route endpoint.

The library includes `corridor_slow`, `short_dwell`, `reversal`, `hotspot`, `bursty`, and `crowded`. The study also supplies separate scenario dictionaries with different layouts and conditions. These are defined in [packet-study.json](../configs/packet-study.json), rather than chosen after seeing outcomes.

The signal in dBm is:

`signal = -36 - 30 × log10(distance in metres) + correlated noise`

The default path is three metres to the side of the AP line. The noise has a 0.4-second correlation time. At the fixed external step `h = 0.02 seconds`, its memory coefficient is `exp(-h / 0.4)`. The noise innovation is scaled so that the scenario's stated signal-noise value is its long-run standard deviation.

The focal link's rate in Mb/s is:

`rate = min(maximum rate, maximum rate × 10^((signal + 55) / 20))`

The default maximum is 54 Mb/s. Below -85 dBm, service is zero. Background links have a fixed 54 Mb/s rate. These are smooth service curves and a hard coverage cutoff, not real modulation/coding choices or a calibrated rate-adaptation model.

## Offered traffic and finite queues

| Stream | Default assumption | Deadline or buffer rule |
|---|---|---|
| Voice | One 160-byte packet every 20 ms | 60 ms from packet creation |
| Video | 30 frames/second, mean 2.4 Mb/s | 150 ms from frame creation |
| Video packets | At most 1,200 bytes each | Every fragment is needed for a complete frame |
| Background | 1,200-byte packets, fixed associations | 256 packets per user; overflow is dropped |
| Mobile queue | Voice and video share a 256-packet queue | Overflow is dropped; expired packets can be removed |

Video frame sizes vary independently between 75% and 125% of their nominal size. Each frame is split into packets, including a smaller final packet when needed. A video frame is complete only when **every** packet arrives by the frame's deadline. The model does not include codec dependencies, keyframes, retransmission requests, concealment, adaptive bitrates, or a real playout buffer. Frames are independent.

The focal queue uses earliest-deadline-first service. This gives voice and video a common, fixed scheduling rule under every roaming policy. It is an assumed packet scheduler, not a claim about the queue inside an ordinary Wi-Fi device.

Background load is a fraction of the AP's nominal 54 Mb/s service rate, split across its fixed users. Flat scenarios keep that mean. Alternating scenarios multiply it by 1.35 at odd-numbered APs and 0.45 at even-numbered APs. Bursty scenarios move a high-load group between APs; the multipliers are 1.65 and 0.45. The result is bounded between zero and 1.5, so an AP can be offered more traffic than it can serve. A `per_ap_load` list replaces the base values before the pattern multiplier is applied.

Each background user receives a random packet batch every 20 ms. Small batches use a Poisson draw; means of ten packets or more use a rounded normal approximation with the same mean and variance. These are synthetic arrivals, not captured network traffic.

Background packets have the same size, so an exact count and the remaining bytes of the partial head packet can represent their FIFO queue. This avoids allocating millions of identical packet objects. Overflow and complete-packet delivery still have explicit counts. The tests check partial heads and packet conservation. Foreground voice and video packets are represented individually.

## How service and completion times work

Within a step, the model calculates how much airtime each nonempty user needs. It divides the available time equally, caps allocations for queues that empty, and shares the unused time again. The sum of these allocations cannot exceed the AP's time budget.

The focal device receives no service during the part of a step occupied by a scan or handoff. Background users can use that time. When the focal link is active, it joins the AP's airtime sharing. Service after a successful handoff uses the **target** AP and its rate, including when the handoff ends partway through a step.

Packet completion times are interpolated across the focal device's active part of the step. This is fluid sharing, not a sequence of real wireless transmissions. An isolated short packet may therefore be credited at the end of the step rather than at its physical transmission finish. Packet-delay values carry this timing approximation, and time-step sensitivity is essential.

Packets completed exactly at their deadline count as on time. A packet already expired at the start of a step is removed when expiry is enabled. A packet that finishes late within a step is counted as delivered but not on time. Partly transmitted packets that expire have consumed service but do not count as complete delivered packets.

## Scanning, handoffs, and failures

Initial association chooses the strongest AP using one free initial signal snapshot of all APs. Initial background-load estimates are a common prior of 0.5, not live truth. This startup exception applies to every policy.

After startup, every policy pays for the same periodic full scan. The defaults are one scan each second and a 12 ms interruption. All AP signal values are sampled at scan start and delivered after the scan and the signal-report delay. The serving AP also has a signal sample every decision interval, delivered after the same 40 ms signal delay. A real scan is more complicated; this is a common assumed measurement budget, not a simulated 802.11 scan exchange.

The default handoff duration is a uniform draw around 80 ms, with a 40 ms half-width. An attempted handoff fails with probability 0.03. A failure adds 120 ms and returns to the original AP. These durations and probabilities are assumptions. They are not measured timings for 802.11r or any particular phone.

By default, packets already in the focal queue are discarded when a handoff starts. Packets generated during the interruption enter the queue and can be served after the attempt ends. The study includes a sensitivity that retains the old queue, because full queue loss is a strong assumption. Scan interruptions retain the queue.

Interruption time is integrated fractionally. A 25 ms interruption with 10 ms steps blocks 10 + 10 + 5 ms. If a scan and handoff overlap, service loses the **union** of their intervals. The separate scan and handoff counters can overlap and should not be added. `radio_blackout_union_seconds` records the actual union.

`handoffs` counts attempts. `failed_handoffs` counts attempts assigned failure. `successful_handoffs` counts completed AP changes. A transition still unfinished at the measurement end is not a completed change.

## What the controller observes

The controller receives cached signals, signal ages and recent slopes, background-load reports, report ages, active background-user estimates, background-queue delay estimates, and a delayed report of its own recent missed deadlines. It does not receive the true current queues, true future rate, route, or pending future packet outcomes.

Each AP issues reports asynchronously, with its own initial offset. Defaults are a report every 0.5 seconds, mean transport delay 0.3 seconds, uniform delay variation of ±0.15 seconds, and normal load error with standard deviation 0.05. Older reports cannot overwrite newer ones.

The load value is an exponential average, with a 0.5-second time constant, of **background airtime** used at that AP. It is not total channel utilization. Reports also contain the number of currently nonempty background queues and their total queued bytes divided by the background link rate. All of these values are sampled from the source state, then delayed. The serving AP has no privileged fresh load/queue observation.

These reports are richer than ordinary candidate signal measurements or a standard BSS-load field. The study assumes an abstract telemetry service. It does **not** claim that 802.11k or 802.11v automatically provides every quantity used here, or provides them at these delays and costs.

The own-miss report contains voice-packet and video-frame deadlines that have already elapsed during the previous second. It is delayed by the configured report delay. Each elapsed voice packet or video frame is one observation in this risk estimate; this is different from the primary outcome's equal weighting of the two stream-level miss fractions. Future or still-pending deadlines cannot enter this report.

All policies receive the same information rule. The values may differ after their actions alter queues and service. Shared external report timing and noise do not imply identical endogenous AP-load reports.

## Estimated quality and the policies

The controllers estimate focal capacity with:

`estimated capacity = rate(cached signal) × max(1 - reported background load, 1 / (reported active users + 1))`

This combines reported unused airtime with an assumed fair-share floor. It is only an estimate. It does not expose the actual service available in the next step.

Let `demand` be the nominal video rate plus the voice rate, and let `budget` be the smaller application deadline. The coarse application score is:

`score = min(1, estimated capacity / demand) × max(0, 1 - reported queue delay / (2 × budget))`

The score is a decision heuristic. It is **not** the measured reward. Outcomes are calculated from actual delivered packets and whole-frame deadlines. A high predicted score can be wrong because of old reports, noise, new traffic, queue loss, interruption, or the model's own simplifying assumptions.

| Policy | Rule |
|---|---|
| `rssi` | Strongest cached signal, with a development-tuned dB margin |
| `load_aware` | Highest estimated capacity, with a development-tuned relative margin |
| `app_myopic` | Highest estimated application score, with a development-tuned fixed margin |
| `cautious_v1` | Application score with fixed-horizon handoff cost and age penalties; adapted from version 1 |
| `session_stay` | Keep the session's AP unless delayed signal crosses the emergency threshold |
| `predictive` | Application score with a signal-trend holding estimate, cost/age caution, and a delayed-risk safety guard |
| `no_dwell` | Predictive rule with a fixed holding horizon |
| `no_guard` | Predictive rule without the additional delayed-risk guard |
| `no_cost` | Predictive rule without the handoff cost discount |
| `no_age` | Predictive rule without the report-age penalty |

Every policy normally has a minimum residence time, initially one second. Delayed serving signal below -78 dBm removes the residence restriction and ordinary improvement margin. This is a common basic emergency condition.

The predictive rule has an additional guard. It activates when delayed serving signal is below -78 dBm **or** the delayed trailing miss report exceeds 0.25. It removes residence, cost, and age restrictions and chooses a genuinely higher estimated application score. It does not know true current service and cannot guarantee rescue. `no_guard` retains the common signal-based emergency behavior but removes this additional protection.

For a candidate whose recent signal is falling faster than 0.15 dB/s, the predictive holding estimate is:

`holding time = clip((cached signal - emergency signal) / -signal slope, minimum dwell, planning horizon)`

Otherwise it uses the fixed planning horizon. The default minimum dwell is 0.25 seconds and the planning horizon is three seconds. The slope uses two already-received signal measurements and their source times. This is a rough trend estimate, not a mobility oracle or a learned prediction model. Noise can make it wrong.

The estimated handoff cost is the assumed mean interruption, multiplied by a configurable belief factor, plus failure probability times extra failure delay. The controller does not know the individual future interruption draw. The cost-underestimate sensitivity changes the belief factor.

Unless the guard is active, a candidate score becomes:

`adjusted score = score × max(0, 1 - cost weight × expected cost / holding time) - age weight × age / (age + 1)`

Here age is the larger of the candidate's signal age and load-report age. Unlike version 1, AP reports are asynchronous, so ages can differ across candidates. The age term is still a heuristic caution term, not a calibrated confidence interval. The serving score receives no switching cost. A strict improvement above the configured margin is required to move.

The development grids and selection objective are in the prospective protocol. The application baseline is independently tuned. Component ablations inherit the selected predictive parameters; they are not separately tuned to win after evaluation.

## Outcomes: exact definitions

All offered foreground packets and frames count in the denominators, including overflow drops, expired packets, packets lost at handoff, and traffic created during interruptions.

| Output | Definition |
|---|---|
| `voice_missed_fraction` | Voice packets not fully delivered by deadline / all generated voice packets |
| `video_complete_fraction` | Frames with every fragment delivered by deadline / all generated frames |
| `video_missed_fraction` | One minus video complete fraction |
| `objective_miss_fraction` | Half the voice miss fraction plus half the video miss fraction |
| `ontime_packet_fraction` | Complete packets delivered by deadline / all offered voice and video packets |
| `voice_missed_slots` | Number of missed scheduled 20 ms voice packet slots |
| `voice_longest_outage_seconds` | Longest consecutive run of missed voice slots × the voice interval |
| `video_longest_outage_seconds` | Longest consecutive run of incomplete frames / frame rate |
| `video_freeze_count` | Number of maximal runs containing at least six consecutive incomplete frames |
| `video_freeze_fraction` | Frames belonging to those long runs / all generated frames |
| `delivered_mbps` | Bytes in fully delivered packets, including late packets, divided by the generation duration |
| `ontime_delivered_mbps` | Bytes in fully delivered on-time packets divided by generation duration |
| `late_packets` | Complete delivered packets that missed their deadline |
| `conditional_packet_delay_p95_ms` | 95th percentile of creation-to-completion delay among delivered packets only |

The six-frame freeze threshold is about 200 ms at 30 frames/second. When a run crosses the threshold, all frames in that run count in the fraction, including its first five. This is a fixed **missed-playout-run proxy**. It is not the W3C WebRTC freeze metric and does not show that a real decoder froze. Likewise, the voice and video “outage” fields describe consecutive missed scheduled deadlines, not an exact gap between real media render events.

The conditional delay statistic excludes packets that never completed, so it can look good even when many packets are lost. `delivered_delay_sample_count` reports its denominator. A zero-sample delay value is stored as 0 solely as a numeric sentinel and must not be interpreted as zero network delay.

Background outputs include offered, delivered, dropped, and still-pending packet counts. `background_delivery_fraction` is their aggregate delivery ratio. `background_worst_delivery_fraction` is the lowest per-user ratio among users with nonzero offered traffic. Background traffic continues during the drain window; its counters cover the full simulated period. `max_background_queue_packets` is the largest queue seen for any one background user, not the sum across an AP.

The foreground conservation check is:

`offered = delivered + queue drops + expiry drops + handoff drops + final pending`

The background check compares offered, delivered, and dropped counts with pending packets independently calculated from remaining queue bytes. It is not just a remainder assigned to make the equation true.

## API, reproducibility, and tests

The public interface is:

```python
from packet_roaming import default_config, make_world, run

config = default_config()
world = make_world(config, "hotspot", seed=20001)
result = run(world, "predictive", params={"cost_weight": 1.0})
```

A scenario dictionary can replace the library name. A parameter dictionary overrides only the supplied policy defaults. `keep_trace=True` also returns decision records, source timestamps, voice deadline outcomes, and complete-frame outcomes. It is intended for validation and diagnostics, not aggregate CSV output.

From the repository root:

```sh
python3 -m unittest discover -s tests -v
python3 scripts/run_packet_study.py --workers 4
```

The study runner freezes development choices before held-out evaluation and records source hashes. The core uses only Python's standard library. A 60-second benchmark on one development world took about 0.27 seconds per policy; machine and scenario conditions affect this time.

Fifteen focused model tests cover queue conservation with partial background packets, finite airtime, complete-frame requirements, drain behavior, exact-deadline completion, fractional handoff completion on the target link, failed returns, overlapping interruption unions, delayed observations, future-trace mutation, deterministic pairing, unchanged external processes under time-step refinement, and guard/dwell ablations. Independent review found no blocking issue within this declared abstraction before study freezing. This is software/model checking, not validation against hardware.

## Remaining limits

This version makes packet deadlines and queue competition explicit, but important real-world effects remain absent. It has no real media codec, adaptive sending, packet retries, transport control, RF interference between APs, hidden terminals, multi-link operation, security exchange, or competing adaptive roamers. Background telemetry is idealized and richer than typical client information. Signal-to-rate curves, interruption distributions, queue loss, and deadline budgets are uncalibrated assumptions.

The study can therefore reject or support policy hypotheses **inside these declared conditions**. It cannot establish a deployable Wi-Fi roaming improvement or a human-quality gain. A stronger next step would replace assumed curves and telemetry errors with measured traces, then test an implementation in a network stack or controlled testbed without changing the evaluation rules after seeing the results.
