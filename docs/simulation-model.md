# What the simulation does

This is a small model of roaming decisions. One moving device chooses between six access points (APs). We ask whether the device should accept a better estimated connection now, or keep its present connection because changing AP has a cost.

This is **not** a simulation of IEEE 802.11 frames. It does not implement 802.11k, 802.11v, 802.11r, authentication, scanning, or radio contention. It does not measure video freezes or human experience. Its results can test ideas inside the model. They cannot show that a real phone will behave the same way.

All numerical choices below are assumptions for an exploratory study. They are not measurements, values copied from a paper, or estimates of a particular campus. Literature provides the problem and useful comparison ideas; it does not validate these equations.

## The world we simulate

There are six APs, spaced 24 metres apart along a corridor. The device travels on a parallel line, three metres from the AP line. An ordinary pass covers 136 metres in 180 seconds. The main simulation checks decisions every 0.25 seconds. All APs belong to one subnet, so there is no IP address change.

The device has a fixed application demand. Background traffic comes from other users, but we do not model these users separately. Each AP has a changing background load between 0.03 and 0.97. The focal device's own traffic does not change that load. Other devices do not react to its choice. This is an important limit: the experiment cannot study many devices moving together or competing for the same free capacity.

The six scenarios are:

| Scenario | Purpose | Assumed conditions |
|---|---|---|
| balanced | Negative/control case | All APs have light background load near 0.18. Signal-based roaming may be enough. |
| hotspots | Unequal load | Alternating APs have background loads near 0.24 and 0.62, with slow change. |
| overloaded | Capacity shortage | Every AP is busy, near 0.87 load. Changing AP may not solve the shortage. |
| abrupt | Stale reports | Every 12 seconds, the group of APs with 0.88 load changes. Others are near 0.28. |
| reversal | Direction changes | The device makes four corridor traversals in 180 seconds, with hotspot loads. |
| short_dwell | Stress case | A 28-second sine-wave shuttle creates short visits, with alternating loads near 0.25 and 0.63. This is not ordinary walking. |

Independent noise changes each AP's signal and load. Both noise processes have memory. Signal noise keeps 0.93 of its previous value and adds a normal random value with standard deviation 0.55 dB each step. Load noise keeps 0.94 of its previous value and adds a normal value with standard deviation 0.018. The trace begins nine seconds before measurement starts, so old load reports already exist at time zero. These are synthetic fading and load patterns, not a physical channel model.

## What a policy is allowed to know

At every decision, every policy receives the current signal level from **all** APs. This assumes signal measurements are freely available. We do not charge for finding APs, measuring their signal, or sending load reports. There is no claim that a real device could collect this information without cost.

The serving AP has an ideal current load/quality observation. Other APs have periodic load reports, issued once per second. A report has an additional transport delay of 0, 2, or 8 seconds. Its total age is therefore 0–0.75, 2–2.75, or 8–8.75 seconds. We combine its old load with the AP's current signal. The same rule applies to every policy.

The policy does not know the future route, future signal, or future traffic. It has no access to the complete trace through its decision interface. The proposed rule's planning horizon is an assumed holding interval, **not** future data or a forecast of the route. Tests change the future part of a trace and check that earlier decisions stay the same.

The main model assumes that policies know the exact link-service equations below. It also assumes they know the exact, constant interruption time of a handoff. This is favorable to the model-based policies. A separate model-mismatch diagnostic, if present in the results, weakens the perfect-model assumption.

## Signal, capacity, delay, and loss

The signal value in dBm is:

`signal = -36 - 30 × log10(distance in metres) + signal noise`

The physical-rate proxy in Mb/s is:

`rate = min(72, 72 × 10^((signal + 55) / 20))`

The remaining capacity is `rate × (1 - background load)`. This smooth curve replaces real rate adaptation, airtime sharing, retransmissions, and channel interference. It is not an 802.11 data-rate table.

The conditional radio-loss proxy is:

`loss = clip(0.002 + 0.20 / (1 + exp((signal + 76) / 3)) + 0.10 × (max(0, load - 0.8) / 0.2)^2, 0, 1)`

The delivered fraction of offered demand is:

`delivery = min(1, remaining capacity / application demand) × (1 - loss)`

The round-trip delay proxy, in milliseconds, is:

`RTT = min(5000, 5 + 4 / (1 - load)^2 + 120 / max(rate, 0.05))`

There are no actual packet queues. The large delay at high load is an assumed penalty, not a result from queue simulation. The model does not simulate packet reordering, TCP congestion control, media codecs, jitter buffers, retransmission deadlines, or file completion time.

## Applications and the main score

| Profile | Offered demand | RTT budget | Radio-loss budget | What it represents |
|---|---:|---:|---:|---|
| realtime | 4 Mb/s | 80 ms | 2% | A synthetic continuous application sensitive to rate, delay, and loss |
| bulk | 20 Mb/s | Inactive in score | Inactive in score | A fixed-demand throughput task, not a TCP flow |

An adequacy factor is 1 when a metric meets its budget. It falls linearly to 0 when the metric reaches twice its budget:

`latency adequacy = clip(2 - RTT / RTT budget, 0, 1)`

`loss adequacy = clip(2 - radio loss / loss budget, 0, 1)`

For realtime traffic, the service-quality proxy is:

`q = delivery × (0.60 + 0.25 × latency adequacy + 0.15 × loss adequacy)`

For bulk traffic, `q = delivery`. The realtime weights are assumptions. Radio loss affects delivery and also the loss-adequacy factor; this is a deliberate heuristic preference, not a validated model of user experience. Application classification is assumed correct and fixed during a run. We use separate application profiles rather than changes during one run.

The main outcome is **service deficit**, `1 - time-average(q)`. A lower value is better. A difference of 0.01 means one percentage point on this artificial scale. It does not mean one percentage point fewer video freezes.

We also report:

- **Unserved fraction:** the share of all offered demand not delivered, including handoff interruptions. This is a demand-based packet-delivery proxy, not counted network packets.
- **Delivered Mb/s:** offered rate multiplied by the delivered fraction.
- **Handoffs:** the number of AP changes after initial association.
- **Ping-pong:** a return A → B → A within five seconds of the A → B change.
- **Blackout time:** the actual accumulated interruption time inside the measurement window.
- **Delivered-weighted RTT:** the modeled RTT averaged with delivered data as weights. No RTT exists for data not delivered, so this alone is not a reliable service measure.

## Handoff accounting

The experiment uses interruptions of 0.02 and 0.20 seconds. These are low- and high-cost assumptions, not measured 802.11r and non-802.11r timings. During an interruption, no data is delivered and `q = 0`. The application keeps offering demand.

For each time step, let `remaining` be the unfinished interruption and let `dt = 0.25 seconds`:

`blocked = min(dt, remaining)`

`active = dt - blocked`

`remaining = max(0, remaining - blocked)`

The step contributes `active × q` to service and `active × delivery` to delivered demand. A 20 ms handoff therefore loses 20 ms, **not** a whole 250 ms step. A longer interruption can span several steps. Decisions wait while an interruption is still active. A handoff close to the end loses only the time inside the window.

## Policies

All policies start on the AP with the strongest initial signal. Initial association has no cost. All use a two-second minimum residence time. If serving signal is below -78 dBm, this residence rule and the usual improvement margin are removed. This emergency condition does **not** remove the proposed cost or age penalties. It does not guarantee a rescue: the policy can stay if every alternative still has a worse estimated score.

| Policy in data | Decision rule |
|---|---|
| `rssi` | Change to the strongest signal only if its signal advantage exceeds a tuned dB margin. |
| `load_aware` | Choose the largest estimated remaining capacity, with a tuned relative improvement margin. It ignores the application's delay and loss budgets. |
| `app_myopic` | Choose the highest estimated application-quality score, with a fixed 0.03 improvement margin. |
| `proposed` | Discount a target's quality by handoff cost over an assumed horizon, subtract an age caution penalty, and require a 0.03 improvement. |
| `no_cost` | The same proposed rule with its cost discount removed. |
| `no_age_penalty` | The same proposed rule with its age penalty removed. |
| `app_static` (added diagnostic) | Application quality with a fixed margin chosen on pilot seeds from 0.03, 0.08, 0.15, 0.25. |

For a target AP, the proposed score is:

`target score = q × max(0, 1 - handoff seconds / horizon seconds) - age penalty × age / (age + 2)`

The serving score is its current `q`. A handoff must beat the serving score by more than 0.03, unless the emergency condition removes this margin. Ties favor the lowest AP index when selecting a target, but a strict improvement is still required to switch.

The age penalty is **not a calibrated confidence interval or probability**. Here all alternative APs have the same report age. The age term therefore adds caution to every alternative equally; it does not change their ranking. In ordinary operation this rule is equivalent to an application-quality hysteresis threshold that depends on report age and handoff cost. The added `app_static` diagnostic checks whether a simpler, fixed threshold can explain its benefit. We make no novelty claim for this rule.

## Pilot, evaluation, and uncertainty

The full main grid has 6 scenarios × 2 profiles × 2 interruption times × 3 report delays = **72 cells**. Each evaluation cell has **40 seed pairs**, shared across policies. The same mobility, signal, and load trace is reused across all policies and treatment settings for a scenario and seed. Policy decisions cannot change those external traces.

Pilot seeds 11–16 are used for parameter choice. Evaluation seeds 1001–1040 are kept separate. The script writes `selected_parameters.json` before it begins the evaluation. It chooses the lowest equally weighted mean service deficit across the pilot grid. The candidate searches nine horizon/age-penalty pairs. RSSI and load-aware each search three margin values. This is limited and unequal tuning, not proof that these baselines are optimally configured. The application-myopic margin is fixed at 0.03. The later static-margin diagnostic searches four values on the same pilot seeds.

The candidate horizon grid is 1, 3, and 8 seconds; the age-penalty grid is 0.05, 0.15, and 0.30. RSSI margins are 2, 4, and 6 dB. Load margins are 0.05, 0.15, and 0.30 of current estimated capacity. Shared constants were set before running the pilot. The fixed config and source hashes are saved with the run.

For each cell, the analysis subtracts a comparator's outcome from the proposed rule's outcome for the **same seed**. It then resamples these 40 paired differences 2,000 times and reports the 2.5th and 97.5th percentiles. A negative deficit difference favors the proposed rule. This uses whole simulated runs as the statistical units; it does not pretend that correlated time steps are independent observations.

The reported 95% intervals describe random variation **inside this model**. They do not include uncertainty about its equations, real hardware, or application weights. They are pointwise intervals, with no correction for testing many cells. Counts of positive and negative intervals are descriptive. Summaries across scenarios and treatment settings are equally weighted descriptive means; they are not independent pooled experiments or campus-wide estimates.

The horizon sensitivity check repeats the proposed rule at 1, 3, and 8 seconds with 8-second report delay and 0.20-second interruption. It keeps the selected age penalty and never changes the main selected parameters. This is exploratory within-model evaluation, not independent confirmation of a real networking claim.

## Reproduce the study

Use Python 3.10 or later. There are no third-party dependencies for the main simulation and analysis.

```sh
python3 -m unittest discover -s tests -v
python3 scripts/run_study.py
```

The second command repeats the pilot, evaluation, paired comparisons, and horizon sensitivity. It writes raw run data and summaries to `results/`. Then run the added diagnostic with:

```sh
python3 scripts/run_static_margin.py
```

`configs/study.json` contains the design, seeds, and main settings. `results/run_manifest.json` records the Python version, full config, chosen parameters, timestamps, and source hashes. Results are deterministic for the same inputs in the recorded environment; timestamps and runtime naturally change. Tests cover exact fractional interruption accounting, past-only reports, future-suffix invariance, trace pairing, score bounds, cooldown bypass, and ablation behavior.

## What would make the evidence stronger

The next useful step is to replace one assumption at a time with measured data: signal-to-throughput mapping, interruption distributions, report errors, and application response to loss or delay. More demanding studies should model queues and retransmissions, several clients that affect each other's load, channel interference, scanning cost, missed handoffs, asymmetric report ages, and actual application traffic. The present study provides a reproducible starting point and tests for errors; it does not replace those later steps.
