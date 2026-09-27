#!/usr/bin/env python3
"""Summarize operator ablation, preserving the archived cumulative control."""
import argparse
import csv
import json
from pathlib import Path
import statistics

import run_cumulative_ervs_panel as common


def main():
    p=argparse.ArgumentParser();p.add_argument('--panel',type=Path,required=True)
    panel=p.parse_args().panel.resolve();root=common.trial.BASE.WORKSPACE
    inputs=common.read(panel/'summary.json')
    assert len(inputs)==3 and {r['dataset'] for r in inputs}==set(common.SCENES)
    assert all(r['valid_execution'] and r['audit_pass'] and r['evaluation']['pass']
               and not r['error'] and not r['source_changed'] for r in inputs)
    for v in common.read(panel/'source_lock.json').values():
        assert common.sha(Path(v['copy']))==v['sha256']
    control=root/'results/campaigns/gain_attribution/cumulative_ervs/gpu40_v1'
    on_metrics={r['dataset']:r['psnr'] for r in common.read(control/'summary.json')
                if r['scope']=='all_rgb'}
    vanilla={r['dataset']:r for r in common.read(common.OLD/'summary.json') if r['arm']=='vanilla'}
    rows=[]
    for r in inputs:
        ds=r['dataset'];on=common.read(control/ds/'all_rgb/render_result.json')
        off=common.read(Path(r['output'])/'render_result.json')
        on_psnr=on_metrics[ds]
        rows.append({'dataset':ds,'vanilla_psnr':vanilla[ds]['psnr'],
            'on_psnr':on_psnr,'off_psnr':r['psnr'],'off_minus_on':r['psnr']-on_psnr,
            'off_minus_vanilla':r['psnr']-vanilla[ds]['psnr'],
            'on_gaussians':on['gaussians'],'off_gaussians':off['gaussians'],
            'on_seconds':on['mapping_seconds'],'off_seconds':off['mapping_seconds'],
            'renders':r['audit']['training_renders'],'adam_steps':r['audit']['optimizer_steps'],
            'birth_calls':off['densify_prune_ablation']['birth_calls'],
            'reset_prunes':len(off['densify_prune_ablation']['tracker_reset_prunes'])})
    result={'verified':True,'rows':rows,'actual_live':False,'seed':0,
            'mean_off_minus_on':statistics.mean(r['off_minus_on'] for r in rows)}
    common.write(panel/'verified_summary.json',result)
    with (panel/'comparison.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    lines=['# Densify/prune OFF — 누적 ERVS40 결과','',
           '2026-09-25 · RTX5090 · seed0 · batch1 · 동일40 renders/KF causal fixed-work','',
           '|장면|공식 vanilla|누적 기존 ON|누적 OFF|OFF−ON|OFF−vanilla|',
           '|---|---:|---:|---:|---:|---:|']
    for r in rows:
        lines.append(f"|{r['dataset']}|{r['vanilla_psnr']:.3f}|{r['on_psnr']:.3f}|{r['off_psnr']:.3f}|{r['off_minus_on']:+.3f}|{r['off_minus_vanilla']:+.3f}|")
    lines+=['','PSNR 단위 dB. 장면별 변화의 단순 평균 '+f"{result['mean_off_minus_on']:+.3f} dB.",
            '', '|장면|최종 Gaussian ON→OFF|mapper 초 ON→OFF|동일 render / Adam step|',
            '|---|---:|---:|---:|']
    for r in rows:
        lines.append(f"|{r['dataset']}|{r['on_gaussians']:,}→{r['off_gaussians']:,}|{r['on_seconds']:.2f}→{r['off_seconds']:.2f}|{r['renders']} / {r['adam_steps']}|")
    lines+=['','## 검증과 해석 범위','',
        '- clone/split/densify/prune/stats 금지 guard 및 birth 유지 확인. 초기화/전체 지도 reset 내부의 제거만 별도 허용. 모든 off run의 금지 operator 호출0회, topology event0회.',
        '- observation topology gate와 단계별 model scheduler도 OFF. 새 관측에서 Gaussian을 생성하는 경로와 opacity reset 정책은 유지.',
        '- 누적 ERVS, native/추가KF/dense 학습량, Adam 수, 입력 prefix render 수, causal 이벤트, trajectory와 held-out cohort를 대조군과 검증.',
        '- 대조군은 직전 검증된 cumulative40 결과를 재사용. 당시에도 frontier→balanced 전환은 없었으므로 이번 비교의 실제 operator 차이는 densify/prune/stats 제거.',
        '- 학습3회(seed0 각1회), 저장 지도 평가2회씩 일치. 학습 반복 재현성·다중 seed 검증은 아니다.',
        '- 실제 tracking을 동시 실행하지 않았다. 시간은 단일 run의 mapper 전체 시간이며 실시간 성공이나 정밀 kernel benchmark를 뜻하지 않는다.',
        '- held-out RGB PSNR 결과이며 floater/geometry 개선은 별도 region GT 검증 전에는 주장하지 않는다.',
        '- gpu40_v1은 정상 초기 reset을 guard가 잘못 차단하여 optimizer0회에서 중단. v2는 reset 예외만 보완; 실패 artifact는 보존.',
        '', '## 산출물','', f'- Raw: `{panel}`',
        '- `verified_summary.json`, `comparison.csv`, scene별 `independent_audit.json`, `render_result.json`, `evaluation_consistency.json`.',
        '- 실험 계약: `context/experiments/campaigns/06_gain_attribution/no_densify_prune/README.md`.']
    text='\n'.join(lines)+'\n'
    (panel/'SUMMARY.md').write_text(text)
    (root/'context/experiments/campaigns/06_gain_attribution/no_densify_prune/SUMMARY.md').write_text(text)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
