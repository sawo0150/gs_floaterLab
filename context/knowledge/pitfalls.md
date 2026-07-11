# Pitfalls — 피해야 할 함정

> 실수/혼동이 실제 있었던 것만 기록. 마지막 갱신 2026-07-07.

## 데이터/좌표

- **SuperSplat에서 export한 ply는 좌표계가 회전/반전되고 속성 인코딩도 바뀐다** (2026-07-11 확인: `point_cloud_cleaned.ply`는 원본 대비 축 교환 + 최대 26m 좌표차, opacity/scale/rot 값도 재인코딩됨). 이 파일의 **좌표·속성을 직접 쓰면 안 되고**, 색 feature(f_dc) KD-tree 매칭으로 삭제 마스크만 추출한 뒤 **원본 ply의 행을 마스킹**해서 써야 한다 (`analyze_manual_floaters.py`, `make_carve_prune_variants.py` 방식). 렌더 비교용 변형도 반드시 원본 행 기반으로 재구성할 것.
- **anchor/포인트 npy를 학습에 쓰기 전, 반드시 학습 데이터셋 world와의 정렬을 검증하라** (표면 NN 거리 또는 reprojection). exp19~26의 plateau anchor는 raw Atlas world 좌표 그대로였는데 MPS world 학습에 무변환 사용됨 — 표면 대비 median 0.48m + scale x0.95 오차 (2026-07-09 exp27에서 발견). `eval/plateau_loss.py`는 anchor_path를 무변환 로드한다. 정렬본/변환: `results/diagnostic/plateau_ellipsoid_v4_20260705_041132/{anchors_all_depth_pro_mpsaligned.npy, T_atlas_to_mps.npz, ALIGNMENT_NOTE.md}`
- **OpenMAVIS `f_*.txt`(전체 프레임 trajectory)는 첫 keyframe body 기준으로 재원점화된 world**이고, `orb_export/*.jsonl`(keyframes/map_points)은 raw Atlas world다. 둘을 합칠 땐 keyframe timestamp 매칭으로 정렬 변환을 계산해야 한다 — `scripts/pipeline/full_traj_to_rgb_3dgs.py`가 처리하고 잔차를 검증함.
- **init 626,811 pts의 출처는 ORB-SLAM이 아니라 Aria MPS semi-dense**다. `aria_to_3dgs.py`가 confidence(`inv_dist_std`/`dist_std`)를 버리고 xyz만 덤프한다. 필터링하려면 이 스크립트를 수정해야 함. (`reference/workspace_map.md`)
- `exp13`은 번호가 중복된다: 메인 트랙 `exp13_pcd_filter_full30k`와 VGGT 트랙 `exp13_vggt64`. result dir 이름으로 구분.
- `data/rgb_3dgs_openmavis_batch_301_1253`(57장)은 초기에 "camera가 57개만 잡힌다"고 혼동했던 ORB keyframe 데이터. full 1311장 MPS 데이터와 별개.
- ORB 좌표계의 Z≥2.0m clip은 Pop2를 거의 못 잡는다 (exp15에서 12개만 제거). Z 기준 pruning은 좌표계별로 재설계 필요.

## 해석

- **low_opacity_ratio가 낮다고 좋은 게 아니다.** low-opacity Gaussian 대부분은 표면 위에 있다 (floater 아님). PSNR/visual과 같이 봐야 함.
- large_scale_ratio가 낮아도 train/test PSNR이 낮으면 "compact하지만 잘못된 geometry"일 수 있다 (VGGT64 사례).
- beta1 낮춤 실험의 의도는 momentum 강화가 아니라 **early 잘못된 gradient 누적 억제**. 재해석 주의.
- `openmavis64_*` EVO 결과는 invalid (MPS subset에서 생성돼 APE≈0). 올바른 파일은 `openmavis_orb_64.*`. rotation APE는 frame convention 이슈 가능성 → translation 위주로 판단.
- **\|Z\|>4m 개수나 "anchor plateau 안/밖 비율"은 floater 지표로 부정확하다** — 둘 다 위치만 보고 opacity(렌더링 기여)와 실제 ray 관측 여부를 무시한다. enlarged tau plateau는 이 지표들로는 좋아 보였지만, ray-density 기반 검증(`scripts/diagnostic/check_gaussian_ray_coverage.py`)으로는 오히려 opacity>0.5인 진짜 floater가 6배 더 많았다 — plateau 반경이 커질수록 관측된 적 없는 공간까지 침범하기 때문(`check_plateau_vs_raydensity.py`). **floater 판정은 "카메라 ray가 한 번이라도 지나간 3D voxel인가" + opacity로 하라.** (`experiments/exp30_37_orb_native_track.md`의 "floater 지표 재검토" 참조)

## 실험 설계

- **모양 기반 floater 판별 prior는 이 장면에서 전멸했다** (2026-07-11) — 평면성(AUC 0.64), 법선 정렬(0.64), SH 고차 에너지(0.49), scale 등방성(0.51). floater는 split 산물이라 표면 조각과 형태가 같다. 작동하는 신호는 위치·맥락 계열: free-space carve(w), 이웃 최대 opacity 부재, 고립도. 또한 **prune 규칙의 부수 피해는 "가시 점 개수"가 아니라 시각 기여량(op×면적×노출수) 기준으로 평가하라** — 저op 점 수만 개의 합은 유의미하다 (`experiments/carve_loss_design.md`).
- sparse depth prior를 강하게 걸면 outlier sparse geometry를 고정한다 (exp12). 필터링 후 + 약한 weight + delayed start가 전제조건.
- plateau loss: λ ≤ 0.10, densification(7k) 이후 시작. opacity_weight/exp_loss/반복 hard pruning은 전부 역효과였다 (`rounds/round7_plateau_mps.md`).
- VGGT frame 수 증가는 RAM이 아니라 **VRAM/attention memory** 병목. 96+ frames OOM.

## 코드 (3dgs-custom)

- **dirty worktree를 revert하지 말 것** — floater metric, sparse prior, renderer compatibility 수정이 커밋 안 된 상태로 들어있음.
- `gaussian_renderer/__init__.py`에 installed `diff_gaussian_rasterization`이 `beta`/`alpha_depth`/`modes`를 지원 안 할 때의 fallback이 있음.
- plateau `post_backward`는 반드시 densification 블록 **이후**에 호출 (아니면 CUDA device-side assert). `tmp_radii=None` 체크도 필요. (`rounds/round6_plateau_orb.md` 버그 기록)

## 운영

- 실험은 W&B run name과 result dir 이름을 반드시 맞춘다.
- 실험 완료 시 갱신은 3개만: exp 카드 + INDEX 한 줄 + STATUS. (`context/README.md`)
