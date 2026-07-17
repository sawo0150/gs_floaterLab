# exp51 — Incremental mapping을 배치급 품질(30dB+)로: depth supervision + keyframe 밀도/중복방지

- 상태: **⚠ 2026-07-17 정정 — "축C 콘텐츠 난이도" 결론 철회, 예산(iteration 수) 재검증 진행 중.**
- 배경: [exp49](exp49_photoslam_plan.md) Phase C~D에서 Photo-SLAM replay가 held-out 22~23dB 정체.
  init 튜닝(D1: PPM +0.97dB, RoMA·하이퍼 무효)으로는 못 넘음. CLAUDE.md North Star의 현재 단계
  ("incremental mapping 30dB+ 먼저, floater는 그다음")를 직접 겨냥.
- baseline: exp49 **D1-b = 23.11dB** (SLAM+PPM init, RGB photometric only, keyframe 57장).
- **⚠ 상한 정정**: "배치 30.2dB"는 **exp48 시절 8,550-iteration 예산 캡을 씌운 통제실험** 수치였지
  진짜 배치 상한이 아니었음. **동일 장면(301_1253=`data/03_rgb_3dgs_full`) 풀 30k-iteration 배치는
  훨씬 높음** — exp30 baseline(ORB init, hybrid 트릭 없음) **test 31.5dB**, exp44d2 챔피언(RoMA+PPM
  hybrid) **test 32.5dB**(exp44_fast_geometry_plan.md 확정표). 즉 축A~C 전부 8,550~16,950 iteration
  캡 안에서만 실험했던 것 — **"콘텐츠가 근본적으로 어렵다"는 축C 결론은 진짜 배치 상한과 비교 안 하고
  내린 성급한 판단이었음(사용자 지적으로 발견, 아래 정정 섹션 참조).**
- **축 A 결과: 25.29dB (λ=0.5, +2.42dB)** — depth supervision 확정 유효. 상세는 아래 런 계획 표.

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
| 51-C (D=2, 고정 예산) | + keyframe 밀도 2배(113청크) | **25.11 (A+B와 동급)** | iters_per_kf 150→75(총 예산 고정) |
| 51-C (D=2, 비례 예산) | + keyframe 밀도 2배, 예산 2배 | **25.30 (A+B와 동급)** | iters_per_kf 150 고정(총 16,950 iter) — **밀도 자체가 레버 아님, 최종 확정** |
| 51-C (D=3/4) | **종료 (미실행)** | — | 위 2건이 정지 규칙(2연속 동일원인) 충족, 반복해도 같은 결론 예상 |
| 51-D | + dense supervision | (다음) | 잔여 개선 |
| 51-E | + floater 억제 | (다음) | 먼지 최소화(region GT) |

**축 A 결론**: depth supervision이 실제 큰 레버임을 확정(+2.4dB, λ=0.5 채택). 단 결정 규칙 기준 26dB
미만이라 **depth 단독으론 30dB 목표에 부족** — 다음은 축 B(init 중복방지)+C(keyframe 밀도) 결합.

**축 B 결론**: dedup 자체는 PSNR을 안 올림(25.29→25.27, 오차범위) — 이미 덮인 곳에 중복 init해도
photometric loss엔 큰 해가 없기 때문. 하지만 **가우시안 수를 16% 줄이면서 품질 무손실**을 확인했고,
로그상 밀도가 찰수록 skip율이 급증(chunk 1: 12494→6798 유지, chunk 56: 9361→130 유지) — **의도대로
"빈 곳만 채우는" 동작 확정.** 진짜 가치는 축 C의 인에이블러: dedup 없이 keyframe 밀도를 2~4배로
올리면 중복점이 그만큼 배로 늘어 메모리·연산 낭비 + 오히려 밀집 부작용 위험 — dedup이 이를 막아준다.

**축 C 소견 (D=2, 고정 예산)**: `build_photoslam_replay_dense.py` 신설 — 원본 57 keyframe 각각의
dense 구간에서 D개 균등 프레임을 승격, sub-frame 0(원 keyframe)만 SLAM extra point를 받고 전
sub-frame이 자기 뷰 기준 causal PPM(depth-pro+calib_depth)+depth 타깃을 받음(`chunk_NNN_Y` 디렉토리,
사전순=시간순). D=2로 113개 서브청크 생성, **총 iteration 예산을 D1-b와 동일하게 고정**(iters_per_kf
150→75)해 학습 → **25.11dB, 축A+B(25.27~25.29)와 오차범위 내로 개선 없음.** N도 927k로 비슷한 규모.
**해석**: "더 촘촘한 supervision 뷰"는 고정 예산 안에서는 무효과 — 뷰가 늘어난 만큼 뷰당 학습량이
희석돼(150→75 iter) 상쇄된 것으로 보임. 이는 **원래 가설("57장은 너무 적다")이 틀렸다기보다,
예산-공유 방식의 밀도 스캔이 순수 밀도 효과를 격리하지 못함**을 시사 — D=3/4을 같은 방식(고정
예산)으로 더 돌려도 같은 결론이 반복될 공산이 큼(정지 규칙: 2연속 동일원인 실패). **다음 결정 필요**:
(a) 예산을 밀도에 비례해 늘려(iters_per_kf 고정, 총 iteration↑) 순수 밀도 효과 재검증,
(b) 축C는 여기서 접고 축D(dense supervision-only, gaussian 생성 없이 view만 추가)나 축E(floater)로
전환, (c) 축A+B 조합(25.29dB)을 현재 최선으로 확정하고 다른 병목(윈도우 방식·아키텍처) 재검토.
→ **사용자 결정: (a)+(c) 동시 진행.**

## 사용자 결정 후속 (2026-07-17): (a) 예산비례 밀도 재검증 + (c) per-view 진단

**(c) per-view 진단 (축A+B 25.29dB 모델, held-out 163뷰 per_view.json 분석)**: 최악 15개 뷰가 뚜렷한
클러스터 2곳에 집중 — ① **frame_00449~473, frame_00665~697 (PSNR 16~20dB)**: exp48이 이미 진단한
"저텍스처 화이트보드 근접면" 구간과 **정확히 일치**(STATUS 2026-07-16 "chunk 14-20, 프레임 ~430-700
최악" 기록). 축A(depth supervision)로도 이 구간은 못 고쳤음 — depth-pro 자체가 저텍스처 근접면에서
약하기 때문(anchor 원인이 depth-pro 실패라 depth loss가 잘못된 타깃으로 supervise). ② **신규 발견:
frame_00313~329, frame_01057~1073 (PSNR 11.6~19dB, 최저 00134=11.64dB)** — 육안 확인(00039.png GT/render
비교) 결과 화이트보드와는 다른 유형: **광택 바닥 반사 + 밝은 천장 형광등 글레어 + 밀집 잡동사니(서버랙,
모니터, 케이블, 큐브)**가 겹친 장면. 렌더에 뚜렷한 바늘형 floater 스펙클과 흐릿한 지오메트리 확인 —
specular/thin-structure 케이스로 SLAM 특징점 매칭과 3DGS 표현 둘 다에게 어려운 콘텐츠. **결론: 남은
갭(25.29→30.2)은 아키텍처(windowed/times-of-use) 문제가 아니라 장면 콘텐츠 난이도(저텍스처면 +
specular/clutter)가 지배적** — Photo-SLAM의 times-of-use 슬라이딩 윈도우(hard evict 없음)가 exp48의
"윈도우 이탈 후 영구 방치" 문제를 이미 해결했다는 기존 결론과 일치. 이 두 클러스터는 축E(floater 억제,
바늘 스펙클 타깃)의 명확한 타깃이 될 수 있음.

**(a) 예산비례 밀도 재검증 (D=2, iters_per_kf=150 고정 → 총 16,950 iter, D1-b의 약 2배)**: 같은
density2 replay(113 서브청크)를 예산 안 나누고 그대로 150 iter/청크로 학습 → **25.30dB** — 고정예산
결과(25.11)와도, 축A+B 단독(25.27~25.29)과도 **전부 오차범위 내로 동일.** 예산을 밀도에 비례해 2배로
줘도 그대로다 → **"예산 희석" 가설도 기각**: 이건 진짜로 밀도 자체가 이 지점에서 추가 레버가 아니라는
뜻. (c)의 per-view 진단과 정합적 — 남은 갭이 "뷰가 부족해서"가 아니라 "일부 뷰의 장면 콘텐츠가
근본적으로 어려워서"이므로, 더 많은 뷰/더 많은 iteration을 넣어도 그 어려운 뷰들의 depth-pro·SLAM
신호 자체가 나빠서 개선이 안 되는 것으로 해석. **축C 최종 결론: 밀도 축은 종료.** D=3/4은 진행하지
않음(같은 패턴 반복이 거의 확실, 정지 규칙 충족). **exp51 현재 최선 = 축A+B, 25.29dB.** 다음은
축E(floater 억제, 진단된 두 클러스터 타깃)로 진행하거나, 여기서 30dB 목표 재검토(콘텐츠 난이도가
지배적이라면 배치 상한 30.2dB 자체도 이 장면에서 재현 가능한지 확인 필요).

## ⚠ 정정 (2026-07-17, 사용자 지적): "콘텐츠 난이도" 결론 철회 — 진짜 원인은 예산 부족일 가능성

위 "축C 최종 결론"의 "콘텐츠가 근본적으로 어렵다"는 해석은 **"배치 30.2dB"를 배치 상한으로 오인한
채 내린 판단이었다.** 실제로 30.2dB는 exp48이 자체구현 incremental(8,550 iter)과 공정 비교하려고
**배치를 8,550 iteration으로 예산 캡을 씌운 통제실험** 수치일 뿐, 진짜 배치 상한이 아니다. 같은 장면
(301_1253=`data/03_rgb_3dgs_full`)의 풀 30k-iteration 배치 결과는 exp44_fast_geometry_plan.md에
이미 있었다: **baseline(exp30, ORB init only) test 31.549dB, 챔피언(exp44d2, hybrid init) test
32.479dB.** 축A~C는 전부 8,550~16,950 iteration(iters_per_kf 150, D=1~2)으로 캡 걸려 있었다 —
배치의 30k에 크게 못 미친다. 즉 "더 촘촘한 뷰/더 많은 총 iteration을 넣어도 안 움직였다"는
근거였던 축C(a) 실험조차 16,950 iter로, 배치 30k의 절반 수준이었다. **재검증 필요**: 축A+B
레시피를 훨씬 큰 예산(iters_per_kf=500, 총 ~28,500 iter, 배치 30k에 근접)으로 재학습해, 순수
"학습량 부족"이 남은 갭의 진짜 원인인지 확인 중 (51-F, 아래).

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
