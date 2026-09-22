# Fig. 3 제작 코드

- **현행 `build_selected_B.py`**: (a) 19 dB 아래 축척을 압축한 원본 PSNR 곡선,
  (b) frame1420·1400 iter의 VIGS-SLAM/Ours/GT 전체 화면+동일 ROI 확대.
  SVG를 Inkscape로 PDF 출력하고 PDF에서 PNG 미리보기를 만든다(CPU).
  기본 실행은 검토본 생성, 검수 후 `--install`로 current/·원고 PDF 두 파일·캡션을 동기화한다.
- 아래 코드는 이전 후보·평가 이력이다. 현행 재생성에는 위 스크립트를 사용한다.
- 이전 `build_table06_frame1420.py`: frame1420, Fig.2와 동일 정사각형 ROI의 3시점 inset으로 SVG/PDF/PNG 생성(CPU).
- `review_frame1420.py`: 해당 ROI의 800/1400/2600 Baseline/Ours/GT 상세 비교판 제작(CPU).

- 최신 `build_table06_layout_v2.py`: 상단 문구 삭제·하단 가운데 범례·수평선 제거 버전 SVG/PDF/PNG 제작(CPU).
- `review_table06_candidates_v2.py`: 기존 렌더로 8개 frame의 GT crop locator와 3시점 Baseline/Ours/GT 비교판 제작(CPU).
- [v2 판단·결과](../analysis/table06_revision/layout_v2.md).

## table_06 높이 축소판

- `render_table06_revision.py`: Fig.2 frame을 제외한 8개 후보 × 3 checkpoint × 2 arm의 실제 렌더와 원본 PSNR 재현 검증. GPU 사용 전 점유 확인 필수. 실행 환경은 `run_convergence_pair.mapping_environment(True)`.
- `build_table06_compact.py`: frame355를 넣고 높이 46.13 mm, y축 14–25.5 dB, 선형 보간 교점으로 SVG/PDF/PNG 제작(CPU).

[최종 결과·재현 명령·캡션](../analysis/table06_revision/README.md).

## 다른 장면의 전체 trajectory 곡선 탐색

- `search_scene_curves.py`: square-1/table_01/table_06의 native pair capture와 full fixed held-out 평가를 순차 실행.
- `evaluate_scene_curves.py`: 기존 distortion-aware 평가를 유지하고 전체 curve/per-view 및 inset PNG 저장.
- `review_scene_curves.py`: Aria 포함 4개 곡선 비교판과 중반 gap 기술통계.
- `build_scene_search_figures.py`: RPNG 두 장면의 Fig.3 스타일 SVG/PNG 생성. 실제 checkpoint와 crop만 사용.

`vigs-slam-5090` Python으로 실행한다. 실행 및 결과 해석은 [탐색 README](../analysis/scene_search/README.md)를 따른다.

- `review_high_gain_views.py`: 기존 aria301_305 최종 map에서 4개 held-out frame 렌더링,
  기존 per-view PSNR 재현 확인. 학습 없음. GPU 사용 전 프로세스 확인 필요.
- `build_high_gain_board.py`: 저장된 실제 PNG를 동일 crop의 SVG로 조합하고 Inkscape로 PNG 출력. CPU 전용.

```bash
/home/colin/miniconda3/envs/vigs-slam-5090/bin/python humanteck/sections/02_method/figure03/scripts/review_high_gain_views.py
python humanteck/sections/02_method/figure03/scripts/build_high_gain_board.py
```

## 실제 수렴 곡선과 도판

- `capture_convergence.py`: 기존 mapper를 외부에서 감싸 50 Gaussian Adam step마다 PLY와 event provenance 저장.
- `run_convergence_pair.py`: source hash와 GPU 점유를 확인하고 Ours → baseline 순서로 실행. 기존 capture는 재사용한다.
- `evaluate_convergence.py`: 모든 map을 동일 held-out 539뷰에서 평가하고 frame 980/1180/1220의 실제 inset 저장.
- `build_convergence_figures.py`: 동일 곡선·서로 다른 inset의 SVG 세 개 생성, Inkscape PDF와 Poppler PNG/200dpi QA 출력.

학습과 평가에는 `vigs-slam-5090` 환경 및 custom VIGS의 CUDA extension 경로가 필요하다.
`run_convergence_pair.mapping_environment(True)`가 해당 환경을 반환한다.
이미 계산된 결과로 도판만 다시 만드는 명령은 다음과 같다(CPU 전용).

```bash
python humanteck/sections/02_method/figure03/scripts/build_convergence_figures.py
```

평가 결과와 map은 `results/figure03_convergence_20260921/aria301_305/`에 보관한다.
곡선 CSV/JSON 사본은 `../analysis/measured_curves/`에 있다.
단위는 실제 누적 optimizer iteration이며 pose correction에 따른 품질 변화도 포함한다.

## 공통 입력 시점의 추가 refinement

- `run_refinement_panel.py`: PSNR 확인 전 선택한 event17/38/68/98/119의 10개 분기 순차 실행.
- `capture_refinement.py`: 각 event 뒤 독립 continuation, 추가0–120 step의 map과 causal 평가 pose 저장.
- `evaluate_refinement.py`: 동일 pose·전처리·renderer에서 90개 map 평가, 1180 inset 저장.
  실행 환경은 `run_convergence_pair.mapping_environment(True)`를 사용한다.
- `build_refinement_figure.py`: 실측 5-event 평균과 실제 inset으로 SVG/PDF/PNG 생성(CPU).

```bash
/home/colin/miniconda3/envs/vigs-slam-5090/bin/python humanteck/sections/02_method/figure03/scripts/run_refinement_panel.py
python humanteck/sections/02_method/figure03/scripts/build_refinement_figure.py
```

위 두 명령 사이에 evaluator 실행이 필요하다. 평가 결과가 이미 있으면 도판만 다시 만들 수 있다.
데이터는 `results/figure03_refinement_20260921/aria301_305/`에 보관한다.
조건·부정적 결과·해석은 [REFINEMENT.md](../output/REFINEMENT.md)를 따른다.
