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
| exp57 | 1차 목표 **strict-disjoint held-out 27dB**(MPS 금지, RGB+IMU only, fixed 1.5×, tail 0). late-iters3 3회는 **27.004/26.949/26.572dB**, 최초 27은 1/3회. static 2단계는 기각. causal replay feedback target5100은 5,233 update지만 low=0/high=38로 제어가 작동하지 않아 26.800; target6500 보정이 다음 | **strict-disjoint 27.004dB 단일 최고 / 반복 27 미달** | [exp57](exp57_causal_background_polishing_plan.md) |
| exp57 adaptive6500 | causal replay target6500은 low13/high25로 실제 제어하고 5,310 update를 확보했지만 fixed **26.807dB**. 처리량 feedback만으로 topology/gradient 변동을 못 잡아 축 종료. 1차 목표는 계속 RGB+IMU-only strict 27dB 반복 달성 | **기각 — deadline/tail0 계약 통과, 27 반복 미달** | [exp57](exp57_causal_background_polishing_plan.md) |
| exp57 freeze1060 | static late-iters3에서 freeze만 1050→1060. fixed **26.720dB**, 4,747 update, 77,007GS, 97.203s/tail0. 후반 bin도 23.415/19.850이라 coverage 개선 없음; freeze1040/1060 양쪽 실패로 경계 스캔 종료 | **기각 — freeze1050 유지** | [exp57](exp57_causal_background_polishing_plan.md) |
| exp57 quota5200 | frame 진행률별 background 누적 step 상한을 두는 causal quota 구현. 두 run fixed **26.859/26.676dB**(평균 26.767), update도 4,676/4,305로 갈림. tail0에서는 부족분 catch-up 불가하고 frame700 전 topology가 이미 달라 분산 억제 실패 | **기각 — opt-in/default off** | [exp57](exp57_causal_background_polishing_plan.md) |
| exp57 pose-variance 진단 | quota 두 run은 keyframe 116개 timestamp가 동일하지만 xyz 평균 절대차 0.60/1.17/1.88cm, 최대 3.83cm. background 시작 전 kf17에서 이미 최대 1.03cm divergence → 다음 대상은 tracker/PGBA 수치 변동·regular GS GPU interleaving | **원인 범위 축소** | [exp57](exp57_causal_background_polishing_plan.md) |
| exp57 tracking-only 대조 | GS 제거 두 run은 keyframe 111개 동일, xyz 평균/최대 차이 1.05/3.82mm. mapping 동시 실행은 최대 38.3mm라 GS interleaving이 pose 변동을 크게 증폭. no-mapping `_gs_queue` guard 버그 2곳 수정 | **원인 확정 — GS/IMU-init interleaving** | [exp57](exp57_causal_background_polishing_plan.md) |
| exp57 IMU scale quantum0.005 | online raw metric scale만 causal 반올림. 3회 모두 1.040, fixed **26.728/26.755/26.712dB**(평균 26.731, 범위 0.043). 분산은 약 10배 감소했지만 평균 품질 −0.111dB·27 미달 | **품질 레시피 기각, opt-in A/B stabilizer** | [exp57](exp57_causal_background_polishing_plan.md) |
| exp57 window8 | frontier window 10→8 + IMU quantum0.005. fixed **26.845dB**, 5,023 update, 97.242s/tail0. window10 quant 평균보다 +0.114dB이나 27 미달이고 applied scale도 1.035로 달라 순수 window 효과 확정 불가 | **미채택 — opt-in 진단 스위치** | [exp57](exp57_causal_background_polishing_plan.md) |
| exp57 window8 scale-bin 대조 | quantum0.01로 raw 1.03995를 1.040에 고정했지만 fixed **26.703dB**, 4,961 update. 첫 window8보다 −0.142dB이며 window10 quant 평균보다도 낮음 | **기각 — frontier window 축 종료** | [exp57](exp57_causal_background_polishing_plan.md) |
| **exp57 pre-IMU GS gate** | IMU metric init 뒤 전부 삭제되던 초반 GS를 init 완료까지 보류. 두 run fixed **27.0039/27.0371dB**(평균 27.0205), 97.207/97.241s, tail0. scale도 tracking-only 0.9736대로 복귀 | **채택 — strict pure-online 27dB 2/2 재현** | [exp57](exp57_causal_background_polishing_plan.md) |
| **exp57 freeze850** | pre-IMU gate + append-only PPM birth + post-freeze dense supervision. fixed **27.5822/27.6958dB**(평균 **27.6390**), 97.282/97.200s, tail0, MPS0 | **채택 — strict27 best 갱신(+0.6185dB vs freeze1050 평균)** | [exp57](exp57_causal_background_polishing_plan.md) |
| **exp57 freeze800** | freeze800 fixed **27.8568/27.8361dB**(평균 **27.8464**), floater proxy **15,252/15,573개**; freeze750은 27.6969로 하락. 97.235/97.271s, tail0, MPS0 | **채택 — strict best 및 floater 동시 개선** | [exp57](exp57_causal_background_polishing_plan.md) |
| exp57 strict27 acceptance audit | freeze800 보존 산출물 2개를 JSON/provenance/config/log/PLY로 재검증. PSNR **27.8568/27.8361**, 97.2349/97.2710s, evaluator exclusion·RGB+IMU-only·MPS0·tail0 2/2, floater **15,252/15,573** 재산출 일치 | **1차 목표 acceptance 완료** | [exp57](exp57_causal_background_polishing_plan.md) |
| exp57 late1000 PPM birth2× | frame1000 이후 birth만 2×. 103.6kGS(+23.5%), fixed **27.8335dB**(freeze800 평균 −0.0129), bin1000–1199 +0.499dB지만 final −0.536dB, floater **16,988(+10.2%)** | **기각 — density 단독 축 종료** | [exp57](exp57_causal_background_polishing_plan.md) |
| exp57 late1000 newborn appearance refine | frame1000 이후 newborn 행만 appearance+opacity 1-step. fixed **27.8391dB**(−0.0074), bin1000–1199 +0.518dB/final −0.280dB, floater **15,412** 동급 | **기각 — keyframe-local 정착 무이득** | [exp57](exp57_causal_background_polishing_plan.md) |
| exp57 recent5% newborn-only | recent dense appearance+opacity를 post-freeze 행에만 적용. fixed **27.9030/27.7545dB**(평균 27.8288, control −0.0177), floater **15,126/15,786**(평균 +43.5) | **기각 — 첫 양성 미재현** | [exp57](exp57_causal_background_polishing_plan.md) |
| exp57 recent50% newborn-only | recent 비중 5%→50%, gradient는 post-freeze 행에만 제한. fixed **26.5736dB**(freeze800 평균 −1.2729), 7개 temporal bin 전부 악화, floater **15,734(27.10%)** | **강한 기각 — uniform replay를 대체하는 recent family 종료** | [exp57](exp57_causal_background_polishing_plan.md) |
| exp57 strict27 background carve | depth-anchor floater paired 평가. background carve off→λ0.05에서 fixed **27.012→26.840dB**, visible floater **16,639→17,036**, 비율 28.976→29.689%. 시간/tail0는 통과 | **기각 — regular carve만 유지** | [exp57](exp57_causal_background_polishing_plan.md) |
| exp57 loss-priority | causal loss EMA priority50은 fixed **26.9249dB**(uniform 평균 대비 −0.0956). 모든 view를 한 번씩 보존한 weighted-without-replacement도 **26.9726dB**(−0.0479), 97.2382s/tail0로 uniform을 못 넘음 | **family 기각 — uniform shuffled 유지** | [exp57](exp57_causal_background_polishing_plan.md) |
| exp57 batch sequential-Adam | batch forward 뒤 view별 `autograd.grad`를 구해 Adam 두 step을 보존하는 gate. 90,770GS/1024²/2-view에서 순차 **7.7485ms** vs batch-grad **11.9746ms**로 54.54% 느림; 현재 autograd가 loss마다 batch 전체 backward를 재실행 | **조기 기각 — smoke/full 미실행** | [exp57](exp57_causal_background_polishing_plan.md) |
| exp57 batch repeat-Adam | batch2 평균 gradient를 Adam에 2회 재사용. paired 600 smoke에서 update **2,714→3,100(+14.2%)**이나 fixed **27.4518→27.2989dB(−0.153)**, SSIM/LPIPS도 악화 | **기각 — full 미승격** | [exp57](exp57_causal_background_polishing_plan.md) |
| exp58 | 고위험 backward 속도 축 착수. 첫 저위험 가지인 fixed background view의 pose-gradient 생략은 90,770GS/1024²에서 full **3.0617ms** vs skip **3.1216ms**로 −1.96%(역효과); Gaussian gradient는 atomic-noise 수준으로 정합했지만 full replay 전 기각. 임시 source/binary는 baseline으로 복구·backward 재검증 | **진행 중 — pose-grad-only 가지 기각** | [exp58](exp58_cuda_visibility_backward_plan.md) |
| **exp60 viewpoint-novelty sampler + GPU 락 버그 수정** | novelty sampler(`background_polish_novelty_fraction`) 구현 후 4장면 확장 중 aria1253rot에서 exp59의 미해결 PGBA 크래시가 재현. `CUDA_LAUNCH_BLOCKING=1`+계측으로 근본 원인 2개 확정: (1) `update_pgba`의 `jj_inac` 하한 미검증(수정, 단독으론 불충분) (2) **`background_polish_step`이 PGBA와 `self.video.get_lock()`을 공유 안 해 GPU 커널이 동시 실행됨(수정 → 크래시 해결)**. 수정 후 4장면(aria1253/rot/301_305/301_12F) 전부 크래시 없이 완주. novelty=0.5 자체는 4장면 평균 약 −0.23dB로 uniform 대비 기각(305: −0.17, 1253: −0.46, rot: −0.35, 12F: +0.08) | **sampler는 기각, 그러나 pre-existing GPU 동시성 버그 발견·수정으로 4장면 안정성 확보** | [exp60](exp60_viewpoint_novelty_sampler.md) |
| **exp59 타 데이터 전이** | freeze800 recipe를 재튜닝 없이 aria1253rot·aria301_305·aria301_12F에 적용. as-is 재현은 **26.00/16.95/26.13dB**로 전부 실패, 경계값 rescale은 PGBA CUDA gather kernel에서 **3/3 재현되는 크래시**(background_polish_start_frame 원복 대조군으로 "background 스레드 타이밍" 가설은 기각, freeze/pgba/late-mapping 값 자체로 원인 범위 축소). aria301_305를 freeze/시간제약 없이 재실행(축 D)하니 **22.96dB로 회복**돼, 305 붕괴의 대부분도 freeze 경계 하드코딩(문제1)의 심한 사례였음을 확인 — 잔여 4~5dB 갭만 진짜 scene 난이도로 남음. 1.5× 데드라인도 세 데이터 모두 초과(+1.50/+3.27/+3.28s). VRS→VIGS 변환기(`build_vigs_aria_input.py`) 신규 작성 | **재현 실패 — 원인 3종(경계 하드코딩·PGBA 크래시·데드라인 초과)으로 수렴, 305 이상치는 대부분 문제1로 환원** | [exp59](exp59_strict27_cross_scene_transfer.md) |
| **exp62 라이브 OKVIS2‖3dgs-custom 병렬 파이프라인** | exp61 §7 격차(콜백은 있지만 incremental 브릿지·매퍼 폴링 루프 없음)를 메우는 구현. Codex CLI(`codex exec`)에게 M1(라이브 소스)~M5(12F 확장) 5단계 마일스톤 위임, 매 단계 exp61 오프라인 reference와 자동 비교 검증 통과해야 다음 단계 진행. **74분 만에 M1~M5 전부 통과** — 트래킹↔매핑 동시 실행을 타임스탬프로 확정(M3), 1253/305/12F 세 장면 모두 real-time 예산(1.5×) 안에서 zero-tail 완주(M4/M5, 12F는 배칭 없이도 통과). PSNR 품질 게이트는 아직 없음(다음 과제) | **M1~M5 전부 통과 — real-time 병렬 파이프라인 최초 성공** | [exp62](exp62_live_okvis2_mapping_pipeline_plan.md) |
| **exp63 VIGS-SLAM 매핑 재튜닝(cross-scene·cross-GPU 강건화)** | exp57 freeze800 레시피(1253 27.85dB)의 305/12F 전이 실패(exp59)를 매핑 레시피 자체를 다시 설계해 해결하려는 계획. 본 세션 코드 감사로 신규 확인: (1) vanilla 트래킹이 exp53~56 속도튜닝보다 305/12F ATE 정확 (2) 실시간 map()/background_polish_step()엔 해상도 다운스케일이 전혀 배선 안 됨(color_refinement 오프라인 전용) (3) `adaptive_density_curve`가 aria1253 keyframe으로 fit된 파일 그대로 재사용됨 (4) `background_polish_idle_guard_ms=0`이 exp59/60 미해결 CUDA crash의 원인 후보 (5) `init_itr_num` 등이 RTX 5070Ti 프로파일링 고정값이라 GPU 무관화도 별도 축 필요. 축 A(트래킹 상향 스캔)~축 G(전역 LR 스케줄)로 계획 수립 후 Codex(`codex exec`)에 축별
위임 시작. **축 D(idle_guard) 완료**: 0/5/20ms 전부 exp59 crash(`vectorized_gather_kernel`)를
못 고침(idle_guard는 원인 아님으로 기각), guard=5는 아리아1253 PSNR은 통과(27.63dB)하나
wall time이 예산을 3.4초 초과해 미채택. crash 원인은 미해결로 축 B(경계 비율화)로 이월 |
**축 D+B 완료** — 축 B(경계 비율화)로 305 16.95→**21.09dB**(+4.14), 12F 26.13→**27.04dB**
(+0.91), crash 없음. Codex는 wall time 초과(예산 3.4~3.5초 초과)로 `adopted:false` 보고했으나
직접 검증 결과 이 초과분은 축과 무관 — 채택된 97.65초 예산이 2026-08-03 exp60 GPU-lock
안전수정(2026-07-29 baseline 측정 이후 추가) 비용을 반영 못 한 stale 값임을 확인해 축 B를
채택으로 뒤집고 예산 기준을 ~101/205/168초로 재보정. **축 A(트래킹 파라미터 상향 스캔)**도
완료: `frontend_radius=2`만 채택(12F +0.72dB), `thresh=3.0`은 305 +1.91dB지만 1253 회귀로
기각, `iters1=2`는 예산 초과+305에서도 crash 재현. 305 잔여 격차는 Gaussian 밀도 부족으로
추정(1253 66.4개/프레임 vs 305 29.7개/프레임). **이후 사용자 요청으로 Claude가 직접 crash
근본 원인 규명·수정**: `update_pgba`의 TOCTOU 버그(`t1` 고정 vs `ii`/`ii_inac` 계속 갱신)
확정, `[0,t1)` 필터링으로 수정 — 305가 오늘 처음 crash 없이 완주(22.82dB). **1253 회귀
게이트도 사용자가 명시적으로 폐지**, 앞으로 305 품질/강건성만 기준. **축 A2 완료·채택**:
`motion_filter.thresh=2.6`+`iters1=2` 스택으로 305 **29.8154dB**(+7.00dB) — 병목이
매핑이 아니라 프론트엔드 트래킹 keyframe 밀도였음을 확인. **축 C/C2 완료·기각**:
"map()/PGBA 끝까지 켜두기" 스펙트럼 양극단(전혀 freeze 안 함 / 초기화 직후 즉시
freeze) 테스트 — 둘 다 A2보다 나쁨(각각 305 -4.92dB·12F OOM, 305 -10.46dB·12F는
완주). 12F OOM은 Claude가 직접 근본원인 규명(freeze가 유일한 학습-비용 상한선이라
없으면 `map()`의 매 keyframe 렌더+역전파 호출이 끝까지 계속되며 메모리 하이워터마크가
계속 커짐) — A2의 61% freeze 지점이 이미 세 지점 중 최선이라 freeze-시점 축 종결.
**축 PF 완료·기각**: background_polish가 `dense_only` 필터로 rgb_dense(별도 sparse
raw 프레임)만 보고 birth를 만든 keyframe 자체는 영원히 폴리시 안 받는다는 갭을
발견해 후보 자격을 넓혀봤으나(opt-in 플래그), 선택이 여전히 균등 랜덤이라 오히려
소폭 악화(즉시freeze -0.58dB, 기존스케줄 -0.28dB) — 후보 풀 확대보다 "폴리시가
보는 후보를 작은 trailing window로 제한"이 다음 유망 방향으로 식별됨. **A2가 12F에서
미검증 상태로 -4.84dB 회귀 중이었음을 발견**(23.15dB, 원인: `background_polish` step이
6,586→772로 88% 감소). `VIGS_TIMING_LOG` 계측을 처음 켜고 `background_polish_step`에
신규 타이밍 계측 추가해 4개 런 실측: frontend가 프레임 단계 시간의 64~73%로 압도적
지배(map() 디스패치는 1~4%뿐), polish는 call당 비용(3.9~6.4ms)이 아니라 실행 **횟수**
(772~9,866, 최대 13배)가 dB를 갈랐음을 확정. 결과 시각화: `context/ppt/ppt0812/`. **이어서
`replay_time_scale` 스윕(1.5/2.0/3.0, `--strict_aria_online` 제외)으로 인과관계를 직접
검증**: scale 2.0(+33% 예산)에서 12F가 23.84→**28.10dB(+4.26)**로 A2 이전 baseline을
넘어 거의 완전 회복(polish 806→5,681회)했지만, scale 3.0은 polish가 10,000-step 캡에
도달했음에도 **25.97dB로 역행(-2.13)** — 역-U자형이며 좁은 후보 풀 과적합 가설(미검증)만
있음. `gs_worker_dispatch`/`background_polish_call`에 epoch 타임스탬프를 추가해 polish
횟수의 "계단식" 양상을 gap 단위로 재구성: 총 횟수는 `Σ floor(gap/step비용 4~6ms)`라는
정수 나눗셈의 합이며, gap의 43~57%는 step 1개도 못 낄 만큼 짧아 zero-polish로 버려짐을
확정. 결과 시각화: `context/ppt/ppt0812/`(15슬라이드로 확장) |
[exp63](exp63_vigs_slam_robust_general_mapping_tuning.md) |
| **exp61 OKVIS2→3dgs-custom 벤치마크 재현** | 팀원(martian35) 벤치마크 `aria-online-3dgs-bench`(OKVIS2/OpenMAVIS stereo+IMU → 3dgs-custom incremental)를 RTX 5070 Ti에서 재현. 팀원 VIGS 재현치가 낮았던 원인은 데이터가 아니라 **GPU(3090, target은 5090)+305/12F 스크립트 오용**임을 확정(자체 재현 27.7735dB로 baseline 일치). OKVIS2 빌드+stage1~6(트래킹 49.3s·chunk 49개·PPM/pool/refilter)이 팀원 3090 수치와 정합적으로 일치. 실제 학습 진입점의 real-time 예산 스케줄러가 팀원 로컬 미푸시 커밋이라 정식 recipe는 보류, 대신 예산 없이 직접 실행해 **순수 학습 wall time 89초(49 events)** 실측. 트래킹 정확도는 OKVIS2(stereo)가 VIGS(mono)보다 305/12F에서 3.6~26배 우세, 매핑 품질은 장면별로 갈림(1253=VIGS 승, 305=OKVIS2 압승, 12F=동률). 코드 감사로 "OKVIS2 자체엔 이미 라이브 콜백 인프라(`okvis_app_realsense.cpp`)가 있지만 incremental 브릿지·매퍼 폴링 루프는 전혀 없음" 확인 | **재현 성공(트래킹~stage6), 정식 학습은 팀원 파일 대기 중** | [exp61](exp61_okvis2_3dgs_custom_benchmark_repro.md) |
