#!/usr/bin/env python3
"""Analyze paired packet experiments without treating runs as independent worlds."""
import argparse
import csv
import hashlib
import json
import random
import statistics
from functools import lru_cache
from collections import defaultdict
from pathlib import Path

METRICS = ['call_miss_fraction', 'voice_missed_fraction', 'video_missed_fraction',
           'voice_longest_outage_seconds', 'video_longest_outage_seconds', 'video_freeze_fraction', 'delivered_mbps',
           'ontime_delivered_mbps', 'conditional_packet_delay_p95_ms',
           'handoffs', 'failed_handoffs', 'background_delivery_fraction', 'background_worst_delivery_fraction']


def quantile(values, p):
    s = sorted(values)
    x = (len(s)-1)*p
    low = int(x)
    return s[low] + (s[min(low+1, len(s)-1)]-s[low])*(x-low)


@lru_cache(maxsize=8)
def _bootstrap_indices(n, repetitions, seed):
    rng=random.Random(seed)
    return tuple(tuple(rng.randrange(n) for _ in range(n)) for _ in range(repetitions))


def bootstrap(values, repetitions=5000, seed=81631):
    if min(values)==max(values):
        return values[0],values[0]
    n = len(values)
    samples = [sum(values[i] for i in indices)/n
               for indices in _bootstrap_indices(n, repetitions, seed)]
    return quantile(samples, .025), quantile(samples, .975)


def read_rows(path):
    rows = list(csv.DictReader(path.open()))
    for row in rows:
        row['seed'] = int(row['seed'])
        for key in METRICS + ['video_complete_fraction']:
            if key in row and row[key] != '':
                row[key] = float(row[key])
        row['video_missed_fraction'] = 1.0-float(row['video_complete_fraction'])
        row['call_miss_fraction'] = .5*(float(row['voice_missed_fraction']) + row['video_missed_fraction'])
    return rows


def write_csv(path, rows):
    if not rows:
        return
    with path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def validate_grid(rows):
    if not rows:
        raise ValueError('Empty result file')
    policies={r['policy'] for r in rows}
    by_cell=defaultdict(list)
    scenario_seeds=defaultdict(set)
    conditions={r.get('condition','main') for r in rows}
    if len(conditions)!=1:
        raise ValueError('Analyze each condition separately')
    for row in rows:
        by_cell[(row['scenario'],row['seed'])].append(row)
        scenario_seeds[row['scenario']].add(row['seed'])
    for key,cell in by_cell.items():
        if len(cell)!=len(policies) or {r['policy'] for r in cell}!=policies:
            raise ValueError(f'Incomplete or duplicate policy cell: {key}')
        if 'input_sha256' in cell[0] and len({r['input_sha256'] for r in cell})!=1:
            raise ValueError(f'Unpaired inputs: {key}')
    seeds=next(iter(scenario_seeds.values()))
    if any(s!=seeds for s in scenario_seeds.values()):
        raise ValueError('Incomplete/unbalanced scenario seed grid')
    if len(seeds)<2:
        raise ValueError('At least two seed blocks required for intervals')
    return policies,set(scenario_seeds),seeds


def analyze(rows, output):
    validate_grid(rows)
    output.mkdir(parents=True, exist_ok=True)
    groups = defaultdict(list)
    for r in rows:
        groups[r['policy']].append(r)
    summaries = []
    for policy, group in sorted(groups.items()):
        result = {'policy':policy, 'runs':len(group), 'seed_blocks':len({r['seed'] for r in group})}
        for metric in METRICS:
            if metric not in group[0]:
                continue
            values = [r[metric] for r in group]
            result[metric+'_mean'] = statistics.mean(values)
            result[metric+'_p95'] = quantile(values, .95)
        summaries.append(result)
    write_csv(output/'policy_summary.csv', summaries)
    cells = defaultdict(dict)
    for r in rows:
        key = (r.get('condition','main'), r['scenario'], r['seed'])
        assert r['policy'] not in cells[key], f'duplicate {key}/{r["policy"]}'
        cells[key][r['policy']] = r
    contrasts = []
    # The primary contrast is predictive minus app_myopic. Other contrasts are diagnostic.
    for comparator in sorted(p for p in groups if p != 'predictive'):
        paired = [cell for cell in cells.values() if 'predictive' in cell and comparator in cell]
        for metric in METRICS:
            if not paired or metric not in paired[0]['predictive']:
                continue
            by_seed = defaultdict(list)
            by_scenario = defaultdict(list)
            for cell in paired:
                r = cell['predictive']
                diff = r[metric]-cell[comparator][metric]
                by_seed[r['seed']].append(diff)
                by_scenario[r['scenario']].append(diff)
            blocks = [statistics.mean(values) for _, values in sorted(by_seed.items())]
            lo, hi = bootstrap(blocks)
            contrasts.append({'comparator':comparator, 'scope':'all', 'metric':metric,
                              'difference':statistics.mean(blocks), 'ci_low':lo, 'ci_high':hi,
                              'seed_blocks':len(blocks), 'paired_worlds':len(paired),
                              'interval':'paired_seed_block_percentile_95'})
            for scenario, values in sorted(by_scenario.items()):
                lo, hi = bootstrap(values)
                contrasts.append({'comparator':comparator, 'scope':scenario, 'metric':metric,
                                  'difference':statistics.mean(values), 'ci_low':lo, 'ci_high':hi,
                                  'seed_blocks':len(values), 'paired_worlds':len(values),
                                  'interval':'paired_world_percentile_95_unadjusted'})
    write_csv(output/'paired_contrasts.csv', contrasts)
    scenario_summaries=[]
    for scenario in sorted({r['scenario'] for r in rows}):
        for policy in sorted(groups):
            group=[r for r in groups[policy] if r['scenario']==scenario]
            if not group: continue
            row={'scenario':scenario,'policy':policy,'runs':len(group)}
            row.update({m:statistics.mean([r[m] for r in group]) for m in METRICS if m in group[0]})
            scenario_summaries.append(row)
    write_csv(output/'scenario_summary.csv',scenario_summaries)
    manifest={'analysis_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'rows':len(rows), 'worlds':len(cells), 'policies':sorted(groups),
              'bootstrap_repetitions':5000,'bootstrap_seed':81631,
              'primary_metric':'equal-weight mean of voice packet and whole-video-frame deadline miss fractions',
              'primary_contrast':'predictive minus app_myopic; negative favors predictive',
              'pooling':'equal scenario average within seed, then equal seed weight',
              'scope':'uncertainty across seeded synthetic conditions; not real-device confidence',
              'multiplicity':'only primary contrast/metric designated primary; other CIs unadjusted descriptive'}
    (output/'analysis_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return summaries,contrasts


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--input',type=Path,default=Path('results/packet/main_runs.csv'))
    p.add_argument('--output',type=Path,default=Path('results/packet'))
    p.add_argument('--protocol',type=Path,default=Path(__file__).resolve().parents[1]/'configs/packet-study.json')
    a=p.parse_args()
    rows=read_rows(a.input)
    policies, scenarios, seeds=validate_grid(rows)
    protocol_path=a.protocol
    if a.input.name=='main_runs.csv':
        protocol=json.loads(protocol_path.read_text())
        expected={'rssi','load_aware','app_myopic','cautious_v1','session_stay','predictive','no_dwell','no_guard','no_cost','no_age'}
        assert policies==expected, 'Missing main policy'
        assert scenarios=={s['name'] for s in protocol['heldout_scenarios']}, 'Missing main scenario'
        assert seeds==set(protocol['heldout_seeds']), 'Missing main seed'
    summaries, contrasts=analyze(rows,a.output)
    manifest_path=a.output/'analysis_manifest.json'
    manifest=json.loads(manifest_path.read_text())
    manifest.update(input_file=str(a.input.resolve()),input_sha256=hashlib.sha256(a.input.read_bytes()).hexdigest())
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
    for c in contrasts:
        if c['scope']=='all' and c['comparator']=='app_myopic': print(json.dumps(c))

if __name__=='__main__': main()
