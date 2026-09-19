# Overview 화살표만 정리

## 고정한 요소

사용자가 승인한 사진·글자·전체 배치를 유지한다. C07 cutaway, C10 modality, trajectory A, Times New Roman, 3열 구조, count/probability는 수정하지 않는다. 기존 build_overview_v02.py만 diff로 수정하고 extractor·원본 지도는 건드리지 않는다.

## 수정한 연결

- 초기화 선은 Shared Gaussian map 제목을 통과하지 않고 지도 왼쪽으로 진입한다. 지도 이미지의 실제 `meet` 표시 영역을 계산해 양쪽 화살촉을 같은 높이, 이미지에서 4단위 떨어진 위치로 맞춘다.
- RGB stream→growth의 불필요한 작은 꺾임을 없앤다. 초기화 선과 교차하는 위치, 완료 update 선과 교차하는 위치에는 작은 비연결 간격을 둔다.
- Frontend→depth/normal의 두 갈래는 각 라벨 중앙에 화살촉이 보이게 맞춘다. 이전처럼 라벨 배경 뒤에 화살촉이 가려지지 않도록 한다.
- Selected camera/RGB와 prior의 세로 경로를 분리한다. RGB가 prior 선을 가로지르는 곳은 prior 선에 틈을 둬 실제 분기와 구별한다.
- Render→RGB/depth는 아래 공통 분기선으로 정렬한다. Depth→normal은 이미지 측면 중앙끼리 연결한다.
- Normal→base 입력과 base→objective 출력은 서로 교차하지 않는 경로를 사용한다. Ray→objective와 base→objective의 병렬 합류 관계를 유지한다.
- Completed updates는 update 선에 분기점을 표시해 되돌아간다. Ray 입력 화살표는 Verified keyframe depth 문구를 침범하지 않고 패널 가장자리에서 끝난다.
- 화살촉은 동일한 9×9 벡터 삼각형으로 직접 그린다. PDF 변환 시 marker와 shaft 끝이 어긋나는 작은 돌출을 막기 위해 선 끝을 화살촉 내부까지 줄인다.

## 검수와 보존

- PDF를 원래 SVG 좌표의 3배 해상도로 확대 렌더링했다. frontend, initialization, map_update, sampling, loss_routes의 수정 전후 10개 crop은 `production/qa/arrows/`에 저장한다.
- Crop과 전체 PDF 재렌더 이미지를 직접 확인한 후 화살촉의 미세한 돌출까지 재수정했다.
- SVG 비교에서 text 92개, image 25개, rect 163개, ellipse 8개의 속성·내용·좌표가 이전과 동일함을 검증했다. 화살표 선·화살촉·update 분기점만 바꿨다.
- 이전 SVG/PDF/PNG와 builder는 `production/archive/before_arrow_cleanup/`에 보존했다.
- PDF font embedding과 SVG parse/export 성공. 본문 TeX compile·실물 인쇄는 이번 범위에 포함하지 않는다.
