# STATUS — 현재 상태 (1페이지 엄수)

> 마지막 갱신: 2026-07-09. 이 문서가 넘치면 내용을 `knowledge/` 또는 `rounds/`로 밀어낸다.

## 현재 Best

| 기준 | 실험 | PSNR@30k | 비고 |
|---|---|---:|---|
| 순수 PSNR | exp08 (baseline) | **33.012** | floater 미해결 (Pop1+Pop2 잔존) |
| Pop1 해결 | exp13 (camera-bound filter) | 32.855 | Z-outlier -74%, \|Z\|max 42.7→4.85m |
| Plateau 계열 | exp25 (tau enlarged) | 32.969 | **⚠ 미정렬 anchor로 얻은 결과 — 재검증 대상** |

## 지금 열려 있는 질문

1. **OpenMAVIS 재현 트랙(exp30~37) 완료 대기** — anchor init/plateau/dense init이 실제 목표 데이터에서도 통하는지 확인 중. **1순위.**
2. ~~Round 7 재검증~~ → exp28/29로 해소: plateau loss는 정렬 여부에 거의 영향 안 받음 (기본 tau, enlarged tau 둘 다 미정렬과 동급). "tau > λ" 결론은 그대로 유효.
3. anchor 자체 품질은 합격 (exp27c: 같은 개수 랜덤 표면점 대비 +1.03dB). 정렬은 anchor init에서만 중요, plateau loss에서는 안 중요 — 이유는 λ가 작아 위치 오차의 영향력 자체가 작기 때문으로 추정.
4. Pop2 (densification floater) 여전히 미해결 — exp27c의 깨끗한 Z 분포는 "init에 outlier가 없으면 densification 오염도 적다"를 시사.

## 최근 흐름 (최신순)

- **2026-07-09 (진행 중)**: exp30~37 — **OpenMAVIS(ORB) 데이터셋 재현 트랙 시작**. MPS 트랙(exp08~29)에서 검증한 방법(anchor init, plateau, 이번에 추가한 dense confidence+monodepth init)을 실제 목표 데이터(`data/03_rgb_3dgs_full`)로 재현 중. exp30 baseline **32.671** 완료, exp31(진행 중)~37은 대기. anchor는 세션 간 변환 없이 native 재생성(`build_native_anchors_neworb*.py`). → `experiments/exp30_37_orb_native_track.md`
- **2026-07-09**: exp28/29 — 정렬 anchor로 plateau 재실행. **예상외 결과**: 기본 tau(exp29=32.752)도 enlarged tau(exp28=32.864)도 미정렬 버전(exp19=32.753, exp25=32.969)과 거의 동일 — plateau loss 자체에는 정렬 효과가 미미함 (λ가 작아 위치 오차의 영향이 작았던 것으로 추정). 정렬이 크게 효과 본 곳은 **anchor를 init으로 쓸 때**뿐 (exp27→27c +2.07dB).
- **2026-07-09**: exp27/27b/27c — anchor를 init으로 사용해 품질 검증. **좌표계 버그 발견**: exp19~26의 anchor는 Atlas world 그대로였음. Umeyama 정렬(rmse 2cm) 후 anchor init 31.611 (대조군 30.583, 미정렬 29.540). → `experiments/exp27_anchor_init.md`
- **2026-07-07**: scripts/·results/ 재구조화. scripts는 pipeline/experiments/diagnostic/analysis/anchors 5분류, results는 experiments/rounds/diagnostic/datasets/logs/archive 6분류 (각 README 참조). 실패 run은 `results/archive/failed_runs/`. 문서 내 경로 참조 일괄 갱신됨.
- **2026-07-07**: data/ 전면 재구축. 순수 OpenMAVIS 체인(VRS→EuRoC→SLAM→전체 프레임 RGB 3DGS)으로 `data/03_rgb_3dgs_full` 생성 (1303장, ORB 7,205pts, reprojection 검증 통과). 재현: `scripts/pipeline/run_full_pipeline.sh`. 기존 심링크 무더기 제거 (`data/README.md` 참조).
- **2026-07-05**: exp19~26 MPS plateau 변형 sweep 완료. tau 확대(exp25)만 유효, opacity_weight/exp_loss/adaptive_prune는 모두 PSNR 악화. → `rounds/round7_plateau_mps.md`
- **2026-07-05**: exp15~18 ORB plateau (Round 6). 어떤 설정도 baseline 못 이김. ellipsoidal >> spherical (+1.0dB). → `rounds/round6_plateau_orb.md`
- **2026-06-30**: exp13 camera-bound filter로 Pop1 -99% 해결 (PSNR -0.16dB). → `rounds/round5_findings_summary.md`

## 다음 실험 후보 (우선순위순)

1. **exp25 재실행 (정렬 anchor)** — config의 anchor_path만 `anchors_all_depth_pro_mpsaligned.npy`로 교체. 정렬된 plateau가 진짜 floater를 줄이는지 확인.
2. 정렬 plateau에서 tau/λ 재탐색 — 미정렬 때의 "tau 확대 필수"가 여전히 성립하는지 (정렬되면 작은 tau가 오히려 정석일 수 있음).
3. anchor init 확장: virtual 시딩 밀도를 높인 정렬 anchor (수만 pts)로 init — exp27c(-1.40dB)의 격차가 개수 문제인지 확정.

## 확정된 사실 (자세한 근거는 knowledge/)

- Floater는 두 집단: Pop1(SLAM init outlier) / Pop2(densification floater) → `knowledge/floater_populations.md`
- init 626,811pts의 출처는 ORB-SLAM이 아니라 **Aria MPS semi-dense**, confidence 필드는 현재 버려짐 → `reference/workspace_map.md`
- VGGT는 현 시점 OpenMAVIS 대체 불가 (닫힌 축) → `archive/vggt_evaluation.md`
