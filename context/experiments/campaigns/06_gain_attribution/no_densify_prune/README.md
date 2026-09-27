# Densify/prune 제거 — 누적 ERVS40

2026-09-25 사용자 요청: densify 및 pruning을 아예 끄고 비교한다.

## 실험 계약

- Aria1253 / RPNG table_06 / UTMM square-1, seed0, 동일40 training camera renders/KF.
- 직전 누적 ERVS `all_rgb`를 대조군으로 사용한다. 최근 횟수 방식으로 바꾸지 않는다.
- initialization 및 regular mapping의 densify/prune와 densification stats를 끈다. topology phase gate 및 model scheduler도 끈다. 장면별 cutoff나 freeze API를 사용하지 않는다.
- 관측 RGB/depth 기반 Gaussian birth, 기존 loss·pose 경로·단일영상 Adam·KF/dense 교대·opacity reset 정책을 유지한다. tracker가 요청한 전체 지도 reset은 유지하며 일반 pruning과 분리해서 기록한다.
- operator guard는 clone/split/densify/prune 또는 stats 호출이 발생하면 실패시킨다. `prune_points`는 tracker map reset 내부에서만 허용한다. 새 Gaussian model에도 guard가 적용된다.
- 입력 prefix별 render, native/extraKF/dense 작업량, Adam steps, pose trajectory, held-out cohort, 누적 count를 재검증한다. 각 저장 지도는2회 평가한다. seed 반복은 아니다.
- 고정 연산량 causal replay이며 동시 tracking/live 성능 검증이 아니다. Gaussian 수 증가·시간 증가·PSNR 하락도 그대로 보고한다.
- integration backend에 기본 OFF인 `mapping_disable_densify_prune` 옵션을 추가한다. 실험 runner에서만 켜며 생산 트리 및 기존 기본 recipe는 바꾸지 않는다.

Runner: `benchmarks/online_gs/campaigns/gain_attribution/run_no_densify_prune_panel.py`

대조군: `results/campaigns/gain_attribution/cumulative_ervs/gpu40_v1/`

결과: `results/campaigns/gain_attribution/no_densify_prune/gpu40_v1/`

**2026-09-25 no densify/prune40 / aria:** execution=False, audit=False, held-out PSNR=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/no_densify_prune/gpu40_v1/aria.

**2026-09-25 no densify/prune40 v1 실패 원인/정정:** Aria는 optimizer 0회에서 중단. pruning guard가 tracker 첫 packet의 `GSBackEnd.reset()`을 미허용하여 정상 초기 지도 reset을 차단했다. 품질 실패/결과가 아니라 실행 하네스 실패이며 결과는 보존. `reset` 및 `remove_all_gaussians` 내부만 허용하도록 보완하고 CPU guard에서 직접/nested reset·모델 교체·금지6경로를 확인했다. 학습 중 일반 prune 금지와 operator OFF 설정은 그대로이며 gpu40_v2에서 재실행한다.

**2026-09-25 no densify/prune40 / aria:** execution=True, audit=True, held-out PSNR=25.021636082015874; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/no_densify_prune/gpu40_v2/aria.

**2026-09-25 no densify/prune40 / rpng:** execution=True, audit=True, held-out PSNR=24.783596671164574; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/no_densify_prune/gpu40_v2/rpng.

**2026-09-25 no densify/prune40 / utmm:** execution=True, audit=True, held-out PSNR=21.700596747574984; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/no_densify_prune/gpu40_v2/utmm.

## 최종 결과

**2026-09-25 densify/prune OFF40 최종 완료:** cumulative all_rgb·40 renders/KF·seed0·batch1에서 Aria/RPNG/UTMM held-out PSNR=25.0216/24.7836/21.7006 dB. 직전 cumulative ON 대비 +0.4170/+0.1173/+0.3711 dB(장면 평균 +0.3018), official vanilla 대비 +4.2703/+2.3226/+2.8760 dB. 세 실행 모두 동일 render/Adam/native·extraKF·dense 작업량, causal event/pose/cohort/count 및 저장 지도2회 평가 PASS. densify/prune/stats 금지 호출0회, topology event0회; observation topology gate·phase scheduler OFF, 관측 birth와 초기화/지도 reset 유지. 최종 Gaussian 131388→192623 / 273917→357071 / 76657→141545; mapper초 50.02→50.68 / 123.41→130.16 / 53.71→51.53. fixed-work 단일seed이므로 actual-live·geometry 개선은 미검증. 실험 옵션은 추가했으며 기존 기본 recipe 변경은 없음.

성공 결과: `results/campaigns/gain_attribution/no_densify_prune/gpu40_v2/`. [상세 결과](SUMMARY.md). v1 하네스 실패는 보존했다. CPU 누적count 회귀6tests 및 guard 검증도 PASS(`gpu40_v2/cpu_validation.json`).
