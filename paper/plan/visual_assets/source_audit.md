# 원본 자산·실험 확인 기록

2026-10-01. 초기 원본 조사를 아래에 보존한다. 후속 실제 측정은 `cvpr_assets` campaign에 기록한다.

## 후속 확인

- 로컬 `repos/main/3dgs-custom/runtime/scheduler.py`에는 `RelativeFloorIntervalSoftmaxRandomReshuffling`이 실제 존재한다. 다만 현재 train/scheduler hash는 원본 benchmark-B와 paper-figures의 source lock과 다르므로 원본 구현의 동일 재현으로 선언하지 않는다.
- `VIGS-SLAM-paper-full/exp70_axes/region_gt/`에서 Aria1253 수작업 empty-space mask와 ORB 정합 pose를 찾았다. 원본 README hash와 timestamp를 대조했고 평가에만 사용했다. 독립 dense surface reference는 아니므로 accuracy/completeness/F-score를 만들 수 없다.

## 휴먼테크 제작 구조

- Overview: `humanteck/sections/02_method/figure01/production/`의 current/assets/candidates/scripts/qa/archive.
- RGB 비교: `humanteck/sections/02_method/figure02/`의 candidates/analysis/scripts/output 및 provenance.
- 수렴 그림: `humanteck/sections/02_method/figure03/`의 plan 성격 분석/후보/output/current/scripts.
- 해당 figure03/AGENTS.md와 README를 읽었다. 휴먼테크 **원고 Fig.2**와 작업 **figure03/current/fig3**는 같은 그림이다.
- 휴먼테크에는 이번 요청처럼 번호별 table 제작 폴더가 확인되지 않았다. 수치 표는 paper/latex 및 ERCB_ablation의 TABLES/생성 스크립트 계열에서 관리한다. 따라서 figure 작업 구조를 table에도 확장한다.
- CVPR에는 `paper/figures/figureXX_*`, `paper/tables/tableXX_*`를 새로 만들고 current 관례를 적용했다. 과거 humanteck 파일과 원고는 수정하지 않았다.
- F2는 overview SVG 디자인을 재사용한다. 원본의 실측 map은 Carve off 설명용이며 sampling/ray는 schematic이다.
- F3는 그래프+사진 배치를 재사용한다. 과거 1400/2400 checkpoint 및 1000회 차이는 최신 실행에서 다시 측정해야 한다.

## T4: 실제 원본 기능의 확인 범위

확인 파일:
- `context/experiments/ERCB_ablation/benchmark-B/prepare_manifest.py`
- `context/experiments/ERCB_ablation/benchmark-B/evidence/manifest.json`
- `context/experiments/ERCB_ablation/benchmark-B/summary.md`
- `context/experiments/exp77/run_training.py`
- `context/experiments/ERCB_ablation/paper-figures/prepare_view_ordering.py`
- `context/experiments/ERCB_ablation/paper-figures/evidence/manifest_view_ordering.json`
- `context/experiments/ERCB_ablation/paper-figures/compute_metrics.py`

| 항목 | 확인 내용 |
|---|---|
| 학습 엔진 | exp77 wrapper가 `--repo .../3dgs-custom-exp77-budget-5070ti-repro`의 train.py를 runpy로 실행 |
| 원고 15/30/60 표 | benchmark-B, stride20, 19 scenes, fixed pose/init replay, fixed topology |
| RR | `causal_rr` |
| 당시 ERCB | `relative_floor_interval_softmax_rr`, scheduler_beta=log(3), block_size=8 |
| 데이터·학습 | seed0, -r4, RGB-only, depth weight0, CPU image storage, llffhold-8 |
| optimizer/보고 | fixed_topology_step_before_report, post-update 완료계수 검사 |
| densification | benchmark-B: densify_until_iter=0 |
| 후속 curve 실험 | paper-figures: densify-on, 24 checkpoint, 15/30/60, 114 jobs |
| manifest 완료 기록 | benchmark-B 152/152(초기화 stride 비교 포함), paper-figures 114/114 |
| 한계 | 원본 `/home/wosas/.../3dgs-custom-exp77-budget-5070ti-repro`는 현재 머신에 없음 |

wrapper는 sampler factory 호출과 draw 계측을 확인시켜 주지만 내부 interval 클래스의 수학적 동작 전체를 증명하지 않는다. 현 머신의 다른 mapper_3dgs/runtime/scheduler.py들은 해당 class를 가진 원본으로 확인되지 않았다. 따라서 **원본 repo/commit snapshot 복원과 hash 대조는 미완료**로 남긴다.

현재 cumulative per-view ERVS와 과거 interval ERCB는 동일 이름으로 합치지 않는다. 원고 기존 PSNR 20.77/22.22/22.88 대 21.39/22.33/23.11은 과거 표의 출처 확인용이다. 후속 densify-on 곡선에 이 endpoint를 붙이지 않는다.

## T5: supervision 비교의 원본

`dense-supervision/prepare_manifest.py`의 두 arm은 같은 causal_rr, 같은 update budget을 사용한다. kf_only에는 `--eligible_names_file .../schedules_kfrr/...`를 주고 kf_dense는 전체 arrived train pool을 사용한다.
원본 engine은 위 3dgs-custom 계열이며 fixed pose/init replay다. densification은 total update의 비율로 종료하므로 현재 unknown-horizon production과 다르다.

- `dense-supervision/evidence/manifest.json`: event60, 19 scenes×2, 38/38 완료 기록.
- event60: 전체 23.31→23.65dB, RPNG 평균은 음수. 기존 TeX는 이 표를 사용한다.
- README의 event120 요약은 전체 23.98→25.09dB와 SSIM/LPIPS/#G를 제공한다. 다른 budget의 결과이며 원래 60 칸을 조용히 덮어쓰지 않는다.
- 현재 VIGS 계열 `kf_rgb_control/SUMMARY.md`, `unified_rr_ervs/SUMMARY15.md`는 별도 구현/예산이다. RGB-only 횟수와 quota/LR 위치 차이도 고려해야 한다.
- 본문은 최종 시스템과 가까운 대조를 우선 검토한다. 원본 replay를 사용하면 scheduler/supervision isolation임을 명시한다. PSNR이 높은 arm만 다른 코드에서 교체하지 않는다.

## 현재 system/time 자료

- `context/experiments/campaigns/06_gain_attribution/fifo_live/README.md`: 4 scenes×2 rates×2 methods=16 actual-tracker runs, seed0. 저장 지도 2회 평가는 독립 seed 반복이 아니다.
- RPNG/UTMM tracker 설정 차이가 있어 mapper-only 인과 비교로 쓰지 않는다. tracker lag 및 종료 지연도 제공한다.
- `live_render_capacity/SUMMARY.md`, `render_budget40_feasibility/SUMMARY.md`: F12를 위한 기존 tracking-only/동시 실행 진단. 서로 다른 과거 recipe의 capacity 숫자를 현재 구조의 값으로 바꾸어 부르지 않는다.
- 기하 통합 자료 `geometry_main_validation/SUMMARY.md`: D3 실행과 PSNR 회귀 확인이다. Carve 또는 독립 GT geometry 개선의 검증이 아니다.

## 추가 문헌 조사

[VIGS-SLAM](https://arxiv.org/html/2512.02293v2)은 본문 평균과 부록 sequence별 rendering 표를 구분하며 final color refinement 전후도 나눈다. 그 구조를 T1/T2에 적용하고, 온라인 종료 결과에 후처리 점수를 섞지 않는다. 호환 방법과 개별 출처는 baseline_registry.md에 정리했다.
