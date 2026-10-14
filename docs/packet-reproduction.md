# Reproducing and checking the packet study

The packet model, study runner, analysis, trace replay, tests, and result validator use Python's standard library. Python 3.10 or newer is required. The recorded runs used the Python version, operating system, process count, and timing stored in each run manifest. Plotting separately requires Matplotlib and NumPy.

Use a fresh copy of the repository when repeating the commands below. They replace generated tables in that copy. Keep the delivered study record available for comparison.

## The saved evidence

The study has separate development and evaluation records:

| Record | Policy runs | Meaning |
|---|---:|---|
| Initial development round | 456 | 19 configurations across 3 scenarios and 8 seeds |
| Expanded development round | 1,032 | 43 configurations across the same 24 development worlds |
| Main held-out evaluation | 2,400 | 6 scenarios × 40 seeds × 10 policies |
| Eight sensitivity conditions | 1,280 | Each condition uses 4 scenarios × 10 seeds × 4 policies |
| Separate load-aware supplement | 320 | One additional frozen baseline in those same eight conditions |
| Matched reference subset | 0 new runs | 160 existing main rows selected to match the sensitivity conditions |
| Saved diagnostic replays | 18 replays | First held-out seed, all 6 scenarios, 3 policies |

The two development rounds total 1,488 executed policy runs. They reuse the same 24 worlds and repeat some settings. The 2,400 main runs reuse 240 external worlds. These counts must not be described as independent networks or independent real-world experiments.

The first development results led to **one documented grid extension before held-out evaluation**. The initial and final protocols, their reasons, unequal tuning budgets, and stopping rule are described in [packet-study-protocol.md](packet-study-protocol.md). The initial record is preserved in [development_history](../results/packet/development_history/). The later round is not presented as if its full grid had been fixed before the first development results were seen.

The 320-run load-aware supplement is also separate. It was requested because load-aware performed strongly in development, while the main evaluation was already running and before its outcomes were reviewed. It uses the frozen 0.75 load margin, with no new tuning. It is a development-informed secondary addition, not part of the original 1,280-run sensitivity plan. See [the supplementary plan](packet-load-supplement.md). The full executed count is 5,488 policy runs across both development rounds and the evaluations, plus 18 diagnostic replays.

## Repeat the tests and simulation

Run these commands from the repository root:

```sh
python3 -m unittest discover -s tests -v
python3 scripts/run_packet_study.py --stage tune --workers 4
python3 scripts/run_packet_study.py --stage evaluate --workers 4
python3 scripts/run_packet_study.py --stage sensitivity --workers 4
```

The first command checks the original model, the packet model, and statistical accounting. At the packet-study freeze, all 29 tests passed. The packet-model checks include partial-packet conservation, finite airtime, whole-frame deadlines, fractional transitions, overlapping interruptions, delayed observations, future-trace changes, and time-step consistency.

The next three commands run the **final expanded grid**, freeze its selected settings, evaluate the 2,400 main runs, and run all eight sensitivities. They do not repeat the archived initial development round. The tuning stage writes the fixed settings to [frozen_parameters.json](../results/packet/frozen_parameters.json) before evaluation. Source and protocol hashes must still match that freeze at later stages.

The runner also supports a single command for the same simulation work:

```sh
python3 scripts/run_packet_study.py --stage all --workers 4
```

Use the three separate stages for the complete reproduction workflow below. They create the named evaluate and sensitivity completion manifests required by the supplementary analysis. The single command creates one `run_manifest_all.json` instead.

Changing `--workers` changes how many processes run at once; it should not change simulated outcomes. The source uses fixed seeds and separate external random streams. A 60-second development benchmark took about 0.27 seconds for one policy, but large background-user scenarios and the computer used can change total time. The run manifests record actual stage durations and process counts, so this benchmark is not a promised runtime.

The initial raw development experiment can also be repeated separately:

```sh
python3 scripts/run_packet_study.py \
  --protocol results/packet/development_history/initial_protocol.json \
  --output work/initial-grid-repeat \
  --stage tune --workers 4
```

This uses the initial 19-configuration JSON grid. It creates a new execution record and timestamp; it does not replace the archived historical record. The runner will record the current checked-in protocol document alongside that archived JSON input. Do not present those new provenance timestamps as the original freeze.

## Repeat the main analysis

```sh
python3 scripts/analyze_packet_study.py
```

This reads `results/packet/main_runs.csv` and writes policy means, scenario means, paired differences, and an analysis manifest. The primary result is predictive minus application-myopic on the equal-weight mean of voice-packet and whole-video-frame deadline misses.

The overall interval first averages paired differences across scenarios within each seed, then bootstraps the 40 seed blocks. It does not treat individual packets, time steps, or all 2,400 policy rows as independent replicates. The 5,000 bootstrap resamples use seed 81631. Scenario-level and other secondary intervals are unadjusted descriptive comparisons. These intervals cover random variation in the declared synthetic conditions, not uncertainty about real hardware or codec behavior.

During analysis, the implementation was made faster by reusing the same deterministic bootstrap index sequences. The [recorded equivalence check](../results/packet/analysis_optimization_check.json) reports identical main contrast-table hashes before and after that change, with four statistical tests passing. The statistical method and frozen simulation sources did not change. The validator checks that this recorded hash still matches the delivered table; it does not reconstruct the older analyzer.

## Analyze all eight sensitivities and their matched reference

This standard-library command repeats the main analysis, analyzes all eight saved conditions, creates the matched reference from the main table, and writes a sensitivity overview. It starts no new simulation runs.

```sh
python3 scripts/analyze_all_packet_results.py
```

It creates `analysis_<condition>` for each sensitivity and `analysis_reference_subset` for the 160 reused main rows. The resulting `sensitivity_overview.csv` puts the primary score differences in one table. Each condition retains its full policy and scenario summaries and paired intervals.

The eight conditions change tight deadlines, relaxed deadlines, transition cost, report freshness, the cost estimate, 5 ms service steps, 20 ms service steps, and whether the queue survives handoff. Their exact overrides remain in the protocol JSON. The matched reference uses the normal 10 ms setting and the same four scenarios, ten seeds, and four policies. Comparing sensitivities with the full six-scenario, 40-seed mean would mix the parameter change with a change in the evaluation sample.

## Replay the preselected application traces

```sh
python3 scripts/trace_packet_study.py
```

This repeats seed 50001 in all six held-out scenarios for RSSI, application-myopic, and predictive policies. It checks exact equality of every saved scalar metric against the main table, then saves [selected_traces.json.gz](../results/packet/selected_traces.json.gz). The archive includes the decision times, observation source times, individual voice deadline outcomes, and complete-frame outcomes. The trace set was selected before evaluation, not chosen because its pictures favor a policy.

The gzip timestamp is fixed, so the compressed trace artifact can be reproduced byte for byte in the same numerical environment. New run timestamps and runtimes elsewhere are expected to differ. Python or platform changes may require a careful numerical comparison rather than assuming all floating-point bytes remain identical.

## Export the figures

```sh
python3 scripts/plot_packet_results.py
python3 scripts/plot_packet_timeline.py
```

This optional step uses Matplotlib and NumPy and reads the saved analysis; it does not tune policies or calculate new intervals. It creates four standalone figures, each as a 300-dpi PNG and a PDF:

- Voice and video deadline misses across all ten policies.
- Predictive-minus-application differences in all six scenarios.
- Handoff count against deadline-miss rate, with every policy shown.
- The distribution of longest voice deadline-miss runs for the four named main policies.

The second command adds a timeline for the preselected short-cell example, seed 50001, in PNG and PDF. It shows missed scheduled voice packets and incomplete video frames for the tuned application margin and predictive policies. Its separate timeline manifest identifies the saved replay input. The ten image files are in [figures](../results/packet/figures/). Their [figure manifest](../results/packet/figures/figure_manifest.json) records plot-source and input-table hashes. Saved PNG and PDF files can be viewed without Python. The reported “voice outage” and “video freeze” quantities are defined missed-deadline-run proxies, not measured audio gaps or decoded video freezes.

## Repeat the separate load-aware supplement

The delivered supplementary specification and results are in [additional_load](../results/packet/additional_load/). Its runner refuses to replace an existing specification or raw table. To repeat the supplement after generating a new main freeze, use a new output directory:

```sh
python3 scripts/run_packet_load_sensitivity.py \
  --output work/load-repeat --stage all --workers 2
```

This creates a new specification, then runs 320 policy evaluations. It uses at most two workers and the same eight conditions, four scenarios, and ten seeds as the original sensitivity study. The input worlds and offered demand must match the original four-policy conditions. Only the extra load-aware policy is newly simulated.

The saved supplementary analyses combine these new rows with the original four policies, giving five-policy tables for each condition. Combined tables contain reused original rows; they do not add another 1,280 simulations. Supplementary intervals remain secondary and unadjusted.

Analyze the newly repeated supplement after the original sensitivity stage has completed:

```sh
python3 scripts/analyze_packet_load_supplement.py \
  --packet-dir results/packet --supplement-dir work/load-repeat
```

To analyze the delivered supplement, run the same script without arguments. It creates eight `analysis_<condition>` directories, each with 200 rows covering five policies in 40 worlds. Its separate `reference_analysis` contains 200 existing main rows with the same scenarios, seeds, and five policies. It also writes `supplementary_contrasts.csv`, `overview.md`, and a supplementary analysis manifest. These combined and reference rows are reused evidence, not new simulation runs.

## Validate the final artifacts

After simulation, analysis, trace replay, and plotting finish:

```sh
python3 scripts/validate_packet_results.py --require-figures
```

The validator writes [validation.json](../results/packet/validation.json). It checks:

- Exactly 456 archived development rows, 1,032 final development rows, 2,400 main rows, and 1,280 sensitivity rows, with no missing or duplicate grid entries.
- The declared scenario, seed, policy, and configuration combinations; disjoint development and held-out seeds.
- Input and world fingerprints, plus identical offered traffic across policies within each world.
- Foreground and background conservation, complete generated denominators, zero remaining expired foreground packets, fraction bounds, and internal score identities.
- Attempted, failed, and completed transition counts, and interruption-union bounds.
- Development selection against the saved raw scores, frozen source hashes, and the data hashes in completed run manifests.
- The 160-row reference as an unchanged slice of the main table; it does not count this as new simulation.
- All main and sensitivity analysis records, the exact 18 replay comparisons, and figure-input hashes and file formats, including the preselected timeline.

When the delivered supplementary specification is present, it also checks the separate 320-row load-aware grid, pairing with the original sensitivity worlds, unchanged selected margin, specification/source/raw hashes, and completed-run status. It requires all nine supplementary analyses, checks that combined tables contain the unchanged original rows plus the new baseline rows, and verifies the 200-row reference against the main table. It keeps this supplementary count separate from the original sensitivity count.

If the main study and supplement were newly repeated, their freeze timestamps and hashes are new execution records. Validate the newly created supplement rather than the delivered historical one:

```sh
python3 scripts/validate_packet_results.py \
  --supplement work/load-repeat --require-figures
```

It does not rerun all 2,400 main policy evaluations. Its replay evidence comes from the separate 18-run trace script. Run tests and reproduce a larger set if a source change, failed check, or new concern justifies it.

The two transition fields need care. `handoffs` counts attempts, `failed_handoffs` counts assigned failures, and `successful_handoffs` counts completed AP changes. The main drain should finish every successful attempt, so their counts must balance. For a general shorter window, at most one successful attempt can still be unfinished; the validator records this inferred remainder rather than inventing a measured pending-handoff field.

The validation JSON records the validation duration, Python version, validator hash, checked tables, manifests, and replay count. Each run manifest separately records the exact simulation settings and actual execution time. A successful check means the saved software artifacts are internally consistent. It does not validate a codec, an IEEE 802.11 implementation, a real network, or human quality of experience.

Read next: [the packet model](packet-model.md), [the independent review](packet-independent-review.md), and [the study protocol](packet-study-protocol.md).
