# Experiment Index

전 실험 목록. 상세는 각 카드 참조. baseline 대비 Δ는 PSNR@30k 기준.

## Full 30k, MPS init 1311장 (메인 트랙)

| Exp | 날짜 | 한 줄 설정 | PSNR@30k | vs exp08 | Verdict | 카드 |
|---|---|---|---:|---:|---|---|
| exp01 | 06-16 | full baseline (886k Gaussians) | - | - | 기준선 | [exp01-12](exp01-12_param_sweep.md) |
| exp02 | 06-16 | sparse densification | 33.377 | +0.37 | 최고 PSNR이나 large-scale 위험 | 〃 |
| exp03 | 06-16 | + large-scale 개선 | 33.052 | +0.04 | 보류 | 〃 |
| exp04 | 06-16 | 구조 개선 계열 | 32.831 | -0.18 | 기각 | 〃 |
| exp05 | 06-16 | beta1=0.95 | 조기중단 | - | 기각 | 〃 |
| exp06 | 06-16 | beta1=0.85 | 32.879 | -0.13 | beta1=0.85 채택 | 〃 |
| exp07 | 06-16 | pruning 완화 | 조기중단 | - | 기각 | 〃 |
| **exp08** | 06-16 | dens_until7000 + prune001 + beta1_low | **33.012** | 기준 | **현재 best baseline** | [exp08](exp08_best_baseline.md) |
| exp09 | 06-16 | densify_until=5000 | 조기중단 | - | 너무 이름, 기각 | [exp01-12](exp01-12_param_sweep.md) |
| exp10 | 06-16 | position LR 낮춤 | 32.574 | -0.44 | 기각 | 〃 |
| exp11 | 06-16 | position LR 완화 | 32.682 | -0.33 | 기각 | 〃 |
| exp12 | 06-16 | + sparse depth prior (0.01→0.002) | 32.587 | -0.43 | 기각 (outlier 고정 위험) | 〃 |
| exp13 | 06-30 | + camera-bound pcd filter | 32.855 | -0.16 | **Pop1 해결 확정** | [exp13](exp13_pcd_filter.md) |
| exp19 | 07-05 | + DepthPro ellipsoidal plateau (λ=0.01) | 32.753 | -0.26 | 보류 | [exp19](exp19_mps_depthpro.md) |
| exp20 | 07-05 | + λ schedule 0.10→0.03→0 | 31.693 | -1.32 | 기각 | [exp20](exp20_mps_scheduled.md) |
| exp21 | 07-05 | + opacity_weight, λ=0.10 | 30.770 | -2.24 | 기각 | [exp21](exp21_mps_opacity_weighted.md) |
| exp22 | 07-05 | + exp loss kernel, λ=0.05 | 29.917 | -3.10 | 기각 | [exp22](exp22_mps_exploss.md) |
| exp23 | 07-05 | + adaptive prune (d>1.5m) | 26.655 | -6.36 | 기각 (후반 붕괴) | [exp23](exp23_mps_adaptive_prune.md) |
| exp24 | 07-05 | exp loss + adaptive prune | 미완 (27k Terminated) | - | 보류 (낮은 우선순위) | [exp24](exp24_mps_exp_and_prune.md) |
| **exp25** | 07-05 | + enlarged tau (2-3x) + λ 0.10→0.03 | **32.969** | **-0.04** | **plateau 최선, floater 지표 검증 필요** | [exp25](exp25_mps_tau_enlarged.md) |
| exp26 | 07-05 | + enlarged tau + λ=1.0→0.03 | 32.706 / 32.674 (2회) | -0.31 | 기각 (λ=1.0 과함) | [exp26](exp26_mps_lambda1.md) |
| exp27 | 07-09 | anchor 7,338 pts를 init으로 (미정렬) | 29.540 | -3.47 | **좌표계 버그 발견** — anchor는 Atlas world였음 | [exp27](exp27_anchor_init.md) |
| exp27b | 07-09 | MPS 랜덤 7,338 init (대조군) | 30.583 | -2.43 | 개수 통제 대조군 | 〃 |
| exp27c | 07-09 | 정렬된 anchor 7,338 init | 31.611 | -1.40 | **anchor 배치 합격** (대조군 +1.03dB), \|Z\|>4m 8개 | 〃 |

> **⚠ 좌표계 발견 (07-09)**: exp19~26의 plateau anchor는 MPS world가 아닌 raw Atlas world였다 (표면 대비 median 0.48m, scale x0.95 오차). **Round 7 결론은 정렬 anchor로 재검증 필요.** 상세: [exp27](exp27_anchor_init.md)

## ORB init 656장 (Round 6, plateau 검증 트랙 — baseline 29.023)

| Exp | 날짜 | 한 줄 설정 | PSNR@30k | vs orb_baseline | Verdict | 카드 |
|---|---|---|---:|---:|---|---|
| exp_orb_baseline | 07-05 | plateau 없음 | 29.023 | 기준 | 기준선 | [round6](../rounds/round6_plateau_orb.md) |
| exp15 | 07-05 | spherical plateau, ORB 앵커 | 27.908 | -1.10 | 기각 (과밀집→투명화) | 〃 |
| exp16 | 07-05 | ellipsoidal plateau, ORB 앵커 | 28.924 | -0.10 | ellipsoidal 채택 | 〃 |
| exp17 | 07-05 | ellipsoidal, Metric3D 앵커 | 27.668 | -1.35 | 기각 (앵커 품질) | 〃 |
| exp18 | 07-05 | ellipsoidal, DepthPro 앵커 | 28.934 | -0.09 | DepthPro 앵커 채택 | 〃 |

## 기타 (닫힌 축)

| Exp | 내용 | 결과 | 기록 |
|---|---|---|---|
| exp13_vggt64 (번호 중복 주의) | VGGT64 3DGS 7k | Test PSNR 17.04 | [archive/vggt_evaluation.md](../archive/vggt_evaluation.md) |
| exp14 | OpenMAVIS64/MPS 3DGS 7k | Test PSNR 18.65 | 〃 |

> **번호 중복 주의**: `exp13`은 pcd_filter (메인 트랙)와 vggt64 (VGGT 트랙) 두 개가 존재. result dir 이름으로 구분.

## OpenMAVIS(ORB) 데이터셋 재현 트랙 — exp30~37 (진행 중, baseline 32.671)

MPS 트랙(exp08~29)에서 검증한 방법들을 실제 목표 데이터셋(OpenMAVIS pose + ORB init, `data/03_rgb_3dgs_full`)으로 재현하는 트랙. exp08과 직접 비교 금지 — exp30이 이 트랙의 기준선.

| Exp | 한 줄 설정 | PSNR@30k | 상태 | 카드 |
|---|---|---:|---|---|
| **exp30** | baseline (ORB 원본 7,205 init) | **32.906** | 완료 — 기준선 (run-to-run 노이즈 ±0.24dB 확인됨) | [exp30-37](exp30_37_orb_native_track.md) |
| exp31 | 일반 anchor(obs≥3, 7,108) init | 32.671 | 완료 | 〃 |
| exp32 | + plateau 기본 tau, 일반 anchor | 32.903 | 완료 (baseline과 동급) | 〃 |
| exp33 | + plateau enlarged tau, 일반 anchor | 32.536 | 완료 (MPS와 반대로 열세, floater는 최소) | 〃 |
| exp34 | 고confidence anchor(obs≥10&fr≥0.5, 1,438) init | 31.970 | 완료 (exp31보다 -0.7dB) | 〃 |
| exp35 | + plateau 기본 tau, 고confidence anchor | 32.799 | 완료 (exp32와 비슷한 패턴) | 〃 |
| exp36 | + plateau enlarged tau, 고confidence anchor | 32.591 | 완료 | 〃 |
| **exp37** | dense confidence+monodepth init (148,564), plateau 없음 | **32.621** | **완료 — \|Z\|>4m=0, 이 트랙 최고 floater 억제** | 〃 |
| exp32_lineage_diag | exp32 + lineage & decoupled grad tracking | 32.903 | 완료 — 진단 및 계보 추적 성공 | [exp32_lineage_diag](exp32_lineage_diag.md) |
| carve_loss_design | (분석만) free-space carve 기반 신규 loss 설계, 수동 라벨 리그전 Round 1~10 | 학습 없음 | 완료 — AUC 0.98, 예산 0.75%로 recall 55%, exp38/39 구현 완료 | [round8_carve_loss_design](../rounds/round8_carve_loss_design.md) · [요약](../rounds/round8_carve_loss_summary.md) |

## Carve Loss 학습 검증 트랙 — exp38~40 (07-12, baseline exp30/30r)

| Exp | 한 줄 설정 | PSNR@30k | region_n/가시 | Verdict | 카드 |
|---|---|---:|---:|---|---|
| exp30r | baseline 재현 (노이즈 측정) | 32.579 | 3,749 / 180 | PSNR 노이즈 ±0.33dB 실측 | [exp38-40](exp38_40_carve_track.md) |
| exp38a | soft0.05+prune+gate | 32.266 | 559 / 27 | 억제 최강, -0.3dB 과비용 | 〃 |
| exp38b | prune+gate만 | 32.663 | 1,744 / 187 | soft가 가시 먼지 주역임을 분리 | 〃 |
| exp38c | softlite0.02+prune+gate | 32.557 | 946 / 33 | PSNR 무손실 스위트스팟 | 〃 |
| exp39 | MPS 트랙 carve (full soft) | 32.666 | (MPS) 가시 96→2 | MPS 전이 성공 | 〃 |
| exp40br | 챔피언 재현 | 32.448 | 462 / 25 | 재현 확인 | 〃 |
| **exp39b** | MPS softlite+force | **32.913** | (MPS) 가시 **0** | **MPS 채택** | 〃 |
| exp40a | prune+gate+**force** | 32.667 | 1,309 / 134 | 3D force 부활 실증 (무비용) | 〃 |
| **exp40b** | softlite+prune+gate+force | **32.576** | **498 / 28** | **채택 — 챔피언 레시피** | 〃 |

> exp30~37 전체 완료 (2026-07-09). 큐 진행 중 발견된 자동 체인 중복 실행 버그와 run-to-run 노이즈(±0.24dB)는 카드 참조.

## 계획 및 신규 트랙 카드

| Exp | 내용 | 상태 | 카드 |
|---|---|---|---|
| exp43 | 교차 장면 완주: rot 점수 AUC 0.98·pseudo-label 정밀도 100% / 305 **depth-anchor carve 재현 성공**(먼지 -83%·PSNR 동급) / 실패 5건 정직 기록 — 결론: carve 성패=앵커 품질 | **완료** | [exp43](exp43_cross_scene_plan.md) |
| exp45 | 채택 큐 4종: 45a 노출 기각(-6dB)·45b dynamic 조건부(깨끗한 init 전제)·44e3 보류(먼지 ×4)·45c progressive resolution 진행 중 | 진행 | [exp44 카드 참조](exp44_fast_geometry_plan.md) |
| exp46 | basin 재프레임: floater=photo loss의 정당한 숏컷 분지 → 압력 대신 '올바른 geometry를 가까운 basin으로'. (a)도달불가=init/(b)환원불가=appearance 이분법 + 다음 실험 7축(원거리 photometric 감쇠 포함) | **완료** | [exp46](exp46_basin_reframe_plan.md) |
| exp47 | 속도 최적화 트랙: 품질 하한 고정하고 속도만 — S1 cuda·S2 carve저빈도·S3 iter·S4 keyframe subset·S5 중간budget. incremental per-chunk 레시피 확정 목적(목표 5분 내) | **완료** | [exp47](exp47_speed_track_plan.md) |
| **exp44** | **고속 geometry 트랙 완료 — 44h 레시피 채택** (스냅 init+densify≤3k+carve, 32.08/7.5분) · 품질 기함 44f(32.67/14분) | **완료** | [exp44](exp44_fast_geometry_plan.md) |
| exp48 | Incremental 3DGS: PPM K=3 + RoMA (Hybrid) 및 온라인 루프 홀인 Selective Opacity Reset 도입 (18.23dB). 종결 — eval 버그(llffhold-8이 test.txt 무시) 규명, 진짜 벽은 저텍스처 영역 + vanilla 3dgs가 online에 안 맞는 틀 | **종결** | [exp48](exp48_incremental_plan.md) |
| exp49 | Photo-SLAM(ORB-SLAM3+GS, CVPR24) 이관: opacity_reset off·상수 LR·times-of-use 슬라이딩 윈도우로 exp48 문제를 설계로 회피한 검증된 online baseline. 빌드 완료(Blackwell+CUDA12.8 호환패치). replay로 Fisheye624 우회 → 배치 baseline → incremental → 방법론 이식 | 계획 | [exp49](exp49_photoslam_plan.md) |
| exp50 | DiskChunGS: Out-of-Core 디스크 스왑 SLAM. B1에서 Fisheye624 라이브 트래킹 root-cause 2건 수정(하드코딩 static_cast, KannalaBrandt-only 게이트) 후 최초 성공(리셋 9~31→0, 매칭 33~76개 지속). 다음: RGB 매핑 카메라 분리 주입 | 진행 | [exp50](exp50_diskchungs_plan.md) |
| exp51 | Incremental mapping 30dB+로: 축A+B(25.29dB)+축C(밀도 무효과)+축F(예산 3.3배→25.59, 소폭). **시각진단 확정: 잔여 갭 = depth-init 바늘형 floater**(GT/render 대조로 확인) — 배치의 carve loss(exp38~44d2 검증됨)를 incremental에 이식하는 축E가 다음 | 진행중 | [exp51](exp51_dense_supervision_plan.md) |
| exp52 | VIGS-SLAM(ECCV2026) 클론·빌드(6가지 환경 이슈 해결)·평가. 소스 분석으로 exp51 가정 검증(isotropic loss+scale clamp 신규, opacity reset은 기본 config 비활성, init dedup은 dead code 확인, normal supervision 신규 발견). 폴리싱 포함 베이스라인: 1253 held-out 26.85dB·keyframe 30.90dB. **`--pure_online` 실측(정정): 순수 온라인 PSNR 22.73dB — 우리 exp51 축A+B(25.29dB)보다 낮음.** 함수 단위 병목 분해(PGBA 신규 발견): gs_mapping rasterize+backward가 최대 원인. **imu_cpp 빌드(IMU 프리적분 −98.5%)+TensorRT 3종(Omnidata −77%·fnet −78%·update_module 효과없음) 전부 적용해 온라인 루프 209.4→180.1초(−14.0%, PSNR 무변화)** — 그런데도 gs_mapping 비중은 30.2%→50.2%로 오히려 커짐(다른 게 줄어든 결과) → gs_mapping을 0으로 줄여도(180.1−90.5=89.6초>65.1초 녹화시간) 순차 구조로는 실시간 불가임을 계산으로 확인, **구조적 전환**: 업스트림 레이스 컨디션(`remove_all_gaussians()` 락 누락, IMU 재초기화 시 `_gs_worker`와 경합) 발견·수정 후 `_gs_parallel: true`(비동기 tracking/mapping 오버랩) 검증 — **온라인 루프 180.1→133.0초(−26.1%), PSNR 무변화, 매핑 비용의 66%가 GPU 유휴시간에 흡수됨**. 여전히 실시간의 2.04배(2.77배에서 개선) — 완전 해결은 아니나 유효한 구조적 레버 확정. **트래킹 전용 fps(20/10/5) 스윕으로 exp50(ORB) vs VIGS 비교**: ORB는 keyframe당 비용 고정(~25ms)이고 keyframe 개수도 fps에 어느 정도 비례(−20.8%)해서 fps 낮추면 실시간 여유가 커짐(20fps부터 이미 0.68배), VIGS는 5fps까지 내려도 여전히 미달(1.11배) — **⚠정정: 원인은 "프레임당 비용 증가"가 아니라 call당 비용은 거의 안 변하고(bundle_adjust만 12.7→15.1ms 소폭↑) keyframe 개수 자체가 fps와 거의 무관(−6.6%, optical-flow 임계값 기반)해서 총 작업량이 안 줄기 때문(frontend 총합은 오히려 48.3→32.9초로 감소, "프레임당 평균"이 분모 착시였음)**. 트래킹 아키텍처도 exp50 경로가 실시간엔 유리함을 확정. **원 논문 대조**: DROID-SLAM 자체도 "2-GPU + 다운샘플/프레임스킵 조건부 실시간"(TartanAir에선 원 저자도 8fps로 실패)이었고, VIGS 저자 공식 벤치마크(RTX 5090)도 tracking만 39.83fps(여유)·tracking+mapping 12.02fps(미달)로 **"매핑이 병목"이라는 우리 결론을 저자 자신의 최상급 GPU 수치가 독립 재확인**. **MPS 기준 evo_ape로 궤적 정확도 비교: 스케일 보정 후(Sim3) ORB 13cm vs VIGS 1.3cm — VIGS의 dense correlation 트래킹이 형태 정확도 10배 우위**(단 절대 스케일은 IMU 1회성 초기화발 편향 3~5%, ORB는 캘리브레이션된 스테레오 기준선이라 더 안정). 소스 추적으로 원인 규명: VIGS는 Gaussian mapping의 depth supervision을 별도 monocular 추정이 아니라 **포즈와 같은 BA에서 공동 최적화된 `disps_up`을 그대로 사용**(`vigs.py:169`) — 우리 exp50/51의 "트래킹과 무관한 독립적 depth prior" 구조와 근본적으로 다름, floater 문제의 뿌리와 동일 메커니즘. **⚠중대정정(07-20): "27초 오버헤드"의 미계측 21.1초를 실제로 계측(pbar/save_trajectory 추가 계측→다 합쳐 0.14초, 가설 기각)하다가 진짜 원인 발견 — `demo.py`의 리더 프로세스 `time.sleep(20)`이 타이밍 마커보다 먼저 실행되는 `reader.join()` 위치 버그로 모든 "온라인 루프 총합"에 인위적 20초가 섞여 있었음(구성요소별 개별 수치는 무관, fps스윕/evo비교도 무관). 코드 수정 후 재검증: 순차 150.56초(2.31배, 기존 2.77배)·gs_parallel 98.94초(**1.52배**, 기존 2.04배) — 오버랩 효율도 66%→88.3%로 상향, 미계측 잔여는 21.1초→0.2초로 사실상 해소**. **GS Mapping 루프 최대 세분화(12단계, `_process_track_data_impl` 전체로 계측 범위 확장)**: rasterize+backward+loss_compute가 81.4%로 여전히 지배적(process_track_data 부가작업은 4.2%뿐, 무시할 수준) — 다만 `map()` 내부에서 기존 5단계 합과 총합 사이에 **12.0초(12.9%)의 새 미계측 포켓 발견**(isotropic loss 계산+viewpoint 샘플링으로 추정, 다음 계측 후보) | 진행중 | [exp52](exp52_vigs_slam_eval.md) |
| exp53 | Frontend Tracking(exp52에서 확정한 진짜 실시간 병목) 자체를 가볍게 만드는 트랙. **전체 완료**: 축A(`iters1`/`iters2`, 4/2→1/0, −20.7%)·축B(`motion_filter.thresh` 2.4→3.6, −15.4%, keyframe 발생률 자체를 줄여 tracking+mapping 양쪽에 동시에 걸리는 최대 레버)·축C(`frontend_window`/`radius` 25/2→15/1, −1.7%) 전부 채택, evo APE(Sim3)는 축A 세 단계 전부 1.59cm로 고정 후 축B+C에서 1.93cm까지 소폭 상승(ORB 13cm 대비 여전히 6.7배 우위). 축D(correlation 해상도)는 조사 결과 사전학습 GRU 가중치에 shape가 고정 결합돼 **재학습 없이는 구현 불가로 판정**(실행 안 함), 축E(커널 튜닝)는 목표 달성으로 불필요. exp54와 통합한 최종 레시피 = **61.34s, 실시간 배수 0.94배(1.0배 미만 최초 달성)** | 완료 | [exp53](exp53_frontend_realtime_plan.md) |
| exp54 | GS Mapping 연산 시간 ablation(exp52의 "rasterize+backward+loss_compute=81.4%" 발견을 구체화). **7축 전부 완료**: 축1(`pcd_downsample` 64→128) 채택(−3.3%) · 축2(`pcd_downsample_init`)·축3(`map() iters`)·축5(`max_viewpoints`) 기각(효과 없음/역효과, 축3에서 tracking이 91% 비중임을 규명해 exp53 우선순위 근거 마련) · 축6+2 결합(densify 공격성 3배 상향+init 밀도 2배 희석) 실험으로 "상쇄" 가설은 확인했으나(최종 gaussian 수 축1보다도 적게 억제 성공) 시간은 그대로라 **이 지점에서 밀도/예산 축 전체가 소진됐음을 확정**, 기각 · **축4(render_downsample) 신규 구현**(`vigs.py::call_gs`에 매핑 전용 다운샘플 추가, eval 해상도 불일치 버그도 수정) — 검증된 유효 레버(−4.2%/−0.8dB)지만 이미 실시간이라 미채택, 코드만 보존 · **축7(PPM) 신규 구현**(`gaussian_model.py`에 Sobel-gradient 기반 content-adaptive 샘플링 이식, `Dataset.ppm_sampling` 플래그) — 동일 예산에서 PSNR 순개선(+0.16dB, exp44 "PPM=품질 왕" VIGS에서도 재현), **채택**. exp53과 통합한 최종 레시피 = **61.34s, 실시간 배수 0.94배** | 완료 | [exp54](exp54_gsmapping_speed_ablation_plan.md) |
| exp55 | 내용-적응 per-frame gaussian 예산(Sobel↔PSNR-이득 상관 실측 r=0.538) + carve loss 이식. **Phase 1+2+3 전부 실행·채택**: Phase1(캘리브레이션 2런)로 배율곡선(0.91~1.57x) 도출 → Phase2(베이스 128→256/init 32→64 + 내용-적응 배율 + per-keyframe 명시적 cap `enforce_kf_caps` 신규)로 **평균 gaussian −35.9%, 최종 −35.3%, PSNR/궤적 손실 없음(오히려 소폭 개선)** — 사용자 목표(평균 gaussian/frame 감소) 달성. Phase3(carve loss 온라인 근사, depth-violation 전용 신규 설계) — 기존 region GT가 1253/VIGS 좌표계에 적용 불가함을 확인 후 **carve_loss.py 자신의 검증된(AUC 0.98) 신호를 오프라인 진단 지표로 새로 구현**(`exp55_score_carve_vigs.py`, 신규 재사용 도구)해 직접 검증 — 가시 floater 수/비율/평균 score 네 지표 전부 일관 개선(−4~8%), PSNR·시간 비용 없음 → `carve_lambda=0.05` 채택. Phase 2Q는 미실행 **부록(07-23): 직렬 실행 분리 결과 tracking 27.9s/mapping 80.1s — exp54 "tracking-bound"는 병렬 한정 결론이었음 발견(GPU 경합으로 병렬 tracking이 1.8배 부풀고, 큐 드롭으로 mapping 호출이 직렬 대비 1/5로 줄어든 합성 결과)**. **부록(07-25): 남는 실시간 예산(5.3s)을 `map()` iters(10→15/20)에 재투자 시도 — 기각(큐 드롭으로 처리 keyframe 수만 줄어 PSNR 개선 없거나 예산 초과), 다음 후보는 `queue_size` 확대** | Phase1+2+3 완료 | [exp55](exp55_adaptive_density_carve_plan.md) |
| exp56 | mapping 고정비(픽셀/커널-launch) 절감 — "gaussian 개수를 줄여도 왜 안 빨라지나"를 기존 `_Sect` 타이밍 계측 재분석으로 규명(신규 실행 없이 Phase 0): 직렬 순수 map() 68.16s 중 rasterize 40%+backward 34%+loss_compute 24%로, loss_compute는 순수 픽셀 고정비(N-무관)이고 rasterize/backward도 이 gaussian 수 규모(85k~130k)에선 고정비가 N-비례 항을 압도함을 exp54 축6+2·exp55 Phase2의 반복 관측과 연결해 확정. **Phase 1(map() iters 10→7→5 스캔)에서 `iters=7` 채택** — 시간 −16.1%(59.80→50.17s)·PSNR mean/kf 둘 다 +0.21dB 개선·map() 성사 횟수 22→26회 증가라는 전 지표 동시 개선(오늘 오전 iters↑ 실험과 대칭 결과: coverage가 반복 깊이보다 지배적임을 재확인). Phase 2(이 새 baseline 위에 `render_downsample=2` 재검증)는 기각(시간 이득 −1.7%뿐, PSNR −0.8dB 손해). exp53+54+55+56 최종 = **50.17s, 실시간 배수 0.77배, PSNR 22.82/23.16(exp55 대비도 개선)**. **Phase 3(coverage/GPU경합 직접 겨냥 3축, 전부 기각)**: `queue_size` 2→4는 역효과(시간·PSNR·coverage 셋 다 악화 — 드롭 정책이 버퍼 크기와 무관하게 "최근 N개만 유지"라 버퍼가 클수록 더 오래된 packet부터 처리하게 됨). CUDA Graph는 조사 후 구조적 부적합 판정(keyframe마다 gaussian 개수·카메라 구성이 달라 매번 재capture 필요, 비용이 iters=7 루프 절감분을 상회할 가능성 높음 — 구현 안 함). mapping 전용 CUDA stream 분리는 **실행 중 CUDA illegal memory access로 크래시**(레포 전체에 명시적 stream 관리가 없어 tracking/mapping이 legacy default stream의 암묵적 교차동기화로 우연히 안전했던 것으로 추정 — custom rasterizer가 진짜 동시실행엔 미검증 상태, 안전하게 원복·GPU 상태 정상 확인). **부록**: "병렬 경합 때문 아니냐"는 재확인 요청에 순수 직렬로 재검증 — render_downsample=2가 직렬(경합 0)에서도 rasterize/backward/loss_compute를 겨우 1~3%만 줄임(병렬 6~8%보다도 작음) — 경합 가설 기각, "데이터量은 거의 공짜, 커널 launch 횟수(iters)만 지배적"이 병렬/직렬과 무관한 구조적 사실임을 확정(iters 10→7 직렬 비교는 −20~24%로 확실히 비례). **Phase 4(신규, 이 세션 최대 발견): `map_call` 세부 로그(iters/n_view/n_gauss)를 처음 집계해 map() 호출 26회 중 단 2~3회(맵 최초 초기화+IMU 재초기화 시 `remove_all_gaussians()`로 맵 전체 삭제 후 재구축, iters=90~131)가 mapping 전체 시간의 49%를 차지함을 발견** — `Training.init_itr_num` 1050→600으로 낮춰 **추가로 시간 −6.2%(50.17→47.08s), PSNR 사실상 무손실(kf +0.05dB), map() 성사 26→30회** 채택(300은 PSNR −0.35~0.44dB 실손실로 기각). exp53+54+55+56 최종 = **47.08s, 실시간 배수 0.72배(exp55 대비 −21.3%), kf PSNR 23.21(+0.26dB)**. **Phase 5(신규): 세션 전체 548개 map() 호출의 map_call 로그를 처음 집계해 회귀분석(`scripts/analysis/exp56_fit_timing_model.py`) — 직렬 R²=0.93~0.998로 rasterize/loss_compute/backward/optimizer_step 관계식 도출, `iters×n_view`(반복×카메라 수)가 압도적이고 gaussian 수·해상도는 부차적임을 계수로 확정(실측 5% 이내 검증). n_view 의존 원인도 코드로 규명: 원본 3DGS render()가 카메라 1대 전용(batch 미지원)이라 매 카메라마다 고정비를 새로 지불 — 다음 후보(rasterizer batch화, 뷰당 고정비 최대 91% 절감 가능하나 CUDA 소스 수정 필요해 고위험)로 식별**. **Phase 6: iters↓·n_view↑ 재배분(같은 view-op 예산) 품질 가설을 실측해 기각 — dead config였던 Training.window_size를 실제 로직에 연결해 테스트, 시간은 회귀식대로 거의 무변화지만 PSNR이 −1.1dB→−3.5dB로 window를 키울수록 단조 악화(프론티어 gradient 희석으로 분석), window_size 기본값 10 원복**. **Phase 7(신규): 프론티어 window는 그대로, 과거-뷰 곁눈질 개수(include_global의 하드코딩 2를 Training.n_global_views로 config화)만 늘려 재검증 — Phase 6과 정반대로 PSNR mean/kf 둘 다 개선(+0.24/+0.22dB), 시간 비용은 무시할 수준(+0.25%) → n_global_views=6 채택. exp55 baseline 대비 최종 누적(Phase 7): **47.20s(−21.1%), PSNR mean +0.36dB·kf +0.48dB, 궤적도 개선**. **Phase 8: 사용자 요청으로 rasterizer batch 구현 조사 — torch.profiler로 확인해보니 진짜 CUDA 커널 비용이라 batch화(forward.cu/backward.cu 수정)는 그래디언트 위험이 커 보류, 대신 프로파일링 중 발견한 안전한 부수 최적화(Camera.world_view_transform/full_proj_transform/camera_center가 pose 불변인데도 매 view마다 torch.linalg.inv() 재계산되던 것을 캐싱, update_RT()에서만 무효화) 적용 — **시간 −3.0%, PSNR +0.52/+0.45dB, map() 성사 +38%, 이 세션 최고 ROI**. exp55 baseline 대비 최종: **45.79s(−23.4%), 실시간 배수 0.70배, PSNR mean +0.88dB·kf +0.93dB**. **Phase 8b(사용자 요청 "물어보지 말고 끝까지"): batch를 실제 구현(기존 단일-카메라 CUDA 커널은 안 건드리고 C++에서 카메라 수만큼 루프, forward bit-exact·backward float32 잡음 수준으로 검증) — 1차 실전 실행에서 PSNR 붕괴(6.65dB) 발견, 원인은 render_batch()의 depth 텐서 shape 불일치(get_loss_normal이 매 호출 조용히 실패, except가 은폐 — 격리 검증이 이 project-specific loss를 안 건드려서 못 잡음). 수정 후 재실행: 크래시 없고 PSNR도 소폭 개선(23.55/24.07)했지만 **시간은 개선 없음**(정규 호출 평균 761.6ms→755.7ms, <1% 차이) — "진짜 병목은 CUDA 커널 실행 자체"라는 Phase 8 예견이 실측으로 확정, `batch_render` 채택 안 함(기본 false 원복, 코드는 향후 커널-레벨 batch화 기반 자산으로 보존)**. **Phase 9(신규, 07-28, exp56 후속분석): "고정비가 지배적" 결론을 통제된 단일-view-op 마이크로벤치마크(카메라 1개 고정, N=1만~9만 서브샘플)로 재검증 — torch.profiler 이중계산 버그(C++ 확장 wrapper가 자식 커널 시간을 self_device_time에 중복 합산, 8.39ms vs 순수 wall-clock 3.43ms) 발견·wall-clock으로 교차검증 후, forward는 N-비례가 56.4%·backward는 84.6%(N=90,770 기준, R²=0.988/0.999)로 실제로는 N이 상당히 유의미함을 확인 — Phase 0/5의 "N-무관 고정비 지배" 결론은 다변량 실측 로그에서 여러 항목이 섞여 희석된 결과였을 가능성. 지도교수가 제안한 visibility 기반 backprop 선별 방향이 이 결과로 재확인됨(backward의 N-slope이 forward의 3.3배) → exp57에 "coarse frustum pre-filter로 유효 N 절감" 항목 공식 추가**. **Phase 10(신규, 07-28): `render_filtered()`/`frustum_prefilter()` 실제 구현(기존 `render()` 무수정, host-side에서 gaussian 부분집합만 뽑아 넘김) — 수치 검증(Phase8b 기준, atomic 노이즈 수준 일치) 통과, length=300 라이브 스모크 통과 후 1253 전체 실측: **온라인 루프 −0.89%(45.79→45.38s, 잡음 수준), PSNR −0.35/−0.29dB, map() 성사 36→30회(−17%) — 기각.** `map_call` 로그로 원인 진단: rasterize avg/call이 오히려 139→290ms로 2배 느려짐 — 필터링 자체(행렬곱+5개 인덱싱 연산, 뷰마다 최대 17회)가 만드는 추가 커널 launch 비용이 줄어든 gaussian 수만큼 아낀 시간보다 컸음. Phase 9를 뒤집는 게 아니라 오히려 재확인: "N-비례가 유의미하다"와 "host-side에서 N을 줄이면 공짜"는 다른 명제 — launch 자체가 비싸다는 Phase 9 결론상 필터링을 CUDA 커널 내부(preprocessCUDA)에 융합해야만 진짜 이득이 나고, 이는 결국 처음부터 고위험으로 미뤄온 forward.cu/backward.cu 직접 수정과 같은 결론으로 수렴. `frustum_prefilter` 기본값 false 유지, 코드는 자산으로 보존**. **Phase 11(신규, 07-28, 사용자 요청 "renderCUDA만 커널 레벨로 batch화"): Phase 8/8b/10이 계속 고위험으로 미뤄온 forward.cu/backward.cu 직접 수정을 범위를 좁혀 시도 — renderCUDA(forward+backward)만 grid.z=camera로 진짜 배치, preprocessCUDA/정렬/computeCov2DCUDA(SE3 포즈 그래디언트 dL_dtau가 있는 곳)는 카메라별 host-loop 그대로 무수정(grep으로 dL_dtau가 renderCUDA엔 없음을 구현 전 확인). 구현 직후 원인불명 segfault(compute-sanitizer 0 errors인데도 크래시) → gdb 백트레이스로 정확히 진단: focal_x_t/focal_y_t를 GPU 텐서로 할당해놓고 host for문에서 CPU가 GPU 포인터를 직접 역참조하던 버그(호스트 벡터에 채운 뒤 한 번만 업로드하는 방식으로 수정, forward/backward 두 곳 다). 재빌드 후 Phase 8b 기준 검증 통과(forward bit-exact, backward 상대오차 atomic 노이즈 수준), length=300 스모크 통과 후 1253 전체 실측: **vigs_track_total 45.79→44.00s(−3.9%), PSNR 23.49/23.88→23.46/23.98(무손실), rasterize avg/call 139.4→66.8ms(−52.1%, 배치화한 부분만 놓고 보면 launch 비용이 정확히 절반) — 채택.** backward는 거의 그대로(348.9→368.5ms) — 배치 안 한 BACKWARD::preprocess가 여전히 backward 시간을 지배하기 때문(다음 후보로 식별, 단 dL_dtau를 직접 건드려야 해서 고위험). Phase 8b/10과 달리 이번엔 시간·PSNR 모두 손해 없는 첫 배치화 계열 순이득. Training.kernel_batch_render(opt-in, 기본 false) 신규 플래그로 배선** | 완료 | [exp56](exp56_mapping_fixedcost_reduction.md) |
| exp57 | causal stable-map polishing + dense RGB. 4-offset 954장 고정-map 15k는 held-out/keyframe **30.389/30.321dB**지만 총 **2.124× live**. Aria **photo+IMU only** strict 1.5×(MPS 거부, tail 0)은 rolling **23.870/24.300dB**. 최초 freeze 18.004dB는 cutoff 단위 버그로 무효. 수정 재실험도 **22.002dB**, prune+online carve 결합은 **21.868dB**, 57,109 GS, visible floater **21.084%**, 약 **1.594×**로 기각 | **품질 상한 성공 / pure-online rolling·same-tensor freeze 실패** | [exp57](exp57_causal_background_polishing_plan.md) |
| exp58 | 구 exp57 후속 구상 번호 이동: host-side filtering 없이 CUDA `preprocessCUDA`/`BACKWARD::preprocess` 내부에 visibility skip을 융합하고 SE3 pose gradient `dL_dtau` 정확성을 보존하는 고위험 속도 축. exp57이 만든 유효 update를 더 싸게 돌리는 후속 | **계획·고위험** | [exp58](exp58_cuda_visibility_backward_plan.md) |
