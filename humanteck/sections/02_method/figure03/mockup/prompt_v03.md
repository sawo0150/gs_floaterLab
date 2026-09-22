# Fig. 3 시안 v03 — 그래프 내부의 3시점 비교

사용자 피드백: 지면을 줄이도록 이미지를 그래프 안에 넣고, 2–3개 시점에서 보여준다.
v02의 그래프 형태와 iteration 축을 유지하면서 아래 별도 이미지 행을 제거한다.

- 초기·중기·후기의 3개 inset, 각 inset은 위 Baseline / 아래 Ours의 동일 view·ROI.
- 초기 inset은 그래프 왼쪽 위, 중기·후기는 곡선 아래 빈 공간에 배치한다.
- 각 inset을 해당 iteration의 곡선 marker와 연결한다.
- GT 반복 열을 생략해 공간을 확보한다. 전체 trajectory 평균 곡선과 단일 view 예시의 역할은 유지한다.
- 시안의 0.8k/1.6k/2.4k는 배치용 가상 checkpoint이며 실측 선정값이 아니다.
- 실제 제작에서는 3개 시점 모두 평가 view의 관련 영역이 이미 관측됐는지 확인하고,
  고정 view·ROI를 유지한다. 한 단 인쇄에서 3개 inset이 작으면 동일 구조의 2시점으로 줄인다.

도구: built-in image_gen. 입력: [v02](layout_v02.png). 출력: [layout_v03.png](layout_v03.png).
곡선과 crop 모두 가상 시안이며 TeX에는 삽입하지 않는다.

## 시안 검수

- 그래프 내부 3개 시점 × 2개 방법, 별도 하단 이미지 행 제거, 가로형 구성을 확인했다.
- 곡선과 목표 품질 화살표는 이미지에 가려지지 않는다.
- 생성된 초기 주황 연결선은 teal marker 쪽으로 향하는 오류가 있다. 최종 제작에서는
  각 방법의 동일 iteration marker에 정확히 연결하고 후기 두 방법의 연결도 구분한다.
- 이미지들은 생성 예시여서 정확한 동일 crop/카메라 일치를 보장하지 않는다.
  최종 제작에서는 원본 렌더링의 고정 crop 좌표를 사용한다.
- 한 단 최종 인쇄 크기에서 글씨와 crop 판독성은 아직 검증하지 않았다.

## 프롬프트

+Use case: scientific-educational.
Edit the provided Figure 3 mockup into a compact single integrated plot with THREE image-comparison insets INSIDE the plotting rectangle. This remains a layout mockup, not experimental evidence.
Preserve the recognizable original graph: white background, black axes, gray light grid, teal solid Ours and orange dashed VIGS-SLAM rising PSNR curves, x "Mapping iterations (×10³)", y "Evaluation PSNR (dB) ↑", numeric tick scale x0–3 and y10–25. Preserve target-quality crossing circles and horizontal "Fewer iterations" arrow in upper right. Both curves and the full arrow must remain readable and unobscured. Use serif scientific-paper typography.
Change the overall composition to landscape roughly 1.6:1. Remove the entire separate lower image row, panel titles (a)/(b), ground-truth image column and k* annotation. Do NOT add any content below the x-axis apart from a compact footnote. The plot occupies almost the entire figure.
Add exactly THREE inset groups inside currently unused whitespace in the graph, each with TWO vertically stacked small landscape crops: baseline above, Ours below. ALL SIX crops depict precisely the same fixed camera view and same patterned poster/table/blue cup scene as the reference, allowing comparison across training checkpoints. Use tight poster/detail crops, rather than tiny full-room views. Each group has a short header "0.8k iter.", "1.6k iter.", or "2.4k iter." and tiny but readable method labels "VIGS-SLAM" above upper crop and "Ours" above lower crop. Orange thin upper-image frame, teal thin lower-image frame. No drop shadows, no opaque rounded dashboard panels, no GT images.
Placement is crucial to avoid covering graph lines:
- Early 0.8k group occupies upper-left empty region, approximately x0.10–0.85 and y18.4–24.6, entirely above both rising curves there.
- Middle 1.6k group occupies lower-middle empty region, approximately x1.08–1.84 and y10.5–16.8, entirely below both curves there.
- Late 2.4k group occupies lower-right empty region, approximately x2.16–2.92 and y10.5–16.8, entirely below both curves there.
Each inset header connects by a subtle dashed leader to the matching x location on the curves. Small orange and teal point markers indicate the two values at each of these three shared checkpoint iterations. Leaders should be short and do not cross other inset groups. Target quality horizontal dash line may begin near x1.0 so it does not run through the early inset.
The SAME fixed-view reconstruction detail should evolve across the three checkpoints: both schematic crops soft early, Ours becomes clearer earlier, baseline improves later. These are illustrative mockup crops, not claimed measurements.
Put a compact horizontal two-method legend just above plotting area; do not leave the old large legend in the lower right because that space is now an inset.
A small but clearly legible top line must say "LAYOUT MOCKUP — NOT EXPERIMENTAL RESULTS". Footnote: "Illustrative curves and crops; replace with measured results."
No percent speedup or fabricated measured numbers. Prioritize compact journal figure space efficiency, legibility, and preserving the graph curves. Exactly one graph, exactly three paired inset groups, no separate image panel.
