# Unified RR vs ERVS 결과 (2026-09-27)

현재 tuned 구조에서 ERVS−RR 평균 held-out PSNR은 **+0.0755dB**다. Aria/RPNG는 개선하고 UTMM은 −0.0171dB다. 작은 평균 이득이며 모든 장면 우세 또는 통계적 유의성은 입증하지 않았다. 기본 ERVS preset 유지.

## 비교 조건

κ16 dense-only growth, 40 renders/KF, window:KF:dense=3:3:6, 영상별 Adam, scale projection ON, densify/prune/Carve/blur OFF, seed0. ERVS τ0=4 및 각 pool τ=4/N. 최근 window는 양쪽 균등 선택하며, full KF/admitted dense 선택만 ERVS↔RR로 변경했다. 양쪽 모두 새로 학습했다.

RR은 KF/dense별 독립 random reshuffling이며 새 영상은 현재 남은 순회 queue 뒤에 shuffle하여 추가한다. Window 학습도 KF epoch에서 사용한 것으로 센다. 배치 내 UID 중복 금지와 commit-only 진행 규칙은 [구현](IMPLEMENTATION.md)을 참고한다.

## Held-out PSNR

| Scene | RR | ERVS | ERVS−RR |
|---|---:|---:|---:|
| aria | 25.7931 | 25.8847 | +0.0916 |
| rpng | 25.0777 | 25.2298 | +0.1521 |
| utmm | 22.2401 | 22.2229 | -0.0171 |
| 세 장면 단순 평균 | 24.3703 | 24.4458 | +0.0755 |

## Mapper 시간 및 작업량

| Scene | RR(s) | ERVS(s) | renders=Adam(양쪽 동일) | GS(양쪽 동일) |
|---|---:|---:|---:|---:|
| aria | 35.30 | 34.46 | 4760 | 192623 |
| rpng | 113.83 | 115.98 | 9080 | 357071 |
| utmm | 38.50 | 37.67 | 3600 | 141545 |

세 장면 mapper 합계는 RR 187.63s / ERVS 188.11s다. 단일 실행의 작은 시간 차이이므로 속도 우위로 해석하지 않는다.

## 검증 및 예외

- GPU6개 모두 실행·개별 audit·저장 지도 평가2회 통과. 도착prefix별 render, 총 Adam, 미래/held-out 입력 배제, zero-tail, pose/cohort/source 일치 검증. ERVS 세 장면의 service trace는 이전 tuned 결과와 정확히 같다.
- 양 arm의 admission ledger/pool membership, 모든 step의 native-vs-RGB loss 종류, batch size/token/LR 위치, 최종 GS 수가 같다.
- 원래 panel의 최종 pair audit는 exact role-label assertion에서 실패했다. Aria generation1의 5회가 ERVS window / RR KF-pool로 갈렸다. 둘 다 동일 native RGBD+normal loss이며 그 map은 이후 reset되었다. 최종 generation에서는 역할도 정확히 같다. 실패를 보존하고 실제 loss schedule과 차이5개를 명시한 재분석으로 검증했다. GPU run을 실패한 것처럼 버리거나 exact role 일치로 꾸미지 않는다.
- RR를 별도 KF-only auxiliary 대조군과 혼용하면 pool 중복 때문에 StopIteration이 날 수 있는 CPU 문제를 추가로 발견했다. 이번 dense_rgb GPU 비교에는 해당하지 않는다. 모든 공유 pool에 실제 사용을 반영하도록 수정하고 회귀테스트 추가. GPU source snapshot과 수정 후 코드의 현재 dense_rgb 동작을 두 selector×5seed×150batch=1500회 비교하여 선택/상태 일치 확인. 수정후 CPU36 tests PASS. 최초 한 번 workspace root에서 unittest 모듈을 못 찾은 실행은 test 디렉터리에서 재실행해 해결.
- GPU 당시 source lock과 사후 변경3개(backend 공유KF-pool 수정, 회귀테스트, panel의 pair audit 설명)는 post_run_validation.json에 분리 기록했다. 원래 GPU snapshot은 그대로 보존했다.

## 해석 범위

- 현재 κ16/τ4 개발 설정에서 ERVS의 평균 효과는 약 +0.076dB다. Dense 관측이나 loss recipe의 기존 이득 전체를 ERVS에 귀속할 수 없다.
- KF와 dense sampler를 동시에 바꿨으므로 어느 pool에서 이득이 나는지는 분리하지 않았다.
- 단일seed·세 개발장면 비교다. 같은 개발장면으로 τ를 고른 뒤 수행한 조건부 비교이므로 독립 test 일반화나 통계적 유의성 근거가 아니다. 저장 지도2회 평가는 독립 학습 반복이 아니다.
- Frozen causal tracker의 fixed-work mapper 실험이며 simultaneous tracking/live 또는 geometry/floater 개선 검증은 아니다.

## 산출물

- [전체 비교 JSON](/home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_rr_ervs/gpu40_v1/comparison.json)
- [사후 검증 및 source 차이](/home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_rr_ervs/gpu40_v1/post_run_validation.json)
- [최초 pair audit 실패 기록](/home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_rr_ervs/gpu40_v1/initial_pair_audit_failure.json)
- [GPU 실행 요약](/home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_rr_ervs/gpu40_v1/summary.json)
- [사전 조건 및 실행 기록](README.md)
