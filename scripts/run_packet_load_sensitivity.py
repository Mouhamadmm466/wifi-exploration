#!/usr/bin/env python3
"""Separately frozen, development-informed load-aware sensitivity supplement."""
import argparse
import csv
import hashlib
import json
import platform
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.run_packet_study import config_for, worker

SOURCES = [
    'src/packet_roaming.py', 'scripts/run_packet_study.py',
    'scripts/run_packet_load_sensitivity.py', 'docs/packet-load-supplement.md',
    'configs/packet-study.json', 'results/packet/frozen_parameters.json',
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def source_hashes():
    return {name: digest(ROOT / name) for name in SOURCES}


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def prepare(output):
    path = output / 'specification.json'
    if path.exists():
        raise FileExistsError('Supplement specification already exists; use --stage run or a new output directory.')
    protocol = json.loads((ROOT / 'configs/packet-study.json').read_text())
    frozen = json.loads((ROOT / 'results/packet/frozen_parameters.json').read_text())
    for name, expected in frozen['source_hashes'].items():
        actual_path = ROOT / ('configs/packet-study.json' if name == 'protocol_content' else name)
        if digest(actual_path) != expected:
            raise ValueError(f'Original frozen source changed: {name}')
    params = frozen['selected']['load_aware']
    if params != {'load_margin': 0.75}:
        raise ValueError('This supplementary plan expects frozen load margin 0.75.')
    seeds = protocol['sensitivity_seeds']
    if seeds != list(range(50001, 50011)):
        raise ValueError('Unexpected sensitivity seed set')
    conditions = []
    for condition in protocol['sensitivities']:
        scenarios = [s for s in protocol['heldout_scenarios'] if s['name'] in condition['scenarios']]
        if len(scenarios) != 4 or len({s['name'] for s in scenarios}) != 4:
            raise ValueError('Expected four unique scenarios per condition')
        conditions.append({'name': condition['name'],
                           'config': config_for(protocol, condition['overrides']),
                           'scenarios': scenarios})
    if len(conditions) != 8 or len({c['name'] for c in conditions}) != 8:
        raise ValueError('Expected eight unique sensitivity conditions')
    specification = {
        'schema_version': 1,
        'prepared_at_utc': utc_now(),
        'designation': 'secondary development-informed supplement; not part of the original prospective sensitivity plan',
        'timing_record': 'Coordinator requested this addition before reviewing any held-out outcomes; main evaluation had already started.',
        'reason': 'Load-aware was the strongest baseline in development and needs the same robustness checks.',
        'policy': 'load_aware', 'variant': 'load_aware', 'parameters': params,
        'parameter_source': 'results/packet/frozen_parameters.json',
        'parameter_frozen_at_utc': frozen['frozen_at_utc'],
        'retuning': False, 'seeds': seeds, 'conditions': conditions,
        'expected_rows': 320, 'maximum_workers': 2,
        'analysis': 'Pair existing predictive rows with these load-aware rows by condition/scenario/seed; equal four-scenario mean within seed, then bootstrap ten seed blocks. Secondary unadjusted 95% intervals.',
        'source_hashes': source_hashes(),
        'original_frozen_source_hashes': frozen['source_hashes'],
    }
    write_json(path, specification)
    print(f'Prepared separate specification: {path}; 320 planned runs.', flush=True)


def execute(output, workers):
    spec_path = output / 'specification.json'
    specification = json.loads(spec_path.read_text())
    spec_hash = digest(spec_path)
    if source_hashes() != specification['source_hashes']:
        raise ValueError('Supplement source changed after preparation.')
    raw_path = output / 'runs.csv'
    manifest_path = output / 'run_manifest.json'
    if raw_path.exists() or manifest_path.exists():
        raise FileExistsError('Supplement outputs already exist; refusing to overwrite evidence.')
    option = {'policy': specification['policy'], 'variant': specification['variant'],
              'params': specification['parameters']}
    tasks = [(condition['config'], scenario, seed, [option], condition['name'])
             for condition in specification['conditions']
             for scenario in condition['scenarios'] for seed in specification['seeds']]
    if len(tasks) != specification['expected_rows']:
        raise ValueError('Supplement grid does not match planned row count')
    start = time.monotonic()
    manifest = {'schema_version': 1, 'status': 'running', 'started_at_utc': utc_now(),
                'specification_file': 'specification.json', 'specification_sha256': spec_hash,
                'source_hashes': specification['source_hashes'], 'workers': workers,
                'python': platform.python_version(), 'platform': platform.platform(),
                'expected_rows': len(tasks), 'raw_file': 'runs.csv'}
    write_json(manifest_path, manifest)
    completed = 0
    with ProcessPoolExecutor(max_workers=workers) as pool:
        with raw_path.open('w', newline='') as handle:
            writer = None
            for batch in pool.map(worker, tasks):
                if len(batch) != 1 or batch[0]['policy'] != 'load_aware':
                    raise ValueError('Unexpected worker output')
                if writer is None:
                    writer = csv.DictWriter(handle, fieldnames=list(batch[0]))
                    writer.writeheader()
                writer.writerows(batch)
                handle.flush()
                completed += len(batch)
                if completed % 40 == 0:
                    print(f'Supplement: {completed}/{len(tasks)} runs; {time.monotonic()-start:.1f}s', flush=True)
    if source_hashes() != specification['source_hashes'] or digest(spec_path) != spec_hash:
        raise ValueError('Frozen supplementary inputs changed during execution; do not use outputs.')
    manifest.update(status='complete', completed_at_utc=utc_now(),
                    elapsed_seconds=time.monotonic()-start, rows=completed,
                    raw_sha256=digest(raw_path))
    write_json(manifest_path, manifest)
    print('Supplement complete; no outcome summaries calculated.', flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'results/packet/additional_load')
    parser.add_argument('--stage', choices=('prepare', 'run', 'all'), default='all')
    parser.add_argument('--workers', type=int, choices=(1, 2), default=2)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if args.stage in ('prepare', 'all'):
        prepare(output)
    if args.stage in ('run', 'all'):
        execute(output, args.workers)


if __name__ == '__main__':
    main()
