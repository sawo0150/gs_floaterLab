#!/usr/bin/env python3
"""Create an SVG contact sheet with identical unmodified saved-render crops."""
import base64
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'candidates/high_gain_review'
rows = json.loads((ROOT.parent / 'figure02/analysis/view_ranking.json').read_text())
# Manual semantic ROIs: desks, chairs, wall boundaries, not maximum-error ceiling.
choices = [(1180, (0, 195, 464, 445)), (980, (0, 205, 464, 455)), (1220, (0, 205, 464, 455))]
parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1260" height="1010" viewBox="0 0 1260 1010">',
         '<rect width="1260" height="1010" fill="white"/>']
def text(x, y, s, size=24):
    parts.append(f'<text x="{x}" y="{y}" font-family="DejaVu Sans" font-size="{size}" fill="#182331">{s}</text>')
text(24, 36, 'Aria 301_305 | actual final-map candidates', 29)
text(24, 65, 'Scene mean PSNR: 21.93 → 25.11 dB (+3.19). High-gain examples; no convergence claim.', 19)
records = []
for row_index, (idx, crop) in enumerate(choices):
    r = next(x for x in rows if x['scene'] == 'aria301_305' and x['frame_index'] == idx)
    source = OUT / f'frame_{idx:04d}' if idx != 1220 else ROOT.parent / 'figure02/candidates/frames/F01'
    y = 95 + row_index*288
    text(24, y+22, f"{'Recommended: ' if idx==1180 else ''}frame {idx} | full-view PSNR {r['baseline_psnr']:.2f} → {r['ours_psnr']:.2f} dB (+{r['delta_psnr']:.2f})", 22)
    x0,y0,x1,y1 = crop
    for col, (name,label) in enumerate([('baseline','VIGS-SLAM'),('ours','Ours'),('gt','Ground truth')]):
        x = 24+col*410
        text(x, y+53, label, 21)
        uri = 'data:image/png;base64,'+base64.b64encode((source/f'{name}.png').read_bytes()).decode()
        scale = min(390/(x1-x0), 210/(y1-y0))
        clip_id = f'crop_{row_index}_{col}'
        parts.append(f'<defs><clipPath id="{clip_id}" clipPathUnits="userSpaceOnUse"><rect x="{x}" y="{y+65}" width="{(x1-x0)*scale}" height="{(y1-y0)*scale}"/></clipPath></defs>')
        parts.append(f'<g clip-path="url(#{clip_id})"><image x="{x-x0*scale}" y="{y+65-y0*scale}" width="{464*scale}" height="{464*scale}" href="{uri}"/></g>')
    records.append({'frame_index':idx,'source':str(source),'crop_xyxy':crop,'crop_basis':'manual semantic ROI shared across all methods','psnr_scope':'full image, not crop'})
text(24, 994, 'Identical crops and display scale. No sharpening, recoloring, or generated pixels.', 19)
parts.append('</svg>')
svg = OUT / 'high_gain_comparison.svg'
svg.write_text('\n'.join(parts))
(OUT/'crop_selection.json').write_text(json.dumps(records,indent=2)+'\n')
subprocess.run(['inkscape',str(svg),'--export-type=png',f'--export-filename={OUT / "high_gain_comparison.png"}'],check=True)
