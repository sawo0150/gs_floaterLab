# exp51 — Incremental mapping을 배치급 품질(30dB+)로: depth supervision + keyframe 밀도/중복방지

- 상태: **축 A+B 완료 (2026-07-17) — depth +2.42dB 확정, dedup은 PSNR 무변화·N -16%. 다음 축 C(keyframe 밀도).**
- 배경: [exp49](exp49_photoslam_plan.md) Phase C~D에서 Photo-SLAM replay가 held-out 22~23dB 정체.
  init 튜닝(D1: PPM +0.97dB, RoMA·하이퍼 무효)으로는 못 넘음. CLAUDE.md North Star의 현재 단계
  ("incremental mapping 30dB+ 먼저, floater는 그다음")를 직접 겨냥.
- baseline: exp49 **D1-b = 23.11dB** (SLAM+PPM init, RGB photometric only, keyframe 57장). 상한: 배치 30.2dB.
- **축 A 결과: 25.29dB (λ=0.5, +2.42dB)** — depth supervision 확정 유효, 그러나 목표엔 부족. 상세는 아래 런 계획 표.

## VIGS-SLAM 조사 결과 (핵심 정정)

VIGS(RGB+IMU GS-SLAM)를 분석한 결과, 처음 세운 가설("VIGS는 전체 프레임을 supervision에 씀")은
**틀렸음** — VIGS도 **keyframe만** supervise(motion_filter로 keyframe 선택, `map()`은 keyframe 풀에서
local window + global random 샘플). 즉 "적은 뷰"는 우리와 같음. **품질 차이의 진짜 원인은 프레임 수가
아니라:**

1. **Depth supervision** (가장 큼): `get_loss_mapping_rgbd`가 RGB + **dense depth** 둘 다로 supervise.
   depth가 gaussian을 올바른 위치에 강하게 앵커링 → 적은 뷰로도 geometry가 잡힘. **우리는 RGB
   photometric only라 이게 빠져 있음.** (exp43 "저품질에선 이미지가 floater를 요구" 벽도 depth 앵커가 없어서였음.)
2. **Floater 직접 억제**: isotropic loss(`|scale-scale.mean|`) + scale clamp(max=0.1) + visible-only
   opacity reset(우리가 exp48서 "selective reset"으로 재발명한 것).
3. **Init 중복 방지 (개념)**: 새 keyframe에서 gaussian 추가 전 현재 맵을 그 뷰로 렌더해
   `transmittance(=1-alpha)`를 받아 "이미 gaussian이 덮은 픽셀"을 판별하는 훅이 있음 — **단 공개
   코드에선 변수만 받고 실제 마스킹은 미적용(미완성)**. 개념은 정석: 빈 곳에만 새 점 추가.

→ 우리 원래 exp51 가설("dense 프레임 추가")보다 **depth supervision + keyframe 밀도/중복방지 init**이
   더 확실한 경로. (dense 프레임 추가는 보조축으로 유지.)

## 사용자 피드백 반영 (2026-07-17)

- **depth-pro를 그냥 쓰지 말고 SLAM point로 보정해서 쓸 것**: raw depth-pro는 상대 깊이 → exp43~48의
  `calib_depth()`(Huber 회귀로 SLAM point에 스케일/오프셋 fit) 재사용. exp50 depth-pro IPC 서버도 재활용.
- **init은 계속 씀**: depth loss가 init을 대체하는 게 아니라 기존 init(SLAM+PPM) **위에 추가**.
- **keyframe 57개는 너무 적음 → 2/3/4배 스캔**: OpenMAVIS가 정한 57개는 못 바꾸지만, dense 프레임에서
  균등 간격 승격으로 gaussian 생성 keyframe을 114/171/228개로 늘려 적정선 탐색.
- **init 중복 방지 필수**: 모든 픽셀에 무조건 init 금지. 이미 gaussian 있는 자리엔 추가 금지 →
  렌더 alpha로 빈 픽셀만 depth-lift init (VIGS 정석, 위 3번).
- **축2(floater 억제)는 후순위**: 품질 먼저.
- **축들이 keyframe 관점에서 다 얽힘**: depth/중복방지/밀도/dense supervision을 통합 레시피로 봄.

## 실험축 (loop)

전부 baseline(D1-b, SLAM+PPM) 위에 **한 번에 하나씩** 적용, held-out PSNR(+ 나중에 region GT 먼지)로 판정.

| 축 | 내용 | 구현 위치 | 우선 |
|---|---|---|---|
| **A. Depth supervision** | 렌더 depth vs SLAM-보정 depth-pro depth의 loss(λ 스캔 0.1/0.5/1.0, L1 vs scale-inv). init은 SLAM+PPM 유지 | `trainForOneIteration` (C++) + depth-pro IPC | **1 (판 가르는 축)** |
| **B. Init 중복 방지** | 새 keyframe init 시 현재 맵을 그 뷰로 렌더 → alpha 높은(덮인) 픽셀 제외 → 빈 곳만 depth-lift로 add. 무조건 전픽셀 init 금지 | `trainReplay` init 경로 (C++) | 2 |
| **C. Keyframe 밀도** | dense 프레임 균등 승격, keyframe 57→114→171→228, 적정선 탐색 | 빌드 스크립트 + trainReplay | 3 (A/B와 결합) |
| **D. Dense supervision** | 승격 안 된 dense 프레임도 supervision-only 뷰(gaussian 생성X)로 추가, 인과 순서 | 빌드 스크립트 + trainReplay | 4 (보조) |
| E. Floater 억제 | isotropic loss + scale clamp + visible-only opacity reset | trainForOneIteration | 5 (품질 확보 후) |

**통합 관점**: A(depth loss) + B(빈 곳만 init) + C(keyframe 밀도↑)가 사실상 하나의 레시피 —
"keyframe을 더 촘촘히, 각 keyframe에서 빈 곳만 depth-lift로 채우고, depth loss로 앵커링". 이게 VIGS급
품질의 실체로 추정.

## 선행 확인 필요 (구현 전)

- **Photo-SLAM 래스터라이저가 depth를 출력하는가?** (VIGS는 `rendered_expected_depth` 냄) — 안 나오면
  래스터라이저 패치 필요. 축 A 구현의 첫 관문.
- depth-pro IPC(exp50 `scripts/depth_pro_server.py`) 재기동 + `calib_depth` 이식(Python→C++ or 사전
  계산 파일 공급).

## 런 계획 (동일 llffhold-8 163뷰 하네스)

| 런 | 축 | held-out PSNR | 비고 |
|---|---|---:|---|
| 51-A0 | =D1-b 재확인 (λ=0) | **22.87** | D1-b(23.11) 대비 -0.24, 기존 run-to-run 노이즈(±0.33) 내 — 래스터라이저 patch 회귀 없음 확인 |
| 51-A1 (λ=0.1) | + depth loss | **25.11 (+2.24)** | |
| 51-A1 (λ=0.5) | + depth loss | **25.29 (+2.42, 최고)** | SSIM 0.861, LPIPS 0.323 — 셋 중 전부 최고 |
| 51-A1 (λ=1.0) | + depth loss | **25.06 (+2.19)** | λ 과대 시 photometric 희생, 소폭 하락 |
| 51-B | + 중복방지 init (α>0.5 스킵) | **25.27 (A와 동급, ±0.02)** | PSNR은 무변화(예상대로 — 중복점 있어도 photometric엔 큰 해 없음). **N 1,089k→917k(-16%)** — C의 인에이블러로 유효 |
| 51-C | + keyframe 2/3/4배 | (다음) | 적정선 |
| 51-D | + dense supervision | (다음) | 잔여 개선 |
| 51-E | + floater 억제 | (다음) | 먼지 최소화(region GT) |

**축 A 결론**: depth supervision이 실제 큰 레버임을 확정(+2.4dB, λ=0.5 채택). 단 결정 규칙 기준 26dB
미만이라 **depth 단독으론 30dB 목표에 부족** — 다음은 축 B(init 중복방지)+C(keyframe 밀도) 결합.

**축 B 결론**: dedup 자체는 PSNR을 안 올림(25.29→25.27, 오차범위) — 이미 덮인 곳에 중복 init해도
photometric loss엔 큰 해가 없기 때문. 하지만 **가우시안 수를 16% 줄이면서 품질 무손실**을 확인했고,
로그상 밀도가 찰수록 skip율이 급증(chunk 1: 12494→6798 유지, chunk 56: 9361→130 유지) — **의도대로
"빈 곳만 채우는" 동작 확정.** 진짜 가치는 축 C의 인에이블러: dedup 없이 keyframe 밀도를 2~4배로
올리면 중복점이 그만큼 배로 늘어 메모리·연산 낭비 + 오히려 밀집 부작용 위험 — dedup이 이를 막아준다.

**구현 메모**: Photo-SLAM CUDA 래스터라이저(forward.cu/backward.cu/rasterizer_impl.cu/rasterize_points.cu)에
3dgs-custom의 `out_invdepth`/`dL_dout_invdepth` 패턴을 이식(alpha-weighted expected inverse depth,
forward accumulation + backward `dL_dtz -= dL_dinvdepth/(t.z)^2`). `GaussianRenderer::render()` 리턴 튜플에
5번째 원소로 추가(4개 기존 호출부는 `std::get<0..3>`라 하위호환, `renderFromPose`의 명시적 튜플 타입 1곳만 수정
필요). depth 타깃은 `scripts/incremental/build_depth_targets.py`(신규, `build_depthmono_ppm_chunks.py`의
causal `calib_depth()` 재사용)로 keyframe RGB에 대해 SLAM-보정 dense inverse-depth를 `.tiff`로 사전계산,
`GaussianKeyframe::target_invdepth_`로 로드. λ는 `EXP51_LAMBDA_DEPTH` env var로 재빌드 없이 스캔(재현용).
init(SLAM+PPM)은 변경 없이 유지 — depth loss는 photometric loss에 additive.

## 결정 규칙 / 정지

- **축 A에서 ≥28dB → 병목=depth 확정**, B/C로 마무리 후 E(floater).
- **축 A가 26dB 미만 → depth만으론 부족**, B(중복방지)+C(밀도)+D(dense) 결합 필요. → **이 갈래로 확정(25.29<26)**.
- 정지: 30dB 근접 / 축 소진 / 2연속 동일원인 실패.
- 문서화: 런마다 exp51 카드 런 테이블 + INDEX + STATUS. Photo-SLAM/gs_floaterLab 각각 커밋.

## 데이터/코드 자산 (이미 보유)

- dense 프레임+pose(인과적): `05_incremental_dense/chunk_NNN/{images, sparse/0/images.txt}` (총 1303장)
- init 점: chunk별 extra/ppm/roma_points3D.txt (D1: slam+ppm이 best)
- depth-pro: `repos/monoDepth/ml-depth-pro` + exp50 IPC 서버(`DiskChunGS/scripts/depth_pro_server.py`)
- `calib_depth()`: `scripts/incremental/build_depthmono_ppm_chunks.py` 내 (Huber 보정)
- replay 진입점: Photo-SLAM `trainReplay` + `build_photoslam_replay.py`(--init-source 옵션)
