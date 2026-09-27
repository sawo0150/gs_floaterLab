# Dense blur screening — same 40 renders/KF

2026-09-26 · seed0 · cumulative ERVS · per-image Adam · scale projection ON · densify/prune OFF

|Scene|Vanilla|No dense (3:9:0)|Dense OFF filter|Dense ON filter|ON−OFF|ON−no dense|ON−vanilla|
|---|---:|---:|---:|---:|---:|---:|---:|
|aria|20.751|24.739|25.596|25.607|+0.011|+0.868|+4.856|
|rpng|22.461|24.799|25.113|25.099|-0.014|+0.300|+2.638|
|utmm|18.825|21.400|22.111|22.104|-0.007|+0.704|+3.279|

|Scene|Rejected / candidates|Screening seconds|Mapper OFF / ON / no-dense seconds|Dense renders OFF / ON|
|---|---:|---:|---:|---:|
|aria|7 / 924|0.735|52.80 / 52.31 / 24.02|2380 / 2380|
|rpng|110 / 1810|1.560|139.33 / 140.08 / 85.11|4569 / 4569|
|utmm|23 / 1133|0.906|55.20 / 55.72 / 30.52|1800 / 1800|

|Scene|Rejected UIDs used by OFF|Their dense renders in OFF|
|---|---:|---:|
|aria|3|4|
|rpng|77|235|
|utmm|16|27|

## Interpretation limits

- Filter thresholds fixed before runs, shared across scenes; no per-scene tuning.
- Dense OFF filter and ON filter both use 3:3:6. No-dense uses 3:9:0: saved dense work is allocated to full-KF ERVS.
- Equal training renders and input-prefix budgets, poses/events, held-out cohort, zero-tail; rejected frames never used in dense service or pose preparation.
- Relative sharpness proxy, not a guaranteed motion-blur detector. Texture changes, noise, and uniformly blurred intervals remain limitations.
- Single seed, three development scenes; two evaluations of each saved map test evaluator reproducibility, not training variance.
- Frozen causal tracker replay, not measured concurrent-tracking/live performance.

## Conservative first gate (0.5 energy / 0.75 frequency)

|Scene|PSNR|Rejected candidates|
|---|---:|---:|
|aria|25.574|0|
|rpng|25.133|2|
|utmm|22.123|0|

The first gate rejected no frames in Aria/UTMM. Their tiny PSNR changes are numerical training variation, not a filtering effect.
The sensitivity gate (0.8 / 0.9) was predeclared after inspecting Aria training RGB scores and images; it is shared across all scenes. No scene-specific thresholds were selected.

## 최종 판단과 사용 설정

- 12 GPU runs(보수적 gate의3arms×3scenes + 민감도 gate3scenes),24 CPU tests PASS. 각 저장지도 평가2회 동일.
- 민감도 gate는 Aria7/RPNG110/UTMM23개의 dense 후보를 제외한다. 제외 UID가 dense pose 준비/학습에 들어가지 않는 것을 검증했다. frontend가 선택한 KF는 별도로 유지한다.
- 필터 ON−OFF는 +0.011/−0.014/−0.007dB(평균−0.003dB)로, 이번 단일seed 조건에서 기존 품질 수준과 dense 사용 이득이 유지됐다. 통계적 동등성이나 PSNR 개선을 입증한 것은 아니다.
- 전체 mapper 시간도52.80→52.31 /139.33→140.08 /55.20→55.72초로, 속도 개선 근거는 없다. 검사 자체는0.74/1.56/0.91초다. dense ON과 no-dense는 pose 준비 비용도 다르므로 이득은 같은 render 예산 기준이다.
- **기존 기본 recipe는 필터 OFF 유지.** opt-in recipe `/home/intern/VIGS-SLAM-online-worker-integration/configs/online_mapping_unified_blur.json`는 검증한0.8/0.9 기준을 포함한다.
- 실제 RGB에서 일부 경계 흐림을 확인했지만 선명도 proxy는 motion blur 정답 판별기가 아니다. 저질감·noise·구간 전체 blur가 한계다.
- 소스 잠금은 보존했다. 실행 후 deferred inventory의 module docstring만 수정했으며 AST 비교로 실행코드 동일을 확인했다.
