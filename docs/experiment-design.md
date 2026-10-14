# Experiment design and interpretation

This is a reproducible exploratory experiment. The question and comparison structure were set before the main evaluation. This document is not an externally registered protocol, and the simulation has not been calibrated to a real network.

## What is being compared

The experiment changes the decision rule while keeping the movement and background load fixed. This lets us ask what the rule caused **inside the chosen model**. It does not show what a real device would do.

The comparison has three simple policies: signal strength with hysteresis, estimated available rate with a switching margin, and application-aware service scoring. The candidate adds an interruption charge and a penalty for old candidate information. Two versions remove one of those additions at a time. Removing a component is called an ablation; it helps show which part of the rule matters.

These are transparent baseline families, not exact reproductions of a named commercial client or published algorithm. Their descriptions and equations are in the [model document](simulation-model.md).

## Why pairing matters

Each random seed creates one movement and load realization for a scenario. Every policy receives that realization. If we used different traces for each policy, an apparent improvement could come from an easier route or lower load.

For each experimental cell, subtract the comparator's result from the candidate's result for every seed. Then summarize those paired differences. For service deficit, a negative difference favors the candidate. A change of −0.01 means one percentage point less deficit, not a one-percent relative reduction.

Timesteps within a route are correlated. They must not be treated as hundreds of independent experiments. A seed is the unit of repetition. When the same seed is used across settings, those settings must remain grouped when building an aggregate confidence interval.

## Statistical interpretation

The paired bootstrap resamples whole seed-level differences and reports the middle 95% of bootstrap mean differences. This estimates variation from the modeled random conditions. It does not cover model error, unknown devices, or unseen sites.

Many cells and comparisons are inspected. Their intervals are exploratory and are not corrected for multiple comparisons. We therefore do not select the best-looking interval as a confirmatory result. Both unfavorable cells and the full result tables remain available.

The limited pilot grid chooses parameters using pilot seeds. The main evaluation uses separate seeds. This protects against direct seed reuse but does not remove bias from selecting the model, scenarios, objective, or parameter grid. A new final test set is needed after further changes guided by these results.

## Negative and control cases

The experiment includes balanced load, uneven load, overload, sudden changes, movement reversals, and short dwell. Balanced load checks whether more complex logic is useful when there is little congestion advantage. Overload checks whether switching can solve a problem shared by all candidates. Reversals and short dwell make a fixed planning horizon less reliable. Sudden changes make old reports dangerous.

The fast shuttle is a stress test, not an ordinary walking-speed campus route. Labels and parameter choices must stay attached to the conclusions.

## What would make the comparison misleading

| Risk | Control in this first study | Remaining limit |
| --- | --- | --- |
| Future information leaks into the policy | A small observation interface; reports only from the present or past; causal tests | Current measurements are still idealized |
| Switching cost rounded to the timestep | Fractional service loss during the modeled blackout | No packet-level timing or transport recovery |
| Weak baseline selected to make a candidate win | Several baseline families and pilot parameter grids | Limited grids and unequal numbers of candidate settings; no exact recent-paper replication |
| A score rewards its own assumptions | Report unserved demand and handoff interruption separately | Service deficit remains a designed proxy |
| Too many correlated observations inflate confidence | Seed-level paired comparisons | Confidence applies only within the model |
| All clients moving together overload one AP | Explicitly excluded from the first model | Cannot claim network-wide stability or fairness |
| The estimator knows the simulator's exact equation | Disclose this favorable assumption; run a separate mismatch sensitivity | A few perturbations do not replace calibration |
| App class or required rate is wrong | Explicit profiles and parameters | Misclassification and simultaneous apps are not in the first experiment |

## Planned continuation after this package

The first priority is to explain any failure against the application-aware comparator. Then test a different layout and load process with frozen parameters, and vary the application thresholds and estimator errors. Add a session-protection baseline inspired by the closest prior work after its full definition is available. A locally designed “stay” rule could be useful sooner, but it must not be presented as a replication.

A later packet or emulation study should introduce real application software, scan cost, variable interruption, candidate failures, and control latency. A multi-client study should let decisions change load and should measure the worst-served client as well as the average. [Future validation](hardware-validation.md) gives a concrete path if equipment becomes available.
