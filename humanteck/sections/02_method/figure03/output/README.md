# Fig. 3 — 실제 PSNR 곡선 기반 3개 선택안

**현행 결과는 [../current/](../current/README.md)를 사용한다.** 이 폴더에는 버전별 출력·대안을 보존한다.

2026-09-21 최신: [반복 횟수 주석 확대 · 그래프 안쪽 배치](fig2_inplot_iteration_note.png).
1,000 fewer iter.*를 약38% 키우고 상단 비교 점선 아래로 옮겼다.
사진·곡선·연결선 및 나머지 글자의 위치와 크기는 유지했다.
최종 설치본은 current/이며, 아래 항목들은 이전 선택 이력이다.

**수평 비교 표시 선택용:** [A:400 iter / B:1000 iter — PNG·SVG·PDF](PEAK_OPTIONS.md). frame1420을 유지하며 괄호 위치만 다른 두 안이다.

**현재 선택본 — frame1420:** [PNG](fig3_table06_compact_frame1420.png) · [SVG](fig3_table06_compact_frame1420.svg) · [PDF](pdf/fig3_table06_compact_frame1420.pdf).
Fig.2와 같은 정사각형 ROI, 800/1400/2600 iteration, 위 baseline/아래 ours. 높이 46.13 mm와 하단 가운데 범례 유지. [캡션·검수](../analysis/table06_revision/frame1420_selected.md).

**최신 v2:** [PNG](fig3_table06_compact_v2_frame355.png) · [SVG](fig3_table06_compact_v2_frame355.svg) · [PDF](pdf/fig3_table06_compact_v2_frame355.pdf).
상단 문구 제거, 범례 하단 가운데 정렬, baseline-final 수평선 제거. [해석·crop 후보](../analysis/table06_revision/layout_v2.md).

**현재 추천 — 납작한 table_06 / frame355:** [PNG](fig3_table06_compact_frame355.png) · [SVG](fig3_table06_compact_frame355.svg) · [PDF](pdf/fig3_table06_compact_frame355.pdf).
동일 폭에서 높이 46.13 mm로 27% 축소, 공통 y축 14–25.5 dB, 원래 곡선 28점 유지.
[이미지 선정·보간 화살표 설명·캡션](../analysis/table06_revision/README.md).

**최신 다른 scene 선택안:** [table_06 / frame1420 PNG](fig3_search_table_06_frame1420.png) · [SVG](fig3_search_table_06_frame1420.svg),
[table_01 / frame330 PNG](fig3_search_table_01_frame330.png) · [SVG](fig3_search_table_01_frame330.svg).
[전체 비교·평가 조건·별표 화살표 해석](../analysis/scene_search/README.md).

**최신 추가 측정:** [frame1180 controlled refinement 도판·결과](REFINEMENT.md).
공통 입력 시점 5곳에서 추가 120 iteration을 실측했으나, 기대한 수렴 가속은 확인되지 않았다.
아래는 기존 전체 trajectory 곡선의 세 선택안이다.

세 버전 모두 **Aria301_305 전체 고정 held-out 539뷰**의 동일 평균 PSNR 곡선을 사용한다.
600 / 1,000 / 1,300 iterations의 실제 지도에서 같은 평가 카메라를 렌더링하고,
위 VIGS-SLAM / 아래 Ours로 배치했다. Inset의 평가 frame만 버전별로 다르다.

| 버전 | 평가 frame | 미리보기 | 논문용 PDF | Inkscape 편집 SVG |
|---|---:|---|---|---|
| A | 1180 | [PNG](fig3_A_frame1180.png) | [PDF](pdf/fig3_A_frame1180.pdf) | [SVG](fig3_A_frame1180.svg) |
| B | 1220 | [PNG](fig3_B_frame1220.png) | [PDF](pdf/fig3_B_frame1220.pdf) | [SVG](fig3_B_frame1220.svg) |
| C | 980 | [PNG](fig3_C_frame980.png) | [PDF](pdf/fig3_C_frame980.pdf) | [SVG](fig3_C_frame980.svg) |

사용자가 선택하기 전이며 원고 TeX에 삽입하지 않았다.
SVG에는 실제 crop PNG가 내장돼 있어 Inkscape에서 바로 열 수 있다.
각 `_provenance.json`에 원본 PNG hash·crop 좌표·곡선 hash·target crossing을 기록했다.

## 실측과 주장 범위

Ours 27개 / baseline 28개 checkpoint를 각각 동일 539뷰로 평가했다.
최종 PSNR은 Ours **25.0936**, baseline **21.8552 dB**이며, 기존 결과와의 차이는
각각 −0.01886 / −0.07151 dB다. 원시 값에 smoothing을 적용하지 않았다.

**회색 구간은 후반 pose correction**: Ours는 1295–1317, baseline은 1327–1347
iteration에 같은 이벤트를 처리한다. 1300 iteration의 큰 차이에는 이 영향이 포함된다.
따라서 순수 optimizer/sampler 수렴 가속으로 단정할 수 없다.
Same PSNR 화살표는 baseline의 최종 PSNR에 대한 사후 도달 위치 비교이며,
checkpoint 사이를 선형 보간한 설명용 위치다. 가속률 숫자는 표시하지 않았다.

전체 실행의 render 예산은 같지만 native iteration당 작업량과 입력 prefix는 다를 수 있다.
Frozen causal tracker / Carve off / fixed-work mapping 결과이며 wall-time 속도 비교는 아니다.

## 재현·검수

1. [checkpoint 저장 wrapper](../scripts/capture_convergence.py)와 [pair 실행](../scripts/run_convergence_pair.py)
2. [고정 held-out 평가와 inset 렌더](../scripts/evaluate_convergence.py)
3. [SVG 생성 → Inkscape PDF → Poppler PNG](../scripts/build_convergence_figures.py)

곡선과 per-view PSNR은 workspace의
`results/figure03_convergence_20260921/aria301_305/evaluation/curves.csv`,
`curves.json`, 각 checkpoint JSON에 저장했다.
도판 폴더 내 곡선 사본: [CSV](../analysis/measured_curves/curves.csv) · [JSON](../analysis/measured_curves/curves.json).
PNG는 실제 PDF를 렌더링한 것이다. 단일 단 폭 약 86.49 mm, 높이 약 63.42 mm이며
200 dpi 인쇄 크기 검토본은 `qa/`에 있다.

## 캡션 초안

> Online mapping quality on Aria301_305. Curves show mean PSNR over 539 fixed
> held-out views; insets compare the same evaluation view at 600, 1,000, and
> 1,300 mapping iterations (upper: VIGS-SLAM; lower: ours). The shaded interval
> spans the late pose-correction event in both runs. Curves include mapping
> and pose-correction effects under a matched total rendering budget.
