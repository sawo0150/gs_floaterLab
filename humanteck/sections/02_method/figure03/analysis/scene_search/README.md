# Fig.3 다른 장면 탐색 — 3개 후보 실측 완료

기존 Aria301_305/1180의 그래프 내부 3시점 inset 구성을 유지할 다른 장면을 탐색한다.
전체 fixed held-out PSNR과 native cumulative Adam iteration이라는 평가 정의도 유지한다.

## 확인 범위

기존 exp94의 17개 scene을 점검했다. 모두 final PLY만 있어 중간 곡선의 신규 계측이 필요하다.
기존 19-scene KF-only/KF+dense ablation 곡선은 overall-system 비교와 조건이 달라 대체하지 않았다.
[17-scene 목록](inventory.json)에 endpoint, pose-correction 빈도, 원본 경로를 저장했다.

3개를 우선 재계측한다:

- UTMM square-1: pose correction 0회이며 해당 UTMM 조건의 final gap이 가장 큼.
- RPNG table_01: final gap +1.65 dB, 이른 관측 frame330의 천 무늬 이미지 후보가 있음.
- RPNG table_06: final gap +1.79 dB, frame1420의 포스터 문자 이미지 후보가 있음.

장면 선택은 illustration을 위한 사후 탐색이다. 17-scene 평균 결과나 수렴 가속의
일반적인 통계 증거로 해석하지 않는다. 결과가 덜 좋은 후보도 모두 공개한다.

## 실행

`results/figure03_scene_search_20260921/`에 기존과 동일한 seed0 mapper pair를 재실행한다.
Checkpoint 저장 간격은 square-1 50, table_01/table_06 200 Adam step이며 마지막 map도 포함한다.
이 간격은 평가를 위한 저장 간격이며 학습 schedule/topology policy 변경이 아니다.
각 scene의 원래 고정 held-out view 전체와 distortion-aware preprocessing으로 평가한다.

[곡선 비교 PNG](curve_comparison.png) · [벡터 SVG](curve_comparison.svg) · [수치 요약](summary.json)

## 최종 판단

**곡선 모양과 확대 이미지의 조합은 RPNG table_06 / frame1420을 우선 추천한다.**
Table_01/frame330은 초기 상승 뒤 안정적인 plateau가 있고 중반 PSNR 차이가 더 큰 대안이다.
두 후보 모두 Aria의 마지막 급상승보다 점진적이다. 다만 처음부터 큰 격차가 있는 것은 아니다.

| 장면 | 중반 평균 gap | 최종 gap | 판단 |
|---|---:|---:|---|
| RPNG table_06 | +0.7542 | +1.7751 | 완만한 상승, 포스터 문자 inset, 1순위 |
| RPNG table_01 | +0.9078 | +1.6594 | 초반 급상승 후 plateau, 중반 gap이 조금 큼 |
| UTMM square-1 | −0.1071 | +1.0513 | 모양은 상승형이지만 Ours가 초·중반 앞서지 않음 |
| 기존 Aria301_305 | +0.7033 | +3.2383 | 마지막 pose correction 구간에서 큰 점프 |

중반은 두 arm의 공통 iteration 범위 중 30–80%의 기술통계다. 이 요약에만 선형 보간을
사용했고 도판 곡선은 실제 checkpoint를 그대로 연결했다. Checkpoint 간격이 달라
smoothness 통계를 정밀한 convergence-rate 검증으로 해석하지 않는다.

## Fig.3 스타일 실제 도판

- **table_06 / frame1420**: [PNG](../../output/fig3_search_table_06_frame1420.png) · [SVG](../../output/fig3_search_table_06_frame1420.svg).
  Inset 800/1400/2600 step; 전체 view PSNR 차이는 각각 +0.33/+0.74/+2.70 dB.
- **table_01 / frame330**: [PNG](../../output/fig3_search_table_01_frame330.png) · [SVG](../../output/fig3_search_table_01_frame330.svg).
  Inset 800/1600/3000 step; 전체 view PSNR 차이는 각각 +0.52/+1.45/+2.24 dB.

Inset 시점은 실제 시간별 렌더를 검토한 뒤 초기/중간/후기 예시로 선택했다. 전체 curve는
선택과 무관하게 모든 측정점을 보존한다. 이미지는 GT 좌표의 동일 crop이며 enhancement가 없다.
기존 Fig.3 A의 그래프 내부 3개 inset-pair 구성을 유지하되 새 곡선을 가리지 않도록 아래쪽에 배치했다.

`Same PSNR*`은 **baseline 최종 평균 PSNR 이상을 처음 기록한 저장 checkpoint**의 비교다.
Table_06은 기준22.6879 dB에서 Ours1200 / baseline2000 step,
Table_01은 기준23.9209 dB에서 Ours1200 / baseline1800 step이다.
200-step 간격이므로 정확한 crossing이나 지속적 도달/가속률이라고 주장하지 않는다.
Native step당 render와 input prefix가 달라 순수 optimizer 또는 wall-clock 속도로 확장하지 않는다.
RPNG에도 중간 pose correction이 있으며 효과를 제거한 실험은 아니다.

## 재현 확인과 원본

새로 6개 run / 92 checkpoint / 41,972 view를 평가했다. 고정 held-out은 square-1 324,
table_01 502, table_06 555뷰다. 각 scene 양쪽 총 training render는 원본과 동일하고
최종 PSNR 변화는 모든 arm에서 절댓값0.011 dB 이내다. 평가 pose와 held-out UID 집합도 일치했다.

- [square-1 CSV](square-1_curves.csv) · [JSON](square-1_curves.json)
- [table_01 CSV](table_01_curves.csv) · [JSON](table_01_curves.json)
- [table_06 CSV](table_06_curves.csv) · [JSON](table_06_curves.json)
- [실험 카드](../../../../../../context/experiments/ERCB_ablation/fig3_scene_search_2026-09-21.md)

완료된 3개 중의 그림 추천이다. 나머지 14개 scene의 수렴 곡선까지 실측한 것은 아니다.
기존 Aria 도판과 원고 TeX는 유지했다.

