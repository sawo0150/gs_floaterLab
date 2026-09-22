# HumanTeck 곡선 도판 (a)/(b) 분리 — 2026-09-22

신규 학습·GPU 평가 없이 기존 실측 데이터의 도판 배치만 수정했다.

- 현행: `humanteck/sections/02_method/figure03/current/fig3.{svg,pdf,png}`.
- 원고 번호 Fig.2, label `fig:photometric_convergence` 유지.
- (a): table_06 고정 held-out 555뷰 평균, 각 방법 14개 측정점.
  19–26.5 dB는 280 SVG units, 14–19 dB는 50 units로 표시한다.
  19 dB 경계의 물결 두 줄과 캡션으로 축척 변경을 명시한다.
  각 구간은 선형이며 측정값 삭제·smoothing 없음.
- (b): frame1420, 1400 mapping iterations의 VIGS-SLAM/Ours/Ground truth.
  전체 화면 위에 동일 ROI=(440,40,564,164) 확대를 겹쳐 배치한다.
  원본 PNG를 그대로 내장하며 pixel enhancement 없음.
- Baseline #000000, Ours #0057FF. 기존 SVG 폭·물리 폭·글자 크기 유지.
  출력 크기 121.08×73.51 mm, 원고 단 폭에서 약86.49×52.51 mm.
  그래프 자체 높이는 1020→360 SVG units로 축소했다.
  세로축 제목은 같은 글자 크기의 `PSNR (dB) ↑`로 줄여 잘림을 해결했다.
- 최초 도달 비교 1400↔2400 / 1000 fewer iter.* 유지.
  지속 도달·wall-clock 가속을 뜻하지 않는다.
- 실제 PDF의 고해상도·단 폭 PNG 확인, 28개 SVG 좌표 역변환과 원본 이미지
  hash 확인, 원고 PDF 두 파일과 current 일치, 캡션 및 BibTeX 키 확인 완료.
  전체 원고 컴파일은 수행하지 않았다.
- 직전 current·스크립트·원고는 `figure03/archive/before_ab_layout_20260922_113456/`에 보존.
- 제작: `figure03/scripts/build_selected_B.py`, 검수: `output/qa/fig3_ab_compressed_axis_validation.json`.

## 후속: 왼쪽 패널 문자·사진 아래 checkpoint 표기

- 사용자 요청대로 (a)/(b)를 각 패널 왼쪽으로, 방법명을 사진 아래로 옮겼다.
- 3DGS-LM Fig.1과 Turbo-GS v1 Fig.1의 실제 페이지를 확인했다. 이미지에 학습량을
  직접 표기하는 방식을 참고해 Baseline/Ours 아래 각각 `1,400 iter.`를 넣었다.
  Ground truth에는 iteration 없음. 그래프에는1.4k tick·세로 점선·두 측정점 표시.
- 글자 크기·색·ROI·모든 원본 측정값·도판 크기 유지. PDF 고해상도·단 폭 검수,
  current/원고 asset 및 캡션 동기화. 신규 학습·GPU 평가 없음.
- 판단/출처: `figure03/analysis/checkpoint_label_review_2026-09-22.md`.
- 현행 검토 산출물 stem: `fig3_ab_left_labels`.
