#!/usr/bin/env python3
"""Produce main and sensitivity summaries, preserving the pairing design."""
import csv
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def main():
    protocol=json.loads((ROOT/'configs/packet-study.json').read_text())
    output=ROOT/'results/packet'
    def analyze(source,destination):
        subprocess.run([sys.executable,str(ROOT/'scripts/analyze_packet_study.py'),
                        '--input',str(source),'--output',str(destination)],check=True)
    analyze(output/'main_runs.csv',output)
    rows=list(csv.DictReader((output/'main_runs.csv').open()))
    first=protocol['sensitivities'][0]
    reference=[r for r in rows if r['scenario'] in first['scenarios']
               and r['policy'] in first['policies'] and int(r['seed']) in protocol['sensitivity_seeds']]
    for r in reference:r['condition']='reference_subset'
    with (output/'reference_subset.csv').open('w',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=list(reference[0]));writer.writeheader();writer.writerows(reference)
    analyze(output/'reference_subset.csv',output/'analysis_reference_subset')
    overview=[]
    names=['reference_subset']+[s['name'] for s in protocol['sensitivities']]
    for name in names:
        directory=output/('analysis_'+name)
        if name!='reference_subset': analyze(output/('sensitivity_'+name+'.csv'),directory)
        comparisons=list(csv.DictReader((directory/'paired_contrasts.csv').open()))
        summary=list(csv.DictReader((directory/'policy_summary.csv').open()))
        for comparator in ['app_myopic','rssi','cautious_v1']:
            c=next(r for r in comparisons if r['scope']=='all' and r['metric']=='call_miss_fraction' and r['comparator']==comparator)
            proposed=next(r for r in summary if r['policy']=='predictive')
            other=next(r for r in summary if r['policy']==comparator)
            overview.append({'condition':name,'comparator':comparator,'proposed_miss':proposed['call_miss_fraction_mean'],
                'comparator_miss':other['call_miss_fraction_mean'],'difference':c['difference'],
                'ci_low':c['ci_low'],'ci_high':c['ci_high'],'seed_blocks':c['seed_blocks'],
                'paired_worlds':c['paired_worlds']})
    with (output/'sensitivity_overview.csv').open('w',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=list(overview[0]));writer.writeheader();writer.writerows(overview)
    print('Completed all main and eight sensitivity analyses; reference is a subset of main runs.')

if __name__=='__main__':main()
