# Application-Aware Handoffs in Dense Wireless Networks

**Completed version 2 simulation study — 14 October 2026.** This repository contains a targeted literature review, an explicit packet-and-queue model, reproducible experiments, all results, and research documentation. The complete 15-page manuscript, with six figures and five tables, is available at [paper/wifi-roaming-paper.tex](paper/wifi-roaming-paper.tex) and [paper/wifi-roaming-paper.pdf](paper/wifi-roaming-paper.pdf).

The proposed rule **did not beat the simpler application-margin rule on the main outcome**. Its mean deadline-miss score was **2.0471%**, compared with **1.9427%** for the application-margin rule. It also attempted more handoffs. The capacity/load rule had the lowest overall score, **1.2821%**, but was worse than other rules in the burst-load and short-cell scenarios. We keep these unfavorable results and explain their limits.

## Start here

1. [Results in simple English, with all five figures](docs/packet-results.md)
2. [What the packet model represents](docs/packet-model.md)
3. [Study protocol and the documented development amendment](docs/packet-study-protocol.md)
4. [Reproduction instructions and evidence checks](docs/packet-reproduction.md)
5. [Research decisions](docs/full-study-decisions.md) and [independent model review](docs/packet-independent-review.md)
6. [Independent numerical review](results/packet/additional_load/main-numerical-review.md) and [the capacity/load sensitivity supplement](results/packet/additional_load/overview.md)

The main outcome gives equal weight to missed voice-packet deadlines and missed whole-video-frame deadlines. It is an engineering score, **not a measurement of human call quality**. The simulation uses assumed traffic, radio-service curves, reporting errors and handoff delays. It is not a complete IEEE 802.11 implementation, an ns-3 experiment, or a hardware testbed.

![Voice and video deadline misses for every tested policy](results/packet/figures/voice_video_deadline_misses.png)

Every main policy is shown. Lower bars mean fewer missed deadlines in this model. [The full results guide](docs/packet-results.md) explains the scenario differences, handoff trade-offs, long missed-deadline runs, and the preselected example timeline.

## What was run

| Part of version 2 | Policy runs | What the count means |
|---|---:|---|
| Two development rounds | 1,488 | Parameter selection on the same 24 development worlds; some settings were repeated |
| Main held-out comparison | 2,400 | 6 scenarios × 40 seeds × 10 policies; 240 paired worlds |
| Eight planned sensitivity conditions | 1,280 | 4 scenarios × 10 seeds × 4 policies per condition |
| Separate capacity/load supplement | 320 | The frozen capacity/load rule in the same eight conditions |

This is **5,488 executed policy runs**, plus 18 diagnostic trace replays. Reused table rows and the matched reference subset are not extra simulation runs. These are not thousands of independent physical networks.

All policies face matched external inputs within a scenario and seed. Parameters were selected on separate development seeds and frozen before the main evaluation. One search-grid extension followed the initial development results; its original records and unequal tuning budgets remain visible in [the protocol](docs/packet-study-protocol.md).

## Literature and research scope

The combined record contains **34 distinct sources: 21 research works and 13 technical documents**, not 34 research papers. Start with the [source index](references/source-index.md), [packet and writing sources](references/packet-sources.json), [recent literature review](docs/literature/recent-review.md), [older foundations](docs/literature/foundations.md), and [roaming mechanisms](docs/literature/mechanisms-and-evidence.md).

Fourteen research works received selected full-text inspection; seven were read at abstract or excerpt level. This is a targeted review, not an exhaustive search. The closest 2026 application-aware works still need full-method comparison. No external paper has been independently replicated, and this project makes no first-ever algorithm claim. [The glossary](docs/glossary.md) explains common terms.

## Reproduce or inspect the evidence

The simulator and analysis use Python's standard library. Python 3.10 or newer is required; the recorded run used Python 3.14.5. Figure export also needs Matplotlib and NumPy. Use a fresh repository copy for a new run, because the main runner writes generated result files.

```sh
python3 -m unittest discover -s tests -v
python3 scripts/run_packet_study.py --stage all --workers 4
python3 scripts/analyze_all_packet_results.py
```

These commands repeat the final development grid, main evaluation and original eight sensitivity conditions. [The full reproduction guide](docs/packet-reproduction.md) covers the separate capacity/load supplement, archived first development round, diagnostic replays, figure export, and artifact validation.

Read the [raw main results](results/packet/main_runs.csv), [policy summary](results/packet/policy_summary.csv), [scenario summary](results/packet/scenario_summary.csv), [paired comparisons](results/packet/paired_contrasts.csv), and [analysis manifest](results/packet/analysis_manifest.json) without rerunning the simulation. Code keys and figure names are mapped in [the results guide](docs/packet-results.md).

## Earlier study and next steps

Version 1 is preserved as a historical decision-level experiment. Its service-deficit score differs from version 2's packet/frame deadline score, so their numerical values are not directly comparable. Read the [version 1 results](docs/results.md), [original model](docs/simulation-model.md), and [original reproduction guide](docs/reproduction.md).

The next stronger test needs measured rate and telemetry errors, a network-stack implementation or physical validation, and fuller comparison with the closest literature. The [future hardware protocol](docs/hardware-validation.md) describes one path. No physical experiment has been performed.

Code, analysis, figures and writing were prepared with AI assistance, with automated checks and independent agent review. These checks are not external peer review. Research authors should verify the final manuscript and follow the selected venue's disclosure policy; [the writing guide](docs/paper-writing-guide.md) records the relevant sources.
