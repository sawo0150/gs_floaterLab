# v12: frontend 출력선 국소 교정

Imagegen 스킬 / 내장 편집. 입력 `overall_pipeline_v11.png`. Depth/normal 이미지와 나머지 영역은 유지하고, frontend 분기선의 단절과 normal에 잘못 붙은 기존 depth 출력선을 교정한다.

```text
Use case: precise-object-edit. Image 1 is the edit target.
Keep the ENTIRE figure unchanged except the few GRAY CONNECTOR LINES in the lower-left "Online observations" panel. Preserve the new Keyframe depth and Keyframe normal thumbnails, labels, sizes, their shared scene, the Poses row, every middle and right region, every sampling number, all typography and canvas.
Fix these three small connector details only:
1. The existing horizontal bracket directly ABOVE the Keyframe depth and Keyframe normal labels currently floats disconnected. Join its LEFT END visibly to the BOTTOM EDGE of the Online frontend box. It must branch to TWO downward arrowheads above the depth and normal thumbnails. This is a fork from Online frontend to both outputs.
2. Remove the old separate gray vertical arrow that runs down the far left of the depth thumbnail. The new connected top fork replaces it. There must be exactly one frontend output arrow per thumbnail.
3. Remove the short horizontal outgoing gray line at the RIGHT EDGE of the Keyframe normal thumbnail. The tall gray connector just outside the left panel must NOT originate from normal. Connect that tall connector instead to the BOTTOM EDGE of the Keyframe depth thumbnail using a thin gray elbow: down from depth, then right in the narrow empty strip BELOW BOTH thumbnails but above the lower blue panel boundary, then up to join the existing tall gray connector. It must not touch the normal thumbnail or either label. No new words or labels.
Nothing else changes. Do not redraw any scenes, bars or losses. Output the same full-width overview.
```
