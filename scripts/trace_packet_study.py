#!/usr/bin/env python3
"""Replay the prospectively selected first seed; preserve application event traces."""
import csv
import gzip
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.packet_roaming import default_config,make_world,run


def main():
    protocol=json.loads((ROOT/'configs/packet-study.json').read_text())
    frozen=json.loads((ROOT/'results/packet/frozen_parameters.json').read_text())
    rows=list(csv.DictReader((ROOT/'results/packet/main_runs.csv').open()))
    seed=protocol['heldout_seeds'][0]
    config=default_config(); config.update(protocol['config'])
    traces=[]
    for scenario in protocol['heldout_scenarios']:
        world=make_world(config,scenario,seed)
        for policy in ['rssi','app_myopic','predictive']:
            result=run(world,policy,frozen['selected'][policy],keep_trace=True)
            original=next(r for r in rows if r['scenario']==scenario['name'] and r['policy']==policy and int(r['seed'])==seed)
            for key,value in result.items():
                if key in original and isinstance(value,(int,float)):
                    assert float(original[key])==value,(scenario['name'],policy,key)
            traces.append(result)
    document={'selection':'First heldout seed for all six scenarios, three policies; declared before evaluation.',
              'seed':seed,'config':config,'traces':traces}
    # mtime zero makes the compressed artifact reproducible byte for byte.
    with (ROOT/'results/packet/selected_traces.json.gz').open('wb') as f:
        with gzip.GzipFile(fileobj=f,mode='wb',mtime=0,filename='') as g:
            g.write((json.dumps(document,separators=(',',':'))+'\n').encode())
    print(f'Replayed {len(traces)} runs with exact scalar metric equality.')

if __name__=='__main__':main()
