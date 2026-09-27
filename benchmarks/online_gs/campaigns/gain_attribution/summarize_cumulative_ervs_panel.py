#!/usr/bin/env python3
"""Summarize exact40 cumulative/recent quality without making a live claim."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import statistics


def read(path): return json.loads(path.read_text())


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--panel',type=Path,required=True)
    args=parser.parse_args();panel=args.panel.resolve()
    root=Path(__file__).resolve().parents[4]
    old=root/'results/campaigns/gain_attribution/render_budget40_feasibility/v1/fixed'
    inputs=read(panel/'summary.json')
    expected={(d,s) for d in ('aria','rpng','utmm') for s in ('all_rgb','recent_photometric')}
    assert len(inputs)==6 and {(r['dataset'],r['scope']) for r in inputs}==expected
    assert all(r['valid_execution'] and r['audit_pass'] and r['evaluation']['pass']
               and not r['source_changed'] and r['error'] is None for r in inputs)
    for entry in read(panel/'source_lock.json').values():
        assert hashlib.sha256(Path(entry['copy']).read_bytes()).hexdigest()==entry['sha256']
    by={(r['dataset'],r['scope']):r for r in inputs}
    previous={r['dataset']:r for r in read(old/'summary.json') if r['arm']=='paired'}
    vanilla={r['dataset']:r for r in read(old/'summary.json') if r['arm']=='vanilla'}
    rows=[]
    for dataset in ('aria','rpng','utmm'):
        c=by[dataset,'all_rgb'];r=by[dataset,'recent_photometric'];v=vanilla[dataset]
        assert c['audit']['training_renders']==r['audit']['training_renders']
        traces=[];details=[]
        for item in (c,r):
            state=read(Path(item['output'])/'render_result.json')
            services=[s for g in state['training']['generations'] for s in g['services']]
            traces.append([(s['role'],s['uids'][0]) for s in services if s['source']=='photometric'])
            details.append({'gaussians':state['gaussians'],
                'native_renders':sum(len(s['uids']) for s in services if s['source']=='native'),
                'extra_kf':item['audit']['extra_kf'],'extra_dense':item['audit']['extra_dense'],
                'optimizer_steps':item['audit']['optimizer_steps']})
        assert len(traces[0])==len(traces[1])
        assert details[0]['native_renders']==details[1]['native_renders']
        assert details[0]['optimizer_steps']==details[1]['optimizer_steps']
        rows.append({'dataset':dataset,'vanilla_psnr':v['psnr'],'old_recent_psnr':previous[dataset]['psnr'],
            'recent_psnr':r['psnr'],'cumulative_psnr':c['psnr'],
            'cumulative_minus_vanilla':c['psnr']-v['psnr'],'cumulative_minus_recent':c['psnr']-r['psnr'],
            'recent_rerun_minus_old':r['psnr']-previous[dataset]['psnr'],
            'renders':c['audit']['training_renders'],'cumulative_seconds':c['mapping_seconds'],
            'recent_seconds':r['mapping_seconds'],
            'different_additional_selections':sum(a!=b for a,b in zip(*traces)),
            'additional_selections':len(traces[0]),'cumulative':details[0],'recent':details[1]})
    result={'verified':True,'rows':rows,
        'mean_cumulative_minus_vanilla':statistics.mean(r['cumulative_minus_vanilla'] for r in rows),
        'mean_cumulative_minus_recent':statistics.mean(r['cumulative_minus_recent'] for r in rows),
        'same_work_poses_events_cohort':True,'live_claim':False,'training_seeds':[0]}
    (panel/'verified_summary.json').write_text(json.dumps(result,indent=2)+'\n')
    fields=[k for k in rows[0] if k not in ('cumulative','recent')]
    with (panel/'comparison.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        writer.writerows({k:r[k] for k in fields} for r in rows)
    lines=['# 누적 ERVS — 40 renders/KF 검증 결과','',
        '2026-09-25 · RTX5090 · seed0 · batch1 · 실제 tracker 동시 실행 없는 causal fixed-work 비교','',
        '|장면|공식 vanilla|최근 count 재실행|누적 count|누적−vanilla|누적−최근|',
        '|---|---:|---:|---:|---:|---:|']
    for r in rows:
        lines.append(f"|{r['dataset']}|{r['vanilla_psnr']:.3f}|{r['recent_psnr']:.3f}|{r['cumulative_psnr']:.3f}|{r['cumulative_minus_vanilla']:+.3f}|{r['cumulative_minus_recent']:+.3f}|")
    lines+=['',f"PSNR 단위 dB. 장면별 차이의 단순 평균: 누적−vanilla {result['mean_cumulative_minus_vanilla']:+.3f}, 누적−최근 {result['mean_cumulative_minus_recent']:+.3f} dB.",
        '', '## 실제 작업량과 소요시간','',
        '|장면|동일 training renders|동일 Adam steps|native / 추가KF / dense (누적)|매핑 초 최근→누적|추가 선택 UID 변경|',
        '|---|---:|---:|---:|---:|---:|']
    for r in rows:
        c=r['cumulative'];lines.append(f"|{r['dataset']}|{r['renders']}|{c['optimizer_steps']}|{c['native_renders']} / {c['extra_kf']} / {c['extra_dense']}|{r['recent_seconds']:.2f}→{r['cumulative_seconds']:.2f}|{r['different_additional_selections']}/{r['additional_selections']}|")
    lines+=['','Mapper 시간에는 pose 준비 등을 포함하지만 실제 tracking 비용은 포함하지 않는다. 비슷하거나 더 좋은 PSNR이 나와도 real-time 성공으로 판정하지 않는다.',
        '', '## 통제와 해석','',
        '- 양쪽 scope를 같은 현재 코드·동일 seed·40회 예산으로 실행. 묶음 업데이트는 적용하지 않았다.',
        '- 누적 all_rgb는 native window+추가 학습을 모두 누적한다. 최근 대조군은 역할별 최근 추가 학습 횟수를 사용한다. 따라서 count 기억 길이와 native 반영 여부가 함께 바뀐 비교다.',
        '- 입력 prefix별 render 수, causal event, 공유 pose trajectory, 평가 cohort를 각 run 및 기존 vanilla와 대조했다.',
        '- 모든 generation의 누적 count와 실제 ERVS 선택 count를 완료 service ledger에서 독립 재집계했다. 총 render와 backward 및 zero-tail도 확인했다.',
        '- 총6회 학습, 각 저장 지도2회 동일 평가 PASS. 평가 반복은 학습 재현성 검증이 아니며 seed0 결과만 보고한다.',
        '- Vanilla는 원래 검증된 official40 결과를 재사용했다. 새로운 sampler 결과와 입력/평가/작업량 계약이 동일한지 재확인했다.',
        '- 과거 최근 count 결과는 변경하지 않았다. 이번 최근 방식 재실행과의 차이는 아래에 공개한다.',
        '', '|장면|이전 최근 PSNR|현재 최근 PSNR|차이|','|---|---:|---:|---:|']
    for r in rows: lines.append(f"|{r['dataset']}|{r['old_recent_psnr']:.6f}|{r['recent_psnr']:.6f}|{r['recent_rerun_minus_old']:+.6f}|")
    lines+=['','## 산출물','',f'- Raw/audit: `{panel}`',
        '- `verified_summary.json`: 최종 검증 및 차이.', '- `comparison.csv`: 숫자 표.',
        '- 각 scene/scope의 `independent_audit.json`, `render_result.json`, `evaluation_consistency.json`.',
        '- [누적 변경 계약](README.md).']
    text='\n'.join(lines)+'\n'
    (root/'context/experiments/campaigns/06_gain_attribution/cumulative_ervs/SUMMARY.md').write_text(text)
    (panel/'SUMMARY.md').write_text(text)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
