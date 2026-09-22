#!/usr/bin/env python3
"""Review-only SVG variants, preserving selected Fig3 and all underlying data."""
import json,hashlib,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'analysis/peak_annotation_review';OUT.mkdir(exist_ok=True)
source=ROOT/'output/fig3_table06_compact_frame1420.svg'
cp=Path('/home/intern/gs_floaterLab/results/figure03_scene_search_20260921/rpng/table_06/evaluation/curves.json')
rows=json.loads(cp.read_text())['curves'];curves={a:sorted([r for r in rows if r['arm']==a],key=lambda r:r['iteration']) for a in ['baseline','ours']}
peak=max(curves['baseline'],key=lambda r:r['mean_psnr']);q=peak['mean_psnr'];ours=curves['ours']
first=next(r for r in ours if r['mean_psnr']>=q)
retained=next(r for i,r in enumerate(ours) if all(z['mean_psnr']>=q for z in ours[i:]))
def px(t):return 125+1345*t/2800
def py(v):return 625-600*(v-14)/11.5
variants={}
for label,point in [('first_sampled',first),('remaining_checkpoints',retained)]:
 xa,xb=px(point['iteration']),px(peak['iteration']);ya,yb=py(point['mean_psnr']),py(q);delta=peak['iteration']-point['iteration'];bar=70
 annotation=f'''<g id="peak-comparison">
 <text x="160" y="68" font-family="Times New Roman" font-size="29" fill="#555">VIGS-SLAM best: {q:.2f} dB</text>
 <path d="M {xa} {ya-7} V {bar} H {xb} V {yb-7}" fill="none" stroke="#777" stroke-width="1.7" stroke-dasharray="5 5"/>
 <path d="M {xa} {bar-5} v 10 M {xb} {bar-5} v 10" fill="none" stroke="#555" stroke-width="1.9"/>
 <text x="{(xa+xb)/2}" y="{bar-12}" text-anchor="middle" font-family="Times New Roman" font-size="28" fill="#333">{delta:,} fewer iter.*</text>
 <path d="M {xa} {ya-7} l 7 7 l -7 7 l -7 -7 Z" fill="white" stroke="#008f93" stroke-width="2.5"/>
 <path d="M {xb} {yb-7} l 7 7 l -7 7 l -7 -7 Z" fill="white" stroke="#d86236" stroke-width="2.5"/>
 </g>'''
 s=source.read_text().replace('</svg>',annotation+'\n</svg>')
 s=s.replace('No threshold or crossing annotation: native streaming curves fluctuate.',f'Review variant {label}: markers are measured checkpoints, not interpolated crossings.')
 path=OUT/f'frame1420_{label}.svg';path.write_text(s)
 subprocess.run(['inkscape',str(path),'--export-type=png','--export-width=1800',f'--export-filename={path.with_suffix(".png")}'],check=True,capture_output=True)
 variants[label]={'ours_iteration':point['iteration'],'ours_psnr':point['mean_psnr'],'baseline_iteration':peak['iteration'],'baseline_psnr':q,'iteration_difference':delta}
report={'source_svg':str(source),'source_svg_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'curves_sha256':hashlib.sha256(cp.read_bytes()).hexdigest(),'variants':variants,'definitions':{'first_sampled':'First stored checkpoint at or above baseline best. Later regressions allowed.','remaining_checkpoints':'First stored checkpoint at or above baseline best with all subsequent stored checkpoints also at or above it. Retrospective on finite observations, not continuous or future guarantee.'},'source_figure_modified':False}
(OUT/'metrics.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(variants,indent=2))
