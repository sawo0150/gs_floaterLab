# Overall pipeline v03 수정 프롬프트

- 내장 imagegen 편집, 입력 `overall_pipeline_v02.png`.
- v02에서 depth가 orange 영역 뒤로 통과하는 시각적 모호성이 남아 경로만 바깥으로 이동 요청. 사라진 randomness label도 복원 요청.

```text
Make ONLY two tiny corrections to this diagram, preserve every other element and its position.
1. Re-route the gray "Verified depth evidence" connector. Currently its vertical part at x approximately 350 runs THROUGH the orange View Growth box (x320 to690). ERASE that full old vertical segment. The new path must be: start from the bottom-left of Online frontend at (354,162), move down to (354,215), turn LEFT to (294,215), turn DOWN to (294,720), then RIGHT along the existing bottom horizontal line into the purple Geometry Constraints box. This places the vertical depth line IN THE WHITE GAP to the LEFT of the orange View Growth box. It must NEVER enter or overlap the orange box or its white inner panel. At its crossing with the short orange horizontal input arrow near y383 use a small bridge hump, NOT a connection dot. Coordinates are approximate for the provided 1860x846 image: preserve proportions. Keep the existing "Verified depth evidence" label near the bottom horizontal line.
2. In the blue View Sampling box replace the italic text "Selection probability" with "Counts + randomness". Keep n=12,n=3,n=7 and the qualitative Lower/Higher/Medium labels and circle sizes unchanged.
Do not modify ANY other arrows, labels, nodes, map image, or layout.
```
