# Carve 보조 설명 제거 — 2026-09-21

- 사용자 요청으로 `Verified keyframe depth`, `Uncertainty`, `D`를 삭제했다.
- 관련 Carve 입력 가지, 내부 depth 연결선, uncertainty leader 및 band, 파란 depth 점선을 제거했다.
- 표면 앞 공간, Gaussian의 opacity 감소(`α ↓`), `Penalize free-space opacity` 설명과 Map objective로의 연결은 유지했다.
- 삭제한 하단 설명 행의 공간을 고려해 내부 도식을 8-unit 아래로 옮기고, opacity 설명을 앞쪽 Gaussian 세 개의 중심에 맞췄다.
- 이번 변경은 overview의 설명량 축소다. 본문의 verified depth, surface-depth posterior, safety margin 또는 손실 구현은 변경하지 않았다.
- 이전 source와 출력은 `archive/before_carve_label_simplification_2026-09-21/`에 보존했다.

검수: PDF 확대 렌더 확인, word bbox 중첩/페이지 밖 텍스트 0개, 삭제 문구 부재, 내장 이미지 동일성 및 원고 PDF 일치 확인.
