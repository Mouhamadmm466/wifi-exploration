#!/usr/bin/env python3
"""Plot the timeline chosen before held-out outcomes were viewed."""
import gzip
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

ROOT=Path(__file__).resolve().parents[1]


def segments(flags,period,deadline):
    result=[];start=None
    for i,ok in enumerate(flags+[True]):
        if not ok and start is None:start=i
        if ok and start is not None:
            result.append((start*period+deadline,(i-start)*period));start=None
    return result


def main():
    source=ROOT/'results/packet/selected_traces.json.gz'
    with gzip.open(source,'rt') as f:data=json.load(f)
    c=data['config'];traces={(r['scenario'],r['policy']):r for r in data['traces']}
    fig,ax=plt.subplots(figsize=(11,3.5),layout='constrained')
    labels=[]
    for row,(policy,kind) in enumerate([('app_myopic','voice'),('app_myopic','video'),('predictive','voice'),('predictive','video')]):
        trace=traces['short_cells',policy]
        flags=trace['voice_ontime'] if kind=='voice' else trace['video_complete']
        period=c['voice_interval_seconds'] if kind=='voice' else 1/c['video_fps']
        deadline=c[kind+'_deadline_seconds']
        y=3-row
        ax.broken_barh([(deadline,c['duration_seconds'])],(y-.3,.6),facecolors='#e8ecef')
        ax.broken_barh(segments(flags,period,deadline),(y-.3,.6),facecolors='#b04632')
        labels.append(('Tuned app margin' if policy=='app_myopic' else 'Proposed')+' — '+kind)
    ax.set_yticks([3,2,1,0],labels)
    ax.set_xlim(0,c['duration_seconds']+max(c['voice_deadline_seconds'],c['video_deadline_seconds']))
    ax.set_xlabel('Scheduled delivery deadline (seconds)')
    ax.set_title('Preselected example: short cells, seed 50001',loc='left',weight='bold')
    ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True)
    ax.spines[['top','right','left']].set_visible(False)
    ax.legend(handles=[Patch(facecolor='#b04632',label='Missing scheduled media unit')],loc='upper right',frameon=False)
    output=ROOT/'results/packet/figures';output.mkdir(exist_ok=True,parents=True)
    for ext in ['png','pdf']:fig.savefig(output/('preselected_timeline.'+ext),dpi=220,bbox_inches='tight')
    plt.close(fig)
    (output/'timeline_manifest.json').write_text(json.dumps({'input':str(source.relative_to(ROOT)),
        'input_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'scenario':'short_cells','seed':50001,
        'selection':'Fixed before held-out evaluation; not selected for an extreme outcome.',
        'metric':'consecutive missing voice packets or incomplete video frames at scheduled deadlines; not decoded media.'},indent=2)+'\n')

if __name__=='__main__':main()
