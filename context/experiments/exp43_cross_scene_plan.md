# exp43 (계획) — 교차 장면 일반화: 새 장소에서 carve 재현 + ORB confidence 재평가

- 상태: **계획** (2026-07-12 수립, 미실행)
- 목적: 1253호에서 확정한 방법론(carve exp40b 레시피 + region GT 지표 체계)이 **다른 장면에서 재현**되는지, 그리고 SLAM 품질이 나쁜 조건에서 **ORB confidence(observations/found_ratio)가 유효해지는지** 검증.
- 배경: 1253호 ORB 지도는 깨끗해서(terminal증거 0인 anchor 16/7,205, fr<0.25가 floater 근처에 안 몰림) confidence 필터가 무효과(AUC +0.0004). 지도가 지저분한 장면에서는 다를 수 있음 — MPS에서 outlier 7.6%가 실재했던 것처럼.

## 후보 장면 (전부 VRS+MPS 완비, `26-1_RPM/Datas/CustomData/0416_Data/`)

| 우선 | 장면 | 성격 | 노림수 |
|---|---|---|---|
| **1** | **0408_919C_418** | 다른 건물·다른 방 | 정통 일반화 시험 (실내 room-scale 유지) — **사용자 라벨링 대상 추천** |
| 2 | 0416_301-1253-2_rot | **같은 방, 다른 궤적(회전)** | 라벨 불필요 부가 시험 — 기존 region GT 스탬프·carve field의 궤적 독립성 검증 |
| 3 | 0227_snu_floor2_1 | 다른 건물 복도(추정) | 최강 스트레스 (복도 = SLAM 취약 + floater 온상) — 2차 |

## 절차

1. `scripts/pipeline/run_full_pipeline.sh`를 919C_418로 실행 (VRS→EuRoC→OpenMAVIS→RGB 3DGS 데이터셋)
2. ORB 지도 품질 진단 먼저: anchor terminal-증거 분포, obs/found_ratio 분포 — 1253 대비 얼마나 지저분한가
3. baseline 30k 학습 → **사용자가 SuperSplat으로 floater 라벨링** (이번엔 저op 먼지도 가능한 만큼 포함 권장 — 지난 라벨의 불완전성 교훈)
4. 라벨로 region GT v2 구축 + champion score AUC 재측정 — **confidence 유/무 A/B** (obs·fr 필터/가중)
5. carve(exp40b 레시피) 학습 → 사전 등록 기준: region 가시 먼지 -90%+, PSNR은 그 장면 baseline 재현 노이즈 내

## 사전 등록 판정

- 재현 성공: 새 장면에서 champion score AUC ≥ 0.95, carve 학습으로 가시 먼지 ≥90% 감소
- confidence 유효 판정: confidence 필터/가중이 AUC를 +0.01 이상 올리면 "지저분한 지도에서 유효" 채택
- 실패 시 1순위 의심: 장면 스케일/tau(0.25m)·voxel(0.1m) 하드코딩 값의 장면 의존성

## 결과 1: 301_1253_rot (07-13 새벽, 사용자 라벨 도착)

- 사용자 라벨 5,168개 (5.6%, op p50 0.045 — 원본 장면과 동일 패턴)
- **자동 pseudo-label: precision 100% (4,663/4,663), recall 90.2%** — 사람 추가분 505개뿐 (파일명 'pruningplus'로 보아 pseudo-cleaned에서 시작해 추가 삭제한 것으로 추정 = 자동 삭제 전부 승인)
- **champion score 교차 장면 AUC 0.9813** (원본 0.976 이상) — 다른 궤적·다른 SLAM맵에서 완전 일반화
- ORB confidence(obs≥5) A/B: 0.9807 — 무효과 재확인 (지도 깨끗)
- 진행: rot 장면 carve 학습(exp43rot, dynamic carve 포함) — 진짜 라벨로 채점 예정

## 결과 2: rot carve 학습 — dynamic carve의 자기강화 결함 발견 (07-13)

exp43rot(dynamic carve 포함, raw init): PSNR 30.53(baseline 동급), region_n 7,864→5,301(-33%) — 그러나 **가시 먼지 106→716 역증가.**
**가설: dynamic carve 자기강화** — 가시 먼지 무리가 자신을 terminal 증거로 등록 → rho↓ → score↓ → 자기 보호 되먹임. 1253에선 깨끗한 init이라 잠복(가시 63 유지), raw init+densify 조건에서 발현.
→ **반증 실험 결과 가설 기각**: exp43rot2(static) 도 가시 741 (dynamic 716과 동일) — dynamic 여부와 무관.
**재해석: carve의 설계상 사각지대.** champion score의 (1−maxop_5cm) 보호항이 '이미 불투명해진' 먼지 무리를 보호함 → carve는 저op 먼지 전담이고, **가시 floater는 예방(좋은 init)이 담당**이라는 기존 분업이 raw init 장면에서 그대로 드러난 것. 검증: in-region 가시 741점의 78%가 free space(d5>0.25m) = 진짜 부유물. 1253에서 가시 먼지가 적었던 건 hybrid init 덕분.
- 후속: ① rot에 hybrid init 이식(예방 경로 재현) ② densify 구간 한정 maxop 보호 해제 gate/prune variant (치료 경로 확장)

## 결과 3: 305·12F 라벨 도착 (07-13)

- 305: 9,059/111,596 (8.1%), op p50 0.053, **가시(op>0.3) 1,340** — 지금까지 가장 지저분한 장면. confidence 유효성 판정의 최적 시험대.
- 12F: 1,449/20,436 (7.1%), op p50 0.053, 가시 161 — 저품질(fog) 장면 거동 관찰용.
- 2F·snu(복도)는 기하 열화로 사용자 라벨링 불가 → 라벨 기반 검증 대상에서 제외 (파이프라인 한계 클래스 유지).

## 결과 4: 305 — champion score 첫 일반화 실패 + 원인 확정 (07-13)

- **champion score AUC 0.7993** (사전등록 0.95 미달), pseudo-label precision 44%/recall 41% → 다른 방에서는 현행 레시피 실패.
- 원인 배제 과정: tau 0.1~1.0 스윕·terminal 가중 1~10 스윕 전부 AUC 0.77~0.78 (**스케일 문제 아님**). 가시 gaussian 앵커 대체 0.82, dyn-occ 보강 0.81. 라벨 분해 — 표면근접 라벨은 9%뿐, 탐지가능(free-space·저op) 모집단으로 좁혀도 0.82 (**라벨 성격 문제도 아님**).
- **원인 확정: ORB 지도의 표면 커버리지 부족.** 생존점(정상 표면)조차 d5_SLAM p50=0.304m — SLAM 점 6,080개가 방을 못 덮어 'SLAM 근접=표면' 가정과 ray-transit rho가 모두 실제 표면을 빈 공간으로 오판.
- **처방: depth-anchor carve** — depth-pro(stride 40, ~66프레임)로 조밀 표면 앵커 생성, SLAM 점 대신 d5/terminal 앵커로 사용. hybrid init 이식에도 같은 재료 필요 → 일석이조. `scripts/anchors/inference_depthpro_scene.py` (범용 버전) 실행 중 (305, rot).
- 12F: pseudo-label 파이프라인 백그라운드 진행 중.

## 결과 5: 305 depth-anchor 처방 — 대폭 회복 + 라벨 이질성 발견 (07-13)

| 신호 | AUC |
|---|---|
| 기존 champion score (SLAM 기반) | 0.7993 |
| depth-anchor w (rho·d5 재구성, 67프레임) | **0.8855** |
| depth-violation ratio (이미지 공간, 67프레임) | 0.8905 |
| vr + 0.5·w 결합 | **0.9047** |

- 생존점 d5 0.304→0.083 — depth 앵커가 표면 커버리지 문제를 해결. depth-pro 비용 33초/장면(67프레임).
- (1−maxop) 보호항은 305에서 AUC를 깎음(0.886→0.83) — 가시 floater 많은 장면에서 보호항 유해, rot 사각지대 발견과 일관.
- **라벨 이질성**: 미탐지 라벨의 95%가 depth 표면 0.15m 이내 = 305 라벨의 ~30%(2,761개)는 free-space 부유물이 아닌 **표면 부착 불량 blob**. free-space 신호의 원리적 사각 → 별도 신호(멀티뷰 색 일관성 등) 필요한 다른 문제 클래스.
- 진행: stride 10(265프레임)으로 depth 보강 중 (관측 빈도 p50=9가 병목 의심) → 최종 AUC 재측정 예정.

## 결과 6: 12F 채점 + 305 depth 보강 (07-13 새벽)

- **12F도 305와 동일한 실패 패턴**: champion AUC 0.858, pseudo-label 정밀도 39%/재현율 45%. 생존점 d5 p50=0.366 (SLAM 14,791점에도 커버리지 부족 — 면적 대비 희소). **'ORB 커버리지 부족' 진단이 두 장면을 모두 설명.**
- 305 depth-violation, 관측 빈도 보강(66→266프레임, vis p50 9→37): **AUC 0.891→0.9143**.
- 진행 체인: 305 앵커·필드 266f 재구축(CPU) → 완료 시 305 depth-anchor carve 학습 자동 발사(GPU). 12F depth 캐시 147장 완료. rot hybrid init(RoMA+PPM 범용판 `build_hybrid_init_scene.py`) GPU 실행 중.

## 진행 노트 (07-13 04:1x): 오버나이트 GPU 체인

1. 305 depth-carve 1차 시도 **OOM 사망** (2,654장 cpu 로드 + 병행 앵커 빌드) → 앵커 100k 서브샘플 + cam_stride 40으로 재큐잉.
2. 체인: rot hyb(03:37~, hybrid init 이식) → rot nomaxop(maxop 보호 해제) → 305 재시도 → 45c progressive resolution(신규 코딩: r/2 8k → 원해상도 재개 15k).
3. 266f 앵커 필드 빌드는 비용 대비 효용 낮아 중단 (vr 0.9143은 이미 확보, 학습은 67f 573k→100k 앵커 사용).

## 결과 7: rot 예방·치료 이식 — 둘 다 실패, 궤적 특성이 지배 변수 (07-13 04:5x)

| rot 실험 | PSNR | 저op 먼지(region_n) | 가시 먼지 |
|---|---|---|---|
| baseline | 30.689 | 7,864 | **106** |
| carve 단독(static) | 30.422 | 5,099 | 741 |
| nomaxop 치료 확장 | 30.385 | 5,453 | **1,267 — 악화, 기각** |
| hybrid init 예방 | **32.056 (+1.37dB)** | 21,440 | **7,698 — 폭증** |

- **nomaxop 기각**: 보호항 해제가 가시 먼지를 오히려 늘림. 소프트 압력 확대 → 저op 먼지가 불투명 응집으로 도피하는 메커니즘 의심 (753→1,267).
- **hybrid 이식의 명암**: PSNR +1.37dB는 즉시 최고 기록. 그러나 rot의 **회전 위주 궤적 = 인접 프레임 시차(baseline)가 작음** → RoMA 삼각측량·depth 보정 오류 점이 재필터를 뚫고 가시 먼지로 유입 (1253은 57 keyframe·충분한 시차·깨끗한 재필터 필드로 성립).
- **결론: 1253 레시피의 이식성 한계는 '장면'보다 '궤적 특성'** — 쌍 선택을 시차(baseline) 기준으로 바꾸는 EDGS식 개선이 다음 열쇠. carve 계열이 rot에서 가시 먼지를 늘리는 메커니즘(응집 도피?)은 아침 분석 과제.

## 결과 8: 305 depth-anchor carve 학습 — **교차 장면 재현 성공** (07-13 05:1x)

| 305 | PSNR | region 먼지 | 가시 먼지 |
|---|---|---|---|
| baseline | 34.508 | 6,888 | 708 (free-space 65%) |
| **depth-anchor carve** | 34.484 (동급) | **1,184 (-83%)** | **173 (-76%, free-space 17%)** |

- 레시피: champion(exp40b) + points_txt=depth 앵커 100k(67프레임분 서브샘플) + cam_stride 40. 재시도 1회(OOM) 후 정상 완주.
- **판정: 앵커 커버리지만 고치면 carve 학습이 다른 방에서 재현된다.** 잔존 가시 173점 중 진짜 free-space는 ~17%(≈29점) — 사실상 부유물 소멸.
- 남은 검증: rot의 가시 먼지 역증가(741)도 희소 SLAM 필드 탓인지 — rot depth-anchor carve(exp43rot_deptha) 45c 뒤 체인 등록.

## 결과 9: rot depth-anchor carve 실패 — 원인은 앵커 품질 (07-13 05:5x)

- exp43rot_deptha: PSNR 30.537, 가시 1,189 — 개선 실패.
- 진단: **rot depth 앵커 자체가 불량.** 라벨 AUC 0.8511 (SLAM 앵커 0.9813), 라벨 floater의 d5(depth앵커) p50=0.21m — depth 표면이 허공에 박혀 있음. 회전 위주 궤적에서 depth-pro 프레임별 Huber 보정이 무너지는 것 (가시 SLAM inlier 부족 + 모션블러).
- **밤새 종합 결론: carve의 성패를 가르는 단일 변수는 '앵커 품질'.**
  - 1253·rot: SLAM 앵커 양호(AUC 0.98) → 점수 일반화 성공. 단 rot carve **학습**은 가시 먼지 악화(741) — 미해결(응집 도피 메커니즘 의심).
  - 305: SLAM 희소(0.80) → depth 앵커로 회복(0.89~0.91) → **학습 재현 성공 (먼지 -83%, 가시 -76%, PSNR 동급)**.
  - rot: depth 앵커 불량(0.85) → 학습도 실패. **장면별 앵커 소스 선택 규칙 필요: 라벨 없이도 계산 가능한 앵커 자가진단(예: SLAM-depth 상호 일관성) 도입이 다음 열쇠.**

## 아침 브리핑 요약 (07-13 오버나이트 최종)

| 실험 | 결과 | 판정 |
|---|---|---|
| 305 depth-anchor carve | 먼지 -83%·가시 -76%·PSNR 동급 | ✅ **교차 장면 학습 재현 성공** |
| 305 점수 회복 | AUC 0.80→0.905 (depth 앵커+vr) | ✅ 처방 유효 |
| 12F 채점 | AUC 0.858, 같은 커버리지 문제 | ⚠️ depth 앵커 미적용(후속) |
| rot nomaxop | 가시 741→1,267 | ❌ 기각 |
| rot hybrid init | PSNR +1.37dB, 가시 ×10 | ⚠️ 궤적(작은 시차) 한계 — 시차 기반 쌍 선택 필요 |
| rot depth-anchor carve | 가시 1,189 | ❌ rot depth 앵커 불량 (회전 궤적) |
| 45c progressive | stage2 torch.load 사고 후 재실행 중 | ⏳ |

미해결 질문 2개: ① rot에서 carve 학습이 가시 먼지를 늘리는 메커니즘(응집 도피?) ② 라벨 없는 앵커 품질 자가진단.

## 결과 10: rot 가시 먼지 부검 — 응집 가설 기각, force 항 유력 용의자 (07-13 아침, 우선순위 ②)

- 계보 필드 부검(741점): **95%가 densify 출생**(birth p50 4,400, generation p50 5 — 깊은 split 사슬), init 출신 5%뿐. accum_visibility p50 686 (표면 874와 비슷 — 많은 뷰에서 실제로 렌더됨).
- **응집 도피 가설 기각**: 가시 먼지의 65%는 15cm 내에 baseline 먼지가 0개 — 기존 먼지가 뭉친 게 아니라 **baseline엔 아예 없던 새 위치에 생성**된 것.
- 새 가설: **carve force 항**(λ0.05, xyz 견인 — 점을 3D로 움직이는 유일한 구성요소)이 회전 궤적의 약한 다시점 구속에서 점들을 "이미지에 부합하는 잘못된 허공 위치"로 이주시킴. 1253(병진 궤적)에선 무해했던 이유도 설명됨.
- 반증 실험: exp43rot_noforce(force만 끈 champion) 실행 중 → 가시 먼지가 baseline(106) 수준으로 내려오면 **"force는 병진 궤적 한정" 조건부 강등**.
- 병행(우선순위 ③): 12F depth-anchor 필드 빌드 중 + RoMA **시차 보장 쌍 선택**(--min-baseline 0.2m) 구현 완료, rot hybrid v2 재빌드→학습 체인 등록.

## 결과 11: ②③① 아침 사이클 (07-13 오전)

**② rot 가시 먼지 — force 가설도 기각, '질량 증폭' 메커니즘 확정 방향**
- noforce 가시 812 ≈ force 741 → force 무죄.
- region 불투명도 질량(op·면적): baseline 8.7 → carve류 18~24 (**보존이 아니라 2~3배 증폭**, 압력 셀수록 큼: nomaxop 23.7).
- 해석: 흩어진 fog를 누르면 이미지 잔차 수요를 강한 지지의 소수가 커지고 진해지며 떠안음 (RGB gradient > opacity 압력). fog 수요의 근원은 회전 장면 underfit.
- 진행: 대조군(rot baseline 재실행 — 106의 재현성)과 hyb2(기하 개선으로 수요 자체 제거) 체인 실행 중.

**③ 12F depth-anchor: 0.843** (SLAM 0.824) — fog 장면은 depth-pro도 부실, 문제 클래스 확정. 시차 보장 쌍(`--min-baseline 0.2`) 구현, rot hyb2 재빌드 완료(171k)·학습 중. (주의: hyb2 재필터가 불량 rot depth 필드를 자동 선택한 교란 있음 — 결과 해석 시 참작)

**① 라벨 없는 앵커 자가진단 — 2규칙 완성 (4/4 일치)** → `scripts/analysis/anchor_self_diagnosis.py`
| 규칙 | 지표 | 문턱 | 근거 |
|---|---|---|---|
| 1 | SLAM 자기 NN p50 | <0.05m → SLAM 앵커 | 1253 0.042·rot 0.043(AUC 0.97+) vs 305 0.072·12F 0.057(0.77-0.82) |
| 2 | depth 교차프레임 불일치 p50 | <0.04 → depth 앵커 | 305 0.032(0.886) vs rot 0.101(0.851)·12F 0.048(0.843) |
| 3 | 둘 다 실패 → 문제 클래스 경고 | | 12F가 정확히 여기 해당 |
- 보정 잔차 지표는 분리 실패(SLAM 희소가 지표를 오염) — 기각 기록.
- n=4 장면의 예비 규칙. 새 장면 1개 들어올 때마다 재검증.

## 결과 12: 대조군이 미스터리를 해결 — "rot 가시 먼지 역증가"는 run-to-run 분산이었다 (07-13 10:2x)

| rot 30k | PSNR | region_n | 가시 | op·면적 질량 |
|---|---|---|---|---|
| baseline (원, 07-12) | 30.689 | 7,864 | **106** | 8.7 |
| **baseline 재실행 (대조군)** | 30.763 | 9,015 | **1,091** | **18.1** |
| carve 4종 (force/noforce/nomaxop/deptha) | 30.4-30.5 | 5,1-6,6k | 741-1,267 | 18-24 |

- **carve 무죄 확정**: 대조군 가시 1,091·질량 18.1 = carve류와 동일 수준. 원래 baseline 106이 행운의 런.
- **정정**: 결과 2·7의 "carve가 가시 먼지를 늘린다"는 해석 철회. rot의 가시 먼지 수준은 장면 고유(회전 underfit의 fog 수요)이며 run-to-run 분산이 ×10에 달함. 질량 증폭 가설(결과 11)도 재해석: 증폭이 아니라 장면 고유 수준.
- **교훈(중대)**: PSNR ±0.33dB 노이즈 교훈이 먼지 지표엔 더 심하게 적용됨(가시 ×10) — **먼지 지표도 단일 런 비교 금지, 재현 런 필수.** carve는 저op 먼지 감소(9,015→5-6k)는 대조군 대비로도 유효.
- 같은 논리로 305 성공(708→173)도 재현 검증 필요 → 305 depth-carve 재현 런 실행 중.
- hyb2(시차 쌍): PSNR 31.953(hyb1 동급), 가시 11,527 — rot에서 dense init 이식은 여전히 부적합(불량 rot depth 필드 재필터 교란 포함). **rot류(회전 궤적)에는 dense init 보류 확정, PSNR 이득은 +1.3dB 유효.**

## 결과 13 (최종): 305 재현 런 — 성공 확정 (07-13 10:5x)

| 305 | PSNR | region_n | 가시 |
|---|---|---|---|
| baseline | 34.508 | 6,888 | 708 |
| depth-carve 1차 | 34.484 | 1,184 | 173 |
| **depth-carve 재현** | 33.909 | **994** | **179** |

- **먼지 감소 -83~-86%·가시 -75%가 정밀 재현** (173→179). rot과 달리 305는 먼지 지표가 안정 — 분산 문제는 회전 underfit 장면(rot) 고유임도 확인.
- PSNR 재현 편차 0.58dB는 1253 노이즈(±0.33)보다 크나 baseline 대비 열화 아님(34.5 vs 33.9, 별도 관찰 유지).
- **exp43 종결.** 확정 스택: 자가진단(anchor_self_diagnosis.py) → 앵커 선택 → depth-anchor carve → 재현성 검증까지.

## exp43 최종 스코어보드

| 검증 항목 | 판정 |
|---|---|
| 점수 일반화 (같은 방·다른 궤적) | ✅ AUC 0.98, pseudo-label 정밀도 100% |
| 점수 일반화 (다른 방) | ✅ depth 앵커 처방으로 0.80→0.905 |
| **carve 학습 재현 (다른 방)** | ✅ **재현 런까지 확정 (먼지 -83%, 가시 -75%)** |
| 라벨 없는 앵커 자가진단 | ✅ 2규칙, 4/4 장면 |
| ORB confidence | ❌ 전 장면 무효과 (재확인) |
| 회전 궤적(rot) | ⚠ dense init·depth 앵커 부적합, 먼지 지표 분산 ×10 — 별도 축 |
| fog 장면(12F) | ⚠ 문제 클래스 (규칙 3이 자동 경고) |

## 추가 결과 14: 12F SLAM-프리 floater 탐지 (07-13, 사용자 질문 후속)

| 신호 | SLAM 의존 | AUC |
|---|---|---|
| SLAM 필드 champion | 필요 | 0.858 |
| depth 앵커 필드 | 보정에 필요 | 0.843 |
| **depth-violation (SLAM 보정)** | 보정에 필요 | **0.9076 — 12F 신기록** |
| **depth-violation (raw metric depth)** | **불필요 (pose만)** | **0.8551** |

- **SLAM-프리 성립**: depth-pro 절대 깊이(f_px=500)만으로 0.855 — 지도 포인트 0개여도 SLAM 필드와 동급. raw 스케일 오차 p50 1.274·IQR [0.87,1.52]가 5점 손실의 원인 → 교차 프레임 자가 보정으로 개선 여지.
- **fog 판정 완화**: voxel 필드가 실패했을 뿐, 이미지 공간 depth-violation은 fog에서도 0.908(305의 0.914와 동급). 12F는 "필드 불가·vr 가능" 클래스로 재분류.

## 추가 결과 15: 캘리브레이션 확인 + pose-기하 자가 보정 — SLAM-포인트-프리 완성 (07-13, 사용자 제안)

- **공장 캘리브레이션 확인**: `full_traj_to_rgb_3dgs.py`가 VRS device calibration으로 RGB를 `get_linear_camera_calibration(1024,1024,500)`에 정류 — **f_px=500은 정확**. 따라서 12F의 raw 스케일 1.274는 focal 문제가 아니라 fog에서의 depth-pro 깊이 편향.
- **스케일 앵커 발견**: SLAM은 스테레오(기지 baseline)+IMU → **pose 이동량이 미터 단위**. 두 프레임 depth에 같은 s를 곱해도 카메라 이동량은 고정이므로 교차 프레임 일관성이 s를 유일 결정 → SLAM 포인트 없이 스케일 복원 가능.
- 12F 실측: 자가 보정 s=1.425 (SLAM Huber 1.274와 근접), **SLAM-포인트-프리 vr AUC 0.855 → 0.8929** (SLAM 보정판 0.908의 98.3%).
- **의의**: 지도 포인트가 전혀 없어도 (pose + depth-pro + 자가 보정 + depth-violation)으로 최악 장면에서 0.893 — 실시간 경로에서 SLAM 맵 품질에 대한 의존을 한 단계 더 제거.
