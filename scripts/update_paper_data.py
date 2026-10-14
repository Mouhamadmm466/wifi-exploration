#!/usr/bin/env python3
"""Refresh marked data/figure/reference regions of the standalone LaTeX paper.

Prose remains editable. Every plotted coordinate comes from saved results.
No simulations are run and no observations are selected by their outcomes.
"""
import csv
import gzip
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'results/packet'
PAPER = ROOT / 'paper/wifi-roaming-paper.tex'
POLICIES = ['rssi','load_aware','app_myopic','cautious_v1','session_stay',
            'predictive','no_dwell','no_guard','no_cost','no_age']
LABELS = ['Signal','Capacity/load','App margin','Earlier caution','Session stay',
          'Proposed','No dwell','No guard','No cost','No age']
SCENARIOS = ['wide_corridor','short_cells','reversals','hidden_hotspot','burst_load','crowded']
SCENARIO_LABELS = ['Wide corridor','Short cells','Reversals','Hidden hotspot','Burst load','Crowded']
INPUTS = set()


def read_bytes(path):
    INPUTS.add(path)
    return path.read_bytes()


def rows(name):
    return list(csv.DictReader(read_bytes(DATA/name).decode().splitlines()))


def put(text, tag, content):
    pattern = rf'(% BEGIN GENERATED {tag}\n).*?(% END GENERATED {tag})'
    updated, n = re.subn(pattern, lambda m: m[1]+content+'\n'+m[2], text, flags=re.S)
    assert n == 1, (tag,n)
    return updated


def coords(values):
    return ' '.join(f'({x:.8g},{y:.8g})' for x,y in values)


def tex(value):
    return value.replace('&',r'\&').replace('%',r'\%').replace('_',r'\_').replace('#',r'\#')


def main():
    text=PAPER.read_text()
    summary={r['policy']:r for r in rows('policy_summary.csv')}
    contrasts=rows('paired_contrasts.csv')
    raw=rows('main_runs.csv')
    assert len(raw)==2400 and set(summary)==set(POLICIES)
    lines=[]
    for p,label in zip(POLICIES,LABELS):
        s=summary[p]
        values=[100*float(s[m+'_mean']) for m in ['call_miss_fraction','voice_missed_fraction','video_missed_fraction']]
        lines.append(label+' & '+' & '.join(f'{v:.3f}' for v in values)+f" & {float(s['handoffs_mean']):.2f} \\\\")
    text=put(text,'MAIN_TABLE','\n'.join(lines))

    bars=r'''\begin{tikzpicture}
\begin{axis}[width=.98\linewidth,height=66mm,ybar,bar width=4pt,ymin=0,ymax=13.5,
 ylabel={Deadline misses (\%)},xtick={0,...,9},xticklabels={'''+','.join(LABELS)+r'''},
 x tick label style={rotate=35,anchor=east,font=\scriptsize},tick label style={font=\small},
 enlarge x limits=.07,ymajorgrids,grid style={gray!20},
 legend style={at={(.5,1.02)},anchor=south,legend columns=2,font=\small}]
'''
    for metric,color,label in [('voice_missed_fraction','blue!65!black','Voice packets'),('video_missed_fraction','orange!85!black','Whole video frames')]:
        bars+=r'\addplot[fill='+color+',draw='+color+'] coordinates {'+coords([(i,100*float(summary[p][metric+'_mean'])) for i,p in enumerate(POLICIES)])+'};\n'+r'\addlegendentry{'+label+'}\n'
    bars+=r'\end{axis}\end{tikzpicture}'
    text=put(text,'BARS',bars)

    selected={r['scope']:r for r in contrasts if r['comparator']=='app_myopic' and r['metric']=='call_miss_fraction'}
    fig=r'''\begin{tikzpicture}\begin{axis}[width=.87\linewidth,height=65mm,
 xlabel={Difference in deadline-miss score (percentage points)},ytick={0,...,5},
 yticklabels={'''+','.join(SCENARIO_LABELS)+r'''},y dir=reverse,ymin=-.5,ymax=5.5,
 xmin=-.3,xmax=.8,xmajorgrids,grid style={gray!20},tick label style={font=\small}]
\addplot[gray,dashed] coordinates {(0,-.5)(0,5.5)};
'''
    for i,s in enumerate(SCENARIOS):
        c=selected[s];lo,hi,mean=[100*float(c[k]) for k in ['ci_low','ci_high','difference']]
        fig+=r'\addplot[blue!65!black,thick,mark=|] coordinates {'+coords([(lo,i),(hi,i)])+'};\n'
        fig+=r'\addplot[blue!65!black,only marks,mark=*] coordinates {'+coords([(mean,i)])+'};\n'
    fig+=r'\end{axis}\end{tikzpicture}'
    text=put(text,'SCENARIO',fig)

    fig=r'''\begin{tikzpicture}\begin{axis}[width=.90\linewidth,height=65mm,
 xlabel={Longest voice miss run per 60 s call (ms)},ylabel={Fraction of runs},
 ymin=0,ymax=1.02,xmin=0,xmajorgrids,ymajorgrids,grid style={gray!20},
 legend style={at={(.98,.12)},anchor=south east,font=\small},tick label style={font=\small}]
'''
    for p,label,color,style in [('rssi','Signal','gray!80','dotted'),('load_aware','Capacity/load','orange!80!black','dashed'),('app_myopic','App margin','blue!65!black','solid'),('predictive','Proposed','green!45!black','dashdotted')]:
        counts=Counter(1000*float(r['voice_longest_outage_seconds']) for r in raw if r['policy']==p)
        pairs=[(0,0)];total=0
        for value,count in sorted(counts.items()):
            total+=count;pairs.append((value,total/240))
        fig+=r'\addplot[const plot,thick,'+color+','+style+'] coordinates {'+coords(pairs)+'};\n'+r'\addlegendentry{'+label+'}\n'
    fig+=r'\end{axis}\end{tikzpicture}'
    text=put(text,'CDF',fig)

    archive=json.loads(gzip.decompress(read_bytes(DATA/'selected_traces.json.gz')))
    traces={(r['scenario'],r['policy']):r for r in archive['traces']}
    cfg=archive['config']
    fig=r'''\begin{tikzpicture}\begin{axis}[width=.88\linewidth,height=47mm,
 xmin=0,xmax=60.2,ymin=-.6,ymax=3.6,ytick={3,2,1,0},
 yticklabels={App margin: voice,App margin: video,Proposed: voice,Proposed: video},
 xlabel={Scheduled delivery deadline (s)},tick label style={font=\small},axis y line=left,y axis line style={draw=none},ytick style={draw=none}]
'''
    for index,(p,kind) in enumerate([('app_myopic','voice'),('app_myopic','video'),('predictive','voice'),('predictive','video')]):
        y=3-index;trace=traces['short_cells',p]
        assert trace['seed']==50001
        flags=trace['voice_ontime'] if kind=='voice' else trace['video_complete']
        period=cfg['voice_interval_seconds'] if kind=='voice' else 1/cfg['video_fps']
        deadline=cfg[kind+'_deadline_seconds']
        fig+=rf'\fill[gray!15] (axis cs:{deadline},{y-.28}) rectangle (axis cs:{deadline+60},{y+.28});'+'\n'
        start=None
        for i,ok in enumerate(flags+[True]):
            if not ok and start is None:start=i
            if ok and start is not None:
                a=start*period+deadline;b=i*period+deadline
                fig+=rf'\fill[red!65!black] (axis cs:{a:.7f},{y-.28}) rectangle (axis cs:{b:.7f},{y+.28});'+'\n'
                start=None
    fig+=r'\end{axis}\end{tikzpicture}'
    text=put(text,'TIMELINE',fig)

    lines=[]
    for p in ['no_dwell','no_guard','no_cost','no_age']:
        c=next(r for r in contrasts if r['scope']=='all' and r['comparator']==p and r['metric']=='call_miss_fraction')
        values=[100*float(c[k]) for k in ['difference','ci_low','ci_high']]
        lines.append(f"{LABELS[POLICIES.index(p)]} & {values[0]:+.3f} & [{values[1]:+.3f}, {values[2]:+.3f}] \\\\")
    text=put(text,'ABLATION','\n'.join(lines))

    sens=[r for r in rows('sensitivity_overview.csv') if r['comparator']=='app_myopic']
    load={r['condition']:r for r in rows('additional_load/supplementary_contrasts.csv') if r['scope']=='all' and r['metric']=='call_miss_fraction'}
    names=['Matched reference','Tight deadlines','Relaxed deadlines','Costly transitions','Stale reports','Cost underestimate','Step 5 ms','Step 20 ms','Queue retained']
    assert len(sens)==len(names)
    lines=[]
    for label,r in zip(names,sens):
        key='matched_main_reference' if r['condition']=='reference_subset' else r['condition']
        values=[100*float(r[k]) for k in ['proposed_miss','comparator_miss']]+[100*float(load[key]['load_aware_mean'])]+[100*float(r[k]) for k in ['difference','ci_low','ci_high']]
        lines.append(label+' & '+' & '.join(f'{v:.3f}' for v in values[:3])+f' & {values[3]:+.3f} & [{values[4]:+.3f}, {values[5]:+.3f}] '+r'\\')
    text=put(text,'SENSITIVITY','\n'.join(lines))

    fig=r'''\begin{tikzpicture}\begin{axis}[width=.9\linewidth,height=70mm,
 xlabel={Mean handoff attempts per 60 s call},ylabel={Mean deadline-miss score (\%)},
 xmin=4,xmax=14,ymin=.5,ymax=8,xmajorgrids,ymajorgrids,grid style={gray!20},tick label style={font=\small}]
'''
    short=['Signal','Capacity/load','App margin','Earlier caution','Session stay','P','D','G','C','A']
    offsets=[(0,-18),(22,-10),(-35,-12),(-36,25),(20,10),(-12,35),(15,22),(-35,12),(5,13),(30,2)]
    for p,label,(dx,dy) in zip(POLICIES,short,offsets):
        x=float(summary[p]['handoffs_mean']);y=100*float(summary[p]['call_miss_fraction_mean'])
        fig+=r'\addplot[only marks,mark=*,blue!65!black] coordinates {'+coords([(x,y)])+'};\n'
        fig+=rf'\draw[gray] (axis cs:{x},{y}) -- ++({dx}pt,{dy}pt) node[text=black,fill=white,inner sep=1pt,font=\scriptsize] {{{label}}};'+'\n'
    fig+=r'\end{axis}\end{tikzpicture}'
    text=put(text,'TRADEOFF',fig)

    # Parse the repository's deliberately simple, one-field-per-line bibliography.
    bib={}
    for path in [ROOT/'references/bibliography.bib',ROOT/'references/packet-bibliography.bib']:
        source=read_bytes(path).decode()
        for match in re.finditer(r'@\w+\{([^,]+),\n(.*?)\n\}',source,re.S):
            fields={m[1]:m[2].strip('{}') for m in re.finditer(r'^\s*(\w+) = \{(.*)\},?$',match[2],re.M)}
            bib[match[1]]=fields
    order=['M01','F01','F02','F03','R03','R06','R04','R13','R07','M06','R01','R02','P01','P02','M12','P06','P07']
    lines=[]
    for key in order:
        b=bib[key];authors=b.get('author','').split(' and ')
        name=', '.join(authors) if len(authors)<=3 else authors[0]+' et al.'
        venue=b.get('journal',b.get('booktitle',b.get('howpublished','Author preprint')))
        year=b.get('year','accessed 14 October 2026')
        notes=''
        if key in ['R01','R02']:notes=' Abstract/metadata reviewed; full methods not inspected.'
        if key=='R04':notes=' ML4Wireless 2025 workshop, not ICML main track.'
        if key=='R06':notes=' Later CCNC 2024 version.'
        if key=='M12':notes=' Dated 25 September 2025.'
        lines.append(r'\bibitem{'+key+'} '+tex(name).rstrip('.')+'. '+tex(b['title']).rstrip('.')+'. '+tex(venue)+', '+year+'.'+notes+'\n'+r'\url{'+b['url']+'}.')
    text=put(text,'BIBLIOGRAPHY','\n\n'.join(lines))
    PAPER.write_text(text)
    (ROOT/'paper/data-generation-manifest.json').write_text(json.dumps({
        'inputs_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(INPUTS)},
        'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'generated_regions':['MAIN_TABLE','BARS','SCENARIO','CDF','TIMELINE','ABLATION','SENSITIVITY','TRADEOFF','BIBLIOGRAPHY'],
        'note':'Only marked regions are generated. Prose is reviewed separately. No data files are loaded by LaTeX; the source is standalone.'},indent=2)+'\n')
    print('Updated standalone paper: four tables, five data figures, inline references; fixed network diagram retained.')


if __name__=='__main__':main()
