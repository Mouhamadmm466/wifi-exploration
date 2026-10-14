#!/usr/bin/env python3
"""Development, frozen held-out evaluation, and declared sensitivity experiments."""
import argparse
import csv
import hashlib
import itertools
import json
import platform
import statistics
import sys
import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.packet_roaming import default_config, make_world, run

POLICIES=['rssi','load_aware','app_myopic','cautious_v1','session_stay',
          'predictive','no_dwell','no_guard','no_cost','no_age']
SOURCES=['src/packet_roaming.py','scripts/run_packet_study.py','configs/packet-study.json',
         'docs/packet-study-protocol.md']


def hashes(protocol_path):
    result={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in SOURCES if p != 'configs/packet-study.json'}
    result['protocol_content']=hashlib.sha256(protocol_path.read_bytes()).hexdigest()
    return result


def options(protocol):
    result=[]
    for policy, choices in protocol['parameter_grids'].items():
        for n, params in enumerate(choices):
            result.append({'policy':policy,'variant':f'{policy}_{n}','params':params})
    return result


def worker(task):
    config,scenario,seed,choices,condition=task
    world=make_world(config,scenario,seed)
    fingerprint=hashlib.sha256(json.dumps({'config':config,'scenario':scenario,'seed':seed},sort_keys=True).encode()).hexdigest()
    rows=[]
    for option in choices:
        result=run(world,option['policy'],option['params'])
        row={'condition':condition,'scenario':scenario['name'],'seed':seed,
             'policy':option['policy'],'variant':option['variant'],'input_sha256':fingerprint}
        for key,value in result.items():
            if isinstance(value,(int,float,str,bool)) or value is None:
                row[key]=value
        row['call_miss_fraction']=.5*(result['voice_missed_fraction']+1-result['video_complete_fraction'])
        rows.append(row)
    return rows


def execute(tasks,path,workers):
    start=time.monotonic()
    rows=[]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        with path.open('w',newline='') as handle:
            writer=None
            for i,batch in enumerate(pool.map(worker,tasks),1):
                if writer is None:
                    writer=csv.DictWriter(handle,fieldnames=list(batch[0]))
                    writer.writeheader()
                writer.writerows(batch)
                handle.flush()
                rows.extend(batch)
                if i%6==0 or i==len(tasks):
                    print(f'{path.name}: {i}/{len(tasks)} paired worlds, {len(rows)} policy runs, {time.monotonic()-start:.1f}s',flush=True)
    return rows


def write_json(path,value):
    path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')


def config_for(protocol,overrides=None):
    config=default_config()
    config.update(protocol['config'])
    config.update(overrides or {})
    return config


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--protocol',type=Path,default=ROOT/'configs/packet-study.json')
    parser.add_argument('--output',type=Path,default=ROOT/'results/packet')
    parser.add_argument('--stage',choices=['tune','evaluate','sensitivity','all'],default='all')
    parser.add_argument('--workers',type=int,default=4)
    args=parser.parse_args()
    protocol=json.loads(args.protocol.read_text())
    assert not set(protocol['development_seeds']) & set(protocol['heldout_seeds']), 'Seed leakage'
    assert set(protocol['sensitivity_seeds']) <= set(protocol['heldout_seeds'])
    for split in ['development','heldout']:
        names=[s['name'] for s in protocol[split+'_scenarios']]
        assert len(names)==len(set(names)), 'Duplicate scenario names'
        seeds=protocol[split+'_seeds']
        assert len(seeds)==len(set(seeds)), 'Duplicate seeds'
    assert not ({s['name'] for s in protocol['development_scenarios']} & {s['name'] for s in protocol['heldout_scenarios']})
    output=args.output.resolve(); output.mkdir(parents=True,exist_ok=True)
    started=datetime.now(timezone.utc).isoformat(); timer=time.monotonic()
    start_hashes=hashes(args.protocol)
    if args.stage in ['tune','all']:
        choices=options(protocol)
        tasks=[(config_for(protocol),scenario,seed,choices,'development')
               for scenario in protocol['development_scenarios'] for seed in protocol['development_seeds']]
        rows=execute(tasks,output/'development_runs.csv',args.workers)
        grouped=defaultdict(list)
        for row in rows: grouped[row['variant']].append(row)
        scores=[]
        for option in choices:
            rs=grouped[option['variant']]
            scores.append({**option,'mean_miss_fraction':statistics.mean(r['call_miss_fraction'] for r in rs),
                           'mean_handoffs':statistics.mean(r['handoffs'] for r in rs),'runs':len(rs)})
        chosen={}
        for policy in protocol['parameter_grids']:
            candidates=[s for s in scores if s['policy']==policy]
            chosen[policy]=min(candidates,key=lambda s:(s['mean_miss_fraction'],s['mean_handoffs'],s['variant']))['params']
        chosen['session_stay']={}
        for ablation in ['no_dwell','no_guard','no_cost','no_age']: chosen[ablation]=dict(chosen['predictive'])
        assert hashes(args.protocol)==start_hashes,'Study source changed during development; rerun before evaluation.'
        write_json(output/'frozen_parameters.json',{
            'frozen_at_utc':datetime.now(timezone.utc).isoformat(),'source_hashes':start_hashes,
            'selection':'lowest equal-cell equal-voice/video deadline miss; ties fewer handoffs then variant ID',
            'development_seeds':protocol['development_seeds'],'selected':chosen,'scores':scores,
            'warning':'Locally frozen before evaluation, not an externally preregistered study.'})
        print('Selected parameters:',json.dumps(chosen,sort_keys=True),flush=True)
    frozen=json.loads((output/'frozen_parameters.json').read_text())
    if frozen['source_hashes']!=start_hashes:
        raise SystemExit('Source/protocol differs from frozen development. Rerun development before evaluation.')
    selected=frozen['selected']
    choices=[{'policy':p,'variant':p,'params':selected[p]} for p in POLICIES]
    if args.stage in ['evaluate','all']:
        tasks=[(config_for(protocol),scenario,seed,choices,'main')
               for scenario in protocol['heldout_scenarios'] for seed in protocol['heldout_seeds']]
        execute(tasks,output/'main_runs.csv',args.workers)
    if args.stage in ['sensitivity','all']:
        for condition in protocol['sensitivities']:
            scens=[s for s in protocol['heldout_scenarios'] if s['name'] in condition['scenarios']]
            use=[c for c in choices if c['policy'] in condition['policies']]
            tasks=[(config_for(protocol,condition['overrides']),s,seed,use,condition['name'])
                   for s in scens for seed in protocol['sensitivity_seeds']]
            execute(tasks,output/('sensitivity_'+condition['name']+'.csv'),args.workers)
    assert hashes(args.protocol)==start_hashes,'Sources changed during run. Investigate before using the data.'
    write_json(output/('run_manifest_'+args.stage+'.json'),{
        'started_at_utc':started,'completed_at_utc':datetime.now(timezone.utc).isoformat(),
        'elapsed_seconds':time.monotonic()-timer,'stage':args.stage,'python':platform.python_version(),
        'platform':platform.platform(),'workers':args.workers,'source_hashes':start_hashes,
        'protocol_file':str(args.protocol.resolve()),'protocol':protocol,'frozen_at_utc':frozen['frozen_at_utc'],
        'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.glob('*.csv'))}})

if __name__=='__main__': main()
