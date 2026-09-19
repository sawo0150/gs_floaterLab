# Overall pipeline v01 생성 프롬프트

- 날짜: 2026-09-19
- 실행 방식: 내장 imagegen 도구. CLI/API fallback 미사용.
- 목적: 휴먼테크 2번 절의 배치 검토용 원본 개념도. 실험 결과 아님.
- 원문 도판은 구조 분석에만 참고하며 입력 이미지로 복제하지 않는다.
- 생성 결과와 검토 상태는 생성 후 별도 QA 기록에 남긴다.

## 실제 전달 프롬프트

```text
Use case: infographic-diagram
Asset type: rough overall-pipeline concept figure for the Method section of a two-page HumanTech extended abstract about online 3D Gaussian Splatting mapping.
Create one original, clean academic diagram, wide landscape around 2.2:1 aspect ratio, white background, crisp flat vector-like rendering, restrained thin lines, generous but efficient spacing, readable black sans-serif text. This is an illustrative concept, NOT experimental evidence. No photographic reconstruction, no numerical performance claims, no logo or institutional branding, no decorative title banner.

Core story: admit arrived training views according to completed mapping work; sample under-selected views stochastically; apply depth-supported ray-space constraints during Gaussian map optimization. Three contribution modules, marked (a), (b), (c). Existing frontend and map initialization are gray supporting infrastructure, NOT novel contributions.

Composition:
Upper narrow support band: at far left a small stack of simple image thumbnails labeled "RGB + IMU stream"; arrow to gray box "Online frontend" with smaller text "Pose + depth". Arrow to gray box "Gaussian initialization", then arrow to the one shared state at upper right labeled "Gaussian map". Represent map with a small schematic room corner made of colored Gaussian ellipses, explicitly illustrative, not a photo.

Main middle learning path, reading left to right:
A branch labeled "Arrived RGB views" from the input, showing 5 simple view thumbnails; only already arrived frames, not future frames.
Orange module "(a) View Growth", subtitle "When to include views". Inside, show a few admitted thumbnails and a few waiting thumbnails separated by a gate. A small label "Completed updates" supplies this gate from a dashed feedback arrow from the mapping update. Growth controls admission, NOT Gaussian densification. The module's output is a stack labeled "Training-view pool"; previous admitted views remain.
Blue module "(b) View Sampling", subtitle "Which views to revisit". Show three thumbnails with unequal small count bars, with a lower count receiving a larger selection-probability marker. Text "Counts + randomness". Output two different selected thumbnails labeled "Selected views". Do NOT draw deterministic lowest-count-only selection.
Then gray box "Mapping update" with small inner text "Render + optimize" and "Appearance loss". Arrows from selected views and the shared Gaussian map into Mapping update; arrow from Mapping update back into the SAME Gaussian map. Not two disconnected maps. The map supports rendering, and the update modifies the map.

Lower-right purple module "(c) Geometry Constraints", subtitle "Where opacity belongs", positioned UNDER the mapping update rather than in series after sampling. A separate line from frontend "Pose + depth" to this module labeled "Verified depth evidence". Inside show a horizontal camera ray, light empty region in front, a softly shaded surface-depth band, several semi-transparent Gaussian ellipses along the ray: a small red ellipse in known free space and green ellipses near the surface band. Short labels "Free space" and "Surface evidence". The module sends a purple arrow labeled "Geometry loss" UP into Mapping update. This is a soft optimization loss, not a post-hoc eraser, hard pruning, or depth sensor. No Carve/Hit formula or fixed choice of an unfinished loss variant.
Use a thin auxiliary connector from Gaussian map to geometry module representing current ray opacity if it can be routed clearly.

Feedback:
A dashed orange arrow from Mapping update back to (a), labeled "Completed updates".
A separate short dashed blue arrow from the Selected views output back to (b), labeled "Selection counts".
All feedback lines routed in clear outside corridors, no lines through text and no unintended arrow junctions. Solid lines mean data or loss input; dashed lines mean scheduling feedback. Tiny legend at bottom: "Solid: data / supervision   Dashed: scheduling feedback".
At bottom right a small note "Concept sketch - not experimental results".

Text should be legible and correctly spelled. Keep exact module titles above, no long paragraphs, no full equations, no fabricated PSNR or convergence curves, no claims of proven faster convergence or floater-free output. Do not copy any source paper's artwork. The figure must visibly distinguish view admission and sampling from the geometric objective inside map optimization.
```
