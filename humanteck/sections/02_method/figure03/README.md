# Fig.3 작업 폴더 — 원고 Fig.2

**현행 결과는 [current/](current/README.md)에서 관리한다.**
[PNG](current/fig3.png) · [SVG](current/fig3.svg) · [PDF](current/fig3.pdf) · [캡션](current/caption.md)

2026-09-22 현행: (a) PSNR 곡선 / (b) VIGS-SLAM·Ours·Ground truth 전체 화면+확대.
RPNG table_06, frame1420, 1400 iteration을 사용한다. (a)의 19 dB 아래 축척은
물결 표시와 함께 압축하며 원본 측정값 28개를 모두 유지한다.
Baseline 검정 / Ours 선명한 파랑. 글자 크기는 직전 현행본과 같다.
페이지 위아래 빈 여백만 잘라 세로를6.35% 줄였다. 내부 좌표·크기·배치는 그대로다.
(a)/(b)는 왼쪽, 사진 아래에는 `VIGS-SLAM (1.4k)`, `Ours (1.4k)`를 한 줄로 적고
그래프의 1.4k tick·점선·측정점 표시로 이미지가 나온 checkpoint를 명시한다.
GT에는 iteration을 붙이지 않는다. [논문 figure 조사·표기 판단](analysis/checkpoint_label_review_2026-09-22.md).

## 작업 순서

1. `scripts/build_selected_B.py`의 배치·색·글자·CAPTION을 수정한다.
2. 워크스페이스 루트에서 `python3 humanteck/sections/02_method/figure03/scripts/build_selected_B.py` 실행.
3. `output/fig3_ab_page_trim.png`와 `output/qa/fig3_ab_page_trim_column.png`를 검수한다.
   원본 좌표·이미지 hash 검증도 스크립트가 수행한다.
4. 검수 후 `--install`로 current/ 및 원고의 두 PDF·캡션을 동기화한다.

원고는 `figure/convergece_comparasion.pdf`를 읽으며 `photometric_convergence.pdf`도
같은 내용으로 유지한다. label은 `fig:photometric_convergence`다.
스크립트 재생성은 원고 캡션을 덮어쓰므로 캡션 수정 시 CAPTION도 함께 갱신한다.
이전 버전은 archive/와 output/에 보존하며 선택되지 않은 시안은 current에 설치하지 않는다.

## 원본과 이력

- 실측 곡선: `results/figure03_scene_search_20260921/rpng/table_06/evaluation/curves.json` (워크스페이스 기준).
- 원본 이미지: `candidates/scene_search/table_06/frame_1420/`.
- [수평선 문헌 조사](analysis/peak_annotation_review/README.md).
- [장면 탐색](analysis/scene_search/README.md), [frame1420 선택](analysis/table06_revision/frame1420_selected.md).
- 최초 imagegen 배치 시안은 mockup/, 실측 결과는 output/, 검토 근거는 analysis/에 있다.
- 직전 current·스크립트·원고: `archive/before_ab_layout_20260922_113456/`.

원고 번호는 Fig.2지만 경로 연속성을 위해 figure03 및 current/fig3.* 이름을 유지한다.
