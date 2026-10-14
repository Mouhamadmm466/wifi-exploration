# Future hardware validation

Status: planned only. No physical Wi-Fi experiment has been run for this project. The current deliverable is simulation, following the user's request on 14 October 2026. This plan explains how a later experiment could test whether the simulated tradeoff exists on real devices.

## The claim to test

The narrow claim is that a policy using application needs and estimated switching cost can improve service during movement compared with strong baselines. The first hardware study should keep one SSID, one IP subnet, one security configuration, and a wired application server. This isolates AP selection and its interruption from internet variability and IP migration.

Use two APs for the initial measurement, then three for a meaningful choice among targets. A dense campus claim needs a later multi-client and multi-AP study. Three APs in a quiet room are not a campus deployment.

## Equipment and setup

| Item | Minimum role | Record before testing |
|---|---|---|
| Two, then three configurable APs | Shared SSID, distinct BSSIDs, wired backhaul | Model, firmware, channel, width, transmit power, security, supported k/v/r settings |
| One Linux research client | Run the policy and collect client events | Adapter, driver, firmware, kernel, supplicant build, power-saving state |
| One ordinary client | Test how network advice works in practice | Model, operating system and version; no assumption of direct roaming control |
| One wired server | Run traffic endpoints and collect logs | Software versions, traffic settings, Ethernet speed, clock configuration |
| Controlled load clients | Produce repeatable airtime demand | Client count, association, direction, packet sizes, offered traffic |
| Monitor interfaces | Observe management/data frames on both AP channels | Supported bands, timestamp source, packet-capture drops |
| Repeatable movement | Fixed path or controlled attenuation | Route, speed, orientation, position markers or attenuation schedule |

These are capability requirements, not a shopping list. First check existing equipment. Use fixed channels and widths during a comparison. Keep backhaul capacity above the intended wireless load unless a backhaul bottleneck is an explicit factor. Keep country and channel settings identical across the experiment. Document unrelated radio activity rather than pretending it does not exist.

## Two distinct control experiments

In the **controlled-client experiment**, one process owns roaming decisions on the Linux client. Check which commands the installed supplicant and driver actually support. Record the requested target, command response, resulting BSSID, and the first useful packet. Avoid having a separate network manager make competing decisions. The older official API documentation is a starting point, not a compatibility promise. [M10](https://w1.fi/wpa_supplicant/devel/ctrl_iface_page.html)

In the **network-advice experiment**, the AP sends a transition suggestion to an ordinary client. Record whether the client acknowledges, accepts, refuses, or ignores it, and whether a transition follows. Do not label a suggestion as a completed roam. Keep client refusal as an outcome; do not remove it from the sample. The practical distinction follows client-controlled roaming described by Apple. [M01](https://support.apple.com/en-euro/guide/deployment/dep98f116c0f/web)

Do not use forced disconnection to represent ordinary application-aware advice. It changes the intervention. If forced disconnection is studied, give it a separate condition and report the extra disruption.

## Establish a measurement timeline

For every attempted transition, store these events when observable:

1. Last observation made available to the policy, including its age.
2. Decision time and reason code.
3. Scan request/start/end, or explicit evidence that a cached result was used.
4. Transition request time and target.
5. Observed authentication/FT and reassociation exchanges.
6. Client association-complete event.
7. First useful application data after the transition.

Use a monotonic clock for intervals on the same machine. For events across machines, measure clock offset and drift before and after a run. Wired PTP is useful when the equipment supports it, but the achieved accuracy must be checked. Without enough synchronization accuracy, use same-clock packet interarrival gaps and round-trip time; do not report precise one-way delay.

A receiver's interarrival gap includes the packet-generation period, loss, and scheduling. It is not automatically the radio handoff duration. Keep at least three measurements separate: control-command-to-association time, absence of useful application delivery, and time until delivery becomes stable again. Show distributions and failed transitions rather than only one mean.

Use separate monitor radios for two channels when possible. A single capture radio hopping between channels may miss the exact exchange we need to measure. Client/AP logs remain useful, but they do not replace missing on-air frames. Record capture loss and missing events in the run manifest.

## Application traffic and outcomes

Begin with a controlled interactive traffic generator and a bulk transfer. Declare rates, packet sizes, burst patterns, and deadlines in the configuration before the main trials. Those choices define the experiment; they are not universal requirements for all calls or games.

| Outcome family | Measure | Interpretation |
|---|---|---|
| Network service | Delivered goodput, loss, reordering, delay or RTT, consecutive loss burst | QoS: what the network delivers |
| Interruption | Longest delivery gap, gap distribution, time to stable delivery | User-visible risk; depends on packet generation |
| Interactive application | Deadline misses under a declared workload | Service-quality measure for that workload |
| Real WebRTC follow-up | Freeze duration/count, concealed-audio fraction, buffer delay, codec and bitrate | Application indicators; check browser support |
| Bulk application | Completion time for a fixed-size transfer | Benefit to an application that can tolerate short interruptions |
| Control cost | Scan count/time, roam count, return-to-old-AP count, rejected advice | Cost and stability of the policy |
| Other users | Their goodput and delay under the same load | Detect whether helping one moving client harms others |

For WebRTC, use synthetic or public test media and record browser statistics, not personal conversations. The W3C draft defines relevant counters; video freezes and audio concealment are still proxies for experience. Do not claim a mean opinion score or human QoE without a separate, valid assessment. [M12](https://www.w3.org/TR/2025/CRD-webrtc-stats-20250925/)

## Candidate-load information

Log the raw advertised load and its receive time. Also log controller-side measurements when available, using separate fields. If the publication or averaging window is known, save it. A fixed BSS Load value used for testing must be marked as injected data. Hostapd exposes these separate settings. [M02](https://android.googlesource.com/platform/external/wpa_supplicant_8/+/e1f26c3029a96c86624ab8f35b28c85d5401a4a3/hostapd/hostapd.conf)

Run one condition with recent reports, one with deliberately delayed reports, and one with missing reports. Apply the same reporting condition to all policies. A candidate throughput estimate must come from a stated model or a real probe. Never feed the controller an experimenter's true target queue and call it ordinary client knowledge.

## Trial sequence and comparisons

1. **Capability check.** Establish that each client can associate, exchange data, and complete the intended transition. Verify FT from the exchange and negotiated mode; a checked configuration box is not enough.
2. **Stationary reference.** Run each application without movement at fixed positions and low load. Check that instrumentation itself does not create large gaps.
3. **Transition-cost measurement.** Request transitions under controlled signal and load. Compare the same equipment with FT enabled and disabled where supported. Preserve the security method and record caching state. Use this stage to estimate an empirical cost distribution.
4. **Policy comparison.** Run a repeatable path with native behavior, signal plus hysteresis, load-aware selection, cost-aware selection without application class, and the proposed application-aware policy. For a native client, report that its internal observations and rules are unknown; it is not an identical-information software baseline.
5. **Stress and failure cases.** Test a stronger but busy candidate, rapidly changing load, stale reports, weak overlap, and a path with little remaining time near the target. Include conditions in which no handoff is the correct choice.
6. **Held-out validation.** Freeze parameters, then test a second route, load schedule, or client model. Report transfer failure as a result if it occurs.

Randomize policy order within route/load blocks. Pair trials by route, offered load, and starting association. Start with a small pilot to measure variance, then choose a fixed main-run sample count before examining policy rankings. A practical initial target is 30 complete path repetitions per main condition, subject to a precision analysis; it is not a universal power calculation. Do not keep adding trials only until a preferred result becomes significant.

The independent unit is the path run, not each packet. Confidence intervals should resample independent runs or blocks. Repeated handoffs on one walk share conditions. A rare-failure claim needs far more than a few dozen runs; report the event count and uncertainty explicitly.

## Reproducible record

Give every run an ID and save a small manifest containing software/configuration hashes, policy parameters, seeds for offered traffic, date, route, load, starting association, and clock checks. Keep application counters, controller observations, decisions, AP/client events, and packet-capture metadata in separate time-stamped files.

Classify outcomes as success, policy refusal to move, client refusal, transition failure, or invalid measurement. A failed transition is not an invalid measurement. Exclude a run only for a predeclared technical reason such as a broken capture or missing workload; retain its manifest and exclusion reason.

Publish anonymized metrics and configuration examples. Use trial-specific device IDs and application classes. Do not include passwords, personal content, or unrelated clients' identifiers. This is also simpler: the policy needs application requirements, not the content of a call.

## What would be enough to strengthen the paper?

Hardware evidence would support the mechanism if the direction of the simulated benefit survives realistic observation age, measured interruption costs, and a held-out condition. It would be stronger if application delivery improves without excessive roaming or harm to other clients. A negative result is useful: it can show that stale information, client discretion, or a very cheap handoff removes the simulated advantage.

IP-changing roaming, QUIC migration, distributed multi-link handovers, and modified openwifi radios remain separate extensions. They change what the controller can do and what an interruption means. They should not be used to inflate the scope of this first study.
