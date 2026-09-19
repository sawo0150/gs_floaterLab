# 승인된 v12 기준 재제작

## 사용자 결정

- 대표 장면/run: Aria 1253, exp94 `normalized_variance_s0`를 overview용 실제 자료로 사용 승인.
- v01 벡터 초안의 디자인은 폐기하지 않고 보존하되, 새 제작본의 기준으로 삼지 않는다.
- `overall_pipeline_v12.png`의 구성과 시각적 밀도를 따른다. 글꼴 변경 가능.
- GPU는 저장 지도에서 도판용 이미지를 렌더링하는 데만 사용 승인. 학습·지도 수정 없음.
- 추가 지시: 이후에는 새 Python 버전을 계속 만들지 않고 현재 `build_overview_v02.py`와 `extract_aria_assets.py`에 diff로 수정한다.

## 재제작 기준

1. v12의 약 26:38:36 열 비율, 옅은 cyan/peach/lavender 배경, 둥근 모서리, 진한 남색 제목을 복원한다.
2. 왼쪽은 카메라 궤적 → 실제 RGB filmstrip → frontend / poses → depth·normal 병렬 thumbnail을 유지한다.
3. 중앙은 3→4→5 view pool과 새 view 강조, 아래에는 selection counts / inverse sampling probabilities / selected-view thumbnail을 유지한다.
4. 오른쪽은 큰 실제 지도 시각화, RGB/depth/normal thumbnail, base supervision, 별도의 ray-space loss, objective와 update feedback을 유지한다.
5. v12의 생성된 방/지도/깊이/normal은 전부 실제 run 자산으로 교체한다. 카메라 아이콘·pool 단계·counts·ray 개념도만 schematic이다.
6. run의 causal carve는 꺼져 있다. 따라서 오른쪽 지도는 구조 설명용 실제 run 예시이지, 제안 ray loss 효과의 실험 증거가 아니다. 캡션에 이 차이를 명시한다.
7. 원본 RGB는 옆으로 누워 있다. 모든 영상 modality에 동일한 90도 표시 회전을 적용하며, normal RGB는 카메라 좌표값으로 유지한다. 원본/표시 회전과 데이터 provenance를 기록한다.

## 검수

- SVG → PDF → PNG 재렌더링 결과를 직접 확인한다.
- v12와 나란히 비교해 열 너비, 핵심 요소 위치, 이미지 크기, 색상, 빈 공간, 선 교차를 확인한다.
- 전체 그림과 확대 crop을 모두 확인한다. 새 결과를 이전 v12와 동일하다고 과장하지 않고 의도적인 차이를 기록한다.
- 원본 v12, v01 layout, 기존 TeX·실험 기록은 덮어쓰지 않는다.

## 실행 중 시각 확인과 수정

- v12와 v01을 실제 열어 비교했다. v01의 회색 큰 박스/빈 데이터 슬롯/텍스트 비중은 승인 디자인과 크게 달랐다.
- v02에서 v12의 배경·열 폭·사진 filmstrip·3단 pool·선택 이미지·ray inset을 복원했다. 글꼴은 사용자 변경 허용에 따라 Arial을 사용한다.
- 실제 run UID K1=229, I2=251, K3=284, I4=323, K5=353을 사용한다. 모두 mapping에 사용되었고 held-out이 아니며 K/I 역할을 archive와 대조했다. pool 단계와 count 자체는 설명용이다.
- RGB/선행 depth/normal/렌더 결과를 정방향으로 회전했다. 실제 RGB를 밝게 보정하거나 생성 이미지로 대체하지 않았다.
- 바깥 시점 6개를 시도했으나 관측되지 않은 뒷면과 퍼진 Gaussian이 지배해 구조 설명성이 낮았다. 최종은 K3 위치에서 시야각을 넓힌 정방향 내부 inspection render를 사용한다. Gaussian 제거, opacity/scale 수정 없음. 물체가 예쁘게 보이도록 기하를 조작하지 않았다.
- 1차 PDF 렌더에서 S+2κ 라벨 가림, 오른쪽 modality 라벨 충돌, sampling 설명과 history 겹침을 확인해 diff로 수정했다. 2차에서 map과 selected-camera 글자 간섭을 추가 수정했다.
- 원본 v12의 예쁜 방 cutaway는 생성된 개념 이미지다. 현재 실제 map 렌더로 그 미관까지 재현했다고 주장하지 않는다. 레이아웃은 가깝게 복원하되 데이터 품질의 차이는 그대로 남긴다.
