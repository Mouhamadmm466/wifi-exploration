# Research process and decision record

This record explains the evidence, assumptions, and reasons behind the work in simple words. It records decisions and their justification, rather than a private stream of internal reasoning.

## The request and constraints

The user asked for a deep research exploration before starting the paper, with clear documentation and experiments in the supplied GitHub repository. On 14 October 2026, the user confirmed that the work should use simulation and that the first package should be ready today, as soon as possible.

That makes this a focused first research cycle. It does not make a one-day review exhaustive, and it does not turn synthetic measurements into hardware evidence.

## How the work was divided

Three parallel workstreams covered recent papers, network mechanisms and future validation, and the simulator. A separate integration pass examined older work, narrowed the research question, checked the implementation and results, and assembled the report.

The researcher remains responsible for checking references, methods, and claims before publication. The use of AI assistance should be disclosed according to the eventual venue's policy. No venue has been selected and no submission has been made.

## Decisions and reasons

| Decision | Reason | What could change it |
| --- | --- | --- |
| Preserve the broad title but narrow the testable question | Earlier work already covers application context and handoff cost | A full review may reveal a clearer, different gap |
| Use primary sources | Abstract aggregators and search summaries can omit conditions or confuse dates | Use an aggregator only to find a primary source |
| Label how deeply each paper was read | An abstract cannot establish what the full method omits | Obtain and inspect the full paper |
| Start with one client | Makes causal policy comparisons easier to inspect | Add interacting clients before network-wide claims |
| Give policies the same observation mechanism | Hidden future or perfect candidate information can create a false advantage | Run a separately labeled oracle only as a bound |
| Keep a strong application-aware comparator | An RSSI-only victory would not isolate the new idea | Reproduce a closer published method when full details are available |
| Charge the actual modeled interruption fraction | Rounding short handoffs to a whole simulation step distorts results | Use a finer event-based model if timing effects matter |
| Use paired random seeds | Each rule should face the same movement and background conditions | Keep pairing when expanding the experiment |
| Include control and difficult cases | A policy must be tested where its assumptions fail | Add cases suggested by observed failures |
| Retain unfavorable results | A failed hypothesis is useful research evidence | Change a rule only in a separately documented experiment |
| Use a proxy service metric | No actual player, codec, or user study is present | Add an application model and validate its outputs |
| Keep a local and Git version of the package | Code, configuration, data, and explanation should be reviewable together | Add archival release identifiers when the work stabilizes |

## Evidence levels

**Source-backed fact:** supported by a linked source, with its setting and reading depth stated.

**Assumption:** a choice that makes the simulation possible, such as a load-to-delay function. It is not a measured property of a campus network.

**Hypothesis:** an expected relationship that the experiment may reject.

**Simulated finding:** a result from the saved configuration and random seeds. It applies to that model and experiment.

**Open question:** something that remains unresolved, including novelty, device compatibility, and real application benefit.

## Search and review limits

The review prioritizes work from 2023 to 14 October 2026, with older papers used to check foundational ideas and novelty. Search terms and selected sources are recorded in the literature files. Search-engine “published ago” labels were not treated as publication dates. Dates were checked against publisher, author, or institutional records where available.

This is a targeted evidence review, not a systematic review. No invented screening totals, database coverage claims, or claim of reading every relevant paper is made. Full-text access and version differences are recorded instead of being hidden.

## How to continue without losing the evidence

Keep the current configuration and results. For a new idea, save a new configuration and result directory. Explain the reason for the change before examining its final evaluation results. Do not repeatedly tune on the current evaluation seeds and continue calling them unseen data.

If a bug changes results, preserve a short explanation of the bug and regenerate all affected comparisons. If an assumption changes, treat that as a new experiment. A statistical interval only describes randomness inside the selected model; it cannot measure the error caused by an unrealistic model.

## What changed during this cycle

The first search found direct prior work, so the research question was narrowed before making a novelty claim. Independent review then showed that the age penalty could act like ordinary switching resistance. A tuned fixed-margin comparator was added to test that explanation.

The main results did not favor the complete candidate over the simple application-aware rule. We retained that result. A separate capacity-error sensitivity found some benefit in narrower conditions, which is reported as a limited follow-up rather than a replacement for the main experiment.

The final reproduction check found two command-path problems in the supplemental scripts. They were fixed and those experiments were rerun. No score equation or main-run setting was changed to improve the result. This sequence is the practical learning from the cycle: check prior work, test a precise idea, challenge the comparison, preserve unfavorable evidence, and make the work repeatable.
