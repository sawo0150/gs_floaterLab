# STATUS — 현재 상태 (1페이지 엄수)

> 마지막 갱신: 2026-07-09. 이 문서가 넘치면 내용을 `knowledge/` 또는 `rounds/`로 밀어낸다.

## 현재 Best

| 기준 | 실험 | PSNR@30k | 비고 |
|---|---|---:|---|
| 순수 PSNR | exp08 (baseline) | **33.012** | floater 미해결 (Pop1+Pop2 잔존) |
| Pop1 해결 | exp13 (camera-bound filter) | 32.855 | Z-outlier -74%, \|Z\|max 42.7→4.85m |
| Plateau 계열 | exp25 (tau enlarged) | 32.969 | **⚠ 미정렬 anchor로 얻은 결과 — 재검증 대상** |

## 지금 열려 있는 질문

1. **exp37(dense init, plateau 없음)이 \|Z\|>4m=0을 달성** — Pop2 densification floater 억제의 가장 강력한 지금까지의 결과. 이걸 왜 되는지(순수 init 밀도/커버리지 효과?) 더 분석하고, MPS 트랙에도 같은 방식 적용해볼 가치. **1순위.**
2. dense confidence init(고confidence anchor seed) + enlarged tau plateau (exp38/39 후보) — 커버리지 검증 결과 이 조합만 앞뒤가 맞음. 아직 학습 안 함.
3. ~~Round 7 재검증~~ → exp28/29로 해소: plateau loss는 정렬 여부에 거의 영향 안 받음. "tau > λ" 결론은 그대로 유효 (단, ORB 트랙에서는 tau 크기 방향이 MPS와 반대 — exp32/33 참조).
4. Pop2 여전히 부분 미해결이지만 exp37이 강력한 실마리 제공.

## 최근 흐름 (최신순)

- **2026-07-09**: exp30~37 — **OpenMAVIS(ORB) 데이터셋 재현 트랙 완료**. MPS 트랙(exp08~29)에서 검증한 방법(anchor init, plateau)을 실제 목표 데이터(`data/03_rgb_3dgs_full`)로 재현. **핵심 결과**: exp37(SLAM core seed dense init 148,564pts, plateau 없음) PSNR 32.621, **|Z|>4m=0** — 이 트랙 최고의 floater 억제. plateau의 tau 크기 효과는 MPS와 정반대(ORB는 기본 tau가 더 나음). 고confidence anchor seed로 추가 dense init 2종(144,830 / 65,095pts)도 생성, 3D 균질성 확인(NN spacing이 voxel 크기와 일치, 근/원거리 편향 없음), plateau 커버리지 확인(enlarged tau만 covers ~99%, 기본 tau는 87%). → `experiments/exp30_37_orb_native_track.md`
- **2026-07-09**: exp28/29 — 정렬 anchor로 plateau 재실행. **예상외 결과**: 기본 tau(exp29=32.752)도 enlarged tau(exp28=32.864)도 미정렬 버전(exp19=32.753, exp25=32.969)과 거의 동일 — plateau loss 자체에는 정렬 효과가 미미함 (λ가 작아 위치 오차의 영향이 작았던 것으로 추정). 정렬이 크게 효과 본 곳은 **anchor를 init으로 쓸 때**뿐 (exp27→27c +2.07dB).
- **2026-07-09**: exp28/29 — 정렬 anchor로 plateau 재실행. **예상외 결과**: 기본 tau(exp29=32.752)도 enlarged tau(exp28=32.864)도 미정렬 버전(exp19=32.753, exp25=32.969)과 거의 동일 — plateau loss 자체에는 정렬 효과가 미미함 (λ가 작아 위치 오차의 영향이 작았던 것으로 추정). 정렬이 크게 효과 본 곳은 **anchor를 init으로 쓸 때**뿐 (exp27→27c +2.07dB).
- **2026-07-09**: exp27/27b/27c — anchor를 init으로 사용해 품질 검증. **좌표계 버그 발견**: exp19~26의 anchor는 Atlas world 그대로였음. Umeyama 정렬(rmse 2cm) 후 anchor init 31.611 (대조군 30.583, 미정렬 29.540). → `experiments/exp27_anchor_init.md`
- **2026-07-07**: scripts/·results/ 재구조화. scripts는 pipeline/experiments/diagnostic/analysis/anchors 5분류, results는 experiments/rounds/diagnostic/datasets/logs/archive 6분류 (각 README 참조). 실패 run은 `results/archive/failed_runs/`. 문서 내 경로 참조 일괄 갱신됨.
- **2026-07-07**: data/ 전면 재구축. 순수 OpenMAVIS 체인(VRS→EuRoC→SLAM→전체 프레임 RGB 3DGS)으로 `data/03_rgb_3dgs_full` 생성 (1303장, ORB 7,205pts, reprojection 검증 통과). 재현: `scripts/pipeline/run_full_pipeline.sh`. 기존 심링크 무더기 제거 (`data/README.md` 참조).
- **2026-07-05**: exp19~26 MPS plateau 변형 sweep 완료. tau 확대(exp25)만 유효, opacity_weight/exp_loss/adaptive_prune는 모두 PSNR 악화. → `rounds/round7_plateau_mps.md`
- **2026-07-05**: exp15~18 ORB plateau (Round 6). 어떤 설정도 baseline 못 이김. ellipsoidal >> spherical (+1.0dB). → `rounds/round6_plateau_orb.md`
- **2026-06-30**: exp13 camera-bound filter로 Pop1 -99% 해결 (PSNR -0.16dB). → `rounds/round5_findings_summary.md`

## 다음 실험 후보 (우선순위순)

1. exp37 방식(dense confidence+monodepth init, plateau 없음)을 MPS 트랙에도 적용 — |Z|>4m=0이 ORB 트랙만의 우연인지 재현 가능한 효과인지 확인.
2. exp38/39: dense confidence init(고confidence anchor seed, 5cm 또는 60k판) + enlarged tau plateau — 커버리지 검증상 유일하게 앞뒤가 맞는 조합.
3. exp37(SLAM core seed) vs 고confidence-seed dense init 직접 비교 — 어느 seed가 더 나은 dense init을 만드는지.

## 확정된 사실 (자세한 근거는 knowledge/)

- Floater는 두 집단: Pop1(SLAM init outlier) / Pop2(densification floater) → `knowledge/floater_populations.md`
- init 626,811pts의 출처는 ORB-SLAM이 아니라 **Aria MPS semi-dense**, confidence 필드는 현재 버려짐 → `reference/workspace_map.md`
- VGGT는 현 시점 OpenMAVIS 대체 불가 (닫힌 축) → `archive/vggt_evaluation.md`
