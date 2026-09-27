# Densify/prune OFF — 누적 ERVS40 결과

2026-09-25 · RTX5090 · seed0 · batch1 · 동일40 renders/KF causal fixed-work

|장면|공식 vanilla|누적 기존 ON|누적 OFF|OFF−ON|OFF−vanilla|
|---|---:|---:|---:|---:|---:|
|aria|20.751|24.605|25.022|+0.417|+4.270|
|rpng|22.461|24.666|24.784|+0.117|+2.323|
|utmm|18.825|21.329|21.701|+0.371|+2.876|

PSNR 단위 dB. 장면별 변화의 단순 평균 +0.302 dB.

|장면|최종 Gaussian ON→OFF|mapper 초 ON→OFF|동일 render / Adam step|
|---|---:|---:|---:|
|aria|131,388→192,623|50.02→50.68|4760 / 3901|
|rpng|273,917→357,071|123.41→130.16|9080 / 7259|
|utmm|76,657→141,545|53.71→51.53|3600 / 2950|

## 검증과 해석 범위

- clone/split/densify/prune/stats 금지 guard 및 birth 유지 확인. 초기화/전체 지도 reset 내부의 제거만 별도 허용. 모든 off run의 금지 operator 호출0회, topology event0회.
- observation topology gate와 단계별 model scheduler도 OFF. 새 관측에서 Gaussian을 생성하는 경로와 opacity reset 정책은 유지.
- 누적 ERVS, native/추가KF/dense 학습량, Adam 수, 입력 prefix render 수, causal 이벤트, trajectory와 held-out cohort를 대조군과 검증.
- 대조군은 직전 검증된 cumulative40 결과를 재사용. 당시에도 frontier→balanced 전환은 없었으므로 이번 비교의 실제 operator 차이는 densify/prune/stats 제거.
- 학습3회(seed0 각1회), 저장 지도 평가2회씩 일치. 학습 반복 재현성·다중 seed 검증은 아니다.
- 실제 tracking을 동시 실행하지 않았다. 시간은 단일 run의 mapper 전체 시간이며 실시간 성공이나 정밀 kernel benchmark를 뜻하지 않는다.
- held-out RGB PSNR 결과이며 floater/geometry 개선은 별도 region GT 검증 전에는 주장하지 않는다.
- gpu40_v1은 정상 초기 reset을 guard가 잘못 차단하여 optimizer0회에서 중단. v2는 reset 예외만 보완; 실패 artifact는 보존.

## 산출물

- Raw: `/home/intern/gs_floaterLab/results/campaigns/gain_attribution/no_densify_prune/gpu40_v2`
- `verified_summary.json`, `comparison.csv`, scene별 `independent_audit.json`, `render_result.json`, `evaluation_consistency.json`.
- 실험 계약: `context/experiments/campaigns/06_gain_attribution/no_densify_prune/README.md`.
