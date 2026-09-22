# Fig.3 — frame 1180, 공통 입력 시점의 refinement 실측

[PNG 미리보기](fig3_refinement_frame1180.png) · [Inkscape SVG](fig3_refinement_frame1180.svg) · [PDF](pdf/fig3_refinement_frame1180.pdf)

기존 전체 trajectory 도판과 별도로 사용자가 요청한 추가 평가를 실제로 실행했다.
**이번 결과도 빠른 수렴의 근거로는 적합하지 않다.** 아래 파일은 결과 확인용 진단 도판이다.

## 그림 구성

- x: Additional mapping iterations, 추가 0–120회 Gaussian Adam update.
- y: 각 구간의 고정 held-out PSNR을 구하고 동일 5개 구간을 동등 가중 평균.
- 공통 입력 event17/38/68/98/119, input prefix513/960/1411/1851/2302.
- 구간별 45/59/56/56/58뷰, 합계 274개 서로 다른 held-out view.
- 10개 독립 분기 × 9 checkpoint = 90개 map, 총 4,932 view 평가.
- Inset: event68의 frame1180, 추가 0 / 30 / 120 iteration. 위 baseline, 아래 Ours.
- 두 방법은 각자 원래 online map/optimizer로 시작한다. 시작 PSNR을 강제로 맞추지 않았다.
- 각 분기에서 이후 입력을 중단하고 현재 causal KF 보간 평가 pose를 고정했다.
  양쪽 pose/held-out 목록 일치, KF pose 변화 0, held-out supervision overlap 0을 확인했다.
- 양쪽 실제 추가 Adam step과 training render가 매번 1:1인지 확인했다.

별표 `VIGS-SLAM*`은 native vanilla의 `map(max_viewpoints=1)`로 iteration당 렌더 수를
맞춘 실험용 baseline이다. 원래 multi-view native 실행과 동일한 조건은 아니다.
Ours는 기존 appearance replay/ERCB 경로를 사용한다. 양쪽 native topology 정책은 유지한다.
순수 sampler ablation 또는 native end-to-end 속도 benchmark로 해석하지 않는다.

## 실측 결과와 판단

| 추가 iteration | Baseline | Ours | Ours − Baseline |
|---:|---:|---:|---:|
| 0 | 21.4908 | 21.4359 | −0.0549 |
| 30 | 21.5272 | 21.4376 | −0.0896 |
| 120 | 20.7582 | 21.3775 | +0.6193 |

Ours의 시작 대비 개선은 **−0.0584 dB**, baseline은 **−0.7326 dB**다.
최종 gap은 Ours가 빠르게 향상된 결과로 볼 수 없다. Baseline의 Gaussian 수 변화는
event38/119에서 추가60–90 사이, event17/68/98에서 추가90–120 사이에 발생했다.
PSNR 하락과 topology 변화가 겹치지만 인과 기여를 분리한 실험은 아니다.

Frame1180 자체는 baseline 23.8346→20.8257, Ours 25.0472→25.3876 dB다.
이 단일 view 결과를 5개 구간 평균의 개선으로 바꾸어 주장하지 않는다.
측정 시작점이 이미 해당 event의 native mapping을 마친 상태라는 점도 고려해야 한다.

## 원본과 재현

- [평균 곡선 CSV](../analysis/refinement_curves/mean_curves.csv)
- [구간별 CSV](../analysis/refinement_curves/per_event_curves.csv)
- [전체 곡선·평가 검증 JSON](../analysis/refinement_curves/curves.json)
- [실험 카드](../../../../../context/experiments/ERCB_ablation/fig3_controlled_refinement_2026-09-21.md)
- [실측 도판 생성 코드](../scripts/build_refinement_figure.py)
- Map, 분기별 manifest, 로그: `results/figure03_refinement_20260921/aria301_305/`

SVG에 실제 crop PNG를 내장했다. Inkscape PDF를 Poppler로 다시 렌더해 검수했다.
Curve smoothing/생성 이미지/임의 gap 보정은 없다. 원고 TeX에는 삽입하지 않았다.

## 진단용 영문 캡션

> Controlled refinement on Aria301_305. At five common input events, each mapper
> is continued from its own online state without further observations or pose
> updates. Curves average held-out PSNR within each fixed event cohort, then
> equally across the five cohorts. Each additional iteration uses one rendered
> view and one Gaussian Adam update; VIGS-SLAM* is adapted to this single-view
> setting. Native topology policies are retained. Insets show frame 1180 at
> event 68. These diagnostic curves do not establish faster convergence:
> the final gap primarily reflects a decrease in baseline PSNR.
