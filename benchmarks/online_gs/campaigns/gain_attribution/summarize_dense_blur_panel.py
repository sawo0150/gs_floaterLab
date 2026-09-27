#!/usr/bin/env python3
"""Verify completed artifacts, then report every blur/no-dense comparison."""
import argparse
from pathlib import Path
import statistics
import run_dense_blur_panel as panel
common=panel.common


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True,type=Path)
    p.add_argument('--control-root',type=Path);args=p.parse_args()
    rows=common.read(args.root/'summary.json');legacy=[]
    roots=[args.root]
    if args.control_root:
        legacy=common.read(args.control_root/'summary.json')
        rows=[r for r in legacy if r['case']!='on']+rows
        roots.append(args.control_root)
    for root in roots:
        lock=common.read(root/'source_lock.json')
        assert all(common.sha(Path(v['copy']))==v['sha256'] for v in lock.values())
    table={}
    for row in rows:
        assert row['valid_execution'] and row['audit_pass'] and not row['source_changed'] and not row['error']
        out=Path(row['output']);audit=panel.audit_run(out,row['dataset'],row['case'])
        assert audit['pass'];table.setdefault(row['dataset'],{})[row['case']]=row
    lines=['# Dense blur screening — same 40 renders/KF','',
           '2026-09-26 · seed0 · cumulative ERVS · per-image Adam · scale projection ON · densify/prune OFF','',
           '|Scene|Vanilla|No dense (3:9:0)|Dense OFF filter|Dense ON filter|ON−OFF|ON−no dense|ON−vanilla|',
           '|---|---:|---:|---:|---:|---:|---:|---:|']
    report=[]
    for dataset,arms in table.items():
        assert set(arms)==set(panel.CASES)
        vanilla=common.read(common.OLD/dataset/'vanilla/psnr/strict_fixed_manifest/final_result.json')
        heldout=[v for v in vanilla['per_view'] if v['predeclared_fixed_manifest_split']]
        vp=sum(v['psnr'] for v in heldout)/len(heldout)
        off,on,no=[arms[k]['psnr'] for k in ('off','on','no_dense')]
        row={'dataset':dataset,'vanilla':vp,'off':off,'on':on,'no_dense':no,
             'filter_delta':on-off,'dense_delta':on-no,'vanilla_delta':on-vp}
        report.append(row)
        lines.append(f'|{dataset}|{vp:.3f}|{no:.3f}|{off:.3f}|{on:.3f}|{on-off:+.3f}|{on-no:+.3f}|{on-vp:+.3f}|')
    lines += ['', '|Scene|Rejected / candidates|Screening seconds|Mapper OFF / ON / no-dense seconds|Dense renders OFF / ON|',
              '|---|---:|---:|---:|---:|']
    for dataset,a in table.items():
        b=a['on']['blur_summary'];counts=[a[k]['audit']['role_renders'].get('dense',0) for k in ('off','on')]
        times=[a[k]['mapping_seconds'] for k in ('off','on','no_dense')]
        lines.append(f"|{dataset}|{b['rejected_images']} / {b['candidate_images']}|{b['seconds']:.3f}|"+
                     ' / '.join(f'{t:.2f}' for t in times)+'|'+' / '.join(map(str,counts))+'|')
    lines += ['', '|Scene|Rejected UIDs used by OFF|Their dense renders in OFF|',
              '|---|---:|---:|']
    for dataset,a in table.items():
        on=common.read(Path(a['on']['output'])/'render_result.json')
        off=common.read(Path(a['off']['output'])/'render_result.json')
        rejected={d['uid'] for d in on['dense_blur_filter']['decisions'] if not d['accepted']}
        uses=[u for g in off['training']['generations'] for s in g['services']
              for u,r in zip(s['uids'],s['roles']) if r=='dense' and u in rejected]
        lines.append(f'|{dataset}|{len(set(uses))}|{len(uses)}|')
    lines += ['', '## Interpretation limits', '',
              '- Filter thresholds fixed before runs, shared across scenes; no per-scene tuning.',
              '- Dense OFF filter and ON filter both use 3:3:6. No-dense uses 3:9:0: saved dense work is allocated to full-KF ERVS.',
              '- Equal training renders and input-prefix budgets, poses/events, held-out cohort, zero-tail; rejected frames never used in dense service or pose preparation.',
              '- Relative sharpness proxy, not a guaranteed motion-blur detector. Texture changes, noise, and uniformly blurred intervals remain limitations.',
              '- Single seed, three development scenes; two evaluations of each saved map test evaluator reproducibility, not training variance.',
              '- Frozen causal tracker replay, not measured concurrent-tracking/live performance.']
    if legacy:
        lines += ['', '## Conservative first gate (0.5 energy / 0.75 frequency)', '',
                  '|Scene|PSNR|Rejected candidates|','|---|---:|---:|']
        for r in legacy:
            if r['case']=='on':
                lines.append(f"|{r['dataset']}|{r['psnr']:.3f}|{r['blur_summary']['rejected_images']}|")
        lines += ['', 'The first gate rejected no frames in Aria/UTMM. Their tiny PSNR changes are numerical training variation, not a filtering effect.',
                  'The sensitivity gate (0.8 / 0.9) was predeclared after inspecting Aria training RGB scores and images; it is shared across all scenes. No scene-specific thresholds were selected.']
    common.write(args.root/'verified_comparison.json',{'scenes':report,
        'mean_filter_delta':statistics.mean(r['filter_delta'] for r in report),
        'mean_dense_delta':statistics.mean(r['dense_delta'] for r in report)})
    (args.root/'SUMMARY.md').write_text('\n'.join(lines)+'\n')
    print('\n'.join(lines))

if __name__=='__main__':main()
