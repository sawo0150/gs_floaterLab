# Metric benchmark v2.1 — evaluator self-consistency repair

> **2026-09-17 원인 확정:** 낮은 두 평가는 Aria 어댑터가 RPNG의
> `--undistort`를 제거한 명령, 높은 수동 평가는 distortion-aware RPNG
> 명령이었다. 시간·이중평가 문제가 아니라 서로 다른 GT 전처리였다.
> 아래 v2.1 gate와 0/17 결과는 실패 provenance이고, exp94는 어댑터
> 위임 수정·명령 invariant·새 source lock으로 별도 실행한다.
> [exp93 원인 카드](../../exp93_evaluator_preprocess_root_cause.md).

- 날짜: 2026-09-17
- 상태: **첫 RPNG gate에서 STOP; 이중 평가도 낮은 군집을 걸러내지 못함**
- runner: `benchmarks/online_gs/run_exp91_normalized_metric_v2_reliable.py`
- 출력: `results/experiments/exp91_normalized_metric_v2_reliable/`
- 자동 장면 표: [summary.md](summary.md) (완료한 pair만 기입)

## 사전 비교 계약

exp88의 첫 저장-map 평가 오류를 확인했으므로 새 source-locked protocol을
사용한다. 유효 scene은 17개(UTMM `slow-straight-1` N/A)이고 R4의 세
ERCB selector만 `Var(count)/mean(count)`의 per-view Gibbs law
`p_i ∝ exp[-log(1.5)n_i/(T+1)]`로 바꾼다. 온도·스케줄러·birth·dense
admission·topology를 scene별로 조정하지 않는다. 이것은 raw-variance
shortfall sampler와 수학적으로 같다고 주장하지 않는다.

두 mapper는 동일 frozen causal tracker, mapping-disjoint fixed held-out,
zero-tail, 동일 physical training render budget을 사용한다. Native vanilla는
normalized arm이 실제 완료한 rendering work에 맞추고 native RGB-D/normal
경로를 유지한다. B-track은 `time_scale=unbounded` mapping-only isolation이며
C-track strict live-time 증거가 아니다.

각 arm의 mapping 후 **15초 cooldown**을 동일하게 적용하고 저장 PLY를 서로
다른 subprocess에서 두 번 평가한다. 두 평가 전후 PLY/trajectory/mapped UID/
manifest SHA를 확인하며, per-view PSNR 최대 차이 `>0.01 dB`, SSIM/LPIPS
최대 차이 `>0.001`, 평가 뷰 또는 Gaussian 수 불일치 시 **높은 점수를
선택하지 않고 즉시 중단**한다. 첫 평가와 두 번째 평가가 모두 통과한 뒤에만
기존 R4 대비 `>0.5 dB` 급락 및 render-match fairness gate를 판정한다.
cooldown은 exp90 1회에서 두 평가 일치를 보였지만 저수준 원인 자체는
아직 미확정이므로 이 이중 평가 gate가 필수다.

최소 acceptance는 유효 17-scene 산술평균 normalized−vanilla PSNR
`≥+0.5 dB`, 엄격한 과반 승리, 모든 pair fairness PASS다. Historical R4의
17/17 승리·평균 +1.2609 dB는 추가 목표다. 개발/노출/confirmation scene
표시는 이전 R4 카드의 분류를 유지하고 새로 scene별 튜닝하지 않는다.

## 사전 gate 검증

exp88 원래 저장 PLY에 남은 첫/두 번째 평가
`20.787371/25.584315 dB`를 이 런처의 self-consistency 함수에 넣자
예상대로 `saved-map evaluation disagreement; stop`이 발생했다.
실패 보고서는 `results/experiments/exp88_normalized_metric_v2/rpng/table_01/normalized_variance_s0/evaluation_consistency.json`에 보존했다.

## 첫 scene 결과와 정정

새 RPNG normalized PLY의 첫/두 번째 독립 평가는 **둘 다
20.783158 dB**로 완전히 일치했다. 구조 gate 12/12는 PASS였지만 기존
R4 25.624315보다 −4.841157 dB이므로 사전 규칙에 따라 vanilla 및 나머지
scene은 실행하지 않았다. 같은 PLY SHA를 유지한 세 번째 독립 평가는
**25.574971 dB**였다. 이중 평가 일치와 15초 cooldown은 evaluator의
낮은 군집을 배제하기에 불충분하다. 높은 세 번째 수치를 공식 score로
선택하지 않았고, 정식 pair는 여전히 **0/17**이다.
→ [exp91 실패 카드](../../exp91_double_eval_guard_failure.md)
