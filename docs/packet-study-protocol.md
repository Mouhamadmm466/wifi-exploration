# Prospective protocol for the second simulation study

Protocol date: **14 October 2026**. Status: initially written before second-study outcomes; amended once after inspecting development outcomes and before any held-out run. The development-informed amendment is recorded below. This is an internal prospective plan, not external preregistration. The first study and all its results remain unchanged.

The policy names, scenario dictionaries and parameter grids are recorded in `configs/packet-study.json`; the simulation defaults are part of the source freeze. Any necessary implementation changes to this document must be logged below before that freeze. A code correction after outcome inspection must be reported; it must not quietly change the research question or discard an unfavorable condition.

## Why a second study is needed

The first study found that fewer handoffs did not reliably give better modeled service. Its full candidate had slightly worse average deficit than simple application-aware selection. Its age term was also extra switching resistance, and the simulator and policy shared the same service formula. The second study addresses these limitations with explicit packet and frame deadlines, independent outcome accounting, queues, association-dependent service sharing and new test environments.

The goal is to test whether a modest application-aware policy can protect delivery deadlines without creating large interruptions or unfairly taking service from other clients. A superior result is not assumed. Neither this study nor the first one measures human experience or validates a particular commercial Wi-Fi client.

## The simulated system and its limits

The planned system has one moving client carrying simultaneous voice-like packets and video-like frames. Other clients create background data traffic and stay associated with their configured APs. Per-user queues are finite. Associated clients share AP transmission opportunities according to one declared scheduling rule. Moving the focal client therefore changes service available to the background clients and their queue state.

Scanning interrupts the focal client on the same schedule for every policy. Candidate signal information is refreshed by these scans. Serving and candidate load reports have measurement delay and noise. Association takes time and may fail. The controller receives observations with explicit measurement times; it receives no future trajectory, future traffic, hidden true queue state or realized future transition duration.

The implementation must name the abstraction accurately. Explicit packets and queues do not by themselves make it an IEEE 802.11 MAC simulator. Any slotted airtime-sharing rule, PHY-rate mapping, loss law and transition distribution remain assumptions. Collision avoidance, retransmissions, authentication, backhaul and codec behavior may be represented only to the extent actually implemented.

## Development and held-out environments

| Split | Seeds | Environment families | Permitted use |
|---|---|---:|---|
| Development | 20001–20008 | 3 | Debugging, selecting fixed thresholds and comparing candidate parameter choices |
| Held out | 50001–50040 | 6 | Final main comparison after code, policy parameters and scenario definitions are frozen |
| Planned sensitivity subset | 50001–50010 | short_cells, hidden_hotspot, burst_load, crowded | Secondary robustness checks; no parameter selection |

These seed sets do not reuse the first study's seeds. Within each split, policies see the same exogenous world for a given scenario and seed. Held-out families must differ from development in AP geometry and include new mobility and load patterns. Merely changing a random seed in the same corridor is insufficient.

The three development scenarios are dev_corridor, dev_hotspot and dev_reversal, using 24 m AP spacing. The six held-out scenarios are wide_corridor (30 m spacing), short_cells (12 m spacing and faster shuttle), reversals (19 m spacing), hidden_hotspot (irregular spacing and unequal AP load), burst_load (irregular spacing and bursty load), and crowded (8 APs, 12 background clients per AP, sinusoidal mobility and bursty load). These are model-defined environments; their names do not imply measured field conditions.

The runner must write the complete scenario dictionaries before evaluation. A scenario cannot be renamed “held out” after its outcomes have helped design the method. The four named sensitivity scenarios are fixed in the configuration, before main results are seen. Results from all declared families are retained.

## Policies and threshold selection

The main comparison is the complete candidate against an application-aware rule with a **pilot-tuned constant switching margin**. The constant-margin rule is essential: the first study showed why an age-dependent threshold must compete with ordinary well-tuned switching resistance.

The agreed main list has 10 policies: `rssi`, `load_aware`, `app_myopic`, `cautious_v1`, `session_stay`, `predictive`, `no_dwell`, `no_guard`, `no_cost` and `no_age`. The complete candidate is `predictive`; `app_myopic` receives an independently tuned constant margin. With 6 held-out families and 40 seeds, the planned main comparison has **2,400 policy runs**. This is 240 paired worlds, not 2,400 independent physical experiments.

The session-stay and earlier-caution rules are stylized baseline families. They are not faithful reproductions of a published algorithm without a separate exact-method comparison.

For every tunable policy, evaluate the declared grid on all 3 development families and 8 development seeds. Select the configuration with the lowest equal-family mean of the primary deadline-miss score defined below. Resolve exact numerical ties first by fewer mean handoffs, then by a fixed lexicographic variant-identifier order. Do not select settings from held-out results. Record every development score, the complete search grid and the chosen parameters.

The candidate's guard activates when delayed serving RSSI is below **−78 dBm**, or delayed recent own missed-deadline fraction exceeds a development-selected threshold. The first development round fixed that threshold at **0.25**; the final grid tests **0.02, 0.10 and 0.25**. It bypasses the residence rule and the cost/age penalties and selects the highest estimated application-quality alternative only when it improves estimated quality. This is a defined response rule, not a guaranteed recovery mechanism. Every policy has the same basic residence bypass when delayed serving RSSI crosses the threshold. The candidate and its ablations except `no_guard` additionally use the delayed own-miss guard; `no_guard` isolates that added component. The own-miss report uses a trailing one-second window and only deadlines already elapsed at the report source time.

The dwell estimate uses cached target-RSSI history. For a slope below **−0.15 dB/s**, estimated remaining time is `(target RSSI − guard RSSI) / (−slope)`, clipped between 0.25 s and the planning horizon. Otherwise it uses the planning horizon. The horizon is 3 s for the complete candidate. This is an assumed linear extrapolation, not known future trajectory. Its value and failure cases must be reported honestly.

The initial development grids, retained as part of the history, were:

| Policy family | Development choices |
|---|---|
| Signal margin | 1, 3, 5 dB |
| Relative load/capacity margin | 0.05, 0.15, 0.30 |
| Constant application-quality margin | 0, 0.03, 0.08, 0.15 |
| Candidate cost weight × age weight | {0.5, 1, 2} × {0.02, 0.08}; 3 s planning horizon |
| Earlier-caution horizon | 1, 3, 8 s |

After the first development round, the final permitted grids are:

| Policy family | Final development choices | Configurations |
|---|---|---:|
| Signal margin | 0, 1, 3, 5 dB | 4 |
| Relative load/capacity margin | 0.05, 0.15, 0.30, 0.50, 0.75 | 5 |
| Constant application-quality margin | 0, 0.03, 0.08, 0.15, 0.25, 0.40 | 6 |
| Earlier-caution horizon | 1, 3, 8, 16 s | 4 |
| Candidate cost weight × age weight × own-miss guard threshold | {0.5, 1, 2, 4} × {0, 0.02} × {0.02, 0.10, 0.25}; 3 s planning horizon | 24 |

This final round has **43 configurations × 24 development worlds = 1,032 runs**. The original 456 runs remain archived. The two rounds therefore execute 1,488 development policy runs, with repeated settings and the same 24 development worlds; they are not 1,488 independent environments. The candidate receives a larger tuning budget than each simpler baseline. This difference must be disclosed, and comparisons must not be described as equal-budget optimization.

This is the **only development-informed grid revision**. Stop after this final round, even if another selected value lies at a boundary or the candidate still performs poorly. Report remaining boundary choices and unfavorable results. Do not change the primary comparator, held-out families, primary score or sensitivity conditions based on those results. The strong load-aware rule remains a required comparison in the main discussion alongside the primary application-margin contrast.

Other model and policy constants must be written in the frozen configuration. Boundary optima are not proof of a globally optimal threshold.

Component removals keep the complete candidate's other selected parameters. This isolates the local effect of removing a component. These ablations do not replace independently tuned simpler baselines. No bulk-goodput acceptance threshold is imposed unless a corresponding foreground bulk application is implemented. Background service is reported as a separate trade-off.

## Primary and complementary outcomes

For each run, define:

- **Voice packet miss fraction:** voice packets not completely delivered by their deadline, divided by all generated voice packets in the eligible measurement window.
- **Video frame miss fraction:** video frames not completely delivered by their deadline, divided by all generated video frames in that window. A frame fails if any required packet or byte is missing or late; successful fragments cannot count as successful whole frames.
- **Primary deadline-miss score:** one half of the voice miss fraction plus one half of the video frame miss fraction.

The equal weights are a declared engineering choice. This score is not a voice quality score, a video quality score or a human satisfaction measure. Report its two components separately so a gain in one cannot conceal harm to the other.

Dropped packets, queue-overflow losses, packets generated during a scan or transition, and failed association periods remain in the relevant denominator. A policy cannot improve the score by suppressing traffic generation or dropping difficult frames before counting them.

Use a common 60-second traffic-generation window and a drain period long enough to resolve every eligible deadline. The configuration requests 0.3 s of drain; the implementation must extend it if any deadline plus one time step is longer. Do not mark unfinished final-window frames as successes. Record generated, delivered-on-time, delivered-late and dropped counts so the accounting can be checked.

Report these complementary outcomes, where supported by the implementation:

| Outcome | Purpose |
|---|---|
| Useful delivered bytes and offered bytes | Distinguish deadline protection from lost throughput |
| Handoff attempts, successes and failures | Separate decision frequency from transition reliability |
| Scan and transition interruption durations | Identify the cost imposed by the control mechanism |
| Longest gap without useful focal delivery; p95/p99 gap or interruption statistics with their sample counts | Expose harmful tails hidden by the average |
| Background delivered/offered fraction, per-client values and worst-client value | Show effects on other clients |
| Decision and measurement counts | Account for control work |
| Queue overflows and unfinished data | Explain losses and end-of-run effects |

The current implementation reports the longest consecutive run of missed scheduled voice or video deadlines, and the fraction of video frame positions in failed-frame runs of at least six frames. These are deadline-run proxies. Actual useful-packet interarrival gaps and decoded-video freeze durations are not implemented and must not be claimed. Report the cross-run p95 of these run maxima with the number of runs.

A no-delivery gap includes all causes and is different from a transition interval. Their definitions must not be interchanged. Percentiles from very few events are unstable; retain event counts and do not claim a reliable p99 from a short list. For cross-run analysis, report the distribution of each run's maximum gap instead of treating thousands of within-run events as independent trials.

## Pairing and statistical analysis

The independent experimental unit is a full world run, not a packet, time step or individual handoff. All policies use the same world seed and scenario. Random inputs for movement, external arrivals, channel changes, report errors and transition outcomes are generated in separate named streams. Policy call order must not change the random world. Policy-dependent events should use stable keys or a declared common-random-number mapping; one policy taking an extra action must not consume another policy's future external arrivals.

For the primary comparison, compute candidate minus tuned application-margin score for every scenario and seed. For each seed, average the 6 scenario differences with equal weight. Bootstrap these 40 seed blocks, keeping all scenarios within the same resampled block. Use 5,000 resamples, a fixed analysis seed of 81631, and a percentile 95% interval. Negative values favor the candidate. The reported overall estimate describes the declared equal mix of families, not all possible networks.

Also report paired results for each scenario and for each primary-score component. Secondary contrasts and per-scenario intervals are exploratory and unadjusted for multiple comparisons. Do not count the number of significant cells as independent evidence of universal success. Report both absolute percentage-point differences and the original miss fractions; relative changes alone can exaggerate small baselines.

Background effects, gap tails and handoff counts are trade-offs, not hidden terms in the primary score. If the candidate lowers deadline misses while sharply reducing background service or worsening long gaps, the conclusion must say so. A single summary rank is insufficient.

## Planned sensitivity analysis

The sensitivity subset is fixed above: 10 paired seeds and four named held-out families. Use `predictive`, the tuned `app_myopic`, `rssi`, and `cautious_v1`. Reuse frozen main parameters; do not retune to the sensitivity outcomes. Each of the eight conditions has 4 scenarios × 10 seeds × 4 policies = 160 runs, for **1,280 sensitivity runs**.

| Condition | Change from the main configuration |
|---|---|
| Tight deadlines | Voice 40 ms; video 100 ms |
| Relaxed deadlines | Voice 100 ms; video 250 ms |
| Costly transitions | Mean 180 ms, jitter parameter 80 ms, failure probability 0.10, failure extra duration 250 ms; scan duration 40 ms |
| Stale reports | Report period 1 s, delay 1.5 s, jitter parameter 0.4 s, load-noise standard deviation 0.12 |
| Underestimated transition cost | Controller's mean transition-duration estimate multiplied by 0.25; expected failure-extra cost and true transition mechanism unchanged |
| Fine time step | Simulation step 5 ms |
| Coarse time step | Simulation step 20 ms |
| Retained handoff queue | Keep queued focal packets during a handoff instead of dropping the queue |

Deadline values and error settings are assumed test conditions, not universal application standards. The exact distributions associated with “jitter” must be documented by the simulator. This plan tests underestimation of transition cost; it does not test both directions of candidate-capacity bias.

The implementation plans to generate exogenous processes on a fixed 20 ms base timeline, independent of the simulation step. Input event timestamps and physical durations should stay fixed as far as possible. Record rounding of scan, transition, arrival and deadline times. If a changed time step also changes input discretization or event ordering, state that the check combines those changes with numerical resolution; do not call it a perfectly paired discretization-only experiment. Policy comparisons within each time-step condition must still use the same world.

If a planned mechanism is unsupported, mark that check unperformed and explain why. Do not replace it with a different favorable test after inspecting results. These sensitivities test narrow assumptions; they do not validate real Wi-Fi behavior.

## Preselected traces

After the frozen main evaluation, replay seed **50001** for all six held-out scenarios with `rssi`, `app_myopic` and `predictive`. Save decision records and voice/video success flags in compressed JSON. The illustrative paper timeline is selected in advance: **short_cells, seed 50001, tuned application-margin rule versus complete candidate**. This example is not selected for an unusually good or bad result. Check that every replay matches its original recorded main-run metrics before using it.

## Required verification before the held-out run

The code review should check at least:

- No service is credited during an actual scan or transition interval; fractional intervals or slot rounding are handled consistently.
- A frame's success depends on all its required data arriving by the deadline.
- Every eligible generated object appears exactly once in outcome accounting.
- Changing future world states cannot change earlier decisions.
- Different policies receive the same observation-generation and action-cost rules.
- Association changes queue sharing and background service; offered traffic does not change with the chosen policy.
- The controller cannot access the actual future transition time or true future dwell time.
- Replaying a fixed configuration and seed reproduces outcomes.
- Empty queues, zero loss, no roaming, a failed transition and end-of-run deadlines have small hand-checkable tests.
- The zero-component ablations differ only in the named term.

Save the configuration, selected development parameters, software versions and source hashes before held-out evaluation. Keep test results and exact commands. Do not overwrite the first study's evidence.

## Initial amendments before outcome generation

- Initial version: agreed seed splits, primary voice/video deadline score, family-balanced paired analysis and planned sensitivities recorded while the packet implementation was under development.
- Before outcome generation: agreed the implementer's 10 policy names, signal/own-miss guard, cached-signal dwell extrapolation and development grids shown above. The main run count becomes 2,400.
- Before outcome generation: adopted the exact three development and six held-out dictionaries in `configs/packet-study.json`, the four named sensitivity scenarios, seven sensitivity conditions and 0.3 s minimum drain described above. Replaced the early generic 60/150/250 ms deadline idea with distinct tight/relaxed voice and video deadlines. Replaced a proposed two-direction capacity-bias test with the implemented transition-cost underestimation test; two-direction capacity error remains untested. The sensitivity comparator set uses `cautious_v1` instead of `load_aware`.
- Before outcome generation: analysis uses 5,000 bootstrap resamples and seed 81631, matching the analysis implementation. Development selection covers 19 configurations × 3 scenarios × 8 seeds = **456 development runs**.
- Before outcome generation: clarified common signal-based residence bypass and candidate-only delayed own-miss guard. Only expired deadlines enter the delayed own-miss feature. The drain is at least the largest application deadline plus one simulation step.

- Before outcome generation: added retained focal queues during handoff as an eighth sensitivity condition. This tests the strong default assumption that queued focal data is dropped at every attempt. The sensitivity run count becomes **1,280**.
- Before outcome generation: fixed the trace replay and illustrative timeline selection above.
- Before outcome generation: identified the implemented tail metrics as scheduled deadline-run proxies. Actual useful-delivery gaps and decoded-video freezes remain unmeasured; the main deadline-miss objective is unchanged.

## Development-informed amendment before held-out evaluation

The first development round completed 456 runs on seeds 20001–20008 in the three development families. The original configuration, protocol, raw table, frozen settings and run manifest are preserved in [development_history](../results/packet/development_history/). No held-out run had started when this amendment was agreed. This statement records the project execution history; it is not an external audit of data access.

The best initial mean deadline-miss fractions were 0.007259 for signal margin 1 dB, 0.002604 for load margin 0.30, 0.006454 for application margin 0.15, 0.007528 for the earlier-caution horizon 8 s, and 0.007134 for candidate cost weight 2 and age weight 0.02. All five selected settings touched a searched boundary. The candidate did not beat either the application-margin rule or the load-aware rule on this development mix.

These findings motivated one revision: extend baseline margins and the caution horizon; allow a larger candidate cost weight and zero age penalty; and test smaller own-miss guard thresholds. The last change is an explicit attempt to improve the candidate based on its development weakness. It is not a result-independent choice. The discarded higher age weight and all original scores remain visible in the archived first round.

The final grids, unequal search budgets and stopping rule are stated above. The model source, evaluation design, primary comparison, 2,400 main runs, 1,280 sensitivity runs and preselected trace plan remain unchanged. The runner must create a new frozen-parameter file with the amended protocol hash before held-out evaluation. No held-out observation may guide another revision or parameter selection.

The study can support conclusions about this explicit simulation and its failure cases. It cannot establish human QoE, production readiness, a new scientific contribution or measured hardware performance by itself.
