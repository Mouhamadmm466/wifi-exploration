# Supplementary load-aware sensitivity comparison

This is a **secondary, development-informed addition** to the packet study. It is separate from the original [protocol](packet-study-protocol.md), its 2,400 main runs and its 1,280 sensitivity runs. It is not external preregistration.

The load-aware rule gave the lowest mean deadline-miss score during development. The original sensitivity plan included signal selection, application-margin selection, the earlier-caution rule and the candidate, but omitted load-aware selection. Testing the strongest development baseline under the same difficult conditions is useful even if the candidate does poorly.

The coordinator requested this addition before reviewing any held-out outcomes, while main evaluation was already running. This timing is the recorded project history, not an external certification. The supplement does not change any frozen main source, parameter, scenario or primary comparison.

## Fixed supplementary design

Use the **frozen load-aware margin of 0.75**, without retuning. Run all eight original sensitivity conditions, the same four scenarios (`short_cells`, `hidden_hotspot`, `burst_load`, `crowded`) and seeds **50001–50010**. This gives **320 additional policy runs**. Use at most two workers. All model inputs come from the original frozen configuration and its existing sensitivity overrides.

Before running, save a separate complete specification containing every condition, full scenario and model configuration, seeds, selected parameter, timestamps and source hashes. Preserve it unchanged throughout execution. The runner uses the original study worker to produce the same row fields and input hash convention. Refuse to overwrite an existing specification or result table.

The saved files are [specification.json](../results/packet/additional_load/specification.json), [runs.csv](../results/packet/additional_load/runs.csv) and [run_manifest.json](../results/packet/additional_load/run_manifest.json). The manifest records completion status, counts, software information, source/specification hashes and the raw table hash.

## Analysis after the coordinator opens held-out results

Keep original sensitivity outputs and their analysis directories unchanged. In a separate `additional_load/analysis_<condition>/` directory, pair these load-aware rows with the matching original sensitivity rows using condition, scenario and seed. Require identical input hashes. Save a combined table and use the existing paired-analysis routine.

The supplementary contrast is candidate minus load-aware. Average each seed's differences over the four scenarios, then bootstrap the **ten seed blocks**, with 5,000 resamples and analysis seed 81631. Report absolute miss fractions, percentage-point differences and unadjusted 95% intervals. These comparisons are secondary; they do not replace the original primary contrast. Report all eight conditions, the two application components, interruption-run tails and background-service trade-offs. The small seed count limits precision.

A matched reference subset can be taken from the existing main table; no additional reference simulations are needed. Never compare sensitivity outcomes against an unmatched main average over different scenarios or seeds.

## Reproduction

From the repository root, prepare the separate specification, then run it:

```sh
python3 scripts/run_packet_load_sensitivity.py --stage prepare --output results/reproduction_load
python3 scripts/run_packet_load_sensitivity.py --stage run --output results/reproduction_load --workers 2
```

The original frozen configuration and selected-parameter file must be available and unchanged. The script refuses overwrites to protect the evidence. This supplementary model still does not measure human QoE, decoded video freezes or physical Wi-Fi behavior.
