# Independent manuscript review

Review date: 14 October 2026. Reviewed file: [wifi-roaming-paper.tex](../paper/wifi-roaming-paper.tex). This review checks numerical and scientific content. It is an internal agent review, not external peer review or the author's independent approval. The reviewer did not edit the manuscript.

**Finding:** no numerical discrepancy was found in the reviewed prose, tables or generated plot data. The negative primary result, stronger simple baseline, scenario exceptions, unequal tuning budgets and limited model scope are represented accurately. The methods and wording corrections listed below were applied and then checked in the revised source. No unresolved numerical or scientific-content correction remains from this review.

## Concrete corrections sent to the writer

| Importance | Location | Correction | Review status |
|---|---|---|---|
| Medium | Shared rule description and settings table | The one-second timer starts at an attempted move, including a failed attempt. Describe an interval between attempts, not a full second of association after a successful handoff. | Resolved; revised source checked. |
| Medium | AP telemetry description | All report fields are delayed. Added measurement noise affects the background-airtime load value only. Active-user counts and backlog-derived delay are exact at their source time, then delayed. | Resolved; revised source checked. |
| Low | Abstract and report-condition interpretation | The stale-report condition changes reporting period, delay/jitter and load noise together. Avoid attributing its full effect to report delay alone; use degraded report quality or freshness. | Resolved; revised source checked. |
| Low | Earlier-study appendix | Describe additional environments as synthetic. “External-environment” can sound like external physical validation. | Resolved; revised source checked. |
| Low | Generated bibliography | Remove duplicated punctuation after “et al.” and after the R02 title. | Resolved; bibliography has no doubled periods. |

The simulator reviewer's clarifications were also checked in the revised source: fixed own-miss report delay, continued idealized signal sampling during interruptions, time-step rounding, complete Earlier caution settings, and the distinction between nearest-rank within-run delay percentiles and interpolated cross-run percentiles.

## Numerical claims checked

The paper correctly reports the main candidate score of 2.047%, application-margin score of 1.943%, primary paired difference of +0.104 percentage points and interval [0.038, 0.173]. Its voice/video component differences and intervals also match. The reported candidate-minus-load and secondary load-minus-RSSI/application comparisons use the correct signs and percentage-point units.

Scenario claims were checked against the scenario summaries and independently computed secondary contrasts. This includes the nearly tied Burst load comparison, the Crowded source of candidate loss, and load-aware's adverse comparisons against RSSI in Burst load and application-margin in Short cells. Proposed is not incorrectly described as making fewer attempts than application-margin.

The voice-run means and interpolated 95th percentiles, longest video-run contrast, video long-run fraction interval, on-time delivery, conditional-delay contrast, aggregate background delivery and mean worst-user ratios match the saved tables. The manuscript correctly explains that conditional packet delay excludes packets that never complete.

The four ablation signs and intervals match the saved comparisons. The cost removal is the largest deterioration in that family; the dwell and guard intervals include zero. These are appropriately described as unretuned local removals, not proof that every component is necessary.

All eight sensitivity conditions and the matched reference agree with saved results. The primary candidate-minus-application point difference is positive in each condition, but several intervals include zero. The paper does not turn those point differences into universal significant wins. Its time-step values and changed ordering against RSSI are correct. It explicitly rejects numerical-convergence and device-level accuracy claims.

The earlier-study appendix correctly reports 17,280 executions, 72 cells, 40 seeds and six policies; deficits round to 0.191824 and 0.191316, and handoffs to 19.831 and 20.685. It does not equate the earlier service-deficit proxy with the packet study's deadline score.

Study counts reconcile: 456 + 1,032 + 2,400 + 1,280 + 320 = 5,488 policy runs in the declared study stages. Replays and small implementation tests are separate verification work. The 24 development worlds are reused during the expanded search, not counted as new independent environments.

## Generated tables and figure data

After the generated regions were populated, an independent read-only check verified:

- Ten policy rows in the main table and both ten-policy voice/video bar series.
- Six scenario point estimates and interval endpoints, including that all endpoints fit inside the plot's stated horizontal limits.
- Four empirical CDFs calculated from all 240 run maxima per policy, with tied durations counted together and each curve ending at one.
- Four ablation rows and nine sensitivity rows, including the supplementary load-aware means and matched-reference row.
- Ten handoff-versus-score points.
- All 24 red timeline spans against the saved flags for Short cells, seed 50001, with the correct voice/video deadline offsets.
- Seventeen citation keys, all with corresponding bibliography entries.

These are numerical, source-code and labeling checks of the generated figures. **The compiled pages have not been visually inspected by this reviewer.** Page layout, text overlap, clipping introduced by rendering and print legibility need separate visual verification. This review does not claim a successful LaTeX compilation.

## Source strength and interpretation

The related-work descriptions are consistent with the repository's reading records. The paper identifies the two close 2026 sources as abstract/metadata-only evidence and does not claim a new application-aware-roaming idea. Workshop/preprint status is visible in the relevant bibliography entries. The research count is 21 distinct works; the additional packet-method sources add six distinct technical/guidance documents to the original seven. The W3C item is a duplicate of an existing source, not an additional distinct document.

Primary-source spot checks confirmed that [Apple's client documentation](https://support.apple.com/guide/deployment/wi-fi-roaming-support-dep98f116c0f/web) describes candidate scoring using channel use and associated-client count. [RFC 7587, section 6.1](https://www.rfc-editor.org/rfc/rfc7587.html#section-6.1) gives a default preferred packet duration of 20 ms; it does not set this study's network deadline. [RFC 8836](https://www.rfc-editor.org/rfc/rfc8836.html) supports the limited usefulness of late interactive media. [F03's primary arXiv record](https://arxiv.org/abs/2004.08110) confirms the IEEE Access 2021 journal reference. The [dated W3C draft](https://www.w3.org/TR/2025/CRD-webrtc-stats-20250925/) uses rendered-frame timing for freezes, supporting the manuscript's distinction from missed-frame-run proxies. [IEEE's disclosure guidance](https://conferences.ieeeauthorcenter.ieee.org/author-ethics/guidelines-and-policies/submission-policies/) supports making AI assistance explicit; this review does not certify compliance with a specific future venue's submission format.

The major limitations are present: no inter-AP interference or actual MAC, correctly specified signal-to-rate calibration, idealized telemetry, one moving client, fixed-rate independent media, finite synthetic scenarios, development budget differences, selected boundary values and strong numerical-resolution dependence. The interpretation that score saturation and delayed penalty terms may explain the candidate's loss is properly marked as a possible explanation, not an isolated causal finding.

## Reviewed snapshot

The generated-data numerical check used manuscript SHA-256:

`38c1f4d74ee1c483e25b5648c786c787ede9488354ea6321c8385bd4a6d7bcd7`

The final wording and bibliography check used revised manuscript SHA-256:

`b1c21c1af3e71f72f9a10b270f73ab6dc8842c2c99418335946189275e83b316`

The generation manifest matched the revised generator's hash. The numerical-data audit and corrected-prose check are complete. Compiled-page visual verification remains the coordinator's separate task; this document does not claim that work was performed by this reviewer.

## Final layout check by the coordinating agent

The final standalone source compiled successfully in the desktop LaTeX compiler and was exported with Tectonic 0.17.0. All 15 pages were rendered and inspected. The six figures and five tables fit the pages. A missing timeline axis-label setting was corrected, and the timeline and tradeoff pages were rendered and inspected again. The final log contains no overfull/underfull boxes, missing characters, unresolved references, or LaTeX warnings. The PDF text has no unresolved citation markers. `paper/validation.json` records the final source and PDF hashes. This remains an automated/agent review, not completed human author verification.
