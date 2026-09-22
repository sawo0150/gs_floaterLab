# Fig. 3 imagegen 시안 v02 — iteration 축

사용자 요청에 따라 주 x축을 **Mapping iterations (×10³)**로 변경한다.
이 결정이 [최초 설계](../analysis/design_2026-09-21.md)의 render 축 권고보다 우선한다.
실제 optimizer iteration을 사용하며 render count를 이름만 iter로 바꾸지 않는다.
방법별 iteration당 view 수와 입력 진행 조건은 실험 설명에서 정의한다.

구성: 위에 전체 trajectory의 fixed held-out PSNR 곡선 두 개, 공통 품질 도달
iteration 차이를 수평 화살표로 표시. 아래에는 같은 중간 iteration의
Baseline / Ours / GT 예시를 배치한다. 15/30/60은 첫 시안에서 제외한다.
스타일 참고: HAMMER Fig. 5, https://arxiv.org/html/2501.14147v2#S4.SS2.SSS2

이미지 생성은 built-in image_gen 사용. 곡선과 crop 모두 구도를 설명하는 가상 예시이며
실측 데이터가 아니다. 논문 제출용 곡선/이미지는 원본 로그와 렌더링으로 교체한다.
초고 TeX에는 아직 삽입하지 않는다.

## 생성 프롬프트

출력: [layout_v02.png](layout_v02.png).
검수: iteration/PSNR 축, 두 곡선, 목표 도달 수평 화살표, 공통 checkpoint와
3열 이미지 배치 및 mockup 표시를 확인했다. 모든 곡선/이미지는 가상 예시다.
최종 도판에서는 k*와 숫자 tick을 분리하고, 실측 곡선의 비단조 변화와
실제 렌더링을 그대로 사용한다. 시안의 최종 품질 동률은 레이아웃용이며 예측이 아니다.

+Use case: scientific-educational.
Asset type: A provisional image-generated Figure 3 layout mockup for a short computer-vision research paper, NOT an actual experimental result.
Create one polished, compact journal-style figure on pure white, approximately square 1200 by 1100. Follow the restrained visual grammar of an IEEE robotics paper convergence plot: thin black axes, subtle light-gray grid, Times-like serif typography, no dashboard cards, no decorative title, no shadows.
At very top clearly print "LAYOUT MOCKUP — NOT EXPERIMENTAL RESULTS".
Upper 65%: one large plot headed "(a) Online reconstruction". Horizontal axis exact text "Mapping iterations (×10³)". Vertical axis exact text "Evaluation PSNR (dB) ↑". Illustrative ticks x 0, 1, 2, 3 and y 10, 15, 20, 25. Two hypothetical gently irregular rising curves, no invented error bars: teal solid labeled "Ours", rust-orange dashed labeled "VIGS-SLAM". Both start near same low PSNR; teal improves earlier then levels off, orange reaches a common quality later. Keep plausible small local fluctuations, not mathematically perfect exponential functions.
A thin gray horizontal dashed target near 22 dB, labeled "Target quality". Place hollow circle markers where EACH curve first crosses target: teal at about x1.4 and rust at about x2.4. Vertical gray dotted projection lines descend from those two crossings to x axis. A black double-headed horizontal arrow between their x positions just above the target line, labeled "Fewer iterations". Absolutely NO numerical speedup or percentage.
A separate small marker on the x axis at x1.0 labeled "k*" identifies the common intermediate checkpoint used for BOTH images below. Do not confuse this checkpoint with the two target crossings.
Lower 30%: centered section label "(b) Same iteration k*". Three equal landscape image panels side by side, labels "VIGS-SLAM", "Ours", "Ground truth". Within each panel show the SAME simple schematic indoor tabletop scene from IDENTICAL camera position: beige wall, framed patterned poster, table edge, a small blue object. These are visibly illustrative stylized image placeholders, not photorealistic claimed experimental outputs. Baseline placeholder has softer pattern, Ours clearer pattern, GT crisp reference. No different objects across panels. Place tiny text "illustrative crop" within each panel.
Below everything a small legible line "Curves: fixed held-out views over the full trajectory. Crops: one example view."
Maintain enough whitespace, perfectly legible plot labels, appropriate bold/regular hierarchy. This is a concrete composition proposal, not a poster. No caption paragraph, no claims of measured superiority, no institution logos.
