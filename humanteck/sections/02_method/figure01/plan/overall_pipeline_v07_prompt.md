# v07 일관성 검수 후 수정 프롬프트

내장 imagegen 편집. 입력 [v06](overall_pipeline_v06.png). 세부 기여 표현은 유지하고 영상 ID 일관성 및 feedback 경로를 정리한다.

```text
Edit this figure with ONLY a scientific consistency cleanup. Keep layout, three territories, colors, all subplot sizes, 3->4->5 pool snapshots, both count/probability bar rows, two-image queue, two supervision branches and Map loss merger exactly as they are. Do not add new modules.
1. Make frame identity visually consistent: the FINAL five-image pool row is the source of truth. Row1 must be identical COPIES of final-row K1,I2,K3 images, and row2 identical copies of final-row K1,I2,K3,I4. Keep badges K1,I2,K3,I4,K5 correct in all rows. Input filmstrip uses those same five thumbnail images. Queue uses exact I2 and K5 thumbnails. This is essential: same ID is same image across time.
2. Appearance Observed RGB and Rendered RGB must depict the SAME viewpoint and corresponding object layout as the selected I2 thumbnail. They compare prediction and observation of the same camera, not two different cameras. Keep arrows from both to RGB loss and RGB loss to Map loss. No changes to geometry loss merge.
3. Replace the TWO disconnected orange dashed feedback segments above map with ONE continuous dashed return path: start at the upward Update arrow, go up the RIGHT outer margin, run LEFT along a narrow corridor directly below the three main headers and ABOVE gray initialization line, then turn down to arrowhead at '(a) View Growth'. Label 'Completed updates' once. No feedback arrow into the map. No hidden segments behind the room.
4. Gray initialization top line must start from the Poses OUTPUT of Online frontend, not from a camera in the input trajectory. Run via an uncluttered gutter into the shared map. Remove the existing raw-camera-origin line. Input filmstrip bracket also needs a SHORT clear arrow into View Growth independently.
5. The blue Selection history arrow must start at the sampled queue and end at the gray Selection counts strip, not the probability labels. Exactly one arrowhead at counts. Keep original views retained.
6. Add a subtle short 'Ray detail' callout line from Shared Gaussian map to the geometry inset, so the plotted Gaussians are understood as that map's ray state. Do not connect the appearance loss into the geometry inset.
7. Remove duplicate 'Arrived views' text above filmstrip; keep it under the bracket only. Keep the clean white footer 'Schematic examples — not experimental results'. Preserve every other correct detail; no new equations, claimed metrics, invented data or extra text.
```
