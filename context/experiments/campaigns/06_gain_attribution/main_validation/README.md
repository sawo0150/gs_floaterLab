# Merged main fixed40 validation — 2026-09-29

사용자 요청: 병합 main에서 기존 Aria1253 / RPNG table_06 / UTMM square-1과 Aria1253_rot를 실행해 vanilla 대비 이득 확인.

- Main commit 5fa8c76e, 채택 recipe 그대로: 40 renders/KF, 336, 누적 ERVS κ16/τ₀4, init0.8 분모, 보호 prune0.1/300, 최근10birth, 영상별 Adam. 튜닝 없음.
- 기존 세 장면도 ours와 official vanilla를 새로 실행한다. Rot는 원본 입력·고정 held-out·causal tracker archive를 먼저 확인/준비한다. 총 네 장면의 한 쌍씩이 목표이며 추가 조건 탐색 없음.
- 같은 tracker archive/pose/depth, held-out cohort, arrival별 render 수를 맞춘다. Vanilla의 원래 optimizer grouping/topology는 유지한다. Fixed-work replay이며 실시간 동시 tracking 검증은 아니다.
- 평가 PSNR과 최종 GS, mapper 시간, render/Adam, zero-tail, source 및 protected pruning audit를 기록한다. 기존 seed0 개발 결과와 main 회귀 여부도 확인한다.
- 새 scene 등록 준비와 과거 데이터 수치가 이번 main 실행 결과에 섞이지 않도록 별도 경로에 저장한다.

## 실행 기록

**2026-09-29 main validation aria/ours:** PSNR=25.77617167698518, audit=True, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/main_validation/gpu40_v1/aria/ours.

**2026-09-29 main validation aria/vanilla:** PSNR=20.743402051561663, audit=True, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/main_validation/gpu40_v1/aria/vanilla.

**2026-09-29 main validation rpng/ours:** PSNR=25.223718175802144, audit=True, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/main_validation/gpu40_v1/rpng/ours.

**Rot 준비:** 원본 `0416_301-1253-2_rot/0416_301-1253-2.vrs`에서 projectaria_tools 2.3.0으로 전체 1521 RGB와 75917 imu-right 샘플을 추출했다. skip-head=0, MPS 사용 없음. 고정 VRS Tcb는 기존 Aria adapter와 일치한다. idx%5 또는 마지막 프레임 held-out=305. 과거1498프레임 결과는 비교값으로 재사용하지 않는다. Source/VRS/manifest 해시는 `results/campaigns/gain_attribution/main_validation/rot_inputs/input_provenance.json`.

**2026-09-29 main validation rpng/vanilla:** PSNR=22.47345105420362, audit=True, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/main_validation/gpu40_v1/rpng/vanilla.

**2026-09-29 main validation utmm/ours:** PSNR=22.285248650444878, audit=True, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/main_validation/gpu40_v1/utmm/ours.

**2026-09-29 main validation utmm/vanilla:** PSNR=18.88187265984806, audit=True, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/main_validation/gpu40_v1/utmm/vanilla.

**Rot capture/입력 검증 완료:** official tracker commit22ffe24, RGB1521·KF176·event183·mapper reset1. Archive validator valid=True, violations=[], capture 중 Gaussian update0. 평가용 post-EOS pose fill은 mapping supervision에 사용하지 않는다. 이후 같은 archive를 main/vanilla에 제공한다.

**2026-09-29 main validation aria_rot/ours:** PSNR=25.018266165061075, audit=True, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/main_validation/rot_gpu40_v1/ours.

**2026-09-29 main validation aria_rot/vanilla:** PSNR=21.801056358462475, audit=True, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/main_validation/rot_gpu40_v1/vanilla.

## 완료

Ours4+vanilla4 전부PASS, 네 장면 모두이득. [최종 결과](SUMMARY.md).
