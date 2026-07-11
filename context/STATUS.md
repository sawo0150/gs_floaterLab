# STATUS — 현재 상태 (1페이지 엄수)

> 마지막 갱신: 2026-07-10. 이 문서가 넘치면 내용을 `knowledge/` 또는 `rounds/`로 밀어낸다.

## 현재 Best

| 기준 | 실험 | PSNR@30k | 비고 |
|---|---|---:|---|
| 순수 PSNR | exp08 (baseline) | **33.012** | floater 미해결 (Pop1+Pop2 잔존) |
| Pop1 해결 | exp13 (camera-bound filter) | 32.855 | Z-outlier -74%, \|Z\|max 42.7→4.85m |
| Plateau 계열 | exp25 (tau enlarged) | 32.969 | **⚠ 미정렬 anchor로 얻은 결과 — 재검증 대상** |

## 지금 열려 있는 질문

1. **exp37(dense init, plateau 없음)이 \|Z\|>4m=0을 달성** — Pop2 densification floater 억제의 가장 강력한 지금까지의 결과. ray-density 지표로 재검증해도 여전히 가장 깨끗함. MPS 트랙에도 같은 방식 적용해볼 가치. **1순위.**
2. ~~dense confidence init + enlarged tau plateau (exp38/39)~~ → **기각**: floater 재검토 결과 enlarged tau plateau는 ray-미관측 공간까지 침범해 진짜 floater(opacity>0.5)를 더 만든다 (exp32 대비 6.6배). plateau 계열 자체가 이 트랙에서는 exp37보다 열세로 확정.
3. ~~Round 7 재검증~~ → exp28/29로 해소: plateau loss는 정렬 여부에 거의 영향 안 받음. "tau > λ"는 MPS 한정 결론으로 재확정 (ORB는 반대).
4. floater 지표 (07-12 갱신): **표준 GT = 수동 라벨 기반 3D 영역** (`floater_metric_region.py`, ORB 트랙 전용, 사람 검증 상속) + ray-density(`check_gaussian_ray_coverage.py`)로 상호보완. \|Z\|>4m·plateau-inside-ratio는 신뢰 안 함. **⚠ 새 GT 지표로 exp37이 baseline의 4.7배 최악 판정** (region_n 16,454 vs 3,477) — exp37 1순위 결론 재고 필요.

## 최근 흐름 (최신순)

- **2026-07-11**: **Carve Loss 설계 완료 (분석만, 학습 없음)** — 카메라→SLAM 포인트 ray의 free-space carving 증거비 ρ(x)에 anchor 거리를 곱한 score w(x)가 수동 floater 판별 **AUC 0.974** (plateau 0.511). 수동 floater가 opacity 중앙값 0.044의 "한계 생존자"임을 발견(카드의 op>0.5 서술은 오류였음, 정정 완료). **부수 피해 재정량**: 원안 prune 규칙은 표면 시각 기여량 3.83% 손실로 폐기, 안전 규칙(w>0.9 & op<0.1 & contrib<p90)은 **recall 69.4%·기여손실 0.39%·구멍 0**. densify 게이트는 출생 91% 차단 가능하나 기여량 13.75% 영역에 걸려 학습 검증 필요. 렌더 PSNR 검증용 pruned 모델 4종 준비 완료(GPU 대기). → [carve_loss_design](experiments/carve_loss_design.md)
- **2026-07-11**: **plateau 방식으로 수동 floater 2,817개를 해결할 수 없음을 학습 없이 정량 확정** (`verify_plateau_capability.py`). 실제 학습 field(DepthPro anchor + ellipsoidal 적응형 tau) 기준 floater의 66%가 plateau 안이라 gradient 0 (측정 telemetry로 교차검증됨), 정규화 거리 D의 floater 판별 AUC 0.511(무작위). 단 raw 유클리드 거리는 AUC 0.93(SLAM) — **신호는 존재하나 적응형 tau가 판별력을 파괴**. λ 크기는 애초에 문제 아니었음. → [exp32_lineage_diag §3](experiments/exp32_lineage_diag.md)
- **2026-07-11**: 사용자가 직접 SuperSplat으로 정밀 편집한 `point_cloud_cleaned.ply` (2,817개 floater 삭제)에 대한 수동 분석 완료. 수동 floater들은 표면 대비 RGB gradient를 2.23배 높게 받으며 소멸에 저항했고, Plateau gradient는 0.58배 적게 받으며 허공(outlier)에 방치되었음을 입증. 대다수(69%)가 3k~7k step 사이의 후반부에 split(평균 5.73회)을 통해 생성되었고, Seed 5061(10%) 등 특정 조상 포인트가 증식을 대량 주도함. -> [exp32_lineage_diag](experiments/exp32_lineage_diag.md)
- **2026-07-10**: floater 계보 및 gradient 분리 진단 실험(`exp32_lineage_diag`) 완료. 명시적 floater가 미관측 void 영역에 갇혀 RGB gradient가 정상의 1/4배(`0.14` vs `0.55`)로 억제되었음을 입증. 특히 Plateau loss가 10배 더 강하게 복구력을 가했음에도 이들이 opacity > 0.5로 생존했으며, 특정 seed 두 개(7015, 5392)가 전체 floater의 70%를 생산하는 주범임을 최초 정량 확인. -> [exp32_lineage_diag](experiments/exp32_lineage_diag.md)
- **2026-07-10**: floater 지표 재검토. \|Z\|>4m·plateau-inside-ratio 둘 다 부정확함을 확인 — plateau loss 없이도 enlarged tau는 자연히 97~98% "안"(tau가 커서 변별력 없음). ray-density 기반(카메라가 한 번도 안 본 3D voxel + opacity) 재측정 결과 **enlarged tau plateau(exp33/36)가 기본 tau(exp32/35)보다 진짜 floater(opacity>0.5)가 6.6배 많음** — enlarged tau의 넓은 plateau가 관측 불가 공간까지 침범하기 때문(불관측 voxel의 8~22배가 plateau 안). exp37(dense init)이 모든 지표에서 최선으로 재확인. → `experiments/exp30_37_orb_native_track.md`, `knowledge/pitfalls.md`
- **2026-07-09**: exp30~37 — **OpenMAVIS(ORB) 데이터셋 재현 트랙 완료**. MPS 트랙(exp08~29)에서 검증한 방법(anchor init, plateau)을 실제 목표 데이터(`data/03_rgb_3dgs_full`)로 재현. **핵심 결과**: exp37(SLAM core seed dense init 148,564pts, plateau 없음) PSNR 32.621, **|Z|>4m=0** — 이 트랙 최고의 floater 억제. plateau의 tau 크기 효과는 MPS와 정반대(ORB는 기본 tau가 더 나음). 고confidence anchor seed로 추가 dense init 2종(144,830 / 65,095pts)도 생성, 3D 균질성 확인(NN spacing이 voxel 크기와 일치, 근/원거리 편향 없음). → `experiments/exp30_37_orb_native_track.md`
- **2026-07-09**: exp28/29 — 정렬 anchor로 plateau 재실행. **예상외 결과**: 기본 tau(exp29=32.752)도 enlarged tau(exp28=32.864)도 미정렬 버전(exp19=32.753, exp25=32.969)과 거의 동일 — plateau loss 자체에는 정렬 효과가 미미함 (λ가 작아 위치 오차의 영향이 작았던 것으로 추정). 정렬이 크게 효과 본 곳은 **anchor를 init으로 쓸 때**뿐 (exp27→27c +2.07dB).
- **2026-07-09**: exp27/27b/27c — anchor를 init으로 사용해 품질 검증. **좌표계 버그 발견**: exp19~26의 anchor는 Atlas world 그대로였음. Umeyama 정렬(rmse 2cm) 후 anchor init 31.611 (대조군 30.583, 미정렬 29.540). → `experiments/exp27_anchor_init.md`
- **2026-07-07**: scripts/·results/ 재구조화. scripts는 pipeline/experiments/diagnostic/analysis/anchors 5분류, results는 experiments/rounds/diagnostic/datasets/logs/archive 6분류 (각 README 참조). 실패 run은 `results/archive/failed_runs/`. 문서 내 경로 참조 일괄 갱신됨.
- **2026-07-07**: data/ 전면 재구축. 순수 OpenMAVIS 체인(VRS→EuRoC→SLAM→전체 프레임 RGB 3DGS)으로 `data/03_rgb_3dgs_full` 생성 (1303장, ORB 7,205pts, reprojection 검증 통과). 재현: `scripts/pipeline/run_full_pipeline.sh`. 기존 심링크 무더기 제거 (`data/README.md` 참조).
- **2026-07-05**: exp19~26 MPS plateau 변형 sweep 완료. tau 확대(exp25)만 유효, opacity_weight/exp_loss/adaptive_prune는 모두 PSNR 악화. → `rounds/round7_plateau_mps.md`
- **2026-07-05**: exp15~18 ORB plateau (Round 6). 어떤 설정도 baseline 못 이김. ellipsoidal >> spherical (+1.0dB). → `rounds/round6_plateau_orb.md`
- **2026-06-30**: exp13 camera-bound filter로 Pop1 -99% 해결 (PSNR -0.16dB). → `rounds/round5_findings_summary.md`

## 다음 실험 후보 (우선순위순)

1. **exp38: Carve Loss 학습 검증 — 구현·config·스크립트 준비 완료, GPU만 뜨면 실행** (`scripts/experiments/run_exp38_carve.sh`: exp38a=soft+prune+gate, exp38b=prune+gate만). 챔피언 score `w·(1−maxop_5cm)` AUC 0.98, 예산 prune 0.5%로 recall ~60% + soft loss 보완 예측 → [carve_loss_design](experiments/carve_loss_design.md). **주의: 챔피언 score 기준 exp37 dense init이 오히려 최다 먼지 부하(4.5배) — |Z|·unseen 지표의 사각지대. exp37 결론 재평가 필요.**
2. exp37 방식(dense confidence+monodepth init, plateau 없음)을 MPS 트랙에도 적용 — |Z|>4m=0·ray-density 우수함이 ORB 트랙만의 우연인지 재현 가능한 효과인지 확인.
3. exp37(SLAM core seed) vs 고confidence-seed dense init(5cm/60k판) 직접 비교 — plateau 없이 seed 종류만 바꿔 dense init 자체의 최적 seed 탐색.
4. ray-density 지표를 앞으로의 모든 신규 실험 평가에 표준 적용.

## 확정된 사실 (자세한 근거는 knowledge/)

- Floater는 두 집단: Pop1(SLAM init outlier) / Pop2(densification floater) → `knowledge/floater_populations.md`
- init 626,811pts의 출처는 ORB-SLAM이 아니라 **Aria MPS semi-dense**, confidence 필드는 현재 버려짐 → `reference/workspace_map.md`
- VGGT는 현 시점 OpenMAVIS 대체 불가 (닫힌 축) → `archive/vggt_evaluation.md`
