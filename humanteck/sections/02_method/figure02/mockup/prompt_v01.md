# Imagegen 구조 시안 v01

Built-in image_gen 사용. 실험 결과가 아닌 구조 검토용. 동일한 가상 장면을 세 열에 동일 품질로 반복하여 가짜 성능 차이를 만들지 않도록 요청한다.

```text
Use case: scientific-educational.
Asset type: layout-only mockup for a single-column robotics paper Figure 2, not experimental evidence.
Create an elegant compact academic qualitative comparison figure on pure white, landscape aspect approximately 1.5:1. Three equal columns with exact headings "VIGS-SLAM", "Ours", "Ground truth" in Times New Roman-style serif, black text, Ours bold. One scene only: a generic indoor laboratory tabletop with small labelled storage drawers, a monitor frame, and a desk edge. Top row: the SAME invented photograph repeated in all three columns at IDENTICAL image quality, viewpoint and exposure. Do NOT synthesize an improvement in Ours, do NOT artificially blur the baseline. This is a layout test, so all three are matching neutral placeholders, not method results. Place one thin amber rectangular region of interest at exactly the same location in every full image, around a group of storage drawers with fine edges. Below each full image, aligned to the same column, place a substantially enlarged view of that exact selected region. Three enlarged patches all use the same amber thin border. Large enough patches, very tight consistent white gutters, no arrows, no shadows, no rounded cards, no charts, no scores. Crops must correspond to the selected region, keep the scene and details identical in all three columns. Small serif label "Full view" above the top row and "Detail" above lower row, only once each, unobtrusive. Overall scholarly understated design inspired by full-image plus matching-detail grids such as MonoGS Figure 4 and Photo-SLAM Figure 6; do not copy their actual photos. At the bottom include the clearly readable disclaimer "Layout mockup - not experimental results". Do not include a fake caption with claims, PSNR, improvement labels or extra text.
```

