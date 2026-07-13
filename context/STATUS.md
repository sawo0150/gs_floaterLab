# STATUS — 현재 상태 (1페이지 엄수)

> 마지막 갱신: 2026-07-13 아침. 이 문서가 넘치면 내용을 `knowledge/` 또는 `rounds/`로 밀어낸다.

## 현재 Best

| 기준 | 실험 | PSNR@30k | 비고 |
|---|---|---:|---|
| **ORB 종합 챔피언** | **exp44d2 (RoMA+PPM 하이브리드 init + densify + carve)** | **33.799 (신기록)** | test 32.479(+0.93dB), 먼지 234, 14분 |
| **ORB fast-track** | **exp44d (하이브리드 init, 15k)** | 32.347 | 먼지 147, 학습 8분 |
| ORB baseline | exp30 / exp30r | 32.906 / 32.579 | run-to-run 노이즈 ±0.33dB 실측 |
| **MPS 트랙 채택** | exp08 (baseline) / **exp39b (carve softlite+force)** | 33.012 / **32.913** | **가시 먼지 96→0, 기여 6.42→0.21%** |
| Pop1 해결 | exp13 (camera-bound filter) | 32.855 | 확정 유지 |

## 지금 열려 있는 질문

1. ~~exp40br·exp39b~~ → 완료: 재현 성공(region 462/가시 25), MPS도 -0.10dB에 가시 먼지 0. **양 트랙 레시피 확정.**
2. **train PSNR은 floater 품질 지표로 부적합 판명** (floater=잔차 기생충, 수동 편집조차 -3.7dB). 품질 판단은 region GT 지표 + 시각 검수. **held-out 뷰 평가 도입** 검토 (eval split 재구성).
3. ~~exp37 1순위~~ → **역전 기각**: 표준 GT 지표로 baseline의 4.7배 최악(region_n 16,454). dense init 축은 carve와 결합해야만 의미.
4. 잔여 가시 floater ~28개(exp40b)는 3D 신호 한계 — multi-view 색 일관성은 기각됐고(흰 방), 렌더-GT 잔차 축은 미탐색.

## 확정된 방법론 (요약: rounds/round8_*)

- **Carve Loss** (`3dgs-custom/eval/carve_loss.py`): 빈공간 증거 score `w·(1−maxop)` (수동 라벨 AUC 0.98) 위에 ① softlite opacity 압력(λ0.02) ② 예산 top-K prune(0.75%) ③ 출생 게이트(0.95; split의 29.5%가 허공 출생) ④ carve-potential force(xyz 견인, 진동 평형 위 일관 편향). 추가 입력 불필요(SLAM+카메라).
- 표준 지표: region GT(`floater_metric_region.py`) + ray-density 상호보완. 오프라인 청소: `extract_floaters_rulebase.py`(예산 top-K) + 3D 삭제 영역(`build_floater_region.py`).

## 최근 흐름 (최신순)

- **2026-07-13 오후 (vr 채널)**: 사용자 질문("SLAM 포인트 없이 12F floater 잡기")에서 출발 — ① **SLAM-포인트-프리 탐지 성립**: depth-pro raw 0.855 → pose-기하 자가 보정(스테레오+IMU 캘리브레이션 덕에 pose가 미터) 0.893, SLAM 보정 상한 0.908=12F 신기록. ② vr을 CarveLoss score 채널로 통합(depth_dir config)했으나 **학습 효과 무** — "탐지≠제거" 간극 확정: underfit 장면에선 이미지가 먼지를 요구해 압력이 못 이김. ③ **12F에서 carve 자체 -1dB → 자가진단 경고 시 carve off가 파이프라인 규칙로 확정.** vr 용도는 오프라인 청소·pseudo-label·SLAM-프리 탐지. → [exp43 카드](experiments/exp43_cross_scene_plan.md)
- **2026-07-13 오전 (231 사이클)**: **exp43 종결** — ① 305 재현 런으로 depth-anchor carve **성공 확정**(먼지 -83% 정밀 재현). ② rot '가시 먼지 역증가' 미스터리 해결: 응집·force·재분배 가설 3연속 기각 끝에 **대조군(baseline 재실행 106→1,091)이 run-to-run 분산임을 입증** — carve 무죄, **먼지 지표 단일 런 비교 금지**(pitfalls). ③ 라벨 없는 **앵커 자가진단 2규칙 완성**(`anchor_self_diagnosis.py`, 4/4 장면): SLAM 자기NN<0.05m → SLAM / depth 교차불일치<0.04 → depth / 둘 다 실패 → 문제 클래스(12F가 정확히 해당). 새 장면 파이프라인 라벨 없이 전자동으로 폐합. 시차 쌍 hyb2는 rot에서 여전히 부적합(회전 궤적 축 보류). → [exp43 카드](experiments/exp43_cross_scene_plan.md)
- **2026-07-13 새벽 (오버나이트)**: **exp43 교차 장면 트랙 완주 — 305에서 carve 학습 재현 성공** (depth-anchor 처방: 먼지 -83%·가시 -76%·PSNR 동급). 사용자 라벨 3종(1253_rot/305/12F) 검증: rot는 pseudo-label 정밀도 100%·AUC 0.98(같은 방 자동화 가능), 305·12F는 SLAM 커버리지 부족으로 champion score 실패(0.80/0.86) → **depth-pro 표면 앵커로 회복(0.905)**. 실패 5건 정직 기록: dynamic carve 자기강화 가설 기각, nomaxop 기각, rot hybrid 이식(+1.37dB나 먼지 ×10, 작은 시차 삼각측량), rot depth 앵커 불량(회전 궤적), 305 1차 OOM. **결론: carve 성패 = 앵커 품질. 다음 열쇠 = 라벨 없는 앵커 자가진단 + 시차 기반 쌍 선택.** → [exp43 카드](experiments/exp43_cross_scene_plan.md)
- **2026-07-12 오후**: **exp44 고속 geometry 트랙 완주 — 44h 레시피 채택** (총 ~11분/장면: SLAM 후 init 전처리 3분 + 학습 7.5분 → PSNR 32.08·먼지 -63%). 4원칙 확립: 먼지는 init에서(필터 -96%)·색은 선불(+1.6dB)·갭은 배치(스냅 init)·용량은 densify 3k로 충분. RoMA(44c) 불필요 판정. 교차 장면: 305 라벨 대기, 1253_rot pseudo-label 완비, 복도류(12F/2F/3F/snu) 전멸 → 저텍스처 한계 별도 축. → [exp44 카드](experiments/exp44_fast_geometry_plan.md)
- **2026-07-12 심야~아침**: **carve loss 학습 검증 트랙(exp38~40) 하룻밤 완주 — exp40b 채택** (학습이 회당 ~10분임이 판명되어 7 run 수행). 렌더 A/B로 "floater=train PSNR 기생충" 발견(수동 편집조차 -3.7dB → train PSNR 지표 부적합), gradient 프로브로 진동 평형 확인 → carve-potential force(3D force 부활) 구현·실증(무비용 -45% 가시 먼지), softlite+force 결합이 PSNR 무손실로 region 먼지 -86%. 출생 로그로 "허공 split 29.5%, 먼지가 먼지를 낳는 연쇄" 규명. → [exp38-40 카드](experiments/exp38_40_carve_track.md), [round8_gpu_queue_plan](rounds/round8_gpu_queue_plan.md)
- **2026-07-11**: **Carve Loss 설계 완료 (분석만, 학습 없음)** — 카메라→SLAM 포인트 ray의 free-space carving 증거비 ρ(x)에 anchor 거리를 곱한 score w(x)가 수동 floater 판별 **AUC 0.974** (plateau 0.511). 수동 floater가 opacity 중앙값 0.044의 "한계 생존자"임을 발견(카드의 op>0.5 서술은 오류였음, 정정 완료). **부수 피해 재정량**: 원안 prune 규칙은 표면 시각 기여량 3.83% 손실로 폐기, 안전 규칙(w>0.9 & op<0.1 & contrib<p90)은 **recall 69.4%·기여손실 0.39%·구멍 0**. densify 게이트는 출생 91% 차단 가능하나 기여량 13.75% 영역에 걸려 학습 검증 필요. 렌더 PSNR 검증용 pruned 모델 4종 준비 완료(GPU 대기). → [carve_loss_design](rounds/round8_carve_loss_design.md)
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

> **프로젝트 목표 재정의 (07-12)**: Aria glass 실시간 촬영 스트림 → 분 단위 turnaround로 geometry 좋은 3DGS recon. 실시간 경로엔 MPS 사용 불가 → ORB 트랙이 본선.

0. **exp44 (고속 geometry 트랙)**: dense init × no-densify × carve — floater 출생 채널(densification) 제거 + EDGS 사상. 목표 5분/장면 → [exp44](experiments/exp44_fast_geometry_plan.md)
0'. ~~exp43 (교차 장면)~~ → **완료** (305 재현 성공, 위 참조). 후속: 앵커 자가진단 규칙 + 시차 기반 쌍 선택 + 12F depth-anchor 적용.
1. ~~held-out 뷰 평가 도입~~ → 완료 (exp41/42: segment split + SSIM/LPIPS 표준화) (eval split 재구성) — train PSNR 부적합 판명 후 유일하게 남은 정량 품질 축. carve 유/무의 novel-view 일반화 차이가 진짜 승부처.
2. exp40b 잔여 가시 floater ~25개의 정체 확인 (패치 투영 or SuperSplat) + 렌더-GT 잔차 기반 신호 탐색.
3. dense init(구 exp37) + carve 결합 — dense init의 PSNR 이점을 carve로 정화해서 취할 수 있는지.
4. carve field의 타 장면 일반화 (새 시퀀스에서 전체 파이프라인 재현).

## 확정된 사실 (자세한 근거는 knowledge/)

- Floater는 두 집단: Pop1(SLAM init outlier) / Pop2(densification floater) → `knowledge/floater_populations.md`
- init 626,811pts의 출처는 ORB-SLAM이 아니라 **Aria MPS semi-dense**, confidence 필드는 현재 버려짐 → `reference/workspace_map.md`
- VGGT는 현 시점 OpenMAVIS 대체 불가 (닫힌 축) → `archive/vggt_evaluation.md`
