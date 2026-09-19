# v05 연결 검수 후 수정 프롬프트

내장 imagegen 편집. 입력: [v04](overall_pipeline_v04.png). 기능별 구성은 유지하고 데이터 흐름과 외곽 배경을 수정한다.

```text
Edit the supplied academic pipeline concept. Preserve the three-region composition, large shared Gaussian room, filmstrip, retained-view array, orange/blue/violet palette, readable labels, and typography. Correct ONLY scientific connection routing and the unfinished outer border/background. Keep all imagery illustrative.
1. Make the entire canvas opaque pure white outside the gently tinted regions. Remove any black speckles, ragged/transparent edge artifacts, heavy outer borders or vertical black seams. Regions should be borderless subtle washes, not thick framed cards.
2. Right territory: move the Observed RGB tile to the LEFT position, Rendered RGB tile to the RIGHT position. The blue arrow from 'One view per update' must feed Observed RGB, not Rendered RGB. Route map Render arrow to Rendered RGB. Put the label 'Appearance loss' between the tiles with two short inward arrows from the tiles to a small loss junction. From this junction draw a clear gray route labeled 'Appearance loss' into a compact circular node labeled 'Update' to the right of the image pair and beneath map. The existing violet Geometry loss arrow must feed the same Update node. From Update draw one arrow back into Shared Gaussian map. Thus both losses feed the update; the update changes the map. Do not draw a direct blue arrow into Rendered RGB.
3. Orange dashed 'Completed updates' feedback must START at Update node, route neatly outside the room map (above it in the top corridor), and end at the orange View Growth admission area. It must not start at the map or terminate in empty space. Keep separate from gray initialization route.
4. Gray top 'Geometry-based initialization' route must start at the frontend OUTPUT (near Poses), not from the raw camera trajectory. Route up via the left-side gutter and across the top into Shared Gaussian map.
5. In middle region add a discreet gray data arrow from the left filmstrip to the orange arrived-view pair. The two-view bracket arrow into the retained pool stays. Local selection history should return from the selected-view action to the blue probability bars (not point to selected images). Keep no numeric probabilities.
6. Preserve bottom keyframe depth route into geometry inset. Keep geometry supervision inside optimization, not postprocessing. Make ray in inset solid violet, so dashed orange feedback is visually distinct.
7. Footer exactly 'Illustrative concept — not experimental results', small but crisp dark gray on white, not overlapping border.
No extra panels, paragraphs, measurements, equations or performance claims. Retain balanced dense academic layout.
```
