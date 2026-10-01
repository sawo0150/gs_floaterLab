# 15 renders/KF dense 관측 대조군 (2026-09-27)

사용자 추가 요청: 저예산에서 dense 관측의 이득도 측정한다. 실행 중인 RR/ERVS dense_rgb6개를 유지하고, 각 selector에서 세 번째 slot을 full KF RGB-only로 바꾼6개를 추가해2×2비교한다.

- 같은 κ16,τ0=4,3:3:6,15 renders/KF,영상별Adam,scaleON,blur/Carve/densify/pruneOFF,seed0.
- Native window/KF loss는 유지. 세 번째역할은 dense RGB vs KF RGB-only로 동일RGB loss함수를 사용하므로 RGBD+normal로 바꾸는 대조군과 다르다.
- RR epoch는 앞선 구현 그대로 모든공유pool에 사용을 반영. KF두역할도window사용까지 실제count에 누적.
- CPU36tests / CPU sharedKF-pool RR coverage 회귀 통과한 backend 사용. 현재 진행중인6run source는 수정하지 않는다.
- 입력·pose·held-out·KF admission·총/prefix render와Adam은 동일하게 검사한다. KF replacement는pool overlap/초기후보수가 달라 batch/실제역할비중이달라질수있다. 이차이와RGB-only실제횟수를별도로보고하고순수픽셀다양성효과로과장하지않는다.
- Dense pose준비가불필요하므로속도차이를함께측정한다. κ는dense admission만제어하며KF후보는원래대로전부사용한다. Dense 후보 admission기록은유지되지만KF replacement에서는dense를학습하거나pose준비하지않음을검증한다.
- 세개발scene·단일seed·frozen causal tracker·zero-tail. Live/geometry검증아님.

## 실행 기록

**2026-09-27 KF RGB replacement RR/ERVS budget15 ervs / aria:** execution=True, audit=True, PSNR=23.059171130638997, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_rr_ervs/dense_control_gpu15_v1/ervs/aria.

**2026-09-27 KF RGB replacement RR/ERVS budget15 ervs / rpng:** execution=True, audit=True, PSNR=23.876651110949815, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_rr_ervs/dense_control_gpu15_v1/ervs/rpng.

**2026-09-27 KF RGB replacement RR/ERVS budget15 ervs / utmm:** execution=True, audit=True, PSNR=20.63515997227327, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_rr_ervs/dense_control_gpu15_v1/ervs/utmm.

**2026-09-27 KF RGB replacement RR/ERVS budget15 rr / aria:** execution=True, audit=True, PSNR=22.71711030625205, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_rr_ervs/dense_control_gpu15_v1/rr/aria.

**2026-09-27 KF RGB replacement RR/ERVS budget15 rr / rpng:** execution=True, audit=True, PSNR=23.88601891801164, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_rr_ervs/dense_control_gpu15_v1/rr/rpng.

**2026-09-27 KF RGB replacement RR/ERVS budget15 rr / utmm:** execution=True, audit=True, PSNR=20.6493724098912, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_rr_ervs/dense_control_gpu15_v1/rr/utmm.

## 완료

**2026-09-27 15renders/KF RR/ERVS+dense 2×2 완료:** κ16/τ4·3:3:6·영상별Adam유지. Dense에서RR→ERVS Aria22.8292→23.2723(+0.4431),RPNG23.4701→24.0295(+0.5594),UTMM21.1453→20.8756(−0.2696)dB;평균+0.2443(40회+0.0755). Dense−KF RGB-only는ERVS평균+0.2022(3/3개선),RR+0.0640(RPNG−0.4159). GPU12개/평가2회/CPU36/audit PASS;render·Adam·admission·pose·GS동일. Dense↔KF replacement는pool/초기quota로RGB횟수·batch/LR일부상이한시스템비교임을명시. ERVS mapper합계96.52→113.96s(+18.1%). 단일seed3개개발scene/frozen tracker;15회재튜닝/live/geometry검증아님. 기본설정유지.

[상세결과](../SUMMARY15.md).
