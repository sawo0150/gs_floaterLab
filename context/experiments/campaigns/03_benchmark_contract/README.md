# BENCH — fair benchmark contract and official main result

## 공식 비교 결과

| 결과 | Candidate | Vanilla | 판정 |
|---|---|---|---|
| [Exp94 normalized R4](../../exp94_fixed_evaluator_normalized_panel.md) | 17-scene main snapshot | official render-matched VIGS | 17/17, 평균 약 +1.25 dB |
| [Exp109 first-persistence](../../exp109_first_persistence_panel.md) | source-backed topology ticket 포함 | fresh official vanilla | 17/17, 평균 +1.286809 dB; R4와 사실상 동률 |

논문 main table은 Exp94를 기준으로 하고, Exp109는 local topology가 R4 품질을
보존함을 보여주는 후속 composition이다. 둘을 합쳐 새로운 숫자로 만들지 않는다.

## 비교 계약

- 동일 frozen causal tracker packet, pose/depth/normal
- 동일 held-out manifest와 dataset-specific evaluator
- zero-tail
- 동일 **physical training-view render budget**
- render와 Adam step을 별도로 보고
- 과거 vanilla 수치와 fresh candidate를 섞지 않음

## 실험 계보

| 범위 | 역할 |
|---|---|
| exp77–78 | dataset 준비, paper reproduction, frozen B-track |
| exp82–87 | Aria transfer, KF/dense 입력, work-credit와 normalized R4 |
| exp88–93 | evaluator 재현성 문제 발견 및 root cause 수정 |
| exp94 | fixed evaluator 공식 panel |
| exp109 | source-backed local topology를 포함한 fresh 17-scene pair |

더 자세한 rule은 [vanilla benchmark plan](../../benchmark_vanila/bc_metric_comparison_plan.md)과
[metric protocol](../../benchmark_vanila/paper_online_metric_protocol_and_baseline_modifications.md)을 본다.
