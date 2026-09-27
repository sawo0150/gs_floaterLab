# 누적 ERVS — 40 renders/KF 검증 결과

2026-09-25 · RTX5090 · seed0 · batch1 · 실제 tracker 동시 실행 없는 causal fixed-work 비교

|장면|공식 vanilla|최근 count 재실행|누적 count|누적−vanilla|누적−최근|
|---|---:|---:|---:|---:|---:|
|aria|20.751|24.860|24.605|+3.853|-0.255|
|rpng|22.461|24.827|24.666|+2.205|-0.161|
|utmm|18.825|21.407|21.329|+2.505|-0.077|

PSNR 단위 dB. 장면별 차이의 단순 평균: 누적−vanilla +2.854, 누적−최근 -0.164 dB.

## 실제 작업량과 소요시간

|장면|동일 training renders|동일 Adam steps|native / 추가KF / dense (누적)|매핑 초 최근→누적|추가 선택 UID 변경|
|---|---:|---:|---:|---:|---:|
|aria|4760|3901|946 / 1908 / 1906|52.03→50.02|2859/3814|
|rpng|9080|7259|2006 / 3539 / 3535|124.12→123.41|5713/7074|
|utmm|3600|2950|717 / 1443 / 1440|51.14→53.71|1913/2883|

Mapper 시간에는 pose 준비 등을 포함하지만 실제 tracking 비용은 포함하지 않는다. 비슷하거나 더 좋은 PSNR이 나와도 real-time 성공으로 판정하지 않는다.

## 통제와 해석

- 양쪽 scope를 같은 현재 코드·동일 seed·40회 예산으로 실행. 묶음 업데이트는 적용하지 않았다.
- 누적 all_rgb는 native window+추가 학습을 모두 누적한다. 최근 대조군은 역할별 최근 추가 학습 횟수를 사용한다. 따라서 count 기억 길이와 native 반영 여부가 함께 바뀐 비교다.
- 입력 prefix별 render 수, causal event, 공유 pose trajectory, 평가 cohort를 각 run 및 기존 vanilla와 대조했다.
- 모든 generation의 누적 count와 실제 ERVS 선택 count를 완료 service ledger에서 독립 재집계했다. 총 render와 backward 및 zero-tail도 확인했다.
- 총6회 학습, 각 저장 지도2회 동일 평가 PASS. 평가 반복은 학습 재현성 검증이 아니며 seed0 결과만 보고한다.
- Vanilla는 원래 검증된 official40 결과를 재사용했다. 새로운 sampler 결과와 입력/평가/작업량 계약이 동일한지 재확인했다.
- 과거 최근 count 결과는 변경하지 않았다. 이번 최근 방식 재실행과의 차이는 아래에 공개한다.

|장면|이전 최근 PSNR|현재 최근 PSNR|차이|
|---|---:|---:|---:|
|aria|24.859212|24.859723|+0.000511|
|rpng|24.833669|24.827266|-0.006403|
|utmm|21.417964|21.406847|-0.011117|

## 산출물

- Raw/audit: `/home/intern/gs_floaterLab/results/campaigns/gain_attribution/cumulative_ervs/gpu40_v1`
- `verified_summary.json`: 최종 검증 및 차이.
- `comparison.csv`: 숫자 표.
- 각 scene/scope의 `independent_audit.json`, `render_result.json`, `evaluation_consistency.json`.
- [누적 변경 계약](README.md).
