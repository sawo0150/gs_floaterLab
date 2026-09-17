# Metric benchmark v2 — normalized-variance ERCB fail-stop

> **2026-09-17 최종 원인 정정 (exp92/93):** 아래 20.787371 dB은 Aria
> wrapper가 혼합 inventory의 RPNG evaluator에도 적용되어 `--undistort`가
> 빠진 **다른 GT 계약**의 점수다. 같은 PLY의 예측 이미지는 같고 GT만 달랐다.
> 따라서 아래의 `first eval`/PIPE·direct 차이·normalized map 급락 해석은
> 무효이며 과거 기록으로만 남긴다. 새 source lock의 올바른 명령을 쓰는
> exp94 결과만 공식 비교에 사용한다. [원인 카드](../../exp93_evaluator_preprocess_root_cause.md).

> **2026-09-17 후속 정정 (exp89/exp90):** 아래 20.787371 dB은 저장 normalized
> PLY의 재평가에서 **25.584315 dB**로 바뀌었다. exp87의 낮은 R4 PLY도
> 재평가하면 25.62 dB다. 따라서 아래의 −4.8 dB를 normalized sampler의
> 실제 map 품질 손실로 해석하는 판정은 **철회**한다. 다만 첫 평가가 크게
> 흔들리는 결함이 확인됐으므로 이 v2 gate/17-scene loop는 계속 STOP이고,
> normalized-vs-vanilla 공식 pair는 여전히 0/17이다. 원인·증거는
> [exp89](../../exp89_normalized_selector_family_isolation.md),
> [exp90](../../exp90_evaluator_first_pass_reproducibility.md)에 보존한다.

- 날짜: 2026-09-17
- 상태: **STOP / 전체 scene 실행 미개시**
- 코드: `benchmarks/online_gs/run_exp88_normalized_metric_v2.py`
- 출력: `results/experiments/exp88_normalized_metric_v2/`

## 목적과 사전 계약

기존 B-track 18개 계획 scene 중 UTMM `slow-straight-1`은 tracker metric
initialization 실패로 N/A다. 나머지 17개에서 R4의 dense/aux-KF/native-KF ERCB를
`Var(count)/mean(count)`의 per-view Gibbs law
`p_i ∝ exp[-log(1.5) n_i/(T+1)]`로 바꾸었을 때 native vanilla 대비 held-out
PSNR 이득이 유지되는지 검증한다. Scene별 knob, phase cutoff, render budget
변경은 없다. B-track frozen causal tracker, fixed mapping-disjoint held-out,
mapping-only `time_scale=unbounded`, zero-tail 평가이며 strict live-time C-track이 아니다.

exp87 RPNG에서 자식 프로세스 stdout PIPE/line-forwarding 실행과 regular-file
stdout 직접 실행이 같은 source/work/선택 trace에서도 약 4.8 dB 갈린 것을
고려하여 v2의 mapper/evaluator는 자식 stdout을 regular file에 직접 연결한다.
각 normalized mapper가 완료되면 historical R4와 archive/config/event/Adam/
physical render/dense admission/opportunity skeleton/held-out/zero-tail parity를
검증한다. 통과한 scene에서는 normalized의 실제 service runtime을 reference로
official vanilla를 **같은 direct-file 방식으로 새로 실행**하고 기존
`verify_exp78b_d1_render_match.py`를 적용한다. 과거 vanilla 숫자를 최종 v2
비교값으로 대체하지 않는다.

안전 중단선은 어느 scene에서든 normalized held-out PSNR이 기존 R4보다
**0.5 dB 초과 하락**하거나 위 불변 검증이 실패하는 순간이다. 순서대로
실행하고, 중단 시 vanilla와 후속 scene은 돌리지 않는다. 작은 손실이나
vanilla 대비 작은 음수는 전체 패널에서 정직하게 기록하되, 급락은 즉시
원인 감사로 전환한다.

## 첫 gate: RPNG `table_01`

| 비교 | fixed held-out PSNR |
|---|---:|
| 기존 R4 shortfall artifact | 25.624315 |
| 현재 source의 direct-file shortfall control | 25.619726 |
| 현재 source의 direct-file normalized variance | **20.787371** |
| 기존 official vanilla artifact — 참고값, v2 재실행 아님 | 23.929422 |

Normalized는 직접 실행 shortfall보다 **−4.832355 dB**, 기존 R4보다
**−4.836944 dB**이며 참고 vanilla보다 **−3.142051 dB**다. 사전 중단선
`−0.5 dB`를 크게 넘었으므로 **17-scene loop를 시작하지 않고 멈췄다.**
v2 vanilla도 실행하지 않았으므로 정식 normalized-vs-vanilla pair 수는
**0/17**, 전체 scene 이득 유지 여부는 **미확인**이다. 첫 scene의 참고 vanilla
대비 이득은 유지되지 않았다.

`quality_gate.json`의 12개 구조 검증은 모두 PASS: 동일 archive, config,
event, 3,030 Adam, 38,302 physical render, dense admission, dense/KF opportunity
skeleton, 502 fixed held-out, mapping overlap 0, zero-tail 0. 최종 Gaussian은
normalized 417,672, direct shortfall 417,632개다. PSNR 손실은 첫/중간/끝
평가 view 전반에 나타난다.

## 중단 후 검토

같은 direct-file source에서 dense 선택의 unique UID 집합은 같고 267개
opportunity 중 실제 선택이 다른 것은 **4개**다. 반면 auxiliary-KF 선택은
**157/267**, native historical-keyframe 선택은 **1,286/1,610** audit row에서
달랐다. Native normalized bonus는 마지막 block에서 `1.49350–1.49993`으로
거의 균일하지만, 과거 native-history *만* uniform으로 둔 R3가
25.580154 dB였으므로 `near-uniform` 하나만으로 이번 4.8 dB 하락을 설명할
수 없다. 세 selector의 상호작용, 구현 경로 차이, 수치적 분기를 분리해야 한다.
Exp87의 normalized−shortfall `−0.014 dB`는 두 arm이 모두 20.8 dB의 낮은
실행 군집에 있었기에 이번 정상 shortfall 기준의 손실을 놓쳤다.

다음 진단은 direct-file 런처를 고정하고 dense/aux/native normalized potential을
**한 family씩만** opt-in하여 어느 경로에서 처음 map이 갈라지는지 확인하는
것이다. 그 전에는 17-scene 실험을 재개하거나 normalized potential을 채택하지
않는다. 이 중단은 실패 결과이지 pipeline 완주 성공으로 기록하지 않는다.

## 증거

- V2 normalized map/eval: `results/experiments/exp88_normalized_metric_v2/rpng/table_01/normalized_variance_s0/`
- V2 stop report: `results/experiments/exp88_normalized_metric_v2/rpng/table_01/quality_gate.json`
- source hash lock: `results/experiments/exp88_normalized_metric_v2/source_lock.json`
- direct shortfall control: `results/experiments/exp87_normalized_variance_r4/rpng/table_01/service_shortfall_direct_s0_repeat3/`
- historical vanilla/R4: `context/experiments/benchmark_custom/r4_all_scenes_fixed_work_20260915/README.md`
