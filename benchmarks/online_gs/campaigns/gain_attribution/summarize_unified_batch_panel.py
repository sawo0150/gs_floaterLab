#!/usr/bin/env python3
"""Combine complete ratio panels, reporting all arms and equal-render limits."""
import argparse
from pathlib import Path
import statistics

import run_cumulative_ervs_panel as common


def label(case):
    micro='m1' in case;base=case[:3]
    return ':'.join(base)+(' / 영상별 Adam' if micro else ' / 묶음별 Adam')+(' / 크기상한 복원' if case.endswith('p') else '')


def main():
    p=argparse.ArgumentParser();p.add_argument('--panels',nargs='+',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=True)
    root=common.trial.BASE.WORKSPACE
    controls={r['dataset']:r for r in common.read(root/'results/campaigns/gain_attribution/no_densify_prune/gpu40_v2/summary.json')}
    all_rows=[]
    for panel in a.panels:
        rows=common.read(panel/'summary.json')
        assert all(r['valid_execution'] and r['audit_pass'] and r['evaluation']['pass']
                   and not r['error'] and not r['source_changed'] for r in rows)
        for v in common.read(panel/'source_lock.json').values():
            assert common.sha(Path(v['copy']))==v['sha256']
        all_rows+=rows
    cases=sorted({r['case'] for r in all_rows});summary=[]
    for case in cases:
        rows=[r for r in all_rows if r['case']==case]
        assert len(rows)==3 and {r['dataset'] for r in rows}==set(common.SCENES)
        summary.append({'case':case,'mean_psnr':statistics.mean(r['psnr'] for r in rows),
            'mean_delta':statistics.mean(r['psnr']-controls[r['dataset']]['psnr'] for r in rows),
            'mean_time_ratio':statistics.mean(r['mapping_seconds']/controls[r['dataset']]['mapping_seconds'] for r in rows),
            'rows':rows})
    summary.sort(key=lambda r:r['mean_psnr'],reverse=True)
    selected=summary[0]['case']
    validated_recipe='336m1p' if '336m1p' in cases else None
    report={'verified':True,'ranked_cases':summary,'selected_by_mean_psnr':selected,
            'validated_recipe':validated_recipe,
            'selection_dataset':'same three development scenes; no independent final benchmark',
            'actual_live':False,'seed':0}
    common.write(a.output/'verified_summary.json',report)
    lines=['# Unified mapping batch 비교','',
        '2026-09-25 · seed0 · 세 장면 공통40 renders/KF · cumulative ERVS · densify/prune OFF','',
        '|window:KF:dense|Aria PSNR|RPNG PSNR|UTMM PSNR|평균 변화 vs paired OFF|평균 시간비 vs paired OFF|',
        '|---|---:|---:|---:|---:|---:|']
    lines.append('|기존 paired OFF|'+'|'.join(f"{controls[d]['psnr']:.3f}" for d in common.SCENES)+'|—|1.000|')
    for row in summary:
        by={r['dataset']:r for r in row['rows']}
        lines.append('|'+label(row['case'])+'|'+'|'.join(f"{by[d]['psnr']:.3f}" for d in common.SCENES)+f"|{row['mean_delta']:+.3f}|{row['mean_time_ratio']:.3f}|")
    lines+=['',f"세 장면 평균 held-out PSNR로 선택한 개발 설정: **{label(selected)}**. 다른 장면별 비율을 섞어 선택하지 않았다.",
        '최종 구조 검증 대상은 **3:3:6 / 영상별 Adam / 기존 크기상한 복원**이다. 상한 누락 상태의 수치는 원인 분석용으로 구분한다.' if validated_recipe else '크기상한 복원 검증 전의 개발 결과다.',
        '', '|설정|장면|training renders|Adam steps|window/KF/dense 실제 사용|mapper초|Gaussians|',
        '|---|---|---:|---:|---:|---:|---:|']
    for row in summary:
        for r in row['rows']:
            audit=r['audit'];roles=audit['role_renders']
            lines.append(f"|{label(row['case'])}|{r['dataset']}|{audit['training_renders']}|{audit['optimizer_steps']}|"+
                '/'.join(str(roles.get(k,0)) for k in ('window','keyframe','dense'))+
                f"|{r['mapping_seconds']:.2f}|{r['gaussians']:,}|")
    lines+=['','## 구조와 해석','',
        '- arrival당 하나의 mapping envelope. tracker/control 반영 → birth/pose 갱신 → unified sampler → 설정한 optimizer 단위로 학습. native 별도 optimizer 및 추가 학습 packet0개.',
        '- recent window는 uniform without replacement. KF/dense는 각 full available pool에서 cumulative ERVS. window에서 이미 뽑힌 KF는 해당 batch의 global KF 후보에서 제외하되 이후 batch에서는 다시 후보가 된다.',
        '- 실제 성공한 batch의 각 영상에 count+1. window 선택도 KF의 누적 count에 포함. 취소·pose 준비는 count를 올리지 않으며 새 map generation에서만 초기화.',
        '- batch가 작아지거나 pool이 부족할 때는 비율이 정확히 일치하지 않는다. 부족분 재배분·잔여 예산4회 및 초기 영상 부족을 실제 사용량에 포함했다.',
        '- KF RGBD+normal과 dense RGB loss 유지. 묶음별 Adam은12장의 gradient를 합산하고1회 업데이트; 영상별 Adam은 같은12장을 준비/선택한 뒤 각 영상마다 업데이트한다. 두 설정의 영상 선택 순서 및 각 영상에 적용한 LR clock을 실행 ledger에서 대조했다.',
        '- Gaussian LR은 선택 묶음 시작의 완료 render 수를 기준으로 정하고 묶음 내에서 유지한다. optimizer 단위를 바꿀 때 LR 배수를 추가하지 않았다.',
        '- 동일 render 예산이 동일 Adam 횟수를 뜻하지 않는다. 기존 paired는 native multi-view+추가 single-view; 새 구조는 통합 sampler와 단일 학습 경로다. paired 대비 비교에는 sampler 비율과 optimizer grouping이 함께 바뀌며 ERVS만의 효과는 아니다. 동일 비율의 묶음별/영상별 Adam 비교는 동일 선택 순서·LR로 optimizer grouping 영향을 분리한다.',
        '- 각 run에서 prefix별 render, 입력 events/trajectory/cohort, 누적 count, native step0, 한 arrival packet1개, topology operator0, 마지막 입력 뒤 update0을 검증했다.',
        '- 한 scene/arm당 seed0 학습1회, 저장 지도 평가2회 일치. 이 cohort를 ratio 개발에 사용했으므로 독립 최종 benchmark와 다르다.',
        '- mapper 전체시간은 단일 실행이며 실제 tracking 동시 실행/실시간 보장/geometry 개선을 뜻하지 않는다.',
        '- 최초 통합 경로는 native map() 끝의 scale≤0.1 후처리를 함께 우회했다. 동일 비율의 묶음별/영상별 Adam은 둘 다 이 조건이 같아 grouping 비교가 유효하다. 최종 p arm은 native map 경계의 기존 scale projection을 복원했다. densify/prune를 켠 것이 아니다.',
        '', '## 산출물','']
    lines.extend('- `'+str(panel.resolve())+'`' for panel in a.panels)
    text='\n'.join(lines)+'\n';(a.output/'SUMMARY.md').write_text(text)
    (root/'context/experiments/campaigns/06_gain_attribution/unified_batch/SUMMARY.md').write_text(text)
    print('selected',selected)
    for r in summary:print(r['case'],round(r['mean_psnr'],4),round(r['mean_delta'],4),round(r['mean_time_ratio'],3))


if __name__=='__main__':main()
