# What we learned about intelligent Wi-Fi roaming

**The first research cycle is complete. The main result does not support adding the proposed extra caution as a generally better roaming rule.** It reduces switches, but the simpler application-aware rule provides slightly better service across the full synthetic experiment.

This is a useful result. It tells us which idea deserves more work and which claim we should avoid. The next paper discussion can start from evidence rather than an assumed improvement.

## What the literature says

Application-aware handoffs are not a new topic. The closest recent work includes an IEICE report that uses application context to control handovers and a 2026 journal article with application-dependent QoS scoring. Earlier work also studies application-based selection and handoff costs. These overlaps mean that “we consider applications” is not a defensible novelty claim. The review records both the sources and the limits of what was accessible. [Recent review](literature/recent-review.md); [foundations](literature/foundations.md).

The standards solve different parts of the problem. Neighbor information, network advice, and a faster transition do not decide whether a particular switch is worth making. Client behavior and measurement access still matter. A future implementation must distinguish network advice from the client's actual decision. [Mechanisms and evidence](literature/mechanisms-and-evidence.md).

We examined **28 distinct sources**, including **21 research works** and **7 technical documents**. Sixteen research works are from 2023–2026. Fourteen papers received selected full-text inspection, while seven remain at abstract or excerpt level. This is a focused review, not a claim to have read all relevant research. [Source index](../references/source-index.md).

## The question we tested

When a device sees a better AP, should it switch now? We tested whether an application-aware decision improves when it also considers the modeled interruption cost and the age of candidate-load reports.

One simulated client moves among six APs. Two fixed application profiles represent different service requirements. Six movement/load regimes include balanced load, overload, sudden changes, reversals, and short visits. Interruption and report delay vary. Every policy faces the same traces and observation rules. [Question and hypotheses](research-question.md); [exact model](simulation-model.md).

The main score is service deficit: how far modeled service falls below an artificial application score. It is **not** the percentage of video freezes, lost calls, or dissatisfied users. The 250 ms decision model charges short interruptions fractionally but does not resolve individual packet deadlines.

## Main results

The table averages all 72 settings equally. Each row uses 2,880 policy runs, based on shared world traces. These averages describe the chosen experiment, not the population of campus Wi-Fi networks. Lower deficit is better. Handoffs are counted over each 180-second run.

| Rule | Service deficit score × 100 | Mean handoffs |
| --- | ---: | ---: |
| Signal strength | 20.065 | 17.263 |
| Load-aware | 19.374 | 20.488 |
| Application-aware myopic | 19.132 | 20.685 |
| Candidate with cost and report-age penalties | 19.182 | 19.831 |
| Candidate without switching cost | 19.165 | 19.941 |
| Candidate without report-age penalty | 19.129 | 20.505 |

The candidate improves the deficit score by **0.883 percentage points** compared with signal-only roaming, but worsens it by **0.051 percentage points** compared with the application-aware myopic rule. It makes about **0.855 fewer handoffs per run** than that myopic rule. Fewer switches therefore do not establish better service.

The cost and age ablations also have slightly lower average deficit than the full candidate. This does not prove that interruption cost never matters. It shows that this particular formula and parameter grid do not give a general benefit in this experiment. [Main results](results.md); [raw overall table](../results/overall_descriptive.csv).

![Difference across every main setting](../results/figures/all_conditions.png)

Each number is candidate minus myopic deficit, in percentage points. Blue favors the candidate; orange favors the myopic rule. All 72 settings are shown. The [paired comparison file](../results/paired_comparisons.csv) includes the corresponding exploratory intervals.

## What the review changed

An independent reviewer noticed that all candidate APs have the same report age in this model. Subtracting the same age penalty from every candidate is an extra switching threshold. It is not a calibrated estimate of uncertainty.

We therefore added a simpler application-aware rule with a constant threshold tuned on pilot seeds. Its selected threshold was 0.03, the same as the original myopic rule. The supplemental evaluation matches that rule. This gives no evidence that the more complex age-dependent threshold is needed in the main grid. The pilot also chose the candidate's longest horizon and smallest positive age penalty, pushing it toward less caution. [Independent review](independent-review.md).

We also changed true capacity while keeping candidate estimates unchanged. The candidate had a small average advantage over the myopic rule in the tested capacity-error cases. Those tests covered only two scenarios and two forms of overestimation. They do not overturn the main negative result or establish general robustness. [Mismatch experiment](model-mismatch.md).

## What we can conclude

Within this model, application-aware selection is worth keeping as a serious baseline. Adding a fixed short-horizon cost charge and a general age penalty needs a better justification. A report being old does not automatically mean that staying is safer: the current AP may already be poor, and an alternative may still be worthwhile.

The next useful research direction is to identify **when extra caution is justified**, rather than assume it should always increase with report age. That may require different uncertainty for each AP, a model of how load changes, and an application outcome that responds to the duration and pattern of interruptions.

## What is ready for the paper discussion

The evidence review, research scope, code, data, figures, and first conclusions are ready. We can now choose the paper's claim and structure together.

A careful exploratory paper could report this comparison and its failure cases. A claim of a new, superior Wi-Fi roaming system is not yet supported. The highest priorities are a full comparison with the closest work, a stronger application model, and evaluation in environments not used to design the rule. [Next steps](next-steps.md).
