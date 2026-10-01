# Unified RR vs ERVS (2026-09-27)

현재 tuned unified 구조에서 selection만 변경하는 세 장면 비교. 기존 결과를 재사용하지 않고 양쪽 모두 새로 실행한다.

- 공통: κ16 dense-only growth, 40 renders/KF, 3:3:6, 영상별 Adam, scale projection ON, densify/prune/Carve/blur OFF, seed0.
- ERVS: KF/dense 각각 누적 count, τ0=4 및 τ_pool=4/N. Window uniform.
- RR: KF/dense 독립 무작위 순회. 새 영상은 현재 남은 queue 뒤에 무작위 순서로 추가한다. KF window 사용도 현재 KF epoch의 사용으로 인정한다(ERVS all_rgb와 일관). Epoch가 끝나면 전체 현재 pool을 reshuffle한다. 같은 batch 내 중복은 금지하고 다음 epoch에서 중복될 UID는 다음 batch로 미룬다. Commit된 prefix만 RR 진행 상태에 반영하며 취소된 나머지는 소모하지 않는다.
- 세 장면: Aria1253, RPNG table_06, UTMM square-1. Frozen causal tracker, 고정 held-out 평가, zero-tail. 동시 tracking/live 검증은 아님.
- 주지표: 장면별 held-out PSNR 및 ERVS−RR 평균. Mapper 시간도 별도 기록. 단일seed이므로 통계적 우월성은 주장하지 않는다.
- 양 조건 admission ledger, pool membership, 총/도착prefix별 render 및 Adam, 역할 배정/배치 크기/LR schedule, pose, cohort 일치 검증. 기본 preset 변경 없음.
- CPU35 tests 통과 후 GPU6 runs 및 지도별 평가2회 예정. 실행 실패도 아래에 보존한다.

## 실행 기록

**2026-09-27 unified RR/ERVS ervs / aria:** execution=True, audit=True, PSNR=25.884680151029396, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_rr_ervs/gpu40_v1/ervs/aria.

**2026-09-27 unified RR/ERVS ervs / rpng:** execution=True, audit=True, PSNR=25.229798847920186, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_rr_ervs/gpu40_v1/ervs/rpng.

**2026-09-27 unified RR/ERVS ervs / utmm:** execution=True, audit=True, PSNR=22.222941828362735, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_rr_ervs/gpu40_v1/ervs/utmm.

**2026-09-27 unified RR/ERVS rr / aria:** execution=True, audit=True, PSNR=25.793071950664956, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_rr_ervs/gpu40_v1/rr/aria.

**2026-09-27 unified RR/ERVS rr / rpng:** execution=True, audit=True, PSNR=25.077735567522478, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_rr_ervs/gpu40_v1/rr/rpng.

**2026-09-27 unified RR/ERVS rr / utmm:** execution=True, audit=True, PSNR=22.240062716566484, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_rr_ervs/gpu40_v1/rr/utmm.

## 최종 결과

**2026-09-27 unified RR vs ERVS 완료:** κ16/τ4·40renders/KF·3:3:6·영상별Adam에서 RR→ERVS: Aria25.7931→25.8847(+0.0916), RPNG25.0777→25.2298(+0.1521), UTMM22.2401→22.2229(−0.0171)dB; 평균+0.0755dB. GPU6개 개별audit/평가2회PASS, 총·prefix render/Adam/admission/pool/loss/LR/GS동일. Pair exact-role audit는 폐기되는Aria 초기generation의window↔KF5회차이로실패; 차이를보존하고loss schedule·최종generation exact-role 일치 재검증. RR공유KF-control CPU오류수정후36tests·기본dense경로1500batch동등성PASS. 기본ERVS유지. 단일seed3개개발scene/frozen tracker이며 보편적우월성·live·geometry근거아님.

[상세 결과](SUMMARY.md).

## 2026-09-27: 15 renders/KF 追試

사용자 요청으로 예산만40→15로 줄인다. κ16, τ0=4,3:3:6,영상별Adam,blur/Carve/densify/prune OFF 및 seed0 유지. 동일3scene RR/ERVS를 새로6run 실행한다. κ 고정으로 admission수도 예산에 따라 감소하는 실제 정책을 그대로 비교하며, 15회에 맞춘 추가튜닝은 하지 않는다. 첫 ERVS15를 RR15의 prefix reference로 사용하고, 기존40회 결과와는 KF admission 및 arrival prefix를 정규화해 입력 동일성과 정확한15/40 예산을 검사한다. RR/ERVS 사이 admission/loss/batch/LR 및Gaussian수검증 유지. Bootstrap window/KF 역할라벨 차이는 원래대로 명시 기록한다.

**2026-09-27 unified RR/ERVS budget15 ervs / aria:** execution=True, audit=True, PSNR=23.27230923776408, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_rr_ervs/gpu15_v1/ervs/aria.

**2026-09-27 unified RR/ERVS budget15 ervs / rpng:** execution=True, audit=True, PSNR=24.029511869275893, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_rr_ervs/gpu15_v1/ervs/rpng.

**2026-09-27 unified RR/ERVS budget15 ervs / utmm:** execution=True, audit=True, PSNR=20.87563637745233, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_rr_ervs/gpu15_v1/ervs/utmm.

**2026-09-27 unified RR/ERVS budget15 rr / aria:** execution=True, audit=True, PSNR=22.8291896208552, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_rr_ervs/gpu15_v1/rr/aria.

**2026-09-27 unified RR/ERVS budget15 rr / rpng:** execution=True, audit=True, PSNR=23.470087779964413, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_rr_ervs/gpu15_v1/rr/rpng.

**2026-09-27 unified RR/ERVS budget15 rr / utmm:** execution=True, audit=True, PSNR=21.145271783993568, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_rr_ervs/gpu15_v1/rr/utmm.

## 완료

**2026-09-27 15renders/KF RR/ERVS+dense 2×2 완료:** κ16/τ4·3:3:6·영상별Adam유지. Dense에서RR→ERVS Aria22.8292→23.2723(+0.4431),RPNG23.4701→24.0295(+0.5594),UTMM21.1453→20.8756(−0.2696)dB;평균+0.2443(40회+0.0755). Dense−KF RGB-only는ERVS평균+0.2022(3/3개선),RR+0.0640(RPNG−0.4159). GPU12개/평가2회/CPU36/audit PASS;render·Adam·admission·pose·GS동일. Dense↔KF replacement는pool/초기quota로RGB횟수·batch/LR일부상이한시스템비교임을명시. ERVS mapper합계96.52→113.96s(+18.1%). 단일seed3개개발scene/frozen tracker;15회재튜닝/live/geometry검증아님. 기본설정유지.

[상세결과](SUMMARY15.md).
