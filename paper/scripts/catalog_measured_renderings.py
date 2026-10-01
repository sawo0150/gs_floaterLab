#!/usr/bin/env python3
"""Review every candidate's actual held-out renders before figure selection.

View and crop proposals use GT structure only. Prediction quality never selects
the crop. All original PNGs remain immutable; contact sheets are layout copies.
"""
import csv
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

PAPER=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PAPER/'scripts'))
from build_measured_tables import CANDIDATES,RESULTS,read
ASSET=PAPER/'figures/figure05_rendering_comparison'


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def proposed_crop(path):
    image=Image.open(path).convert('RGB')
    gray=np.asarray(image.filter(ImageFilter.GaussianBlur(1)).convert('L'),dtype=float)/255
    gx,gy=np.gradient(gray)
    energy=np.hypot(gx,gy)
    h,w=gray.shape;cw,ch=max(8,w//3),max(8,h//3)
    choices=[]
    for y in np.linspace(0,h-ch,9,dtype=int):
        for x in np.linspace(0,w-cw,9,dtype=int):
            region=gray[y:y+ch,x:x+cw]
            structure=float(energy[y:y+ch,x:x+cw].mean())
            valid=float(((region>.04)&(region<.96)).mean())
            choices.append((structure*valid,[int(x),int(y),int(x+cw),int(y+ch)]))
    return max(choices,key=lambda r:r[0])


def main():
    directory=ASSET/'analysis';directory.mkdir(exist_ok=True)
    catalog=[];all_views=[]
    for dataset,scenes in CANDIDATES.items():
        for scene in scenes:
            panel=RESULTS/('cvpr_assets/fixed_work_12f_v1' if scene=='aria301_12F' else 'cvpr_assets/fixed_work_v1')
            base=panel/'render40'/dataset/scene
            row={'dataset':dataset,'scene':scene,'status':'awaiting_final_checkpoint_evaluation'}
            summaries=[base/arm/'curve_evaluation/summary.json' for arm in ['vanilla','d3']]
            if not all(p.exists() and any(r['name']=='final' and r['status']=='evaluated' for r in read(p)) for p in summaries):
                catalog.append(row);continue
            final={arm:base/arm/'curve_evaluation/final' for arm in ['vanilla','d3']}
            metric={arm:read(final[arm]/'psnr/curve_fixed_subset/final_result.json') for arm in final}
            for m in metric.values():
                q=m['predeclared_fixed_manifest_posthoc'];assert q['mapping_disjoint'] and q['mapping_view_overlap_count']==0
            by_id={arm:{r['frame_index']:r for r in m['per_view'] if r['predeclared_fixed_manifest_split']} for arm,m in metric.items()}
            assert set(by_id['d3'])==set(by_id['vanilla'])
            proposals=[]
            for uid in sorted(by_id['d3']):
                paths={arm:final[arm]/'images'/f'{uid:06d}_render.png' for arm in final}
                gt=final['d3']/'images'/f'{uid:06d}_gt.png'
                assert sha(gt)==sha(final['vanilla']/'images'/gt.name)
                assert all(p.exists() for p in paths.values())
                score,crop=proposed_crop(gt)
                view={'dataset':dataset,'scene':scene,'frame_index':uid,'gt_structure_score':score,'crop':crop,
                    'gt':str(gt),'gt_sha256':sha(gt),'vanilla':str(paths['vanilla']),'d3':str(paths['d3']),
                    'vanilla_sha256':sha(paths['vanilla']),'d3_sha256':sha(paths['d3']),
                    'vanilla_psnr':by_id['vanilla'][uid]['psnr'],'ours_psnr':by_id['d3'][uid]['psnr']}
                proposals.append(view);all_views.append(view)
            selected=max(proposals,key=lambda r:r['gt_structure_score'])
            row.update(status='actual_renderings_reviewed',proposed_view=selected,
                view_selection='maximum blurred-GT gradient energy times exposure coverage; no prediction scores',
                evaluated_heldout_views=len(proposals),curve_summaries=[{'path':str(p),'sha256':sha(p)} for p in summaries])
            catalog.append(row)
    payload={'rows':catalog,'complete_candidate_render_review':all(r['status']=='actual_renderings_reviewed' for r in catalog),
        'expected_scenes':sum(len(s) for s in CANDIDATES.values()),'crop_selection_uses_prediction':False,
        'script_sha256':sha(__file__)}
    (directory/'rendering_catalog.json').write_text(json.dumps(payload,indent=2)+'\n')
    if all_views:
        with (directory/'heldout_view_structure_scores.csv').open('w',newline='') as f:
            writer=csv.DictWriter(f,list(all_views[0]));writer.writeheader();writer.writerows(all_views)
    complete=[r for r in catalog if r['status']=='actual_renderings_reviewed']
    out=ASSET/'output/full_cohort_review';out.mkdir(exist_ok=True)
    try: font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',12)
    except OSError:font=ImageFont.load_default()
    for page,start in enumerate(range(0,len(complete),10),1):
        group=complete[start:start+10]
        contact=Image.new('RGB',(840,185*len(group)+30),'white');draw=ImageDraw.Draw(contact)
        for i,row in enumerate(group):
            v=row['proposed_view'];y=30+185*i
            draw.text((8,y),f"{row['dataset']}/{row['scene']} · held-out frame {v['frame_index']}",fill='black',font=font)
            for j,(key,label) in enumerate([('vanilla','VIGS-SLAM'),('d3','Ours (D3)'),('gt','Ground truth')]):
                image=Image.open(v[key]).convert('RGB')
                image=ImageOps.contain(image,(270,150))
                contact.paste(image,(j*280+(270-image.width)//2,y+28))
                draw.text((j*280+6,y+14),label,fill='black',font=font)
        contact.save(out/f'contact-{page:02d}.png')
    print('ACTUAL_RENDER_CATALOG',len(complete),'/',len(catalog),'scenes',len(all_views),'views')


if __name__=='__main__':main()
