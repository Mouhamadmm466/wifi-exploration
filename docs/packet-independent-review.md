# Independent methods review of the packet study

Review time: 2026-10-14T21:47:15.587456+00:00. This review was completed before inspecting held-out results. It is an internal review by a separate research agent, not external peer review. The reviewer helped define the prospective protocol but did not implement the simulator or choose settings from outcomes.

**Decision:** the reviewed code is suitable for running the declared synthetic experiment. No blocking information-leakage, service-time or packet-accounting error was found in the reviewed snapshot. This is a limited verification judgment, not evidence that the candidate works better.

## What was checked

The review covered [the model](../src/packet_roaming.py), [the runner](../scripts/run_packet_study.py), [the analysis](../scripts/analyze_packet_study.py), [the exact scenario configuration](../configs/packet-study.json), and [the prospective protocol](packet-study-protocol.md). The earlier study's unfavorable results were retained and used to justify a stronger constant-margin baseline and separate packet outcomes.

- All policies use a shared pre-generated world. Separate random streams determine signals, external traffic, report error, frame size and transition outcomes. Decision-time and target-AP keys keep transition draws independent of how many earlier actions a policy took.
- The controller sees cached signals, delayed load observations and delayed reports of already elapsed deadlines. It does not receive future movement, future offered traffic or the realized next handoff duration. The initial signal snapshot is common to all policies.
- Service during overlapping scan and transition blocks uses the union of their durations. A fractional transition end can use the target link for the remainder of a slot; a failed transition returns service to the original link.
- A voice success requires a complete packet by its deadline. A video success requires every packet of that frame by its deadline. Overflow, expiry and handoff drops remain in the generated denominator. The drain covers the longest application deadline.
- Moving the foreground client changes airtime available to background queues. It does not change externally generated background demand. Queues have finite packet capacity.
- Development and evaluation seeds and scenario names are disjoint. The runner saves selected settings and source hashes before evaluation and checks that they stay unchanged. The declared main design has 240 paired worlds and 2,400 policy runs.
- Analysis rejects incomplete policy cells, mismatched input hashes and unbalanced scenario/seed grids. It first averages paired differences over scenarios within each seed, then bootstraps the 40 seed blocks. Packet counts are not treated as independent experimental replicates.

## Findings and resolution

| Finding | Importance | Resolution before outcomes |
|---|---|---|
| A cost/age rule needs a well-tuned ordinary switching margin as a comparator. | High for scientific interpretation | The application-margin grid is tuned separately on development seeds. It is the primary comparator. |
| Dropping all queued focal packets at a handoff can favor policies that switch less. | High model dependence | Keep the assumption explicit and include the prospectively added retained-queue sensitivity. Its result must be reported even if unfavorable. |
| A background conservation residual based on a derived pending count would always be zero. | Medium verification defect | Implementer changed pending counts to use actual queued bytes and added a partial-packet/overflow test. |
| Conditional packet delay can hide dropped and late data. | Medium reporting risk | Report generated-deadline fractions as primary, plus late counts, on-time throughput and delay sample counts. |
| “Outage” and “freeze” field names could imply measured application behavior. | High claim-strength risk | Protocol defines them as consecutive missed scheduled-deadline runs. Actual useful-delivery gaps and decoded video freezes remain unmeasured. |
| Only the assumed mean transition duration is scaled in the underestimation condition. | Low wording mismatch | Protocol wording now distinguishes that term from the unchanged expected failure-extra term. |
| Generic source hashing and incomplete grids could weaken reproducibility. | Medium reproducibility risk | Runner hashes the actual selected protocol; analysis validates pairing and the expected main grid. |

## Limits that remain

This is a packet-and-queue model with slotted fluid airtime sharing. It does not implement an IEEE 802.11 contention process, retransmissions, inter-AP interference, authentication, real driver behavior or codec decoding. Dense geometry alone does not model dense-channel interference. The background rate and equal-airtime scheduler are declared assumptions.

Allocated focal service is spread across the active part of a slot. An isolated short packet can therefore be credited at the slot end even when physical serialization would finish earlier. Packet completion and measurement processing have time-step error. The predeclared 5/10/20 ms comparison is necessary; it cannot establish hardware timing accuracy.

Reported busy load measures background airtime and excludes focal airtime. The delayed background backlog divided by background rate is a score feature, not a measured FIFO wait for the arriving focal client. The model supplies telemetry more complete than many ordinary clients can obtain. Its practical collection and signaling cost require separate validation.

The own-miss guard uses a count-weighted mixture of voice-packet and video-frame deadline events. The primary outcome instead gives each stream equal weight. This is a fixed policy design choice. The candidate and its ablations receive this feature; the simpler baselines use their declared signal, load or application-quality rules. The guard removal helps separate this component's local effect.

All deadlines, load distributions, mobility paths, weights and noise parameters are assumed conditions. There is one moving foreground client, and background clients keep fixed associations. The study cannot show multi-client roaming stability, real fairness, human quality of experience or deployment readiness. Strong recent prior work also prevents a novelty claim from this experiment alone.

## Verification record

Independent command: `python3 -m unittest discover -s tests -v`.

Result: **29 tests passed**: 15 packet-model tests, 4 packet-analysis tests and 10 earlier model tests. Packet tests cover partial background packets, finite airtime, packet conservation under overflow, incomplete frames, final-window drain, fractional transitions and failure return, target-link service, overlapping blocks, exact-deadline success, delayed observations, future-state mutation, replay/order independence, fixed external streams across time steps, guard removal and dwell removal. Analysis tests cover a known constant paired effect and malformed pairing grids.

These tests are small internal checks. They do not validate the model against measurements. This review did not inspect or certify final held-out estimates, sensitivity results or paper claims; those require a later numerical audit.

## Reviewed snapshot

| File | SHA-256 |
|---|---|
| `src/packet_roaming.py` | `f31be12c232fd98f3fc6b57e92bb07a3014a0925c1395813245d1a34526fd27f` |
| `scripts/run_packet_study.py` | `4edbcdbfef362d4a7438d75a2be943ac373116ca97497c794933822cf7999074` |
| `scripts/analyze_packet_study.py` | `9546daec8c99b79622f9f8f3966361b6a820d53244c76247f1015a5c7f975219` |
| `configs/packet-study.json` | `f2c594eae07b80c2b18eb9a8a0e1ff5eff0dfe1b73d7f1a63809ed6839ae5db1` |
| `docs/packet-study-protocol.md` | `a76848b4af4769c5175d69f845fa2e04f2bc9a11b97f5ef40da1d5b727528bd4` |
| `tests/test_packet_roaming.py` | `c140a3cadd0ad4690eaf2a91a3201fceebfeea967589ee1aeb979674fddfffea` |
| `tests/test_packet_analysis.py` | `f126659bde7151f7473ca1166a9f42fc4330029097d772e1f57526fff23ea0ab` |
