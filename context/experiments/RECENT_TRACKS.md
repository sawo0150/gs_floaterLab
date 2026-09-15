# 최근 실험 묶음 — exp69~78 (번호 통합 후)

정리: 2026-09-11. 사용자 요청으로 이전 exp77~80 폴더를 **exp77 A~D**로 통합했다. 아래 표의 이전 번호는 과거 기록 식별용이다. [통합 카드](exp77/README.md) · [현재 exp77 E](exp77/e_reserve_ablation/README.md). 원본 실행 결과의 run ID는 유지한다.

## 1. final-v7 지도 유지와 floater loss — exp69~70

질문: 지도 품질을 유지하면서 불필요한 Gaussian을 억제할 수 있는가?

- [exp69: 지도 유지 정책](exp69/exp69_result.html): active/archive 등 정책을 여러 장면에 적용했으나 범용 후보는 기각.
- [exp70: detached opacity loss](exp70/exp70_score_free_detached_termination_loss.html): 교정된 final-v7 1× 기준에서 두 loss 모두 품질·floater 지표가 악화해 미채택.

exp70의 scheduler 시뮬레이션은 다음 묶음의 출발점이다. 같은 exp 안에도 loss 검증과 scheduling 분석이 함께 들어 있다.

## 2. 들어온 영상을 얼마나, 어떤 순서로 학습할 것인가 — exp70-S~76

질문: 성장하는 replay pool에서 학습 기회의 균형과 뷰 혼합을 함께 개선할 수 있는가?

| 단계 | 기록 | 역할과 결론 |
|---|---|---|
| 문제 정의·시뮬레이션 | [exp70-S](exp70/exp70_max_entropy_view_scheduler_sim.md), [exp71](exp71/exp71_joint_admission_scheduler_problem.md) | 선택 균등성·혼합·admission 조건을 분석. 공동 목표의 충돌 확인 |
| 실제 VIGS 적용 | [exp72](exp72/exp72_entropy_count_scheduler_real_ablation.md), [exp73](exp73/exp73_gate_free_token_admission_real_ablation.md) | scheduler와 admission을 각각 검증. exp72 교차 장면 실패, exp73 token admission 후보 확보·기본값 채택 보류 |
| pose를 고정한 분리 실험 | [exp74](exp74/exp74_offline_causal_full_pool_scheduler_ablation.md), [exp75](exp75/exp75_block_weighted_rr_30k_loop.md), [exp76](exp76/exp76_mean_normalized_softmax_ablation.md) | count 균등화의 한계 확인 → relative-floor softmax 개선 → 단순 normalized 대체안 기각 |

exp74의 30k 재검증은 exp74의 후속 단계다. exp75의 개선은 fixed-pose offline 실험 안의 causal replay 결과이며, 실제 strict VIGS 성능 개선으로 읽으면 안 된다. exp75/76 후보가 exp77~80에 적용됐다는 의미도 아니다.

## 3. final-v7 재현·종료 조건·기존 데이터셋 전이 — exp77 A~D (이전 exp77~80)

질문: Aria에서 얻은 품질이 기존 벤치마크에서도 유지되는가? 종료 조건을 엄격하게 적용하면 어떻게 달라지는가?

| 단계 | 기록 | 조건 | 결과 |
|---|---|---|---|
| A. 기존 데이터셋 기준선 | [exp77](exp77/exp77_vigs_final_v7_rpng_utmm_16seq.md) | RPNG/UTMM 16개, 1.5× + 종료 뒤 queue drain | 15개 평가, 평균 19.018 dB. zero-tail 명칭 정정 |
| B. Aria 재현 확인 | [exp78](exp77/b_aria_reproduction/exp78_aria_final_v7_reproduction.md) | Aria, 1× final-map, 종료 뒤 추가 update 있음 | 2회 평균 27.924 dB. zero-tail 아님 |
| C. 종료 조건 검증 | [exp79](exp77/c_aria_zero_tail/exp79_aria_1x_sensor_eos_zero_tail.md) | Aria, 1× + sensor-EOS optimizer zero-tail | 2회 평균 26.838 dB. tail 0은 2/2, 27 dB는 1/2 |
| D. 동일 종료 조건으로 전이 | [exp80](exp77/d_benchmark_zero_tail/exp80_vigs_1x_zero_tail_16seq.md) | RPNG/UTMM 16개, exp79 설정 | 13개 평가, 평균 17.268 dB. 3개 실패 |
| D의 원인 분석 | [exp80 분석](exp77/d_benchmark_zero_tail/exp80_root_cause_analysis.md) | 기존 코드·로그 분석, 추가 실행 없음 | 30fps에서 40ms reserve로 tracking 중 replay 허용 0회, 짧은 시퀀스 초기화 지연 확인 |

exp77~80은 서로 독립적인 네 방법론이 아니라 **한 재현·전이 검증의 네 단계**다. exp77↔80과 exp78↔79는 여러 설정이 함께 바뀌었으므로 단일 요인의 효과로 해석하지 않는다. exp77 C/D의 zero-tail 확인 범위는 optimizer update이며, 모든 map/SLAM 상태 갱신의 EOS 종료를 인증한 것은 아니다.

### 현재 작업: exp77 E

[exp77 E](exp77/e_reserve_ablation/README.md)에서 최적화 부족 원인을 검증한다. Aria1253·RPNG table_06·UTMM fast-straight가 주 대상이며 전체 16개를 후보마다 반복하지 않는다. table_06 reserve E1(40↔20ms)과 E2(20↔0ms)를 완료했고, 20→0ms에서 fixed held-out PSNR +0.428dB·dense replay +12.36%를 확인했다. RPNG 고정 shape TensorRT 엔진을 준비했으며, 다음은 같은 fixed 1×·optimizer zero-tail·held-out split에서 TensorRT on/off matched 비교다. 동일 질문의 후속 설정과 반복은 exp77 안에서 기록한다.

> 번호 운영 규칙(2026-09-11 사용자 지시): **exp78로 넘어가라는 명시적 지시 전까지 현재 및 후속 작업은 exp77 하위 단계에 기록한다.**
