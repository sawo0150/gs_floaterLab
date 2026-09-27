#!/usr/bin/env python3
"""Summarize the completed predeclared search; emit a measured opt-in preset."""
import argparse
import hashlib
import json
from pathlib import Path
from statistics import mean
ROOT=Path('/home/intern/gs_floaterLab')
BACKEND=Path('/home/intern/VIGS-SLAM-online-worker-integration')
DOC=ROOT/'context/experiments/campaigns/06_gain_attribution/growth_entropy_blur'
SCENES=('aria','rpng','utmm')

def read(p):return json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args();out=args.output.resolve()
    rows=read(out/'summary.json');selection=read(out/'final_selection.json');winner=selection['selected']
    assert len(rows)==21 and all(r['valid_execution'] and r['audit_pass'] and not r['error'] and not r['source_changed'] for r in rows)
    assert all(hashlib.sha256(Path(path).read_bytes()).hexdigest()==v['sha256'] for path,v in read(out/'source_lock.json').items())
    groups={}
    for r in rows:groups.setdefault(r['case'],{})[r['dataset']]=r
    assert all(set(g)==set(SCENES) for g in groups.values())
    baseline=groups['immediate_t1_blur'];chosen=groups[winner];cfg=chosen['aria']['config']
    assert all(r['config']==cfg for r in chosen.values())
    original_rows=read(ROOT/'results/campaigns/gain_attribution/kf_rgb_control/gpu40_v1/summary.json')
    original={r['dataset']:r for r in original_rows if r['case']=='dense_rgb'}
    details={};matrix=[]
    for case,g in groups.items():
        line={'case':case,'config':g['aria']['config'],'psnr':{d:g[d]['psnr'] for d in SCENES},
              'mapping_seconds':{d:g[d]['mapping_seconds'] for d in SCENES},
              'mean_psnr':mean(g[d]['psnr'] for d in SCENES),
              'mean_mapping_seconds':mean(g[d]['mapping_seconds'] for d in SCENES),
              'worst_scene_delta_vs_blur_baseline':min(g[d]['psnr']-baseline[d]['psnr'] for d in SCENES)}
        matrix.append(line);details[case]={}
        for d,r in g.items():
            x=read(Path(r['output'])/'render_result.json');pol=x['training']['generations'][-1]['policy']
            roles=r['audit']['role_renders'];metric=read(Path(r['output'])/'psnr/strict_fixed_manifest/final_result.json')
            details[case][d]={'renders':x['render_counts']['backward'],'adam_steps':x['main_optimizer_steps'],
                'gaussians':x['gaussians'],'dense_fraction':roles.get('dense',0)/x['render_counts']['backward'],
                'roles':roles,'offered':len(pol['offered_dense']),'admitted':len(pol['admitted_dense']),
                'prepared':len(set(x['deferred_audit']['prepared_uids'])),'sampler_pool_tau':pol['sampler_pool_tau'],
                'pose_seconds':x['visual_pose_audit']['wall_seconds'],'blur_rejected':x['dense_blur_filter'].get('rejected_images',0),
                'heldout_count':sum(bool(v['predeclared_fixed_manifest_split']) for v in metric['per_view'])}
    for d in SCENES:
        for key in ('renders','adam_steps','gaussians'):
            assert len({details[case][d][key] for case in groups})==1,(d,key)
    comparisons={}
    for d in SCENES:
        comparisons[d]={'original_psnr':original[d]['psnr'],'original_seconds':original[d]['mapping_seconds'],
            'blur_baseline_psnr':baseline[d]['psnr'],'blur_baseline_seconds':baseline[d]['mapping_seconds'],
            'selected_psnr':chosen[d]['psnr'],'selected_seconds':chosen[d]['mapping_seconds'],
            'delta_vs_original':chosen[d]['psnr']-original[d]['psnr'],
            'delta_vs_blur_baseline':chosen[d]['psnr']-baseline[d]['psnr'],
            'time_reduction_vs_original':1-chosen[d]['mapping_seconds']/original[d]['mapping_seconds']}
    preset=read(BACKEND/'configs/online_mapping_unified.json')
    preset.update(membership='immediate' if cfg['kappa'] is None else 'growth',kappa=cfg['kappa'] or 64,
        tau=cfg['tau'],growth_budget_scope='dense_only',auxiliary_mode='dense_rgb',
        dense_blur_filter={'energy_ratio':.8,'frequency_ratio':.9} if cfg['blur'] else False)
    for d,r in chosen.items():
        x=read(Path(r['output'])/'render_result.json')
        for g in x['training']['generations']:
            pol=g['policy']
            for key in ('membership','kappa','tau','growth_budget_scope','auxiliary_mode','entropy_weight_policy','selection_count_scope','batch_quotas'):
                assert pol[key]==preset[key],(d,key)
        assert x['dense_blur_filter']['enabled']==bool(preset['dense_blur_filter'])
        assert x['optimizer_batch_size']==preset['optimizer_batch_size']==1
        assert x['kf_render_budget']['renders_per_kf']==preset['renders_per_kf']==40
        assert x['unified_scale_projection']['enabled']==preset['scale_projection']
    target=BACKEND/'configs/online_mapping_unified_tuned.json';write(target,preset);write(out/'recommended_config.json',preset)
    write(out/'config_validation.json',{'pass':True,'selected':winner,'target':str(target),'compared_against_all_three_actual_runtime_reports':True,'baseline_presets_unchanged':True})
    mean_delta=mean(v['delta_vs_original'] for v in comparisons.values())
    time_reduction=1-sum(r['mapping_seconds'] for r in chosen.values())/sum(r['mapping_seconds'] for r in original.values())
    write(out/'comparison.json',{'selected':winner,'config':preset,'all_cases':matrix,'scene_details':details,
        'comparisons':comparisons,'mean_psnr_gain_vs_original':mean_delta,'aggregate_time_reduction_vs_original':time_reduction,
        'valid_gpu_runs':21,'preserved_pretraining_failures':1,'cpu_tests':30,'source_lock_pass':True})
    s=f'''# κ / τ / motion-blur 탐색 결과 (2026-09-26)

이번 탐색의 공통 권장 설정은 **{winner}**다. κ={cfg['kappa']}, tau={cfg['tau']}, blur={'ON' if cfg['blur'] else 'OFF'}. 기존 immediate/tau1/blurOFF 대비 세 장면 평균 held-out PSNR {mean_delta:+.4f}dB, 세 mapping 시간 합계 {100*time_reduction:.1f}% 감소다. 실제 동시 tracking/live 기준이 아니라 같은40 renders/KF 조건이다.

권장값은 [별도 실행 preset]({target})과 [결과 내 복사본]({out}/recommended_config.json)에 저장하고 세 장면의 실제 runtime report와 대조했다. 기존 baseline preset은 유지했다. VIGS의 `online_mapping` options에 이 JSON 내용을 전달하는 방식이다.

## 기존 코드 설정과 비교

기존은 κ 비활성(immediate), tau1, blurOFF이며 바로 앞 KF RGB-only 대조군에서 새로 실행한 dense baseline이다. 탐색 중의 기준은 별도로 fresh immediate/tau1/blurON을 사용했다. 아래는 사용자가 원래 사용하던 blurOFF baseline과의 비교다.

| 장면 | 기존 PSNR | 선택 PSNR | 변화(dB) | 기존 mapping(s) | 선택 mapping(s) | 시간 감소 |
|---|---:|---:|---:|---:|---:|---:|
'''
    for d,v in comparisons.items():
        s+=f"| {d} | {v['original_psnr']:.4f} | {v['selected_psnr']:.4f} | {v['delta_vs_original']:+.4f} | {v['original_seconds']:.2f} | {v['selected_seconds']:.2f} | {100*v['time_reduction_vs_original']:.1f}% |\n"
    s+='''
## 전체 탐색 결과

장면별 하락이 fresh blur baseline 대비0.05dB를 넘으면 공통 추천 후보에서 제외했다. 허용 후보 중 최고 평균PSNR과0.02dB 이내이면 가장 빠른 설정을 선택했다. 이 값은 공학적 선택 기준이며 신뢰구간이 아니다.

| 조건 | Aria | RPNG | UTMM | 평균PSNR | 평균 mapping(s) | 품질 guard |
|---|---:|---:|---:|---:|---:|---|
'''
    for z in matrix:
        s+=f"| {z['case']} | {z['psnr']['aria']:.4f} | {z['psnr']['rpng']:.4f} | {z['psnr']['utmm']:.4f} | {z['mean_psnr']:.4f} | {z['mean_mapping_seconds']:.2f} | {'통과' if z['worst_scene_delta_vs_blur_baseline']>=-.05 else '제외'} |\n"
    s+='''
## 무엇을 알게 됐는가

- κ4/8/16의 효과는 단조롭지 않았다. κ8은 Aria에서 유리했으나 RPNG/UTMM은 하락했다. κ16/tau1은 기준 대비 평균PSNR을 유지·개선하면서 약25%의 mapping 시간을 줄였다. 세 장면 공통값으로 비교했고 장면별 κ는 만들지 않았다.
- tau0.25는 κ16에서 세 장면 모두 악화했다. 특히 Aria는 tau1의25.8319→23.5295dB였다. 해당 두 실행의 admissions, LR positions, render/Adam 수, Gaussian 수가 같음을 별도 확인했다. 더 강하게 선택 횟수를 균등화하는 것이 더 좋은 map을 보장하지 않았다.
- tau4는 κ16에서 tau1보다 세 장면 모두 개선됐다(Aria+0.0673/RPNG+0.0719/UTMM+0.1638dB). KF와 dense 양쪽의 entropy coefficient를 함께 바꾼 비교이므로 어느 pool에서 온 효과인지는 분리하지 않았다.
- κ 제한으로 실제 준비하는 dense pose/image 수가 줄었다. Dense에 쓰는 렌더링 몫은 약50%를 유지한다. Admission 감소와 dense 학습 비중 감소를 혼동하면 안 된다. 큰 시간 이득을 blur 필터 자체의 효과로 돌리지 않는다.

## 최종 blur ON/OFF

같은 κ16/tau4의 비교다. 기존 energy0.8/frequency0.9 gate를 그대로 사용했고 임계값을 장면별로 튜닝하지 않았다.

| 장면 | blurON PSNR | blurOFF PSNR | OFF−ON(dB) | ON mapping(s) | OFF mapping(s) |
|---|---:|---:|---:|---:|---:|
'''
    on=groups['k16_t4_blur'];off=groups['k16_t4_no_blur']
    for d in SCENES:
        s+=f"| {d} | {on[d]['psnr']:.4f} | {off[d]['psnr']:.4f} | {off[d]['psnr']-on[d]['psnr']:+.4f} | {on[d]['mapping_seconds']:.2f} | {off[d]['mapping_seconds']:.2f} |\n"
    s+='''
## 실제 admission / sampling

κ는 현재 generation에서 완료한 optimizer step 단위의 dense admission credit이다. KF는 제한하지 않는다. 영상별Adam이라 이 실험에서는 step과 training render 수가 같다. tau는 코드의 기본 계수이며 각 pool N으로 나눠서 entropy 가중치로 사용한다. Count는 window 사용까지 포함한 누적 사용 횟수다. 예산40 renders/KF와3:3:6 비율은 유지했다.

| 장면 | 최종 offered/admitted dense | 실제 준비 distinct dense | dense 렌더링 비율 | KF/dense 실제 entropy weight | renders=Adam |
|---|---|---:|---:|---|---:|
'''
    for d,z in details[winner].items():
        w=z['sampler_pool_tau'];s+=f"| {d} | {z['offered']}/{z['admitted']} | {z['prepared']} | {100*z['dense_fraction']:.2f}% | {w['keyframe']:.6f} / {w['dense']:.6f} | {z['renders']} |\n"
    s+='''
## 検証 / 범위

- 유효GPU21조건과 각 저장 지도 평가2회 PASS. CPU30 tests 및 선택규칙검사 PASS. 모든 조건에서 scene별 total/prefix renders, Adam 수, map GS 수, 평가 cohort와 tracker poses가 동일하다. Future/held-out training0, zero-tail, actual loss route/count, blur rejection, admission credit, source hash를 audit했다.
- v1은 baseline3개 완료 뒤 첫growth run이 runtime의 full-pool-only guard 때문에 학습 전 실패했다. 실패 로그를 보존하고 guard를 paired schedule에만 제한했다. Runtime growth 배선을 회귀 테스트했다. v2는 세 baseline을 재audit/재사용했고 나머지18개를 실행했다. baseline 재사용 시 source 차이와 backend가 정확히 guard 한 줄만 달라졌다는 검사도 보존했다.
- 세 개발 장면 seed0의 coarse staged search다. 모든 κ×tau 조합을 탐색한 global optimum이나 독립 test 일반화는 아니다. 지도 두 번 평가도 독립 학습 반복은 아니다. τ4보다 큰 값 또는 κ16보다 큰 값의 최적성은 확인하지 않았다.
- Frozen causal tracker의 실제 mapper worker를 사용했으며 tracking 동시 실행/strict1.5×wall-clock/live 성능을 입증하지 않는다. Geometry/floater 지표를 평가하지 않았으므로 photometric 결과를 geometry 개선으로 해석하지 않는다.

## 연결

- [사전 계획 / 실행별 ledger](README.md)
- [구현과 정책 단위](IMPLEMENTATION.md)
- [앞선 KF RGB-only 대조군](../kf_rgb_control/SUMMARY.md): loss recipe 교체 평균+0.2892dB, 추가 dense 경로+0.3303dB로 양쪽 효과 확인.
'''
    s+=f"- [전체 수치]({out}/comparison.json)\n- [선택 기준 결과]({out}/final_selection.json)\n- [실행 코드]({ROOT}/benchmarks/online_gs/campaigns/gain_attribution/run_growth_entropy_blur_panel.py)\n"
    (DOC/'SUMMARY.md').write_text(s.replace('## 検証 / 범위','## 검증 / 범위'))
    with (DOC/'README.md').open('a') as f:f.write('\n## 완료\n\n[결과 요약](SUMMARY.md) / [구현](IMPLEMENTATION.md)\n')
    message=(f'**2026-09-26 κ/τ/blur 탐색 완료:** 공통선택 {winner}, 기존immediate/tau1/blurOFF 대비 평균held-out PSNR{mean_delta:+.4f}dB·합산mapper시간{100*time_reduction:.1f}%감소. '
        +' / '.join(f"{d}{v['original_psnr']:.4f}→{v['selected_psnr']:.4f}dB,{v['original_seconds']:.2f}→{v['selected_seconds']:.2f}s" for d,v in comparisons.items())
        +'. dense-only κ growth와 실제 pool별tau 보고 연결,40renders/KF·3:3:6·영상별Adam·누적ERVS·scaleON·densify/pruneOFF 유지. 유효21run/CPU30/저장지도평가2회/causal-prefix-cohort-source audit PASS. 초기runtime guard 학습전실패1건 보존·수정, baseline3개 명시재사용. 별도online_mapping_unified_tuned.json 저장, 기존baseline preset유지. 단일seed3개개발scene/frozen tracker/coarse search이며 live·geometry검증 아님.')
    link='campaigns/06_gain_attribution/growth_entropy_blur/SUMMARY.md'
    for name,heading,target_link in [('context/STATUS.md','## 최근 흐름 (최신순)\n','experiments/'+link),('context/experiments/INDEX.md','# Experiment Index\n',link)]:
        path=ROOT/name;text=path.read_text();assert heading in text
        path.write_text(text.replace(heading,heading+'\n- '+message+' → [결과]('+target_link+')\n',1))
    campaign=DOC.parent/'README.md'
    with campaign.open('a') as f:f.write('\n## 2026-09-26 추가 검증\n\n- [KF RGB-only 대조군](kf_rgb_control/SUMMARY.md)\n- [κ / τ / blur 공통 설정 탐색](growth_entropy_blur/SUMMARY.md)\n')
    print(json.dumps({'selected':winner,'config':str(target),'comparisons':comparisons,'mean_delta':mean_delta,'aggregate_time_reduction':time_reduction},indent=2))

if __name__=='__main__':main()
