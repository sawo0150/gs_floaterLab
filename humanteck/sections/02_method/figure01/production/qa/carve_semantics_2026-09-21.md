# Fig. 1 용어 및 Carve 도식 정리 — 2026-09-21

## 용어 확인

- `Penalize free-space opacity` 및 free-space/opacity/penalize 조합을 검색했으나, 정확한 문구가 널리 정착된 명칭이라는 근거는 확인하지 못했다. 검색 결과 부재를 용례가 전혀 없다는 증거로 해석하지 않는다.
- [StableGS, §3.2.1](https://arxiv.org/html/2503.18458v1)은 free space의 translucent Gaussian과 opacity를 논의한다. 이는 개별 개념의 용례이며 우리 Carve와 동일한 손실이거나 이 문구의 선행 용례라는 뜻은 아니다.
- 따라서 loss 제목은 `Free-Space Carve Loss`를 유지하고 `Penalize free-space opacity`는 그 작용을 설명하는 일반 문장으로 사용한다.
- frontend → map: `Gaussian initialization`. 선택 뷰 → Render: `Camera pose`.

## 도식 변경

- Depth/normal → Base 경로와 depth → Carve 경로를 분리. Normal 및 Base 선과의 교차는 gap으로 표시해 junction과 구별했다.
- 검증된 keyframe depth라는 원고 의미를 유지하면서 라벨을 `Verified depth`로 축약했다.
- 관측 깊이 D, ray endpoint, 표면의 교차 위치를 같은 x 좌표에 정렬했다.
- 표면 주변에는 양끝이 옅어지는 depth uncertainty band와 `Uncertainty` 라벨을 표시했다. 특정 수식의 hard cutoff나 표면에서의 zero penalty를 주장하지 않는다.
- Free-space 범위의 양방향 화살촉을 없애고 끝표시가 있는 구간선으로 변경했다.
- 앞쪽 Gaussian 세 개를 같은 붉은 계열과 옅은 opacity로 표현하고 각각 `α ↓`를 표시했다. Gaussian 위치 이동을 지시하던 독립 화살표는 제거했다.
- `Penalize free-space opacity`와 `Uncertainty`의 설명 행을 정렬하고 기호와의 간격을 확보했다.

## 검수 및 범위

- Inkscape SVG → PDF/PNG 생성, Poppler PDF 전체 및 loss 영역 확대 렌더 확인.
- Poppler word bbox: 0.25pt 초과 가로·세로 동시 중첩 0쌍, 페이지 밖 단어 0개.
- PDF 폰트 전부 embedded. 원고용 PDF와 production PDF 바이트 일치.
- 이전 SVG와 내장 이미지 25개의 바이트·순서 동일. 자산 provenance hash는 builder에서 검증.
- Python AST / SVG XML parse 통과. 전체 180×75.37mm 및 기존 제목 위계 유지.
- 직전 결과는 `archive/before_carve_semantics_2026-09-21/`에 보존.
- 원본 지도·렌더 asset·학습·손실 구현은 변경하지 않았다. 실제 예시 run은 Carve OFF이며 opacity 감소 표현은 방법 설명용 도식이다. 전체 원고 컴파일 및 인쇄 검수는 수행하지 않았다.
