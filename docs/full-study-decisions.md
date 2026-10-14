# Decisions for the completed simulation study

This log records research choices and their reasons. It is an explanation of the method, not a private thinking transcript. The study date is 14 October 2026.

## Scope agreed with the researcher

Mouhamad Mamane requested a simulation study, followed by a complete LaTeX paper. The practical goal is to help a moving device change access points while protecting real-time traffic. The simulation can test particular mechanisms and failure cases. It cannot prove that every real call will continue without interruption.

The first study is kept as the original experiment. Its code, measurements and negative result are not replaced. The new packet study has separate code, configurations, raw results and documentation. This makes the development of the research visible.

## Why the model changed

The original model converted signal and load into one service score. That was useful for checking a decision rule, but it did not represent packets arriving, waiting, expiring or reaching a playback deadline. Two policies with the same average service could cause very different interruptions.

The new study therefore uses generated voice packets and packetized video frames. It tracks delivery against deadlines. Background clients share AP service with the moving client. Their queues change when the moving client changes AP. This allows a direct check of application-delivery gaps and an explicit account of effects on other users.

The radio service remains an abstraction. Implementing packets does not implement channel contention, authentication, retransmissions or an actual media codec. This limitation belongs in the paper, not only in this log.

## Why the algorithm changed

The original age penalty sometimes delayed a useful move. A uniform delay penalty can behave like extra hysteresis rather than a meaningful estimate of uncertainty. The new candidate uses AP-specific report ages, a short prediction based on earlier signal readings, an estimated transition cost, and a response to a degraded serving connection.

Each added component has a version with that component removed. A fixed-margin application-aware rule is tuned independently. The candidate is allowed to lose. A method is not better just because it is more complex or changes AP less often.

The name `predictive` describes this study's simple signal-trend heuristic. It does not mean machine learning, knowledge of the future, or demonstrated novelty compared with every published method.

## How favorable selection is limited

The new development seeds and final seeds differ from those in the original study. Three development environments are used for parameter selection. Six final environments change AP placement, speed, direction or traffic pattern. The exact grid is stored before final evaluation.

Every final policy faces the same external inputs within a scenario and seed. The comparison uses differences within these pairs. The uncertainty calculation resamples whole seed blocks and retains all six scenarios together. Packets are not treated as thousands of independent experiments.

The primary outcome gives equal weight to the voice packet miss fraction and the video frame miss fraction. This weighting is an engineering choice, so both parts are also reported separately. Background service, long gaps and switching counts remain visible rather than being hidden inside a convenient score.

## Why the paper uses careful language

Application-aware Wi-Fi selection already appears in earlier work. The closest 2026 abstracts overlap with the broad motivation. Their full methods were not obtained, so this project does not claim to reproduce them or establish a first-ever algorithm.

A complete simulation paper can still make a useful contribution: a clear model, a transparent decision rule, a controlled comparison, reproducible evidence and an explanation of failures. Its language should match that evidence. The paper uses simple sentences, defines technical terms, and separates observed results from possible real-world implications.

## Execution and corrections

The prospective protocol is in `packet-study-protocol.md`; the runnable settings are in `../configs/packet-study.json`. The selected parameters and source hashes are saved before the held-out evaluation. The final results report and independent review record the completed runs and any corrections made during verification.

## A development result that changed the search

The initial packet-development run tested 19 parameter settings on 24 worlds. The best settings for several families lay at a search boundary. The load-aware baseline also had a lower deadline-miss score than the more complex candidate. These were development results; the held-out environments had not been evaluated.

We therefore made one documented search extension. It widened the simpler baselines' margins and the earlier rule's horizon. It also tested whether the candidate should react to a smaller fraction of recently missed deadlines. The new round contains 43 settings on the same 24 development worlds. The original 456 runs and their exact protocol remain in `results/packet/development_history`.

This change was informed by development results. It was not part of the original pre-outcome grid. The candidate received 24 settings, while each simpler tunable family received four to six; their tuning budgets are unequal. The protocol states this directly. We committed to ending the search after this one extension and reporting any remaining boundary choices. No held-out result is used to select the parameters.

## Completed evaluation and the conclusion

The packet study completed 5,488 policy executions, plus 18 exact trace replays. The proposed rule had a 2.047% deadline-miss score, compared with 1.943% for the tuned application-margin baseline. The paired difference was +0.104 percentage points, with a 95% interval from +0.038 to +0.173. The candidate also made more handoff attempts. We did not change its parameters after this unfavorable result.

Capacity/load had the lowest overall score, 1.282%, but performed worse than Signal in the burst-load scenario and worse than App margin in short cells. These exceptions remain visible. The paper presents the study as a controlled comparison with a negative primary result, not a successful demonstration of interruption-free roaming.

The eight sensitivity conditions and the separately frozen capacity/load supplement all completed. The time-step check materially changed effect sizes and some rankings. It does not establish numerical convergence. The stale-report condition changes several report properties together, so the paper does not attribute its whole effect to delay alone.

## Analysis optimization and independent checks

The bootstrap code originally recreated the same resampling indices for every contrast. We cached that identical sequence to reduce analysis time. The main paired-results CSV was byte-identical before and after this optimization, and all four analysis tests passed. The evidence is in `results/packet/analysis_optimization_check.json`. Frozen simulation code, parameters, raw outcomes and the statistical method did not change.

Separate reviews checked the implementation, numeric claims, source strength and figure data. They clarified that the one-second rule starts at a handoff attempt, only load reports have added measurement noise, and numerical step changes also affect observation processing. These were manuscript corrections to match the existing implementation. The detailed review is in `packet-paper-review.md`.

## Visual evidence and manuscript

The paper contains a model diagram, all-policy voice/video bars, per-environment paired intervals, a distribution of long voice miss runs, a preselected call timeline, and a handoff-versus-miss plot. Values and coordinates are generated from saved results, not drawn by eye. The illustrative timeline was selected before held-out outcomes. Standalone graph files and their input hashes are retained in `results/packet/figures`.

The LaTeX manuscript uses simple language and a conventional scientific structure: abstract, background, related work, model, algorithm, experiment design, results, discussion, limits, conclusion, reproducibility, disclosure and references. It is a complete manuscript for author review. It does not invent an affiliation, funding source, acceptance status, hardware experiment, or completed human review.
