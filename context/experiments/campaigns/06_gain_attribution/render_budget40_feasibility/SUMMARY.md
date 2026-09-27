# 40 renders/KF 공통 예산 검증

2026-09-25 · RTX5090+i9-12900 · Aria1253/RPNG table_06/UTMM square-1 · seed0

기존 paired 정책을 유지하고 예산만15→40으로 바꿨다. 새로운20/10/10 배분이나 Growth/count/Carve 변경은 없다.

## 같은 pose와 실제 총 렌더링 수의 비교

| 장면 | 바닐라 PSNR15→40 | 우리 PSNR15→40 | 40회에서 우리−바닐라 | 실제 학습 renders(양쪽 동일) | Mapper 시간 바닐라/우리 |
|---|---:|---:|---:|---:|---:|
|aria|18.91→20.75|20.73→24.86|+4.11 dB|4760|24.65/51.43 s|
|rpng|21.23→22.46|22.28→24.83|+2.37 dB|9080|77.58/123.04 s|
|utmm|15.88→18.82|18.42→21.42|+2.59 dB|3600|34.18/51.54 s|

고정된 causal tracker trace를 prefix 순서대로 전달했다. 평가 pose/cohort, 학습 및 보조 render prefix 모두 양쪽 동일함을 독립 검증했다. 실제 tracking은 함께 돌리지 않았으므로 위 시간은 전체 시스템 시간이 아니다.
KF 분모는 map generation별 training KF admission이며 reset 뒤 재등록을 포함한다.40은 image별 학습 render 수다. 여러 이미지를 묶은 optimizer step과 구분한다.
Loss/topology 및 Adam grouping은 각 구조대로 유지하므로 ERVS 단독 ablation은 아니다.

## 실제 tracking 포함: 같은40회 상한

|장면|실제 학습 renders/KF 바닐라→우리|Held-out PSNR 바닐라→우리|Tracking 시간 바닐라/우리/입력|우리 추가KF/dense|입력지연p95 바닐라/우리|
|---|---:|---:|---:|---:|---:|
|aria|39.87→17.32|19.94→19.30|65.76/66.91/65.10 s|350/350|2.17/2.68 s|
|rpng|40.00→12.39|21.30→17.82|150.49/112.12/92.24 s|0/0|60.96/22.29 s|
|utmm|39.50→9.79|18.60→11.45|54.25/54.19/53.81 s|8/8|2.81/1.10 s|

Frontend4/2, IMU pose prediction20/20/15. 원본 timestamp1× 입력, mapping optimizer는 입력 종료 시각에 중단하며 지연된 tracking 처리시간은 포함한다. Model/engine loading과 저장 후 evaluation은 clock 밖이다.
실제 tracker가 생성한 pose/KF와 완료 work가 서로 다르므로 위 live 표는 동일 연산량 ablation이 아니다.40 상한을 소비하지 못하는 결과로 GPU의 최대 처리량이40 미만이라고 결론 내릴 수 없다.
Mapping 초기화, dense pose 준비/전송 및 optimizer 계측 비용은 runtime에 포함된다. No-grad 보조 render와 취소된 학습 forward는 별도로 집계했다.

## 판정과 KF 빈도 확인

40 renders/KF는 세 장면에서 비교 가능한 품질 차이를 보인 공통 예산 후보다. 다만 현재 구현의 실시간 예산으로 검증된 값은 아니다. 실제 동시 tracking에서는 우리 추가 학습이 idle 구간에 제한되어, 상한을 40으로 올려도 실제 수행량은 17.32/12.39/9.79회에 그쳤다. 특히 RPNG는 추가 KF/dense 학습이 모두 0회다. 실제 pose, 지도 coverage, 완료 연산량도 달라 live 품질 저하를 ERVS나 dense 자체의 효과로 분리할 수 없다.

RPNG table_06의 최종 tracker KF 수는 논문 Table 9의 232개, 이번 vanilla의 232개, paired의 211개다. 논문보다 최종 KF가 과다하게 남았다는 증거는 없다. 다만 최종 개수만으로 중간 KF 생성·제거 빈도나 순간적인 집중을 배제하지는 못한다. 이 개수는 reset 재등록과 held-out 제외가 반영되는 mapper admission 분모와 다르다.

같은 integration frontend의 mapping-off 대조군도 92.245초 입력에 111.477초가 걸렸고 최종 KF는 211개다. 따라서 mapping 연산만 약 1/3로 줄여 전체 처리시간도 1/3이 된다고 볼 수 없다. 원 논문은 RTX 5090+i7-14700K에서 table_06 tracking 34.02 FPS, mapping 포함 11.04 FPS를 보고한다. 이번 CPU는 i9-12900이고 실행·계측 경로도 달라 동일 구현 성능 재현이라고 주장하지 않는다.

Aria/UTMM vanilla는 약 40회를 소비하며 총 시간이 입력 길이에 근접했지만 p95 지연이 각각 2.17/2.81초라 엄격한 지연 제한까지 만족했다고 볼 수 없다. 다음 진단은 RPNG frontend 비용과 idle-only 추가 학습의 실행 기회다. 이번 검증에서는 scheduler나 역할별 quota를 변경하지 않았다.

- 논문 근거: [VIGS-SLAM Table 9 / runtime](https://arxiv.org/html/2512.02293v2#S10).
- Mapping-off 근거: `results/campaigns/gain_attribution/live_render_capacity/tracking_controls/rpng_imu20/result.json`.
- Fixed 6회와 live 6회 실행 audit 모두 통과, 각 저장 지도 2회 평가 일치. 이는 실행·계측 검증이며 품질/실시간 목표 달성 판정과 구분한다.

## 해석 범위

- 40회가 실제로 수행되었을 때의 품질 비교와, 현재 online scheduler가40회를 실현하는지를 구분한다.
- 40은 원래 VIGS 정상 mapping 호출의 약1/3 학습량을 겨냥한 후보이지, 실시간 인증 값이나 수렴 완료 기준이 아니다.
- 15 대비40 품질 향상은 확인할 수 있지만130 설정을 이번에 실행하지 않았으므로 품질 포화 여부는 판단하지 않는다.
- 각 조건 seed0 한 번 실행, 저장된 지도 평가2회 일치. 학습 재현성이나 통계적 유의성을 검증한 것은 아니다.
- Production mapper와 논문 tex는 변경하지 않았다. 원본15회 결과는 그대로 보존한다.

## 결과 파일

- Fixed-work CSV: `results/campaigns/gain_attribution/render_budget40_feasibility/v1/fixed/summary.csv`
- Live CSV: `results/campaigns/gain_attribution/render_budget40_feasibility/v1/live/summary.csv`
- 전체 실행/평가: `results/campaigns/gain_attribution/render_budget40_feasibility/v1/summary.json`
