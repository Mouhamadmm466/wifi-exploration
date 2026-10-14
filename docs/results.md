# What the exploratory experiment found

The proposed rule did **not** improve the main service score over the simpler application-aware rule across the full test grid. It made fewer handoffs, but keeping a connection longer sometimes caused more harm than the saved interruptions. This negative result matters. It prevents us from claiming that adding more caution automatically gives better roaming.

These are results from a small, assumed decision model. They are not measurements from Wi-Fi hardware or proof of better video calls. Read [the simulation model](simulation-model.md) for every equation, policy, information limit, and main assumption.

## What was run

The main evaluation used 72 settings: six scenarios, two application profiles, two handoff interruption times, and three load-report delays. Each setting used the same 40 evaluation seeds for all six policies. This produced **17,280 policy runs**. These runs reused **240 underlying world traces**: six scenarios × 40 seeds. The policy runs are not 17,280 independent physical experiments.

The pilot used six separate seeds. It selected a 2 dB RSSI margin, a 15% relative capacity margin, an 8-second candidate horizon, and a 0.05 age penalty. These choices were written to a file before evaluation began. The candidate chose the longest horizon and smallest age penalty in its grid. This suggests that the pilot preferred relatively little extra caution. It does not establish that these are globally optimal settings.

The full main script took about 175 seconds in the recorded environment. It also ran 6,480 pilot policy runs and 1,440 horizon-sensitivity runs. The [run manifest](../results/run_manifest.json) records the environment, fixed config, parameters, and source hashes.

## Overall results

This table averages all 72 settings equally. It describes this test grid, not the average experience of a real campus user. Lower service deficit is better. All handoff counts are per 180-second run.

| Policy | Mean service deficit | Mean unserved demand fraction | Mean handoffs | Mean ping-pong returns |
|---|---:|---:|---:|---:|
| Signal-only, `rssi` | 0.200652 | 0.178633 | 17.262 | 2.171 |
| Capacity-aware, `load_aware` | 0.193739 | 0.171389 | 20.488 | 3.965 |
| Application quality, `app_myopic` | 0.191316 | 0.171308 | 20.685 | 4.353 |
| Proposed cost-and-age caution | 0.191824 | 0.171462 | 19.831 | 3.647 |
| Proposed without cost penalty | 0.191648 | 0.171420 | 19.941 | 3.737 |
| Proposed without age penalty | 0.191287 | 0.171187 | 20.505 | 4.201 |

The proposed rule reduced deficit by 0.008829 compared with signal-only roaming. This is 0.883 percentage points on the artificial service scale. Against the simple application-aware rule, it **increased** deficit by 0.000508, or 0.051 percentage points, while saving 0.854 handoffs per run. The difference is small, but it has the wrong direction for a broad improvement claim.

Removing either extra penalty improved the overall mean deficit. This does not prove that handoff cost or stale data never matter. It shows that this particular rule did not balance those concerns well across the declared scenarios.

The full source table is [overall_descriptive.csv](../results/overall_descriptive.csv). Its pooled means are descriptive; we do not attach an interval that incorrectly treats reused settings as independent runs.

## The outcome depends on the setting

Each confidence interval below comes from 2,000 bootstrap samples of the 40 paired seed differences **within one setting**. A difference is proposed minus application-myopic. Negative values favor the proposed rule.

| Illustrative setting | Mean deficit difference | Pointwise 95% interval | Mean handoff difference |
|---|---:|---:|---:|
| Abrupt loads, realtime, 200 ms interruption, 8 s report delay | -0.007084 | [-0.009974, -0.004125] | -5.625 |
| Short dwell, bulk, 200 ms interruption, 8 s report delay | +0.006177 | [+0.005525, +0.006841] | -0.050 |

These are the best and worst observed mean differences against application-myopic, selected **after** seeing the results. They are useful examples, not independent confirmation. The first pattern is consistent with caution avoiding changes based on misleading reports. The second is consistent with delayed useful changes during short visits. These are interpretations of the aggregate pattern; event-level traces are needed to verify the mechanism.

Across the 72 settings, the pointwise intervals favor the proposed rule over application-myopic in 8 settings and favor application-myopic in 41. The remaining 23 include zero. These counts have **no multiple-comparison correction** and are descriptive. The result is not a tally of 72 independent research claims.

Negative and control cases also matter:

- Under balanced load with realtime traffic, signal-only deficit was 0.009922 and proposed deficit was 0.010234. The extra logic was unnecessary in this control case.
- Under overload with bulk traffic, all policies left about 71% of offered demand unserved on average. Choosing another AP did not create missing capacity.
- With abrupt loads, bulk traffic, 200 ms interruption, and 8 s report delay, the proposed rule was worse than signal-only by 0.006540, with a pointwise interval [0.002138, 0.011142]. Richer but stale information can lead to worse choices.

See [all paired comparisons](../results/paired_comparisons.csv), [cell means](../results/cell_summary.csv), and [scenario summaries](../results/scenario_descriptive.csv). The complete seed-level observations are in [seed_metrics.csv](../results/seed_metrics.csv).

## A simpler explanation was checked

Independent review found an important issue: all alternative APs have the same report age. The age penalty therefore acts as an extra switching threshold. It does not rank APs by different levels of uncertainty.

We added a diagnostic application-aware policy with a fixed quality margin. It searched 0.03, 0.08, 0.15, and 0.25 using only the original pilot seeds. The selected margin was **0.03**, the same as the original application-myopic rule. Its evaluation outputs match that rule exactly. The simpler alternative was therefore already competitive, and the added diagnostic does not support a need for the proposed age caution in the main grid.

This diagnostic was added after the main run started, following code review and before inspection of its evaluation results. It is an exploratory addition, not an independently preregistered test. Its pilot choices are in [static_margin_pilot_selection.csv](../results/static_margin_pilot_selection.csv), and its results are in [static_margin_seed_metrics.csv](../results/static_margin_seed_metrics.csv) and [static_margin_paired.csv](../results/static_margin_paired.csv).

## The planning horizon is an important assumption

At an 8-second report delay and 200 ms handoff interruption, we repeated all scenarios and profiles with three horizons. We kept the selected age penalty and did not choose new parameters from these results.

| Assumed holding horizon | Mean service deficit | Mean handoffs |
|---|---:|---:|
| 1 second | 0.226232 | 17.785 |
| 3 seconds | 0.206947 | 20.281 |
| 8 seconds | 0.205751 | 20.581 |

A short horizon makes the same handoff cost look large. The policy avoids more handoffs, but service becomes worse in this sensitivity set. A fixed horizon is not a good substitute for knowing whether the device will stay near an AP. See [horizon_sensitivity.csv](../results/horizon_sensitivity.csv).

## What happens when the prediction model is wrong

A separate review-added diagnostic changed true capacity while keeping the candidate predictions unchanged. It used only hotspot and abrupt-load scenarios, fewer seeds, and selected delays and costs. In these selected cases, overestimating candidate capacity made caution more useful. This is a reason to study prediction errors, not a reason to replace the main negative result with a favorable subset.

Read [the model-mismatch diagnostic](model-mismatch.md) for its exact design, results, limitations, and seed-block intervals. It reuses evaluation seeds, tests only certain overprediction errors, and does not add a newly tuned static-margin competitor for that subset. It is an exploratory sensitivity check.

## What the evidence supports

The evidence supports a narrow statement: **application information helped relative to signal-only selection in many settings of this model, but fixed cost-and-age caution did not improve on simple application-quality selection across the full grid.** Caution helped in some stale or overoptimistic cases and hurt in others, especially when useful opportunities were short.

It does not establish a new roaming method, a real application-quality gain, a complete comparison with published methods, or a result about 802.11k/v/r performance. It also does not show that reinforcement learning is needed. A more complex method must first beat simple, well-tuned thresholds under the same observations.

The next research question should be more focused: **Can a device decide when its candidate estimates are trustworthy, and when there is enough useful time to repay a handoff?** A stronger study would vary report ages separately by AP, include errors in both directions, measure realistic interruption distributions, and compare adaptive policies against tuned static thresholds. Those experiments need new held-out traces after the design is fixed.

Read next: [the research question](research-question.md), [the experiment design](experiment-design.md), and [the model assumptions](simulation-model.md).
