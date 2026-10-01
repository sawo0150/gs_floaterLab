"""Collect measured fixed40 maps; no imputation or scene selection."""
import csv, json, statistics
from pathlib import Path
import run_dense_depth_four_scene as P

def main():
    rows=[]
    manual=P.read(P.RESULT/'manual_region.json') if (P.RESULT/'manual_region.json').exists() else None
    regions={r['label']:r for r in manual['runs']} if manual else {}
    for key,(dataset,scene) in P.SCENES.items():
      for seed in [0,1]:
       for arm in P.ARMS:
        run=P.RESULT/key/f'seed{seed}'/arm
        path=run.parent/f'{arm}_summary.json'
        if not path.exists(): continue
        r=P.read(path)
        if not r['passed']: continue
        q=P.read(run/'psnr/strict_fixed_manifest/final_result.json')['predeclared_fixed_manifest_posthoc']
        assert q['mapping_disjoint'] and q['mapping_view_overlap_count']==0
        x=P.read(run/'render_result.json')
        rt=r['runtime'];g=r['geometry']
        assert rt['stats']['kf_d3_views']+rt['stats']['dense_views']==x['main_optimizer_steps']
        if arm==P.ARMS[0]: assert rt['stats']['dense_views']==0
        else: assert rt['stats']['dense_views']>0
        row=dict(scene=scene,arm=arm,seed=seed,heldout_psnr=r['psnr'],heldout_ssim=q['mean_ssim'],heldout_lpips=q['mean_lpips'],heldout_views=q['view_count'],
            gaussians=r['gaussians'],mapping_seconds=r['mapping_seconds'],updates=x['main_optimizer_steps'],kf_updates=rt['stats']['kf_d3_views'],dense_updates=rt['stats']['dense_views'],
            dense_target_coverage=rt['dense_stats'].get('target_coverage'),ba_mae_m=g['depth_mae'],ba_front=g['opaque_front'],ba_within=g['opaque_within'],ba_behind=g['opaque_behind'],ba_holes=g['hole_fraction'],ba_views=g['heldout_keyframes'],ply=str(run/'3dgs_before_final.ply'))
        if (run/'geometry_mps_local.json').exists():
            m=P.read(run/'geometry_mps_local.json')
            row.update({f'mps_{k}':m[k] for k in ['opaque_front','opaque_within','opaque_behind','hole_fraction','absrel_median','points','local_align_rms_median','local_align_rms_max']})
        if (run/'termination_mps_local.json').exists():
            t=P.read(run/'termination_mps_local.json')
            row['termination_kernel_max_error']=t['kernel_max_abs_err']
            for k in ['front_mass','surface_mass','behind_mass','pre_mass','median_front','n']:
                row['mps_termination_'+k]=t['strata']['all_opaque'][k]
            row['mps_termination_holes']=t['strata']['all_any']['hole']
        if key=='aria' and f'{arm}__seed{seed}' in regions:
            m=regions[f'{arm}__seed{seed}']
            for mask in ['eroded_1','nominal','dilated_1']:
                row[f'region_{mask}_count']=m['counts'][mask]['opacity_gt_0_3']
                row[f'region_{mask}_support']=m['counts'][mask]['opacity_support_mass']
            row['region_alignment_p90_m']=m['alignment_p90_m']
        rows.append(row)
    pairs=[]
    for key,(_,scene) in P.SCENES.items():
      for seed in [0,1]:
        paths=[P.RESULT/key/f'seed{seed}'/arm/'render_result.json' for arm in P.ARMS[1:]]
        if not all(p.exists() for p in paths): continue
        reports=[P.read(p) for p in paths]
        trace=lambda x:[(g['policy']['generation'],s['uids'],s['roles'],s['counts_before'],s['dense_anchors']) for g in x['training']['generations'] for s in g['services']]
        identical=trace(reports[0])==trace(reports[1])
        assert identical, (scene,seed,'B/C supervision trace changed')
        pairs.append(dict(scene=scene,seed=seed,same_B_C_supervision_trace=identical,updates=reports[0]['main_optimizer_steps']))
    P.write(P.RESULT/'paired_trace_audit.json',pairs)
    P.write(P.RESULT/'comparison.json',rows)
    keys=list(dict.fromkeys(k for row in rows for k in row))
    with (P.RESULT/'comparison.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
    mean=lambda rr,k:statistics.mean(r[k] for r in rr)
    lines=['# Fixed40 measured comparison','',f'Completed maps: {len(rows)}/24. Mapper seeds 0 and 1 on the same frozen tracker; arithmetic means below.','',
        'A = KF RGB+depth; B = KF RGB+depth + dense RGB; C = KF RGB+depth + dense RGB+depth.','',
        'All depths: metric L1, weight 0.25. Normal losses off. Causal frozen tracker replay, 40 single-view updates/KF; not a real-time deadline test.','',
        '## Held-out appearance','', '| Scene | Arm | n | PSNR mean [min, max] dB ↑ | SSIM ↑ | LPIPS ↓ | GS count |', '|---|---|---:|---:|---:|---:|---:|']
    groups={}
    for key,(_,scene) in P.SCENES.items():
      for label,arm in zip('ABC',P.ARMS):
        rr=[r for r in rows if r['scene']==scene and r['arm']==arm]
        if not rr: continue
        groups[scene,label]=rr
        vals=[r['heldout_psnr'] for r in rr]
        lines.append(f'| {scene} | {label} | {len(rr)} | {mean(rr,"heldout_psnr"):.3f} [{min(vals):.3f}, {max(vals):.3f}] | {mean(rr,"heldout_ssim"):.4f} | {mean(rr,"heldout_lpips"):.4f} | {mean(rr,"gaussians"):.0f} |')
    lines+=['','## Paired PSNR effects','', '| Scene | B − A dB | C − B dB | C − A dB |', '|---|---:|---:|---:|']
    for _,scene in P.SCENES.values():
        if not all((scene,l) in groups and len(groups[scene,l])==2 for l in 'ABC'): continue
        means=[mean(groups[scene,l],'heldout_psnr') for l in 'ABC']
        lines.append(f'| {scene} | {means[1]-means[0]:+.3f} | {means[2]-means[1]:+.3f} | {means[2]-means[0]:+.3f} |')
    lines+=['','## Common geometry: held-out tracker depth agreement','',
        '**Auxiliary, not independent GT.** MAE is in tracker metric coordinates; front/within/behind use ±6.25% bands and alpha ≥0.95. Holes use alpha ≤0.9. Fractions below are percentages.','',
        '| Scene | Arm | MAE m ↓ | Front % ↓ | Within % ↑ | Behind % ↓ | Holes % ↓ |','|---|---|---:|---:|---:|---:|---:|']
    for (scene,label),rr in groups.items():
        lines.append(f'| {scene} | {label} | {mean(rr,"ba_mae_m"):.4f} | {mean(rr,"ba_front")*100:.2f} | {mean(rr,"ba_within")*100:.2f} | {mean(rr,"ba_behind")*100:.2f} | {mean(rr,"ba_holes")*100:.2f} |')
    lines+=['','## Independent MPS termination distribution (Aria only)','',
        'Evaluation-only semidense MPS with local 30-KF Sim(3). Front/behind mass are normalized accumulated opacity on opaque rays; surface band ±6.25%. Lower front mass alone is insufficient if behind mass grows.','',
        '| Scene | Arm | Front mass % ↓ | Surface mass % ↑ | Behind mass % ↓ | Holes % ↓ | Local alignment RMS median m |','|---|---|---:|---:|---:|---:|---:|']
    for (scene,label),rr in groups.items():
        if not all('mps_termination_front_mass' in r for r in rr): continue
        lines.append(f'| {scene} | {label} | {mean(rr,"mps_termination_front_mass")*100:.2f} | {mean(rr,"mps_termination_surface_mass")*100:.2f} | {mean(rr,"mps_termination_behind_mass")*100:.2f} | {mean(rr,"mps_termination_holes")*100:.2f} | {mean(rr,"mps_local_align_rms_median"):.4f} |')
    lines+=['','## Independent MPS mean-depth agreement','',
        'Semidense reference points, same projection/alignment for all arms. These mean-depth classes supplement the termination distribution above.','',
        '| Scene | Arm | Median absolute relative error % ↓ | Front % ↓ | Within % ↑ | Behind % ↓ |','|---|---|---:|---:|---:|---:|']
    for (scene,label),rr in groups.items():
        if not all('mps_absrel_median' in r for r in rr): continue
        lines.append(f'| {scene} | {label} | {mean(rr,"mps_absrel_median")*100:.2f} | {mean(rr,"mps_opaque_front")*100:.2f} | {mean(rr,"mps_opaque_within")*100:.2f} | {mean(rr,"mps_opaque_behind")*100:.2f} |')
    lines+=['','## Independent manual empty-space region (aria1253)','',
        'Mean Gaussian count at opacity >0.3 and opacity-weighted support in the annotated empty region. Erosion/dilation and registration residual are retained to expose alignment sensitivity.','',
        '| Arm | Eroded count ↓ | Nominal count ↓ | Dilated count ↓ | Nominal opacity support ↓ | Alignment p90 m |','|---|---:|---:|---:|---:|---:|']
    for (scene,label),rr in groups.items():
        if not all('region_nominal_count' in r for r in rr): continue
        lines.append(f'| {label} | {mean(rr,"region_eroded_1_count"):.1f} | {mean(rr,"region_nominal_count"):.1f} | {mean(rr,"region_dilated_1_count"):.1f} | {mean(rr,"region_nominal_support"):.2f} | {mean(rr,"region_alignment_p90_m"):.4f} |')
    lines+=['','## Budget and depth coverage','',
        '| Scene | Arm | Updates | KF updates | Dense updates | Dense target coverage % | Mapping seconds* |','|---|---|---:|---:|---:|---:|---:|']
    for (scene,label),rr in groups.items():
        cov=mean(rr,'dense_target_coverage')*100 if all(r['dense_target_coverage'] is not None for r in rr) else None
        coverage = f'{cov:.2f}' if cov is not None else '—'
        lines.append(f'| {scene} | {label} | {mean(rr,"updates"):.0f} | {mean(rr,"kf_updates"):.0f} | {mean(rr,"dense_updates"):.0f} | {coverage} | {mean(rr,"mapping_seconds"):.2f} |')
    lines+=['','*Replay mapper time excludes tracking and evaluation; descriptive only, not an end-to-end real-time claim.','',
        'PLY files are symlinks to preserved raw results. Per-run values and source paths: `comparison.csv` and `comparison.json`.','']
    report='\n'.join(lines)
    (P.RESULT/'COMPARISON.md').write_text(report)
    card=P.ROOT/'context/experiments/campaigns/06_gain_attribution/dense_depth_four_scene'
    (card/'SUMMARY.md').write_text(report)
    browse=P.RESULT/'ply'
    for name in ['comparison.csv','comparison.json']:
        target=browse/name
        if not target.exists(): target.symlink_to(P.RESULT/name)
    index=['# PLY index','', 'Raw artifacts are stored under `results/campaigns/gain_attribution/dense_depth_four_scene/v1/`.','',
           'A = KF RGB+depth; B = +dense RGB; C = +dense RGB+depth. All maps use 40 updates/KF.','',
           '| Scene | Seed | Arm | PLY |','|---|---:|---|---|']
    for r in rows:
        name=f'{r["scene"]}__{r["arm"]}__iter40__seed{r["seed"]}.ply'
        target=browse/r['scene']/name
        index.append(f'| {r["scene"]} | {r["seed"]} | {r["arm"]} | [{name}]({target}) |')
    (card/'PLY_INDEX.md').write_text('\n'.join(index)+'\n')
    print(f'Collected {len(rows)}/24 maps')

if __name__=='__main__': main()
