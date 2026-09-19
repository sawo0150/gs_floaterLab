# v06 세부 시각화 재설계 프롬프트

내장 imagegen 편집. 입력 [v05](overall_pipeline_v05.png)의 3영역 구조와 스타일을 유지하고 내부 표현을 재설계한다. 조사 근거: [7개 논문 도판 분석](../plan/04_detail_visualization_literature_2026-09-19.md).

```text
Use case: infographic-diagram. Edit the provided scientific figure into a substantially clearer v06. Preserve ONLY its three functional territories and polished academic illustration style; redesign their contents according to the specification below. Keep headers exactly "Online observations", "Training-view management", "Gaussian map optimization". Wide landscape about 2.1:1, high resolution, opaque white, restrained very pale territory washes, clean margins, concise readable typography. No title banner. Dense but uncluttered scientific plate, not a business flowchart. Territory widths 23%, 41%, 36%. Gaussian map should be smaller than in input to make room for actual loss explanation.

PRIORITY 1 — frame identity:
LEFT: a short five-camera trajectory above a chronological strip of FIVE consistent illustrative indoor-room images. Badges exactly K1, I2, K3, I4, K5, in order. K badges dark gray, I badges teal. Small key: "K: keyframe   I: intermediate". Both kinds remain visibly in use throughout figure; never remove badges in the pool or sampling outputs. A bracket under ALL FIVE images labelled "Arrived views" leads to middle. Below left strip, one modest gray "Online frontend" block produces "Poses" and a small colored "Keyframe depth" tile. Initialization via thin gray top route into shared Gaussian map; depth via thin gray bottom route to geometry supervision. No depth sensor.

PRIORITY 2 — growing retained pool, not sliding window:
MIDDLE upper half headed orange "(a) View Growth". THREE left-aligned successive pool rows use the same thumbnail identities and order:
row 1 label "S": exactly K1, I2, K3.
row 2 label "S + κ": exactly K1, I2, K3, I4.
row 3 label "S + 2κ": exactly K1, I2, K3, I4, K5.
Same-sized thumbnails aligned in columns. Added I4 in row2 and K5 in row3 alone receive orange outer outlines. The old images remain in every subsequent row. Thin downward arrow at left labelled "Completed updates". Above rows one short phrase "Retain old views; admit arrived views". No empty slots representing future frames. This is a schematic example, not data.
The THIRD row is the current training pool and directly connects to sampling below; do NOT create a different unexplained pool.

PRIORITY 3 — sampling means history -> probability -> random outcome:
MIDDLE lower half headed blue "(b) View Sampling".
Below the five columns of the final pool row, place two aligned five-bar mini strips. First strip labeled "Selection counts": gray bars heights HIGH, LOW, HIGH, LOWEST, MEDIUM in column order K1 I2 K3 I4 K5.
Second strip labeled "Sampling probabilities": blue bars heights LOW, HIGH, LOW, HIGHEST, MEDIUM in the SAME order. All five blue bars nonzero. No numeric probabilities needed. Show small arrows from counts to probabilities. Selection is not simply argmax: highlight I2 and K5 with blue outline and connect COPIES into a compact two-image output queue labelled "Sample without replacement", with small subtitle "One view per update". Originals remain in pool. Badges I2 and K5 visible in queue. A tiny blue return arrow from this selection to count-strip is labelled "Selection history". Main outgoing arrow to observed RGB in right territory, not rendered RGB.

PRIORITY 4 — losses show WHAT is constrained, and merge:
RIGHT top about 28% of territory height: compact attractive isometric room from translucent Gaussian ellipses, labelled "Shared Gaussian map". Not a giant dollhouse dominating whole figure.
RIGHT middle: "Appearance supervision" with a pair of SAME-view room thumbnails, labels "Observed RGB" and "Rendered RGB". Each has the same small corresponding-pixel crop marker. The selected-view route enters Observed RGB; a gray arrow from the map enters Rendered RGB with label "Render". Both images have inward arrows to a small junction beneath them labelled "RGB loss".
RIGHT bottom: violet heading "(c) Geometry supervision". Draw an explanatory camera ray with several Gaussian ellipses and a vertical observed surface band. Align a simple ray-termination weight profile directly below on the SAME horizontal depth axis. Left of the surface shade pale red "Free space", and show a small unwanted early peak/ellipse highlighted red, labelled "Unwanted opacity". Around depth D, use a narrow violet "Surface evidence" band. The depth evidence route from frontend ends at D/band. Vertical axis label "Termination weight", horizontal "Depth". No target-matching KL formula, no fake before/after curve, no hard-pruning X marks. This is a diagram of what is supervised, not performance measurements. A violet output from this local ray comparison is labelled "Geometry loss".
Use a small common circular plus node at the far-right margin between appearance and geometry, label "Map loss". One gray arrow RGB loss -> Map loss, one violet arrow Geometry loss -> Map loss. From Map loss a single exterior upward arrow labelled "Update" returns into Shared Gaussian map. NEVER connect RGB loss down into Geometry supervision. NEVER route Rendered RGB directly to Update bypassing RGB loss. Both objectives act on the SAME map. Existing other mapping loss terms are abstracted; do not write a complete loss equation.
A single dashed orange "Completed updates" feedback from the UPDATE path routes around the top into (a), not from an arbitrary point on the room. Keep all routes continuous and avoid crossings; use little jumps when unavoidable. No spurious reciprocal arrowheads.

Text is important: spell "Rendered RGB", "Selection counts", "Sampling probabilities", "Intermediate" correctly. Do not invent extra labels or numeric experimental results. Footer exactly "Schematic examples — not experimental results". No copied paper artwork, no logos, no watermarks. Key scientific visual facts are BOTH K/I retained, pool 3->4->5, count/probability inverse relationship but stochastic selection, and two distinct supervision branches merged into one map update.
```
