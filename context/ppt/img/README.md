# img/ — PPT 시각자료 폴더

`build_ppt.py`는 이 폴더의 이미지를 슬라이드에 삽입할 수 있도록 설계돼 있으나,
현재 각 슬라이드의 `[시각자료]` 항목은 대부분 "제작 필요" 상태라 텍스트 안내 박스로만 들어가 있다.

## 여기에 넣을 이미지 (ppt_outline 의 "제작 필요 시각화" 목록)

1. 라벨 floater 하이라이트 렌더 (원본 위 빨강)
2. 사면체 확장 단계별 3D 뷰 (라벨 점 → 사면체 → 채택 영역)
3. region 영역 오버레이 (방 전경 위 반투명)
4. ray 커버리지 히트맵 (높이별 ray 밀도)
5. carve score / φ 거리장 단면 히트맵
6. SLAM vs depth 앵커 점군 비교 (`data/scenes/301_305/depth_anchors.npz`)
7. Huber 보정 산점도 (D vs z_SLAM)
8. PPM 확률맵 (Sobel vs ConvNeXt)
9. 렌더 A/B (exp30r vs exp40b 등 — 슬라이드별 데이터 소스 참조)
10. 세 장면 대표 이미지 (1253 고텍스처 / 305 저텍스처 / 12F fog)

## 삽입 방법

이미지를 만들어 이 폴더에 두고, `build_ppt.py`의 슬라이드별 이미지 매핑을 추가하면
해당 슬라이드에 자동 삽입된다 (현재는 매핑 미설정 — 텍스트 안내만).
파일을 채운 뒤 `python build_ppt.py` 재실행 → `soffice --headless --convert-to pdf` 로 갱신.
