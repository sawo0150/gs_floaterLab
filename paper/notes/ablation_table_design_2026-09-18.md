# 현재 method에 대응하는 ablation table 설계안

작성: 2026-09-18. 사용자 요청에 따른 구상안이며, 기존 TeX 표나 확정 계획을 교체하지 않는다.
기준 원문: [현재 method](../latex/sec/4_method.tex). 아래 수치는 기존 실험의 재집계이며 신규 학습 실험이 아니다.

**권장 구성은 본문 ablation 4표다: supervision의 필요성과 한계 → growth 법칙의 효과 → sampling의 두 요소 → geometry 목적함수.**
페이지가 부족하면 첫 표의 밀도 sweep을 그림으로 옮긴다. 기존 시스템 비교는 Main Results에 둔다.
현재 자료만으로 네 표 모두를 완성할 수는 없다. 특히 현재 수식의 ERCB 단독 효과와 새 Carve/Hit 효과는 별도 대조가 필요하다.

## 1. 먼저 구분해야 할 데이터

| 자료 | 실제로 검증하는 것 | 사용 위치 / 제한 |
|---|---|---|
| `ERCB_ablation/dense-supervision` | 같은 update 예산에서 KF-only와 dense pool 비교; view 밀도 및 예산 sweep | §3.1 동기. 고정 pose/init replay, seed0, llffhold-8 |
| `ERCB_ablation/benchmark-A` | full history / recent-window / 과거 interval ERCB; 13장면, 3예산 | history 보존 및 저예산 진단. final pose/init 및 historical tail admission 때문에 strict causal 실증 아님 |
| `ERCB_ablation/benchmark-B` | init stride40/20 × RR/과거 ERCB, 19장면 | initialization과 scheduler 상호작용, 보충자료. fixed topology, seed0 |
| `ERCB_ablation/exp01`, `exp03` 및 후속 A–H | 과거 interval ERCB의 tuning / replay / 실제 mapper 전이 | 보충자료와 한계. 현재 normalized per-view sampler의 on/off 표로 대체 불가 |
| `benchmark_custom/metric_benchmark_v2_fixed_eval_20260917` | 현재 normalized sampler를 포함한 전체 mapper vs fresh vanilla, 17 pair | Main Results. frozen causal tracker, render-matched, zero-tail; 실시간 성능이나 ERCB 단독 인과효과 아님 |
| `VIGS_ERCB_ablation` | frontend 처리량, KF/dense 역할, pre-IMU 초기화 등의 시스템 변경 | 시스템 진단 보충자료. 폴더명과 달리 순수 ERCB on/off 실험이 아님 |
| `benchmark_vanila` | unbounded / streaming / strict / paper reference별 baseline | 같은 계약의 결과끼리만 비교. exp94에는 그 실험에서 새로 실행한 vanilla를 사용 |

현재 method §3.2는 `exp[-n_i/(tau(T+1))]`인 **per-view normalized Gibbs**다.
과거 `relative_floor_interval_softmax_rr(K=8,rho=.5,gamma=log3)`의 결과와 같은 방법으로 표기하면 안 된다.
Exp94는 기존 block/global residue 안에서 조건부로 선택하므로, 단순히 전체 pool에서 K장을 뽑는 현재 본문 설명과의 대응도 밝혀야 한다.

## 2. Table A — What supervision should the mapper retain?

대응: §3.1 첫 두 문단. 질문은 “중간 frame이 도움이 되는가, 전부 넣으면 항상 좋은가?”다.

**Panel (a): 19장면의 KF-only vs KF+dense, 60 updates/interval.**
열은 `Dataset | #Scenes | KF-only | KF+dense | ΔPSNR | Wins`.
가족 내 scene 산술평균이며, 전체는 19 scene 산술평균이다. 가족 평균의 단순 평균이 아니다.

| Dataset | #Scenes | KF-only | KF+dense | ΔPSNR | Wins |
|---|---:|---:|---:|---:|---:|
| RPNG | 8 | 23.41 | 23.06 | −0.34 | 4/8 |
| UTMM | 7 | 20.25 | 21.12 | +0.87 | 7/7 |
| Aria | 4 | 28.50 | 29.25 | +0.75 | 4/4 |
| All | 19 | 23.31 | 23.65 | +0.33 | 15/19 |

출처: [TABLE_X.md](../../context/experiments/ERCB_ablation/dense-supervision/TABLE_X.md).
가족 평균은 manifest의 complete run별 `evaluation_curve.jsonl`에서 final `split=test` PSNR을 다시 읽어 계산했다.
정밀 수치와 run 경로는 [CSV](../results/tables/ablation_dense_supervision_20260918.csv)에 보관한다.

**Panel (b): 같은 장면에서 view 밀도와 예산을 교차 비교.**
열은 `Scene | updates/interval | m=1 | m=2 | m=4 | m=8 | all`.
여기서 **m**은 interval당 후보 view 수다. §3.2의 sampling block size **K**와 다른 기호를 쓴다.
본문에는 Aria1253 / RPNG table_01 / UTMM square-1의 15·30·60 budget 격자를 권장한다.
숫자는 [summary.md](../../context/experiments/ERCB_ablation/dense-supervision/summary.md) 및 원본 로그에 있다.
해당 요약의 table_01/budget60/m8 빈칸은 원본 final iteration 14461에 **23.6596dB**가 존재하므로 다음 생성 때 보완 가능하다.

분량이 부족하면 panel (b)를 세 subplot의 `m–PSNR` 곡선으로 바꾸고, 예산을 선 색으로 표시한다.
단일 seed의 argmax를 “정답 m*”로 강조하지 않는다. 예를 들어 Aria/budget30의 m2와 m8 차이는 0.0045dB에 불과하다.

추가로 모든 dense 음수 장면의 budget 확장 결과를 보충자료에 함께 둔다:

| RPNG scene | dense−KF @60 | dense−KF @120 |
|---|---:|---:|
| table_03 | −0.721 | +0.451 |
| table_04 | −0.943 | +0.560 |
| table_05 | −2.080 | +0.827 |
| table_06 | −0.741 | +0.223 |

60/120 각각의 pair는 동일 final update에서 비교했다. 출처는
`results/ERCB_ablation/dense_supervision_densify/rpng/<scene>/event<budget>/{kf_only,kf_dense}_s0/evaluation_curve.jsonl`.
이는 실패 장면의 사후 진단이며 독립 generalization panel이 아니다.

**허용되는 주장:** 중간 frame은 유용한 supervision이며, 모든 frame의 무조건적 admission은 유한 예산에서 손해를 낼 수 있다.
**아직 입증하지 못하는 주장:** 제안한 κ-growth가 최선이다; 예산 부족만이 원인이다; 실시간으로 더 빨리 수렴한다.
Budget 확대 시 LR horizon과 densification 일정도 함께 바뀌므로 단독 원인 확정은 불가하다.

이 replay의 densification 종료는 총 iteration의 1/2를 사용한다. 이는 현재 unknown-horizon active recipe와 다르므로
기존 진단으로만 인용하고 새로운 strict ablation의 출발점으로 재사용하지 않는다.
“같은 #GS”도 아니다. 최종 Gaussian 수가 비슷해도 geometry/topology 경로가 같다고 볼 수 없다.

## 3. Table B — Does optimization-guided growth improve quality?

대응: §3.1 식 (growth constraint / growth bound). Table A의 동기가 실제 제안법으로 이어지는지 검증한다.

| Row | Admission / retention | Selector | 목적 |
|---|---|---|---|
| B0 | KF-only, history 유지 | 공통 RR | supervision 기준선 |
| B1 | 모든 arrived train frame, history 유지 | 공통 RR | 무조건적 dense 확장 |
| B2 | 고정 시간 간격의 causal admission, history 유지 | 공통 RR | compute와 무관한 성장 |
| B3 | completed updates에 따른 κ-growth, history 유지 | 공통 RR | 제안 growth의 순효과 |
| B4 | B3와 같은 admission, 과거 view를 window 밖에서 제거 | 공통 RR | history 유지 효과 |

열: `Policy | RPNG PSNR | UTMM PSNR | Aria PSNR | #admitted | updates/view | #renders | time`.
본문이 넓으면 마지막 resource 열들은 보충자료로 옮기되 동일-work 조건은 caption에 남긴다.
Fixed-rate 상수와 κ는 개발 세트에서 고정하고 결과별 optimal m/κ를 고르지 않는다.
Retained pool size와 cumulative admission 수는 B4에서 다르므로 구분한다.

같은 causal packet/pose revision, initialization 정책, loss, frontend, 평가 UID, work credit을 공유한다.
RR와 현재 ERCB 각각에 대해 B3의 admitted-view trace가 같은 completed-work clock에서 어떻게 대응하는지도 감사한다.
같은 최종 pool 크기만 맞추는 것은 admission 시점 통제가 아니다.

**현재 상태: 이 표를 완성할 동일 구현·동일 계약의 전체 대조군은 지정 자료에서 확인하지 못했다.**
Benchmark-A의 window 결과는 보조 동기에는 쓸 수 있지만 이 B4에 직접 붙일 수 없다.
같은 update 예산과 같은 wall time은 다르다. 먼저 fixed-work 효과를 보이고 실시간 주장은 별도 live 실험에서 확인한다.

## 4. Table C — Which part of entropy-regularized sampling matters?

대응: §3.2의 count preference, entropy, without-replacement block. 가장 중요한 신규 ablation이다.
Growth와 admitted UID/시점 trace, KF/dense role, work budget을 고정한다.

| Row | Count preference | Selection | 검증할 대비 |
|---|---|---|---|
| C0 | 없음 | uniform with replacement, K=1 | 기본 stochastic sampling |
| C1 | 현재 normalized Gibbs | with replacement, K=1 | C1−C0: count bias 효과 |
| C2 | 없음 | uniform without replacement, K=K0 | C2−C0: block 효과 |
| C3 | 현재 normalized Gibbs | without replacement, K=K0 | C3−C2: 동일 block의 count bias; C3−C1: block 추가 효과 |
| C4 | least-count | deterministic selection | entropy/randomness 제거 |
| C5 | 없음 | causal RR | 강한 history coverage 기준선 |

열: `Sampler | RPNG/UTMM/Aria PSNR | late-20% PSNR | Φ | H(p)/log|eligible|`.
본문 폭을 줄이면 가족 PSNR은 전체 mean PSNR + paired Δ로 압축하고 가족별 결과를 보충자료에 둔다.
Selection statistics는 품질 지표를 설명하는 보조 지표다. Final Φ 하나보다 arrival 전후 또는 공통 checkpoint의 Φ 추이를 함께 보는 편이 좋다.
Late subset은 timestamp로 사전 정의한다. RR-hard subset을 쓰면 RR 기준 UID를 모든 arm에 고정한다.
각 arm에서 별도 worst quartile을 고르는 지표와 동일-frame 비교를 혼동하지 않는다.

No-repeat residue를 모든 arm에 남겨두면 C0/C1은 실제 with-replacement 대조군이 아니다.
Count bias/블록/전역 residue 중 무엇을 제거했는지 명시하고, 최종 C3가 배포 구현과 정확히 같게 한다.
Least-count의 tie-breaking도 명시한다. deterministic 제거 실험에서 tie를 임의 shuffle하면 완전한 entropy 제거가 아니다.

보충표는 `K ∈ {1,4,8,16}`의 전역 sweep과 fixed-beta vs normalized-beta 대조를 권장한다.
τ는 공통으로 고정하고 K를 scene별로 고르지 않는다. 실제 pool이 작으면 effective K도 기록한다.
서로 다른 frame도 이미지가 거의 같을 수 있으므로 “중복 선택 감소”로 “gradient가 uncorrelated”까지 주장하지 않는다.

**현재 상태: exp94는 현재 C3를 포함한 전체 mapper의 성능만 제공한다. 이 표의 C0–C5 대조를 대신하지 않는다.**
Exp94의 전체 개선 **+1.2538dB, 16/17**에는 birth/density, supervision role, topology 정책 등의 효과도 포함된다.
과거 benchmark-B의 interval ERCB 개선은 low/mid/high **+0.6154/+0.1137/+0.2313dB**이지만 다른 sampler다.
Exp03-H의 실제 mapper 진단 **+0.0614/−0.0614dB**도 함께 공개해 replay 개선의 전이 한계를 설명한다.
과거 결과를 현재 방법의 단독 검증으로 소급하지 않는다.

## 5. Table D — Does ray-space supervision improve geometry without losing appearance?

대응: §3.3의 mean-depth 한계, free-space 제거, surface hit 확보, factorization.

| Row | 추가 목적함수 | 핵심 질문 |
|---|---|---|
| D0 | 없음: 동일 L_base | geometry 기준선 |
| D1 | conventional mean-depth term | 평균 depth만으로 충분한가? |
| D2 | Carve-ENLL | free-space 억제가 작동하는가? |
| D3 | Carve-MARG | marginalization 방식 차이가 중요한가? |
| D4 | Hit | surface termination을 설명하면 무엇이 개선되는가? |
| D5 | factorized Carve+Hit | free-space와 surface를 함께 확보하는가? |

열: `Objective | held-out PSNR ↑ | region-GT floater ↓ | surface recall ↑ | time ↑cost`.
Surface GT가 있다면 동일 기준의 precision/recall 또는 F-score를 사용하고, 없다면 이 열은 미측정으로 남긴다.
Training에 사용한 ray의 hit mass/free-space mass는 작동 진단이며 독립 geometry GT를 대신하지 않는다.
Floater 감소만 보면 opacity를 전부 지우는 해가 유리하므로 surface 보존 지표가 필요하다.

L_base에 이미 rendered-depth term이 들어 있으면 D0와 D1을 중복시키지 않는다.
모든 arm에서 기존 depth loss를 유지하고 추가항만 바꾸거나, 명확한 별도 replacement 비교로 설계한다.
Ray 집합, causal depth, uncertainty, ray 수를 고정한다. Carve opacity-only / Hit full-gradient 차이를 명시한다.
Factorization의 별도 이득까지 주장하려면 `naive global Carve+Hit` 대조를 보충자료에 추가한다.
ENLL/MARG 전체 표는 개발용으로 쓰고, 본문에는 선택된 목적함수 중심의 4–5행만 남길 수 있다.

**현재 상태: 지정한 네 폴더에서 현재 §3.3의 목적함수별 region-GT 대조 결과는 확인하지 못했다.**
과거 prune/gate/force carve 수치를 새 ray-termination objective의 결과로 옮기지 않는다.
현재 27dB 미달 active map에 hard carve/pruning을 먼저 도입하는 실험은 이 제안에 포함하지 않는다.

## 6. 본문과 보충자료 배치

본문 권장 순서:

1. Main Results: exp94의 전체 mapper 대 vanilla, PSNR/SSIM/LPIPS 및 resource 비용.
2. Ablation Table A: dense supervision의 가능성과 과도한 pool 확대의 한계.
3. Table B: 실제 κ-growth와 history 보존의 기여.
4. Table C: 현재 normalized sampling의 count bias와 block 효과 분해.
5. Table D: geometry 목적함수와 surface 보존.

보충자료: 19/17 scene 원표, initialization stride 2×2, 과거 interval ERCB의 budget interaction,
실제 mapper 전이 실패, K/τ sensitivity, geometry 세부 후보 및 resource profile.
3-component 체크마크 표가 필요하면 동일 backbone에서 growth×sampler의 2×2를 먼저 완성하고 geometry를 추가한다.
Vanilla→옛 custom→새 custom→carve를 서로 다른 실험에서 가져와 하나의 누적 ablation으로 연결하지 않는다.

## 7. 제출 전 숫자와 주장 정리

- 현재 main 결과는 17 scene, dense 진단은 19 scene, benchmark-A는 13 scene이다. 모두 동일 장면 집합처럼 쓰지 않는다.
- llffhold-8 replay와 exp94의 `idx%5==0 OR final` fixed evaluator를 같은 PSNR 열에 혼합하지 않는다.
- Seed0 결과를 mean±std(3 seeds)로 표기하지 않는다. 과거 ±0.33dB는 현재 실험의 confidence interval이 아니다.
- 신규 최종 ablation은 대표 개발 장면에서 설계를 고정하고 복수 seed와 고정 transfer panel로 확인한다.
- 최종 PSNR만으로 시간에 대한 수렴 가속을 확정하지 않는다. 기존 evaluation_curve는 동일 update checkpoint끼리 비교 가능하지만, checkpoint마다 이용 가능한 관측량도 명시해야 한다.
- 현재 method의 “dense improves quality”는 모든 장면에 대한 단정에서 평균/조건부 표현으로 줄이는 것이 데이터와 맞는다.
- 현재 가장 우선적인 누락은 **같은 최신 mapper에서의 normalized ERCB on/off**와 **κ-growth 대조**다. 추가 scene 수 확대보다 이 비교가 기여의 인과성을 직접 설명한다.
