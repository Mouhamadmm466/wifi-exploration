#!/usr/bin/env python3
"""Independent secondary paired contrasts for the frozen capacity baseline."""
import argparse
import csv
import hashlib
import json
import random
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

METRICS = ('call_miss_fraction', 'voice_missed_fraction', 'video_missed_fraction',
           'handoffs', 'background_delivery_fraction')


def quantile(values, p):
    values = sorted(values)
    position = (len(values) - 1) * p
    lower = int(position)
    return values[lower] + (values[min(lower + 1, len(values) - 1)] - values[lower]) * (position - lower)


def interval(values):
    rng = random.Random(81631)
    n = len(values)
    means = [sum(values[rng.randrange(n)] for _ in range(n)) / n for _ in range(5000)]
    return quantile(means, .025), quantile(means, .975)


def calculate(path):
    rows = list(csv.DictReader(path.open()))
    cells = defaultdict(dict)
    for row in rows:
        key = (row['scenario'], int(row['seed']))
        if row['policy'] in cells[key]:
            raise ValueError(f'Duplicate row: {key}/{row["policy"]}')
        cells[key][row['policy']] = row
    if len({r['condition'] for r in rows}) != 1:
        raise ValueError('Use one condition at a time')
    scenario_seeds = defaultdict(set)
    for (scenario, seed), cell in cells.items():
        scenario_seeds[scenario].add(seed)
        if not {'load_aware', 'rssi', 'app_myopic'} <= set(cell):
            raise ValueError(f'Missing required comparator: {scenario}/{seed}')
        if len({r['input_sha256'] for r in cell.values()}) != 1:
            raise ValueError('Unpaired model inputs')
    seeds = next(iter(scenario_seeds.values()))
    if len(seeds) < 2 or any(values != seeds for values in scenario_seeds.values()):
        raise ValueError('Incomplete or insufficient seed blocks')
    for row in rows:
        for name in METRICS:
            row[name] = float(row[name])
        expected = .5 * (row['voice_missed_fraction'] + row['video_missed_fraction'])
        if abs(row['call_miss_fraction'] - expected) > 1e-12:
            raise ValueError('Inconsistent primary outcome')
    output = []
    for comparator in ('rssi', 'app_myopic'):
        for metric in METRICS:
            for scope in ['all'] + sorted(scenario_seeds):
                by_seed = defaultdict(list)
                focal_values, comparator_values = [], []
                for (scenario, seed), cell in sorted(cells.items()):
                    if scope != 'all' and scope != scenario:
                        continue
                    focal = cell['load_aware'][metric]
                    reference = cell[comparator][metric]
                    by_seed[seed].append(focal - reference)
                    focal_values.append(focal)
                    comparator_values.append(reference)
                blocks = [statistics.mean(values) for _, values in sorted(by_seed.items())]
                lo, hi = interval(blocks)
                output.append({'focal_policy': 'load_aware', 'comparator': comparator,
                    'scope': scope, 'metric': metric,
                    'focal_mean': statistics.mean(focal_values),
                    'comparator_mean': statistics.mean(comparator_values),
                    'difference': statistics.mean(blocks), 'ci_low': lo, 'ci_high': hi,
                    'seed_blocks': len(blocks), 'paired_worlds': len(focal_values),
                    'designation': 'secondary_descriptive_unadjusted',
                    'interval': 'paired_seed_block_percentile_95'})
    return output, len(rows), len(cells)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, default=Path('results/packet/main_runs.csv'))
    parser.add_argument('--output', type=Path,
                        default=Path('results/packet/additional_load/secondary_capacity_comparisons.csv'))
    args = parser.parse_args()
    output, rows, worlds = calculate(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(output[0]))
        writer.writeheader()
        writer.writerows(output)
    manifest = {'generated_at_utc': datetime.now(timezone.utc).isoformat(),
                'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                'input_sha256': hashlib.sha256(args.input.read_bytes()).hexdigest(),
                'output_sha256': hashlib.sha256(args.output.read_bytes()).hexdigest(),
                'source_rows': rows, 'paired_worlds': worlds, 'contrast_rows': len(output),
                'bootstrap_seed': 81631, 'bootstrap_repetitions': 5000,
                'sign': 'load_aware minus comparator; negative favors load_aware for miss fractions',
                'designation': 'secondary descriptive comparisons; primary study contrast is unchanged',
                'pooling': 'equal scenario weight within seed, then equal seed weight; all scenarios travel together in overall resampling'}
    args.output.with_suffix('.manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    for row in output:
        if row['scope'] == 'all' and row['metric'] == 'call_miss_fraction':
            print(json.dumps(row))


if __name__ == '__main__':
    main()
