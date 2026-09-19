# Overall pipeline v02 수정 프롬프트

- 방식: 내장 imagegen의 기존 이미지 편집.
- 입력: `overall_pipeline_v01.png`.
- 이유: v01에서 frontend depth가 Growth를 경유하고, RGB→geometry 경로가 추가되었으며, 일부 피드백이 양방향으로 보였다. 임의 p 수치도 exact sampling 식과 혼동될 수 있어 제거한다.
- 전체 배치는 유지하며 아래 연결과 label만 수정 요청.

```text
Edit this existing academic pipeline concept image. Preserve the overall layout, all three colored contribution modules, room illustration, typography, white background and major labels. Only correct wiring and illustrative probability labels:
1. Remove the gray downward connection from Online frontend into the top of (a) View Growth. Remove the entire gray line from the bottom of View Growth to Geometry Constraints. Instead route ONE gray line labeled "Verified depth evidence" from the bottom of Online frontend, down a clear vertical corridor BETWEEN Arrived RGB views and View Growth (left of the orange module), then right through the open bottom corridor into the left side of (c) Geometry Constraints. It must bypass every orange box, not touch or cross them. This represents direct frontend depth evidence.
2. Remove the extra long gray line from the bottom of Arrived RGB views into Geometry Constraints completely. RGB views should only connect to View Growth.
3. Rightmost map-update loop: retain the existing downward arrow from Gaussian map into Mapping update. The outer return path must start at the RIGHT edge of Mapping update with NO arrowhead at that edge, travel right then up, and end with ONE arrowhead pointing LEFT into Gaussian map. Label this return path "Map parameter update", not "Updated Gaussian map". Do not draw a bidirectional outer line.
4. Blue dashed Selection counts feedback: start from bottom edge of Selected views with NO arrowhead there, route down then left, and end with ONE upward arrowhead into the bottom of View Sampling. Keep orange Completed updates feedback as it is.
5. In View Sampling retain example counts n = 12, n = 3, n = 7 and different circle sizes, but remove ALL numerical p values. Replace the three p labels with "Lower", "Higher", "Medium" respectively; add one small common label "Selection probability". These are qualitative illustrations, not exact sampled probabilities.
6. Keep the purple Current ray opacity connection from Gaussian map to Geometry Constraints, and the Geometry loss arrow from Geometry Constraints into Mapping update.
No extra nodes, performance numbers or claims. Retain the bottom note "Concept sketch - not experimental results". Do not change the existing figure's composition or rewrite other text. All connectors must have unambiguous direction.
```
