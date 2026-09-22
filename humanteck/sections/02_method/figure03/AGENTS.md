# Fig.3 작업 규칙

사용자 요청: 현행 결과는 항상 `current/`에서 관리한다.

- 최종 선택·수정본을 완료할 때 `current/fig3.svg`, `current/fig3.pdf`,
  `current/fig3.png`, `current/caption.md`, `current/provenance.json`,
  `current/README.md`를 일치시킨다. 파일명은 유지한다.
- 사용자에게 전달하는 현행 링크는 `current/`를 우선한다.
- 대안·실험 시안은 `output/` 또는 `analysis/`에 두고, 선택되지 않은 안으로
  현행본을 자동 덮어쓰지 않는다. 과거 버전은 보존한다.
- 향후 제작 스크립트도 현행 파일 갱신을 포함한다. 현재 선택본은
  `scripts/build_selected_B.py`가 SVG/PDF/PNG/provenance 갱신을 수행한다.
- PDF 렌더링 확인 뒤 현행본을 갱신하고, 이미지·곡선의 원본 데이터와
  캡션의 비교 조건이 맞는지 확인한다.
- 현행 그림은 HumanTeck 원고의 **Fig.2**에 설치되어 있다. 작업 폴더명과
  `current/fig3.*`는 유지한다. 업데이트 시 원고의
  `humanteck/HumanTeck_Song_s_intern/figure/photometric_convergence.pdf`도 동기화한다.
  캡션은 원고 `paper.tex`의 `fig:photometric_convergence`와 `current/caption.md`를 일치시킨다.
- 현재 원고가 직접 읽는 파일명은 `figure/convergece_comparasion.pdf`다.
  이 파일과 기존 `photometric_convergence.pdf`를 모두 동일한 현행 PDF로 동기화한다.
- 2026-09-22 현행 배치: (a) 그래프 / (b) VIGS-SLAM·Ours·Ground truth 전체 화면+확대.
  Baseline 검정, Ours #0057FF. 19 dB 아래는 축척을 압축하고 물결로 표시한다.
  원본 28개 측정점과 글자 크기를 유지하며 축척 변경은 캡션에 명시한다.
- 생성 스크립트의 `CAPTION`과 원고·current 캡션을 함께 수정한다.
  기본 실행은 검토본 생성이며, PDF 렌더 검수 후 `--install`로 현행본에 반영한다.
- (a)/(b)는 각 패널 왼쪽에, 방법명은 사진 아래에 둔다.
  사진 아래에 `VIGS-SLAM (1.4k)`, `Ours (1.4k)`를 한 줄로 적고 GT에는 iteration을 붙이지 않는다.
  그래프의 1.4k tick·세로 점선·두 방법의 측정점 표시로 이미지 checkpoint를 연결한다.
- 2026-09-22 페이지 여백 최소화: 내부 도형의 좌표·크기는 유지하고 페이지 viewBox만
  `0 17 2100 1194`로 잘랐다. 재생성 시 페이지 crop을 유지하며 내부 재배치를 하지 않는다.
