# Supplementary robustness results for the load-aware baseline

This analysis is the separately frozen, development-informed addition described in [the supplementary plan](../../../docs/packet-load-supplement.md). It does not replace the original primary comparison. All eight conditions are reported below. Parameters were not retuned.

There are 320 additional load-aware runs. Each condition uses 40 paired worlds: four scenarios and ten seeds. Its combined analysis contains five policies and 200 rows. Each input fingerprint and offered-traffic count matched the corresponding original candidate run. The matched main reference uses precisely the same four scenarios and ten seeds; it is not the full six-scenario main mean.

The difference is candidate minus load-aware. Positive values mean more missed deadlines for the candidate. Each 95% interval resamples ten complete seed blocks after averaging their four scenario differences. Intervals are secondary, unadjusted and limited by the small number of seeds.

| Condition | Candidate score, % | Load-aware score, % | Difference, points | 95% interval, points |
|---|---:|---:|---:|---:|
| matched_main_reference | 2.6936 | 1.7104 | +0.9832 | +0.6961 to +1.2913 |
| tight_deadlines | 3.8528 | 2.0865 | +1.7662 | +1.3491 to +2.1735 |
| relaxed_deadlines | 2.1708 | 1.4300 | +0.7408 | +0.4699 to +1.0615 |
| costly_transitions | 5.2256 | 3.6826 | +1.5429 | +1.0723 to +2.0550 |
| stale_reports | 5.2029 | 2.9539 | +2.2490 | +1.4665 to +2.9513 |
| cost_underestimate | 2.7183 | 1.7104 | +1.0079 | +0.6844 to +1.3427 |
| time_step_5ms | 2.9700 | 1.7451 | +1.2249 | +0.8590 to +1.5717 |
| time_step_20ms | 2.3343 | 2.0911 | +0.2432 | +0.0094 to +0.4794 |
| retain_handoff_queue | 2.4956 | 1.3328 | +1.1628 | +0.8101 to +1.5410 |

The score gives equal weight to voice-packet misses and whole-video-frame misses. It is not human QoE. [The full supplementary table](supplementary_contrasts.csv) also reports the two components, handoffs, deadline-run tails, on-time delivery and background-service measures. Per-scenario comparisons and policy summaries are stored in each separate analysis directory. Report exceptions and trade-offs together with any overall gain.

Reproduce from the repository root after both complete run manifests are available:

```sh
python3 scripts/analyze_packet_load_supplement.py
```

[The analysis manifest](supplementary_analysis_manifest.json) records source and input hashes. Original sensitivity tables and their analysis directories are unchanged.
