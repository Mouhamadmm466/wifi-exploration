# Independent numerical review of the main packet study

The raw table contains **2,400 policy runs in 240 paired worlds**: six scenarios, 40 seeds and ten policies. Every world's policies have the same input hash. The primary score was checked against one half of the voice packet miss fraction plus one half of the video frame miss fraction.

An independent calculation reproduced all 18 overall comparisons checked against the published analysis: candidate minus application-margin and candidate minus load-aware, each for nine metrics. Point estimates and confidence limits agreed within 0.000000000001. The calculation used one equal-scenario average per seed and 5,000 bootstrap resamples of the 40 complete seed blocks, with seed 81631.

## Main finding

The added candidate did not improve the primary outcome. Its mean score was **2.0471%**, compared with **1.9427%** for the tuned application-margin rule and **1.2821%** for the tuned load-aware rule. Positive candidate-minus-comparator differences mean more missed deadlines.

| Comparison | Score difference, percentage points | Paired 95% interval |
|---|---:|---:|
| Candidate minus application-margin: original primary comparison | +0.1044 | +0.0384 to +0.1732 |
| Candidate minus load-aware: secondary comparison | +0.7650 | +0.6680 to +0.8652 |
| Load-aware minus RSSI: secondary comparison | −0.6859 | −0.7760 to −0.5945 |
| Load-aware minus application-margin: secondary comparison | −0.6606 | −0.7517 to −0.5727 |

The load-aware comparisons were computed directly from paired raw rows. Their intervals were not made by subtracting other confidence intervals. The primary comparison remains candidate minus application-margin; the capacity-baseline comparisons are descriptive secondary analyses.

Both voice and video miss fractions were higher for the candidate than for the two strong baselines overall. The candidate made **8.6292 handoff attempts per run**, compared with **7.4333** for application-margin and **9.5125** for load-aware. The first study's narrative about fewer switches cannot simply be carried into this result: the candidate switches more than application-margin here.

The candidate's mean longest video deadline-miss run was 23.3 ms shorter than application-margin, but 144.0 ms longer than load-aware. These are means of per-run missed-frame-run maxima, not decoded video freeze measurements. Average background delivery was 96.2232% for the candidate and 96.1533% for load-aware, a small measured trade-off inside this model.

## Exceptions matter

The load-aware rule is the best overall tested rule on the declared equal mix; it is not best in every situation. Compared with RSSI in `burst_load`, it increases the score by **0.2839 percentage points** (secondary interval +0.1844 to +0.3807). Compared with application-margin in `short_cells`, it increases the score by **0.2114 points** (+0.0726 to +0.3496). These results rule out a universal-winner claim.

The candidate also has different trade-offs by scenario and application. For example, relative to load-aware in `short_cells`, its voice miss fraction is lower while its video miss fraction is higher. The equal-weight score is an explicit engineering choice and cannot replace both component results.

The controller and the actual service model share the assumed RSSI-to-rate curve. Observations are still delayed and noisy, and packet outcomes are calculated separately, but the load-aware rule has correctly specified rate calibration inside this model. The transition-cost underestimation check does not test an incorrect rate map or candidate-capacity estimate. This limits any claim about real-client capacity estimation.

## Evidence and reproduction

- [Independent main audit values](independent_main_audit.json) record raw-table hash, policy means, 18 paired contrasts and scenario differences.
- [Secondary comparison table](secondary_capacity_comparisons.csv) contains overall and per-scenario paired capacity-baseline comparisons for five metrics.
- [Secondary comparison manifest](secondary_capacity_comparisons.manifest.json) records source, input and output hashes, the seed and the number of resamples.
- [Reproduction script](../../../scripts/secondary_capacity_comparisons.py) reads raw rows and computes those secondary intervals independently of the main analysis script.

Run from the repository root:

```sh
python3 scripts/secondary_capacity_comparisons.py
```

These intervals describe variation across the chosen seeded synthetic environments. They do not establish real-device confidence, human QoE, scientific novelty or universal superiority. Sensitivities require separate review after their complete manifests are available.
