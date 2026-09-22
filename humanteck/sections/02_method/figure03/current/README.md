# 현행 수렴 비교 — 원고 Fig.2

작업 폴더명 figure03 및 fig3.* 파일명은 유지한다.

- [PDF](fig3.pdf) / [미리보기](fig3.png) / [SVG](fig3.svg)
- [캡션](caption.md) / [출처·좌표](provenance.json)

2026-09-22: (a) PSNR 곡선과 (b) 렌더 비교를 상하 패널로 분리했다.
(a)/(b) 표기는 각 패널 왼쪽에, 방법명은 사진 아래에 둔다.
사진 아래에 VIGS-SLAM (1.4k), Ours (1.4k), Ground truth를 각각 한 줄로 적는다.
괄호는 mapping iteration이며 1.4k는 1,400회를 뜻한다.
이번 색상 변경에서는 원고 캡션 문구를 유지하고 current/ 및 생성 스크립트에 동기화했다.
(a)의 1.4k tick·중립 점선·두 측정점 원형 표시로 (b)의 checkpoint를 연결한다.
(a)는 RPNG table_06의 고정 held-out 555뷰 평균, 각 방법 14개 원본 측정점이다.
19 dB 이상은 넓게, 14–19 dB는 얇은 구간에 압축하며 물결 두 줄로 축척 변화를 표시한다.
값을 생략하거나 smoothing하지 않는다. 최초 도달 비교는 Ours 1400 / baseline 2400이다.
(b)는 frame1420의 1400 iteration: VIGS-SLAM / Ours / Ground truth 순서다.
전체 화면에 동일 ROI=(440,40,564,164)를 표시하고 같은 영역을 확대한다.
원본 PNG를 그대로 SVG에 내장하며 색상/선명도 보정은 없다.
Baseline은 검정(#000000), Ours는 선명한 파랑(#0057FF), GT는 주황(#E66100)이다.
2026-09-22 색상 변경: GT 글자·ROI 테두리·확대 테두리·연결선에 주황을 적용했다.
직전 버전과 SVG 폭·물리 폭·글자 크기·모든 내부 도형 좌표를 유지한다.
페이지 위아래 여백만 잘라 viewBox를 0 17 2100 1194로 변경했다.
단 폭 삽입 높이는 약49.17mm로 이전52.51mm보다6.35% 줄었다.

재생성(워크스페이스 루트에서):
`python3 humanteck/sections/02_method/figure03/scripts/build_selected_B.py`
기본 실행은 output/에 검토본만 생성한다. PDF를 PNG로 렌더링하여 검수한 뒤
`--install`로 current/ 및 원고 PDF 두 파일·캡션을 동기화한다.
설치 시 원고 캡션을 스크립트 CAPTION으로 갱신하므로 캡션 수정도 함께 반영해야 한다.
표기 참고: analysis/checkpoint_label_review_2026-09-22.md (3DGS-LM / Turbo-GS 실제 figure).
전체 원고 컴파일·인쇄는 별도다. 이전 버전은 archive/ 및 output/에 보존한다.
