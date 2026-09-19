# v11: Online observations에 keyframe normal 추가

Imagegen 스킬 / 내장 imagegen 편집. 입력: `overall_pipeline_v10.png`. 왼쪽 frontend 아래에 Keyframe depth와 Keyframe normal을 동등한 크기로 병렬 배치한다. Poses는 유지한다. Sampling 예시와 오른쪽 loss 설계는 변경하지 않는다.

두 thumbnail은 동일 장면·시점을 의도한 설명용 생성 이미지이며 실제 추정 결과가 아니다. Frontend-side keyframe prior로 표시하며 normal의 추정 알고리즘을 새로 정의하지 않는다. Backend에서는 tracking packet의 depth와 normals를 함께 Camera 초기화에 전달하는 기존 구조를 확인했다 (`vigs/gs_backend.py:6256`).

```text
Use case: precise-object-edit.
Input image 1 is the EDIT TARGET, our current wide academic overview.
Change ONLY the lower portion of the LEFTMOST light-blue "Online observations" territory, below the Online frontend / Poses row. The requested change is to display BOTH keyframe geometry outputs.

Keep the Online frontend box, its incoming image arrow and Poses output exactly where they are. Replace the single large Keyframe depth thumbnail below it with TWO equal-sized adjacent thumbnails:
- LEFT: label exactly "Keyframe depth", with the existing false-color depth image, resized to fit.
- RIGHT: label exactly "Keyframe normal", with a surface-normal color image of the EXACT same room, camera viewpoint, furniture silhouettes and crop as that depth thumbnail. Normal-map colors should be conventional lavender, pink, cyan and blue with coherent planar regions, NOT another rainbow depth map or an RGB photo.
Fit both compact thumbnails neatly inside the left panel, at the same vertical level, aligned with matching margins. Their labels are just above each image, clear and unclipped. Do not overflow into the middle panel.
From the bottom edge of "Online frontend", use a tidy thin gray branching connector with two arrowheads, one to each keyframe thumbnail, showing both as frontend-side keyframe priors. Do not connect depth and normal in a serial chain, and do not imply normal comes from the selected intermediate view. Preserve the existing outgoing depth-evidence connector attached to the DEPTH thumbnail only; do not make the normal thumbnail feed the verified-depth-only path.

Everything OUTSIDE this small left-panel edit must remain unchanged: camera trajectory, five input frames and K/I badges; ALL View Growth snapshots; ALL sampling values 12,9,6,3,0 and 10%,14%,18%,25%,33%, admission-order annotations and selected I2; the entire right optimization map, RGB/depth/normal outputs, base supervision and ray-space geometry diagram; all headings, colors, typography, footer and canvas dimensions. Do not fix or redesign other areas. No new modules, equations, claims or sensor-GT labels. Preserve the existing clean academic overview style. Output the full wide overview, not a cropped panel.
```
