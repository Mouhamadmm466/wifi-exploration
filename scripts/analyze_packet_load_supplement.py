#!/usr/bin/env python3
"""Analyze the separately frozen load-aware supplement without editing originals."""
import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.analyze_packet_study import analyze, read_rows


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path, rows):
    with path.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def compare_metrics(summary, contrasts, condition):
    by_policy = {r['policy']: r for r in summary}
    rows = []
    for c in contrasts:
        if c['comparator'] == 'load_aware' and c['scope'] == 'all':
            rows.append(dict(condition=condition, **c,
                candidate_mean=by_policy['predictive'][c['metric'] + '_mean'],
                load_aware_mean=by_policy['load_aware'][c['metric'] + '_mean'],
                designation='secondary_development_informed_supplement'))
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--packet-dir', type=Path, default=ROOT / 'results/packet')
    parser.add_argument('--supplement-dir', type=Path, default=ROOT / 'results/packet/additional_load')
    args = parser.parse_args()
    packet, supplement = args.packet_dir.resolve(), args.supplement_dir.resolve()
    original_manifest_path = packet / 'run_manifest_sensitivity.json'
    original_manifest = json.loads(original_manifest_path.read_text())
    if original_manifest.get('stage') not in ('sensitivity', 'all') or not original_manifest.get('completed_at_utc'):
        raise ValueError('Original sensitivity completion manifest is required')
    spec_path, manifest_path = supplement / 'specification.json', supplement / 'run_manifest.json'
    spec, manifest = json.loads(spec_path.read_text()), json.loads(manifest_path.read_text())
    if manifest['status'] != 'complete' or manifest['rows'] != 320:
        raise ValueError('Supplement must have completed all 320 planned runs')
    if digest(spec_path) != manifest['specification_sha256'] or digest(supplement / 'runs.csv') != manifest['raw_sha256']:
        raise ValueError('Supplementary specification or raw result hash mismatch')
    for name, expected in spec['source_hashes'].items():
        if digest(ROOT / name) != expected:
            raise ValueError(f'Supplement source changed: {name}')
    supplementary = list(csv.DictReader((supplement / 'runs.csv').open()))
    if len(supplementary) != 320:
        raise ValueError('Unexpected supplementary raw count')
    report, input_hashes, combined_hashes = [], {}, {}
    reference_scenarios, reference_policies = None, None
    for condition in spec['conditions']:
        name = condition['name']
        original_path = packet / f'sensitivity_{name}.csv'
        if digest(original_path) != original_manifest['files'].get(original_path.name):
            raise ValueError(f'Original sensitivity hash mismatch: {name}')
        input_hashes[original_path.name] = digest(original_path)
        original = list(csv.DictReader(original_path.open()))
        extra = [r for r in supplementary if r['condition'] == name]
        expected_keys = {(s['name'], str(seed)) for s in condition['scenarios'] for seed in spec['seeds']}
        expected_policies = {'rssi', 'app_myopic', 'cautious_v1', 'predictive'}
        if len(original) != 160 or len(extra) != 40:
            raise ValueError(f'Incorrect condition row count: {name}')
        if {(r['scenario'], r['seed'], r['policy']) for r in original} != {
                (scenario, seed, policy) for scenario, seed in expected_keys for policy in expected_policies}:
            raise ValueError(f'Incomplete original comparison grid: {name}')
        if {(r['scenario'], r['seed']) for r in extra} != expected_keys or any(r['policy'] != 'load_aware' for r in extra):
            raise ValueError(f'Incomplete supplementary grid: {name}')
        original_cells = {(r['scenario'], r['seed']): r for r in original if r['policy'] == 'predictive'}
        for row in extra:
            counterpart = original_cells[(row['scenario'], row['seed'])]
            for field in ('input_sha256', 'world_fingerprint', 'offered_packets', 'generated_voice_packets',
                          'generated_video_frames', 'background_offered_packets'):
                if row[field] != counterpart[field]:
                    raise ValueError(f'Unpaired {field}: {name}/{row["scenario"]}/{row["seed"]}')
        directory = supplement / ('analysis_' + name)
        directory.mkdir(exist_ok=True)
        combined = sorted(original + extra, key=lambda r: (r['scenario'], int(r['seed']), r['policy']))
        combined_path = directory / 'combined_runs.csv'
        write_csv(combined_path, combined)
        summaries, contrasts = analyze(read_rows(combined_path), directory)
        combined_hashes[str(combined_path.relative_to(supplement))] = digest(combined_path)
        report.extend(compare_metrics(summaries, contrasts, name))
        scenarios = {s['name'] for s in condition['scenarios']}
        policies = expected_policies | {'load_aware'}
        if reference_scenarios is not None and (reference_scenarios != scenarios or reference_policies != policies):
            raise ValueError('Sensitivity conditions lack a common matched reference subset')
        reference_scenarios, reference_policies = scenarios, policies
        print(f'Analyzed {name}: 200 paired rows, 40 worlds, 10 seed blocks.', flush=True)
    main_path = packet / 'main_runs.csv'
    main_manifest = json.loads((packet / 'run_manifest_evaluate.json').read_text())
    if digest(main_path) != main_manifest['files']['main_runs.csv']:
        raise ValueError('Main reference hash mismatch')
    input_hashes[main_path.name] = digest(main_path)
    main_rows = list(csv.DictReader(main_path.open()))
    reference = [r for r in main_rows if r['scenario'] in reference_scenarios
                 and int(r['seed']) in spec['seeds'] and r['policy'] in reference_policies]
    if len(reference) != 200:
        raise ValueError('Matched reference must have 200 rows')
    reference_dir = supplement / 'reference_analysis'
    reference_dir.mkdir(exist_ok=True)
    reference_path = reference_dir / 'combined_runs.csv'
    write_csv(reference_path, reference)
    summaries, contrasts = analyze(read_rows(reference_path), reference_dir)
    report = compare_metrics(summaries, contrasts, 'matched_main_reference') + report
    combined_hashes[str(reference_path.relative_to(supplement))] = digest(reference_path)
    summary_path = supplement / 'supplementary_contrasts.csv'
    write_csv(summary_path, report)
    table = ['| Condition | Candidate score, % | Load-aware score, % | Difference, points | 95% interval, points |',
             '|---|---:|---:|---:|---:|']
    for row in report:
        if row['metric'] == 'call_miss_fraction':
            table.append(f'| {row["condition"]} | {row["candidate_mean"]*100:.4f} | {row["load_aware_mean"]*100:.4f} | {row["difference"]*100:+.4f} | {row["ci_low"]*100:+.4f} to {row["ci_high"]*100:+.4f} |')
    overview = '''# Supplementary robustness results for the load-aware baseline

This analysis is the separately frozen, development-informed addition described in [the supplementary plan](../../../docs/packet-load-supplement.md). It does not replace the original primary comparison. All eight conditions are reported below. Parameters were not retuned.

There are 320 additional load-aware runs. Each condition uses 40 paired worlds: four scenarios and ten seeds. Its combined analysis contains five policies and 200 rows. Each input fingerprint and offered-traffic count matched the corresponding original candidate run. The matched main reference uses precisely the same four scenarios and ten seeds; it is not the full six-scenario main mean.

The difference is candidate minus load-aware. Positive values mean more missed deadlines for the candidate. Each 95% interval resamples ten complete seed blocks after averaging their four scenario differences. Intervals are secondary, unadjusted and limited by the small number of seeds.

''' + '\n'.join(table) + '''

The score gives equal weight to voice-packet misses and whole-video-frame misses. It is not human QoE. [The full supplementary table](supplementary_contrasts.csv) also reports the two components, handoffs, deadline-run tails, on-time delivery and background-service measures. Per-scenario comparisons and policy summaries are stored in each separate analysis directory. Report exceptions and trade-offs together with any overall gain.

Reproduce from the repository root after both complete run manifests are available:

```sh
python3 scripts/analyze_packet_load_supplement.py
```

[The analysis manifest](supplementary_analysis_manifest.json) records source and input hashes. Original sensitivity tables and their analysis directories are unchanged.
'''
    (supplement / 'overview.md').write_text(overview)
    analysis_manifest = {
        'completed_at_utc': datetime.now(timezone.utc).isoformat(),
        'analysis_script_sha256': digest(Path(__file__)),
        'paired_analysis_script_sha256': digest(ROOT / 'scripts/analyze_packet_study.py'),
        'specification_sha256': digest(spec_path), 'supplement_raw_sha256': digest(supplement / 'runs.csv'),
        'original_manifest_sha256': digest(original_manifest_path),
        'original_input_hashes': input_hashes, 'combined_table_hashes': combined_hashes,
        'summary_sha256': digest(summary_path), 'supplementary_runs': 320,
        'conditions': 8, 'worlds_per_condition': 40, 'seed_blocks_per_condition': 10,
        'comparison': 'predictive minus load_aware', 'designation': 'secondary, unadjusted, development-informed',
    }
    (supplement / 'supplementary_analysis_manifest.json').write_text(json.dumps(analysis_manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
