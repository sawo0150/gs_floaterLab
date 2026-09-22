# Fig. 1 세로 높이 축소

- 변경 전: SVG 1815×870, 논문 크기 180×86.28 mm.
- 변경 후: SVG 1815×760, 논문 크기 180×75.37 mm.
- 높이 감소: 약 12.64% (10.91 mm). 가로세로비 2.09:1 → 2.39:1.
- 기존 `build_overview_v02.py`를 diff로 수정했으며 새 builder를 만들지 않았다.

## 유지 사항

세 모듈 구조, 모든 설명 문구와 Times New Roman 폰트 크기, 선택된 C07/C10/A 장면, K/I frame ID, 예시 count/probability 값은 유지한다. Gaussian 자산·원본 데이터·학습 상태를 수정하지 않는다. 이미지에 비균등 scale을 적용하지 않는다.

## 배치 조정

1. View Growth의 세 행 pitch를 100→88로 줄였다. 행 내 thumbnail은 같은 종횡비로 축소하고 badge 크기는 유지했다.
2. Frontend를 위로 당기고, `meet` 모드의 trajectory 슬롯에서 남는 세로 공간을 줄였다. Depth/normal pair도 같은 비율로 축소했다.
3. Shared map 슬롯 높이를 199→155로 줄이고 종횡비 유지 배치(`meet`)를 사용했다. 바뀐 실제 이미지 경계에 맞춰 initialization/update 화살표 endpoint를 다시 계산한다.
4. 오른쪽 Render, modality 이미지, base supervision과 ray-loss 블록을 위로 이동했다. Ray schematic 자체의 크기·기하 관계와 본문 글자 크기는 유지했다.
5. Sampling 그래프의 세로 간격과 막대 높이 스케일을 조정했지만 값 및 상대 비율은 그대로다. Count→probability 화살표가 33% 라벨에 닿는 초기 문제를 수정했다.
6. 하단 prior corridor는 패널 아래로 분리해 마지막 sampling 설명과 겹치지 않게 했다.

## 검수와 산출물

`current/overview.pdf`를 다시 PNG로 렌더링하여 전체 그림과 sampling/연결선 확대를 확인했다. 전후 비교판은 가로 폭을 동일하게 두고 원래 종횡비로 나란히 배치한다. PDF는 `HumanTeck_Song_s_intern/figure/overview.pdf`로도 복사하며 원고 fallback 경로를 현재 `figure01` 폴더에 맞췄다. 캡션과 Fig. 2는 변경하지 않았다.

직전 PDF·PNG·SVG 및 builder는 `archive/before_height_compaction/`에 보존한다. 원고 전체 컴파일을 대신하는 검수는 아니며 이번 작업에서는 그림 PDF의 배치만 검증한다.
