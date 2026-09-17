# exp87 — R4의 normalized-variance Gibbs selector pilot

> **2026-09-17 후속 원인 정정 (exp93):** 이 카드의 RPNG/UTMM 절대 PSNR은
> 혼합 inventory의 Aria 평가 어댑터가 `--undistort`를 누락한 **잘못된 GT
> 전처리 계약**으로 얻었다. 동일하게 잘못된 계약 안의 상대 차이는 당시
> pilot 관측으로만 남기고 공식 B-track 품질 비교에 쓰지 않는다. RPNG
> archived R4 재현 실패나 PIPE·direct 영향이라는 아래 해석도 철회한다.
> [원인 카드](exp93_evaluator_preprocess_root_cause.md), [수정 후 재실행](benchmark_custom/metric_benchmark_v2_fixed_eval_20260917/summary.md).

- 날짜: 2026-09-17
- 질문: 최종 R4 ERCB의 relative service-shortfall 선택을, 원래 수학적 유도인 `Var(count)/mean(count)` Gibbs 법칙으로 바꾸면 fixed held-out 품질이 크게 하락하는가?
- 판정: **시험한 4개 scene/mapper seed0의 fresh 동일-source pair에서는 큰 하락 없음**(scene 평균 −0.0142 dB, 최대 손실 −0.0457 dB). 최종 R4를 교체·승격하지 않음. RPNG `table_01`의 과거 R4 절대 PSNR 재현 실패는 별도 OPEN.

## 사전 고정한 selector 대안

현재 eligible per-view 완료 서비스 count를 `n_i`, `T=sum_i n_i`라 한다. 사용자 제안의
`Phi(n) = [sum_i n_i^2 - T^2/N] / (2T)`가 낳는 Gibbs log weight는 공통항을
제외하면 `-gamma*n_i/(T+1)`이다. `T=0`에서는 모든 view를 동일하게 취급한다.
R4와 같은 `gamma=log(1.5)`(즉 `tau=1/gamma`)를 고정하고 새 scene별 knob는
두지 않았다. 현재 eligible pool이 바뀔 때 `N,T`를 그 시점의 인과적 pool에서
다시 계산한다.

R4의 dense queue는 기존에 causal interval을 group으로 썼다. 여기서는 제안식이
**per-view variance**이므로 dense를 view별 singleton group으로 바꾸고, auxiliary
keyframe과 native historical keyframe에도 같은 log weight를 적용했다. 따라서
"계수만 변경"이 아니라 selector의 grouping/ordering 변경까지 포함한다. C1 admission,
FRONTIER/local window, separate appearance step, Adam/render 횟수, `K=8` block,
global no-repeat residue, birth/topology/loss는 그대로다. 선택 count는 제안 시점이
아니라 성공한 Adam 이후에만 증가한다. 테스트는 기존 R4 B-track의 frozen tracker
archive와 mapping-disjoint fixed held-out split, zero-tail, `time_scale=unbounded`를
그대로 썼다. C-track live-time 검증이 아니다.

## 결과: 현재 source로 새로 실행한 matched pair

단위 dB, `Δ = normalized - 현재 shortfall ERCB`. 4개 scene 모두 seed0.

| dataset/scene | fresh R4 shortfall | normalized variance | Δ | archive/work/held-out/zero-tail parity |
|---|---:|---:|---:|---|
| UTMM `fast-straight` | 16.368639 | 16.387485 | **+0.018846** | PASS |
| UTMM `square-1` | 21.232878 | 21.217412 | **−0.015466** | PASS |
| RPNG `table_01` | 20.806748 | 20.792387 | **−0.014361** | PASS |
| Aria `aria1253` | 25.758445 | 25.712790 | **−0.045655** | PASS |
| **Scene 산술평균 Δ** | | | **−0.014159** | 4/4 |

Parity PASS는 같은 archive hash, processed event IDs, dense admitted UID,
Adam step, physical rasterized-view update, fixed dense/KF opportunity skeleton,
held-out mapping/origin overlap 0, EOS 후 optimizer update 0을 뜻한다. Selected
UID가 달라지는 것은 selector ablation의 의도된 변화라 parity 대상이 아니다.
`fast-straight`에서는 native historical 서비스가 0회라 그 결과는 dense/aux
selector만의 매우 약한 진단이다. 각 scene은 1 seed뿐이고 17-scene 전체의
분포·worst-case 손실은 검증하지 않았다.

UTMM 두 장면과 Aria의 최초 normalized run은 이후 진단용 cache CLI가 harness에
추가되기 전 source였다. 위 primary 표에는 **동일 harness SHA-256**인 각 장면의
`normalized_variance_s0_repeat1`과 `service_shortfall_replay_s0`를 사용했다.
첫 normalized run도 각각 16.393813/21.223577/25.714835 dB로 같은 방향·규모다.
RPNG의 primary 두 arm은 처음부터 동일 harness source에서 실행됐다.
RPNG에서는 실행 wrapper 파일 hash만 중간에 달라졌고, 실제 mapping harness와
`map_scheduler.py`/`gs_backend.py`의 SHA-256은 두 arm에서 같았다.

왜 영향이 작은가: RPNG native historical pool의 완료 서비스 `T=8400`에서
`beta=log(1.5)/8401≈0.0000483`이다. final block의 normalized bonus 범위는
`1.49350–1.49993`(odds 약 `1.0043`)으로, current shortfall의 `1–1.48091`보다
훨씬 균일 RR에 가깝다. Aria에서도 normalized bonus는 `1.48853–1.5`다.
Global no-repeat residue가 count spread를 이미 좁혀 이 차이를 더 작게 만든다.
이것은 현재 gamma를 고정한 **한 normalization 구현**의 결과이지, 모든
normalized-variance temperature가 동등하다는 뜻은 아니다.

## 중대한 별도 발견: archived RPNG R4 절대값 재현 실패

기존 `table_01` R4 archive는 **25.624315 dB**였다. 그러나 현재 source의
shortfall R4를 같은 archive/split/config/seed/work에서 새로 두 번 실행하자
**20.806748 / 20.804699 dB**였고, 과거처럼 geometry cache를 사실상
무제한으로 되돌린 진단도 **20.805846 dB**였다. 따라서 LRU cache 변경만으로는
차이를 설명하지 못한다. 최초 fresh R4의 dense/aux selected UID와 native
historical selection ledger는 archived R4와 exact였고, full trajectory 파일
SHA-256도 같았다. Gaussian 수는 archived 417,618, fresh 417,652로 근접했지만
map 품질은 크게 다르다. 원인은 **미확정**이며 normalized selector의 −4.8 dB
효과로 해석하면 안 된다. 과거 all-scene R4/vanilla +1.2609 dB를 이 fresh
source에서 재현했다고 주장할 수도 없다. 이 불일치는 paper 수치 재현성 감사의
우선 대상이다.

## 구현·증거

- Opt-in 구현: `/home/intern/VIGS-SLAM-paper-full/vigs/map_scheduler.py`, `vigs/gs_backend.py`; 기본값은 기존 `service_shortfall`.
- Replay flag: `benchmarks/online_gs/exp78b_replay_gsslam_mapping.py --ercb-selection-potential normalized_variance`.
- Runner: `benchmarks/online_gs/run_exp87_normalized_variance_r4.py`. 기존 hash-locked R4 promotion runner의 판정/결과 파일을 덮어쓰지 않았다.
- 각 run의 `mapping.log`, `evaluation.log`, `mapping_replay_runtime.json`, `psnr/strict_fixed_manifest/final_result.json`, `ablation_pair.json`: `results/experiments/exp87_normalized_variance_r4/{dataset}/{scene}/` 아래. Primary normalized는 UTMM/Aria에서 `normalized_variance_s0_repeat1/`, RPNG에서 `normalized_variance_s0/`; control은 모두 `service_shortfall_replay_s0/`.
- RPNG 추가 진단: 같은 디렉터리의 `service_shortfall_replay_s0_repeat1/`, `service_shortfall_replay_s0_legacy_cache/`.
- Scheduler 회귀 테스트 25+10 PASS, X4 runner 테스트 9 PASS, py_compile PASS.

**결정:** normalized variance는 이번 범위에서 catastrophic PSNR 하락을 보이지
않았지만 R4의 default/논문 §3.2를 소급 교체하지 않는다. 새로운 method claim이나
17-scene adoption을 하려면 RPNG 재현성 문제를 먼저 해결하고, 동일-source 다중 seed
및 service-scarce scene을 별도 사전 계약으로 확인해야 한다.

## 2026-09-17 추가 진단: RPNG R4의 실행 경로 민감성

위의 "archived R4 절대값 재현 실패"는 **R4 recipe 자체의 재현 실패로 단정하면
안 된다.** 동일 RPNG archive/고정 held-out 502장/seed0/config/3,030 Adam/
38,302 physical render에서 아래처럼 실행 방식에 따라 두 품질 군집이 갈렸다.

| 실행 | held-out PSNR | 비고 |
|---|---:|---|
| 9/15 archived R4 | 25.624315 | 기존 artifact를 현재 evaluator로 재평가해도 정확히 동일 |
| 9/15 paper commit + 당시 harness 직접 재실행 | 25.626920 | 동일 입력·현재 GPU; 진단용 임시 경로 |
| 당시 harness + 현재 paper source 직접 실행 | 25.625405 | 현재 mapper 추가 코드 단독으로는 하락 없음 |
| 현재 harness + paper source 직접 실행(`/tmp`) | 25.630379 | default shortfall, 동일 인자 |
| 현재 harness, 래퍼와 같은 환경·인자 순서로 직접 실행(`/tmp`) | 25.627015 | 환경·인자 순서 단독 원인 아님 |
| **exp87 래퍼** 현재 source 재실행 `service_shortfall_replay_s0_repeat2` | **20.810871** | 원래 20.806748/20.804699의 낮은 군집 재현 |
| **현재 source 직접 실행** exp87 폴더 `service_shortfall_direct_s0_repeat3` | **25.619726** | 결과 경로 단독 원인 아님 |

마지막 두 실행은 mapper/하네스의 active source SHA-256, archive/config/평가
manifest, seed, dense/aux/native 선택 UID trace, event별 작업량, Adam/render 수,
held-out disjoint와 zero-tail이 동일하다. 전체 Gaussian 수는 각각
417,657/417,632로 가깝지만 지도 품질은 약 **4.809 dB** 다르다. 원래 archived
PLY 재평가도 25.624315 그대로라 evaluator/GT가 숫자를 잘못 읽은 문제도 아니다.

따라서 현재 확인한 결함은 **exp87 래퍼의 자식 프로세스 실행·로그 수집 경로와
직접 실행 사이의 대규모 품질 분기**다. `run_logged`는 stdout PIPE를 한 줄씩
읽어 즉시 stdout/파일로 flush하지만, 이 I/O가 CUDA/optimizer state에 어떤
방식으로 영향을 주는지는 아직 입증되지 않았다. pipe 자체를 원인으로
확정하지 않는다. work/selector parity만으로 수치 재현성을 보장하지 못한다.
RPNG의 normalized−shortfall **−0.014361 dB는 래퍼의 낮은 군집 내부 상대값**일
뿐, 정상 25.6 dB 군집에서 normalized potential의 효과는 미검증이다.

영구 증거: `results/experiments/exp87_normalized_variance_r4/rpng/table_01/`
아래 `service_shortfall_replay_s0_repeat2/`와
`service_shortfall_direct_s0_repeat3/`의 `mapping_replay_runtime.json`,
`psnr/strict_fixed_manifest/final_result.json`, PLY. 과거 25.624315 증거는
`results/experiments/exp78/paper_full_staged_v1/stage6r_r4_native_global_keyframe/rpng/table_01/r4_native_global_keyframe_ercb_s0/`.

**판정 정정:** RPNG R4 자체는 직접 재현됐으나, 현재 B-track 평가 실행 경로에는
심각한 재현성 결함이 남았다. 원인 분리와 재현 가능한 실행 계약이 마련되기
전까지 exp87의 RPNG selector 수치와 기존 17-scene 평균을 현재 실행의
검증 완료 수치로 승격하지 않는다.

## 2026-09-17 후속 판정 정정 — exp88 high-cluster gate 실패

정상 direct-file shortfall R4 `25.619726 dB`를 확인한 뒤 같은 launch mode,
source/archive/config/seed/work로 normalized variance를 다시 실행했다. RPNG
`table_01` normalized는 **20.787371 dB**로 shortfall보다 **−4.832355 dB**였다.
따라서 이 카드의 `RPNG −0.014361 dB`는 낮은 실행 군집의 내부 대비에만
한정된다. **"RPNG에서 normalized variance가 크게 하락하지 않는다"는
일반적인 결론은 철회**한다. 전체 17-scene 확인은 첫 scene의 사전 fail-stop
gate에서 멈췄다. 상세 계약과 증거는
[metric benchmark v2](benchmark_custom/metric_benchmark_v2_normalized_variance_20260917/README.md)에 있다.

## 2026-09-17 추가 정정 — 낮은 PLY가 아니라 첫 evaluator 실행 문제

위 `실행 경로에 따라 두 품질 군집`과 `normalized −4.8 dB map 손실` 해석은
후속 exp89/exp90 증거로 **철회**한다. exp87 wrapper repeat2의 동일 PLY가
첫 평가 **20.810871**, 재평가 **25.620909 dB**였고, 신규 wrapper repeat4도
**20.803644→25.632411 dB**였다. exp88 normalized PLY 역시
**20.787371→25.584315 dB**였다. 따라서 mapper/PIPE가 낮은 지도 자체를
만들었다고 할 수 없다. PIPE 재평가도 높아 PIPE 단독 원인도 아니다.
남은 문제는 첫 평가의 저수준 비결정성이며, normalized를 채택하거나
17-scene 비교를 재개하기 전에 동일 map 독립 평가 일치 gate가 필요하다.
→ [exp89](exp89_normalized_selector_family_isolation.md),
[exp90](exp90_evaluator_first_pass_reproducibility.md).
