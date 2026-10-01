# CVPR Figure / Table 제작 목록 — 사용자 선택본

2026-10-01. 휴먼테크 제출은 완료되었고 대상은 `paper/`의 CVPR 원고다.
**이번 범위는 항목별 폴더와 한국어 MD 계획 작성이다. 최종 figure/table 제작 및 새 GPU 실험은 아직 수행하지 않았다.**

## 선택 범위

- Figure 10개: F1–F7, F9, F11, 추가 F12(tracking 부담별 KF당 mapping 처리량).
- Table 계획 8개: T1-main/T1-supp, T2-main/T2-supp, T3–T6.
- F8/F10 및 이전 답변의 기타 appendix 후보는 이번 채택 목록에 자동 포함하지 않는다.
- 번호는 사용자와 합의한 식별자다. 논문 최종 순서에 따른 번호 변경과 작업 폴더명은 분리한다.
- F2는 휴먼테크 overview 재사용. F3는 휴먼테크 곡선+사진 구도를 유지하고 신규 값/이미지로 교체.
- F9는 sampling 수렴 곡선. F11은 실제 tracking 동시 실행의 동일-time 그래프. F12는 시간 구간별 tracking 부담과 mapping 처리량.
- T4는 기존 예산별 RR/ERCB 표를 유지한다. T5는 KF-only/+between-frame 비교를 유지한다.
- T6는 scene별 VIGS 최고 관측 PSNR 최초 도달 학습량 비교다.

## 작업 안내

[공통 비교 규칙](protocol.md) · [원본 코드/자산 확인](source_audit.md) · [baseline 후보와 입력 조건](baseline_registry.md) · [sequence 목록](dataset_registry.md)

| ID / 항목 | 계획 |
|---|---|
| F1 — Teaser | [열기](../../figures/figure01_teaser/plan/CURRENT.md) |
| F2 — System overview: 휴먼테크 재사용 | [열기](../../figures/figure02_system_overview/plan/CURRENT.md) |
| F3 — Photometric convergence: 곡선·사진 갱신 | [열기](../../figures/figure03_photometric_convergence/plan/CURRENT.md) |
| F4 — 새 관측 영역의 수렴 | [열기](../../figures/figure04_new_region_convergence/plan/CURRENT.md) |
| F5 — 여러 scene의 RGB 비교 | [열기](../../figures/figure05_rendering_comparison/plan/CURRENT.md) |
| F6 — Geometry 및 solid ellipsoid 비교 | [열기](../../figures/figure06_geometry_comparison/plan/CURRENT.md) |
| F7 — Geometric convergence | [열기](../../figures/figure07_geometry_convergence/plan/CURRENT.md) |
| F9 — RR vs ERCB/ERVS 수렴 ablation | [열기](../../figures/figure09_sampling_convergence/plan/CURRENT.md) |
| F11 — 동일 시간에서의 online 품질 비교 | [열기](../../figures/figure11_equal_time_online/plan/CURRENT.md) |
| F12 — Tracking 부담과 KF당 mapping 처리량 | [열기](../../figures/figure12_tracking_mapping_capacity/plan/CURRENT.md) |

| ID / 항목 | 계획 |
|---|---|
| T1-main — Dataset 평균 rendering 비교 | [열기](../../tables/table01_rendering_main/plan/CURRENT.md) |
| T1-supp — 모든 sequence별 rendering 비교 | [열기](../../tables/table01_rendering_supp/plan/CURRENT.md) |
| T2-main — 동일 시간 Dataset 평균 비교 | [열기](../../tables/table02_time_main/plan/CURRENT.md) |
| T2-supp — 모든 sequence의 시간 조건 비교 | [열기](../../tables/table02_time_supp/plan/CURRENT.md) |
| T3 — Geometry 정량 비교 | [열기](../../tables/table03_geometry/plan/CURRENT.md) |
| T4 — Update budget별 RR vs ERCB/ERVS | [열기](../../tables/table04_sampling_budget/plan/CURRENT.md) |
| T5 — Keyframes only vs + in-between frames | [열기](../../tables/table05_dense_supervision/plan/CURRENT.md) |
| T6 — VIGS-SLAM 최고 관측 PSNR 도달 비용 | [열기](../../tables/table06_baseline_peak/plan/CURRENT.md) |

## 제작 순서와 연결

1. Ours geometry/학습 구조와 공통 cohort·budget 단위를 source-lock한다.
2. T1/T2 본문·부록은 각각 같은 run 데이터에서 생성한다. 공통 scene subset과 실패/미측정 상태를 공개한다.
3. F3→T6, F11→T2, F9→T4, F6/F7→T3가 동일한 측정을 공유한다.
4. F4/F12는 신규 timestamp 계측이 필요한 분석이다. 기존 endpoint만으로 곡선을 만들지 않는다.
5. F1은 검증된 F3/F5/F6 자산에서, F2는 기존 overview에서 제작한다.
6. 검토본은 output, 선택/검수 완료본만 current에 둔다. 새 실험 문서/runner/raw result는 campaign-first 규칙을 따른다.

과거 plan/figures와 plan/experiment_table의 CURRENT도 이 선택본을 가리키는 새 버전으로 갱신했다. 과거 계획과 실험은 삭제하지 않았다.
