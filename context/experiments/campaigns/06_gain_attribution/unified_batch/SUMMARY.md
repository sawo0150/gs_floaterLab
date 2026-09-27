# Unified mapping batch 비교

2026-09-25 · seed0 · 세 장면 공통40 renders/KF · cumulative ERVS · densify/prune OFF

|window:KF:dense|Aria PSNR|RPNG PSNR|UTMM PSNR|평균 변화 vs paired OFF|평균 시간비 vs paired OFF|
|---|---:|---:|---:|---:|---:|
|기존 paired OFF|25.022|24.784|21.701|—|1.000|
|3:3:6 / 영상별 Adam|26.264|25.279|22.398|+0.812|1.077|
|3:3:6 / 영상별 Adam / 크기상한 복원|25.592|25.118|22.126|+0.444|1.060|
|4:4:4 / 영상별 Adam|24.472|25.270|22.194|+0.143|1.005|
|3:3:6 / 묶음별 Adam|23.067|23.924|19.986|-1.509|1.019|
|3:6:3 / 묶음별 Adam|23.133|23.795|19.942|-1.545|0.902|
|4:4:4 / 묶음별 Adam|22.754|23.739|19.897|-1.705|0.950|
|6:3:3 / 묶음별 Adam|22.703|23.506|19.759|-1.846|0.913|

세 장면 평균 held-out PSNR로 선택한 개발 설정: **3:3:6 / 영상별 Adam**. 다른 장면별 비율을 섞어 선택하지 않았다.
최종 구조 검증 대상은 **3:3:6 / 영상별 Adam / 기존 크기상한 복원**이다. 상한 누락 상태의 수치는 원인 분석용으로 구분한다.

|설정|장면|training renders|Adam steps|window/KF/dense 실제 사용|mapper초|Gaussians|
|---|---|---:|---:|---:|---:|---:|
|3:3:6 / 영상별 Adam|aria|4760|4760|1190/1190/2380|53.31|192,623|
|3:3:6 / 영상별 Adam|rpng|9080|9080|2270/2241/4569|142.90|357,071|
|3:3:6 / 영상별 Adam|utmm|3600|3600|900/900/1800|55.71|141,545|
|3:3:6 / 영상별 Adam / 크기상한 복원|aria|4760|4760|1190/1190/2380|52.64|192,623|
|3:3:6 / 영상별 Adam / 크기상한 복원|rpng|9080|9080|2270/2241/4569|138.62|357,071|
|3:3:6 / 영상별 Adam / 크기상한 복원|utmm|3600|3600|900/900/1800|55.47|141,545|
|4:4:4 / 영상별 Adam|aria|4760|4760|1586/1563/1611|49.95|192,623|
|4:4:4 / 영상별 Adam|rpng|9080|9080|3011/2971/3098|133.70|357,071|
|4:4:4 / 영상별 Adam|utmm|3600|3600|1201/1157/1242|51.71|141,545|
|3:3:6 / 묶음별 Adam|aria|4760|454|1190/1190/2380|50.18|192,623|
|3:3:6 / 묶음별 Adam|rpng|9080|879|2270/2241/4569|133.63|357,071|
|3:3:6 / 묶음별 Adam|utmm|3600|344|900/900/1800|53.53|141,545|
|3:6:3 / 묶음별 Adam|aria|4760|454|1190/2331/1239|44.29|192,623|
|3:6:3 / 묶음별 Adam|rpng|9080|879|2270/4445/2365|120.81|357,071|
|3:6:3 / 묶음별 Adam|utmm|3600|344|900/1731/969|46.54|141,545|
|4:4:4 / 묶음별 Adam|aria|4760|454|1586/1563/1611|47.02|192,623|
|4:4:4 / 묶음별 Adam|rpng|9080|879|3011/2971/3098|126.54|357,071|
|4:4:4 / 묶음별 Adam|utmm|3600|344|1201/1157/1242|48.93|141,545|
|6:3:3 / 묶음별 Adam|aria|4760|454|2380/1141/1239|44.81|192,623|
|6:3:3 / 묶음별 Adam|rpng|9080|879|4498/2217/2365|121.80|357,071|
|6:3:3 / 묶음별 Adam|utmm|3600|344|1780/851/969|47.42|141,545|

## 구조와 해석

- arrival당 하나의 mapping envelope. tracker/control 반영 → birth/pose 갱신 → unified sampler → 설정한 optimizer 단위로 학습. native 별도 optimizer 및 추가 학습 packet0개.
- recent window는 uniform without replacement. KF/dense는 각 full available pool에서 cumulative ERVS. window에서 이미 뽑힌 KF는 해당 batch의 global KF 후보에서 제외하되 이후 batch에서는 다시 후보가 된다.
- 실제 성공한 batch의 각 영상에 count+1. window 선택도 KF의 누적 count에 포함. 취소·pose 준비는 count를 올리지 않으며 새 map generation에서만 초기화.
- batch가 작아지거나 pool이 부족할 때는 비율이 정확히 일치하지 않는다. 부족분 재배분·잔여 예산4회 및 초기 영상 부족을 실제 사용량에 포함했다.
- KF RGBD+normal과 dense RGB loss 유지. 묶음별 Adam은12장의 gradient를 합산하고1회 업데이트; 영상별 Adam은 같은12장을 준비/선택한 뒤 각 영상마다 업데이트한다. 두 설정의 영상 선택 순서 및 각 영상에 적용한 LR clock을 실행 ledger에서 대조했다.
- Gaussian LR은 선택 묶음 시작의 완료 render 수를 기준으로 정하고 묶음 내에서 유지한다. optimizer 단위를 바꿀 때 LR 배수를 추가하지 않았다.
- 동일 render 예산이 동일 Adam 횟수를 뜻하지 않는다. 기존 paired는 native multi-view+추가 single-view; 새 구조는 통합 sampler와 단일 학습 경로다. paired 대비 비교에는 sampler 비율과 optimizer grouping이 함께 바뀌며 ERVS만의 효과는 아니다. 동일 비율의 묶음별/영상별 Adam 비교는 동일 선택 순서·LR로 optimizer grouping 영향을 분리한다.
- 각 run에서 prefix별 render, 입력 events/trajectory/cohort, 누적 count, native step0, 한 arrival packet1개, topology operator0, 마지막 입력 뒤 update0을 검증했다.
- 한 scene/arm당 seed0 학습1회, 저장 지도 평가2회 일치. 이 cohort를 ratio 개발에 사용했으므로 독립 최종 benchmark와 다르다.
- mapper 전체시간은 단일 실행이며 실제 tracking 동시 실행/실시간 보장/geometry 개선을 뜻하지 않는다.
- 최초 통합 경로는 native map() 끝의 scale≤0.1 후처리를 함께 우회했다. 동일 비율의 묶음별/영상별 Adam은 둘 다 이 조건이 같아 grouping 비교가 유효하다. 최종 p arm은 native map 경계의 기존 scale projection을 복원했다. densify/prune를 켠 것이 아니다.

## 산출물

- `/home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_batch/gpu40_v1`
- `/home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_batch/optimizer1_v1`
- `/home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_batch/projected_v1`
