# Research steps before writing and extending the paper

The first package gives us a research question and an initial answer: the tested extra caution is not generally better than a simple application-aware rule. We should build the paper around what the evidence supports.

## Decide the intended contribution

There are two reasonable paths. An **exploratory simulation paper** can explain the trade-off, show why a plausible rule fails, and provide a reproducible benchmark. A **new roaming-system paper** needs a distinct method, a close comparison with earlier work, and much stronger validation. The current evidence is closer to the first path.

A possible narrower working title is **Application-Aware Wi-Fi Roaming Under Stale Load Information: An Exploratory Simulation Study**. The user's original title remains the overall project title. This is a title proposal, not a finished paper.

## Priorities and decision points

| Priority | Work | Why it matters | Completion evidence |
| --- | --- | --- | --- |
| 1 | Obtain the full IEICE application-context report and the RAQOH article | Their abstracts directly overlap with the broad idea | A step-by-step method comparison, with any unavailable detail marked |
| 2 | Explain the main failure cases using event traces | We need to know why caution delays a useful switch | Selected and counterexample traces chosen by a declared rule; before/after service around decisions |
| 3 | Give each AP different report ages and error patterns | The current age penalty treats all alternatives alike | Frozen comparisons against a pilot-tuned fixed margin on new environments |
| 4 | Add a simple, independently defined application model | Average missing service cannot distinguish a harmful long gap from several short gaps | Deadline misses or buffer stalls defined separately from the policy reward |
| 5 | Test unseen environments | New random seeds in the same equations are a limited test | Held-out layouts, load processes, movement speeds, and application requirements |
| 6 | Add real measurement costs and variable transitions | Free fresh RSSI and exact interruption costs are favorable assumptions | Scanning/report overhead, candidate failure, observation delay, and cost-estimation error |
| 7 | Add clients whose decisions change load | Needed for “dense network” and fairness claims | Worst-client service, network totals, and synchronized-switch stability |

The first two tasks should shape the manuscript plan. The later tasks depend on the strength of the claim we choose. More simulations alone will not repair a missing or invalid application model.

## A focused next experiment

Freeze the current simple baselines. Create a new layout and independent test seeds before changing the candidate. Give APs different load-report ages and different load-change rates. Compare three approaches: the simple application-aware rule, a tuned constant margin, and an AP-specific estimate of likely service. Use the same input information for all eligible baselines.

The key test is whether knowing **how unreliable a particular estimate is** helps beyond ordinary switching resistance. Age should be an input to the uncertainty model, not automatically treated as a probability. Check calibration: estimates labeled reliable should actually be wrong less often. The design should include cases where older reports remain useful and fresh reports become wrong quickly.

Any new rule must be tuned only on its training/pilot conditions. Keep the current data as exploratory evidence and create fresh test conditions for the next claim. Include the simplest baseline even when it wins.

## Application model choices

For an interactive profile, a first simulation extension could track packets with explicit delivery deadlines. For a streaming profile, it could track a playback buffer and stalls. These are different applications and should not be merged under one “video” label. Bulk traffic could use file completion time or useful delivered bytes.

The required thresholds, traffic pattern, and buffer size must be sourced or clearly stated assumptions. Test a range. Optimize one quantity and measure other outcomes too; otherwise the evaluation may simply reward the policy's own definition of success.

## Later validation

The user chose simulation for this stage. If equipment becomes available, the [validation protocol](hardware-validation.md) describes how to test the control path and actual useful-data gaps. A simulator or emulator extension must be checked for the exact roaming features it models. Using a well-known tool does not automatically validate missing handoff behavior.

## A paper outline for our next discussion

1. The practical decision and why interruption, application demand, and old information interact.
2. Related work and the precise contribution boundary.
3. Model, observations, policies, and every numerical assumption.
4. Experimental design, baseline tuning, pairing, and statistical limits.
5. Main findings, negative results, ablations, and model-error sensitivity.
6. Threats to validity and what would change the conclusion.
7. Reproducibility materials and a restrained conclusion.

Before submission, verify every bibliographic entry and numerical statement, update the literature search, follow the venue's AI-disclosure policy, and release a versioned evidence package. The present repository contains preparation for that discussion; it contains no submitted or finished manuscript.
