# LIVE — strict streaming and mapper runtime

## 질문

센서가 계속 들어오는 동안 zero-tail과 causal order를 지키면서 얼마나 많은
mapping work를 완료하고, held-out 품질을 유지할 수 있는가?

| 묶음 | 대표 실험 | 판정 |
|---|---|---|
| vanilla VIGS 재현 | [exp52](../../exp52_vigs_slam_eval.md) | online 22–23 dB와 offline polish 값을 분리함 |
| runtime 원인 분석 | [exp53–56](../../exp56_mapping_fixedcost_reduction.md) | view/kernel 고정비와 init burst를 규명 |
| strict quality | [exp57–60](../../exp59_strict27_cross_scene_transfer.md) | Aria1253 27 dB는 달성했지만 scene-specific cutoff는 일반화 실패 |
| robust/live 방향 | [exp61–65](../../exp65_status_report.md) | unknown-horizon·causal 설계 필요 |
| cross-dataset strict | [exp77](../../exp77/README.md), [exp78](../../exp78/README.md) | benchmark와 live deadline을 분리하는 계기 |

## 현재 사용 규칙

- live claim은 native timestamp producer, tracking+mapping 동시, zero-tail로만 한다.
- B-track mapping-only의 unbounded fixed-render 결과를 realtime 결과로 부르지 않는다.
- 과거 freeze800/late-map 절대 cutoff는 provenance일 뿐 재사용하지 않는다.
