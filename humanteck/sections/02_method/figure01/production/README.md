# Overview 그림 작업 폴더

현재 반영: **지도 영역 C07(UID786), 렌더·prior C10(UID1091), 궤적 A**. 먼저 [현재 overview](current/overview.png)를 보면 된다. Shared map은 C07 주변을 외부에서 보는 표시용 cutaway이며, 아래 C10 렌더에는 절단을 적용하지 않았다.

이전 변경(2026-09-21 후속)은 **기여 제목 9pt 통일·작은 설명 확대·오른쪽 공간 재배치**다. 일반 설명은 약 7.03pt, modality 라벨은 약 6.75pt로 확대했다. K/I 배지는 6.47pt를 유지한다. 지도 제목·이미지·Render·modality를 약 3.77mm 위로 옮기고, Base supervision과 Carve에 큰 글자와 행간을 확보했다. 사용자 요청에 따라 `Rendered normal`로 표기하며, (c)는 `Free-Space Carve Loss`로 줄여 (a)/(b)와 같은 크기로 맞췄다. [검수 기록](qa/typography_spacing_2026-09-21.md), [확대 검수본](qa/arrows/). 직전 작업본은 `archive/before_type_spacing_2026-09-21/`에 보존했다.

앞선 상세 정리에서 입력 묶음→frontend, Growth→Sampling, 렌더 결과→Base supervision을 괄호 끝만으로 이어지게 했으며 이 표현을 유지한다. `Arrived views`, 지도 아래 내부 후보 설명, 선택 카드 위아래 문구, admission 시점 설명을 덜고, 긴 completed-update feedback은 Growth 내부 `+κ updates`로 바꿨다. 영상·궤적·ray와 count/probability 값은 유지했다. [전후 비교](qa/detail_cleanup_before_after.png), [검수 기록](qa/detail_cleanup_2026-09-21.md). 당시 수정 전 작업본은 `archive/before_detail_cleanup_2026-09-21/`에 보존했다.

이전 높이 축소 작업에서 180×86.28 mm를 **180×75.37 mm**로 바꿨으며 이후 2026-09-22에69.42mm로 추가 축소했다. [높이 전후 비교](qa/height_before_after.png), [당시 검수 기록](qa/height_compaction_2026-09-20.md)을 참고한다.

## 지금 볼 파일

최신 제목 수정(2026-09-22): (a) View Set Growth. 기존 위치·크기 유지, 원고 Fig.1 캡션도 동기화.

최신 제목 수정(2026-09-22): (a) Training-Set Growth로 변경. 기존 위치·크기 유지, 원고 Fig.1 캡션도 동기화.

최신 수정(2026-09-22): [Initialization 경로·Training-view management 간격](qa/initialization_growth_spacing_2026-09-22.md). 초기화 문구를 지도 입력 옆으로 옮기고 상단 경로를 올렸다. (a)를 올리면서 뷰 행/괄호/(b) 제목 주변 간격을 확보했다.

최신 수정(2026-09-22): [작은 글자 미세 축소·오른쪽 공간 재배치](qa/right_panel_balance_2026-09-22.md). 설명은4%만 줄였다. Shared map과Update 반환선을 정리하고 결과 라벨/괄호/Base/Carve 간격을 늘렸다. 도판180×69.42mm 유지.

최신 수정(2026-09-22): [제목 크기 및 세로 간격 축소](qa/height_tightening_2026-09-22.md). 기존 구조를 유지하면서180×75.37→180×69.42mm로 약7.9% 낮췄다. 큰 제목을 줄이고 설명 글자 크기·이미지 비율을 유지했다.

최신 미세 수정(2026-09-22): [Depth 화살표 추가 상향](qa/depth_arrow_raise_2026-09-22.md). Depth 라벨과 화살표를 약0.79mm 더 올렸다.

최신 수정(2026-09-22): [Carve 박스 하단 정리·라벨 왼쪽 정렬](qa/carve_raise_left_align_2026-09-22.md). (c) 박스를 위로 조정하고 높이를 줄여 하단 여백을 확보했다. Priors/RGB/Depth는x=1188에서 왼쪽 정렬한다.

최신 수정(2026-09-22): [Depth/Priors/RGB 오른쪽 이동](qa/input_label_shift_2026-09-22.md). 세 라벨과 Depth 배경을 함께 약0.79mm 오른쪽으로 이동해 점선 겹침과 배경 돌출을 해소했다.

최신 미세 수정: [Depth 배경 레이어 순서](qa/depth_background_layer_2026-09-21.md). 위치를 유지하고 라벨 배경만 보라색 점선 뒤로 보냈다.

최신 도식 정리: [Carve 박스 복원 및 Depth 화살표](qa/carve_box_restore_2026-09-21.md). 원래 넓은 Carve 박스를 유지하며, `Priors`, `RGB`, `Depth`의 가로 중심을 맞추고 Depth 화살표가 박스 안쪽까지 들어가도록 했다. [Carve 보조 설명 제거](qa/carve_label_simplification_2026-09-21.md)에서 삭제한 내부 `Verified keyframe depth`, `Uncertainty`, `D`는 생략한 상태를 유지한다. `Gaussian initialization` / `Camera pose`를 사용하며, Carve 내부의 `Penalize free-space opacity`는 작용을 설명하는 문구다.

1. [지도 시점 후보 12개](candidates/01_view_candidates.png)
2. [동일 후보의 입력 RGB / rendered RGB / depth / normal](candidates/02_modalities_all.png)
3. [실제 궤적 + 카메라 frustum, A/B 시점 비교](candidates/03_trajectory_options.png)
4. [선택을 반영한 overview](current/overview.png)
5. [LaTeX용 PDF](current/overview.pdf), [SVG](current/overview.svg), [삽입 예제](current/overview_insert.tex)
6. [Cutaway 외부 시점 6개 비교](candidates/04_cutaway_cameras.png) — 현재 벽 정렬 S5 적용 (정면, 위에서 24°)

## 폴더 안내

| 폴더 | 내용 |
| --- | --- |
| current/ | 현재 overview PNG·PDF·SVG·TeX, 여기에는 최종 확인 대상만 |
| candidates/ | 선택용 비교판 4개, 후보 manifest, frames/ 아래 원본 크기 자산 |
| assets/aria1253/ | overview에서 사용 중인 RGB·prior·render 및 provenance |
| assets/trajectory/ | 실제 keyframe pose 기반 궤적 PNG·SVG·provenance |
| assets/cutaway/ | 표시용 절단 지도 6개 시점, 선택본, 절단 범위·camera provenance |
| scripts/ | 유지보수하는 기존 Python 코드 2개 |
| qa/ | PDF 재렌더 검수본, v12 비교판, 검증 JSON·QA 기록 |
| archive/ | 이전 layout·후보판·pose 수정 전 overview; 삭제 없이 보존 |

생성형 v01–v12 시안은 상위 [plan/](../plan/), 참고 논문 도판은 [reference_figures/](../reference_figures/README.md)에 유지한다. 최신 결정은 [선택·cutaway 작업 기록](../../plan/10_selected_views_cutaway_2026-09-20.md)에 기록한다.

## 자산과 해석

- 사용자 승인 run: exp94 Aria1253 normalized_variance_s0. 지도나 학습 상태를 수정하지 않고 저장 PLY를 렌더링한다.
- 후보 C01–C12는 동일 prefinal 지도와 실제 keyframe pose를 사용한다. Mapping에 사용된 view이며 held-out 비교가 아니다. 시퀀스 전반을 시간순으로 골랐고 최고 PSNR로 선별하지 않았다.
- 입력 RGB와 모든 modality는 정방향으로 표시한다. RGB 밝기 보정, normal smoothing, 원본 Gaussian 삭제 없음.
- C10의 입력 K3·RGB/depth/normal·frontend prior가 같은 UID다. C07은 별도 외부 inspection camera의 기준 영역이며 C10과 같은 저장 지도를 사용한다.
- Cutaway는 실제 Gaussian 중심에서 추정한 벽 평면에 camera 좌우 방향과 절단 상자를 정렬했다. 위에서 24° 내려다보며, 공간 상자에 중심이 포함된 30,587/177,099개 Gaussian만 임시 표시한다. 품질·opacity 기준 pruning이 아니며 원본 PLY와 C10 전체 지도 렌더는 그대로다. 천장·가까운 벽 쪽을 열어 실내 구조를 보여주는 도해이지 floater 제거 성능 증거가 아니다.
- 궤적은 traj_kf_beforeBA.txt의 115개 실제 pose와 지도 좌표를 함께 투영한다. 카메라 위치·회전은 실제 값, frustum 길이만 표시용 0.45m다. A는 pose의 주성분 평면, B는 oblique projection이며 중력 정렬 floor plan이 아니다.
- 궤적 배경은 Gaussian 중심의 DC 색상 점 투영이다. A의 구도는 유지하고 직전 대비 alpha를 0.26→0.34, 점 크기를 0.65→0.85로 높였다. Gaussian 자체 opacity를 바꾼 것이 아니다.
- Run의 ray-space loss는 꺼져 있다. 실제 이미지는 overview용이며 해당 loss의 개선 효과로 주장하지 않는다.
- Pool 크기/count/probability/ray는 설명용 도식이다. 실제 pose 그림만 새로 데이터 기반으로 바꿨다.

## 재생성

이미 있는 asset으로 overview만 갱신 (GPU 사용 안 함):

```bash
python3 humanteck/sections/02_method/figure01/production/scripts/build_overview_v02.py
```

GPU 후보 렌더 / CPU pose 시각화는 기존 extractor의 --candidates / --trajectory 옵션을 사용한다. --apply-selection은 C07/C10/A 선택과 K/I 자산을 적용하고, --cutaway는 공간 절단 6개 시점을 렌더하며, --select-cutaway S5는 선택본의 빈 캔버스만 줄여 연결한다. VIGS 환경과 프로젝트의 mapping_environment(True)로 실행해야 한다. 최초 전체 자산 생성용 무옵션 실행은 선택 상태가 있으면 차단한다. 후보 렌더 실행 전 GPU 상태 확인, 타 계산 작업 종료 금지. 기존 생성 코드를 복제하지 않고 **같은 두 파일에 diff로 수정**한다.

현재 PDF는 Times New Roman embedded, 180×69.42 mm다. 제목 Bold / 설명 Regular와 개별 폰트 크기를 유지했다. 후보판은 화면 비교용 Arial을 유지한다. PDF→PNG 확인을 수행하며, 원고 `HumanTeck_Song_s_intern/figure/overview.pdf`도 동일 파일로 갱신한다. 전체 원고 컴파일 및 인쇄 검수는 별도다. 원본 수상자 PDF·paper/latex·실험 데이터는 수정하지 않았다.
