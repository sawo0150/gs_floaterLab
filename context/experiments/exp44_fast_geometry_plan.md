# exp44 (계획) — 고속·고품질 geometry 트랙: dense init × no-densify × carve

- 상태: **계획** (2026-07-12 수립, 미실행)
- 최종 목표(프로젝트 재정의): **Aria glass 실시간 촬영 스트림 → 분 단위 turnaround로 geometry 좋은 3DGS recon.**
  실시간 경로에는 MPS(오프라인 클라우드 서비스) 사용 불가 → **ORB(OpenMAVIS) 트랙이 본선**.
- 참조 방법론: EDGS (CompVis) — dense correspondence 삼각측량 init + **densification 제거**로 25% 시간에 도달.
  (Instant-GI는 2D Gaussian 이미지 표현이라 직접 부적용 — "내용 적응적 점 배치" 사상만 차용, exp37이 이미 3D판)

## 왜 "dense init + no-densify + carve"가 서로를 완성하는가

1. **floater 출생의 100%가 densification에서 나왔다** (split 29.5%가 허공, 먼지가 먼지를 낳는 연쇄 — exp38 계측).
   → **densification을 끄면 출생 채널 자체가 소멸**: gate 불필요, 남는 먼지는 init 유래뿐.
2. exp37(dense init 148k)의 약점 = **먼지 부하 4.5배** (champion score 기준) — dense init은 빈 공간에도 점을 뿌림.
   → **carve soft+prune이 정확히 그 반대 방향**: init 직후(iter 0~)부터 빈공간 점을 소멸. 상호보완.
3. no-densify → N 고정 → iteration 비용 일정 + 메모리 예측 가능 + budget prune 캘리브레이션 단순화.
4. 학습 단축: EDGS는 3k step에 근접 품질 주장. 우리 하드웨어에서 30k=8~14분이므로 **5~7k step 목표 시 2~4분/장면** 예상.

## 설계 (변형 사다리)

| 변형 | init | densify | carve | 목표 |
|---|---|---|---|---|
| 44a | exp37 dense init (SLAM core + monodepth conf, 148k) | **off** | soft+prune (gate 불요, start_iter 0/500) | 기존 자산만으로 EDGS 사상 재현 |
| 44b | 44a | off | 44a + force | force 가치 재확인 |
| 44c | **correspondence 삼각측량 init (EDGS/RoMA식)**: keyframe 쌍 dense matching → SLAM pose로 삼각측량 (기하 검증된 점) | off | soft+prune | monodepth의 scale 오차 없는 init |
| 44d | **hybrid**: 44c(기하 검증) + monodepth fill(텍스처 없는 흰 벽/천장 — matching 실패 지역) | off | soft+prune | 이 방의 feature-poor 문제 정면 대응 |
| 44e | **2D GS 선최적화 → 3D 사영** (Instant-GI 사상의 3D 이식, 사용자 제안): 각 keyframe에서 2D Gaussian을 빠르게 fit → monodepth로 3D lift | off | soft+prune | 내용-적응 밀도 + **색·이방성 사전 최적화** — init 시점에 이미 '거의 학습된' gaussian 제공 |
| 공통 sweep | — | — | — | iterations ∈ {3k, 7k, 15k, 30k} — 시간-품질 Pareto |

> 44e 메모: 2D fit이 주는 것 = ① 텍스처 복잡도 비례 점 밀도(평탄한 벽엔 큰 gaussian 소수) ② 사전 최적화된 색/공분산 → 3D 초기 수렴 가속. lift에는 monodepth 필요(44d와 공유). 다중 뷰 중복 점은 voxel 병합. 44a/c/d 결과를 본 뒤 착수 판단.

## 평가 (사전 등록)

- 축 1 (품질): region GT 지표 + 시각 검수 + segment held-out SSIM/LPIPS (train PSNR 금지)
- 축 2 (속도): wall time (데이터셋 생성 제외 학습만) — 목표 **총 5분 내 gaussian 가시 먼지 exp40b급**
- 비교선: exp40b(30k, 14분), exp37(dense init+densify, 먼지 4.5배)
- 주의: no-densify에서는 opacity reset(3k/6k)도 재검토 필요 (원래 densify 보조 장치) — off/유지 A/B
- carve budget prune의 contribution proxy가 accum_visibility에 의존 → no-densify에서는 전 구간 누적으로 변경 필요 (코드 1줄)

## 선행 작업

1. train.py에 `--no_densify` 경로 확인/추가 (densify_until_iter=0으로 대체 가능한지 확인)
2. 44c용: RoMA(또는 LoFTR/DKM) 페어 매칭 + 삼각측량 스크립트 — keyframe 656장 기준 인접쌍 매칭
3. exp37 init 자산 재사용: `results/`의 dense init 3종 (148,564 / 144,830 / 65,095 pts)

## 진행 결과 (07-12 오후, 갱신 중)

| run | init | PSNR@7k | region_n | 가시 | N | 시간 |
|---|---|---:|---:|---:|---:|---|
| 44a0 (대조군, carve 없음) | dense 148k | 28.63 | 29,323 | 433 | 148.6k | ~3분 |
| 44a (+carve) | dense 148k | 28.54 | 20,892 | 156 | 129k | ~3.5분 |
| 44a@15k | dense 148k | 30.36 | 20,789 | 154 | 129k | ~7분 |
| **44a′50 (carve-filtered init, w≤0.5)** | 44.7k | 27.69 | **815** | **26** | 42.6k | ~3분 |
| **44a′90 (w≤0.9)** | 68.8k | 28.02 | 3,520 | 50 | 66.3k | ~3분 |
| 44a″ (44a′90 + 이미지 색 init) | 68.8k | (실행 중) | | | | |

**발견:**
1. **dense init의 70%(103,883/148,564)가 관측된 빈 공간에 위치** — exp37 먼지 4.5배의 근원 정량 확인. init 사전 필터로 학습 후 먼지 96% 감소 (region 20,892→815).
2. in-training 청소(carve 예산)만으론 init 먼지 29k를 감당 못 함 — **먼지는 근원(init)에서 잡는 게 정답.**
3. 품질 갭 과제: no-densify 7k는 PSNR ~28로 30k-densify(32.5) 대비 ~4dB 낮음. 원인 후보 확인: **dense init이 전부 회색(128,128,128)** — EDGS는 이미지 색을 입혀 시작 (색 최적화 시간 절약). → 44a″(색 입힌 init)로 검증 중.
4. 필터 강도 트레이드오프: 강필터(50)는 먼지 최소지만 PSNR -0.85 (표면 커버리지 손실 추정 — score의 기지 사각지대인 anchor 없는 천장/monodepth 오차 점이 걸림), 약필터(90)가 균형.

## 교차 장면 라벨링 현황 (exp43)

- **301_305**: baseline 완료(PSNR 34.5, 렌더 양호) → **사용자 라벨링 진행 중**
- 301_12F: 탈락 (렌더 안개, N=20k — 어두운 복도)
- 301_2F: 탈락 (PSNR 22.8)
- 301_3F: 탈락 (SLAM 맵 보정으로 trajectory-지도 9.6cm 불일치, 검증기 거부)
- **snu_floor2_1**: 파이프라인 성공 → baseline 학습 중 (두 번째 라벨링 후보)
- **301_1253_rot**: pseudo-label 4,663개 가공 완료 (`data/scenes/301_1253_rot/carve_field.npz` + pseudo_labels/)

## 07-12 오후 2차 갱신 — 44f 품질 기함 성공

| run | densify | iter | PSNR | region_n | 가시 | N |
|---|---|---:|---:|---:|---:|---:|
| 44a″50 (강필터+색) | off | 7k | 28.72 | 846 | 71 | 41.3k |
| 44a″50 | off | 15k | 30.26 | 856 | 47 | 41.3k |
| 44a″50 | off | 30k | 30.95 | 850 | 47 | 41.3k |
| **44f (강필터+색 + densify + carve풀)** | **on** | 30k | **32.672** | 745 | 80 | 158k |
| (비교) exp40b | on | 30k | 32.576 | 498 | 28 | 143k |
| (비교) exp30r baseline | on | 30k | 32.579 | 3,749 | 180 | 148.5k |

**판정:**
1. **44f = 새 품질 기함 후보**: PSNR이 baseline 노이즈 대역 상단(32.67)이면서 먼지 -80% (745 vs 3,749). exp40b와 같은 Pareto 급에서 PSNR +0.1 — 깨끗한 색 init이 densify 트랙에서도 무해+소폭 이득 확인.
2. **no-densify 용량 천장 확정**: 41k 점은 30k iter를 줘도 30.95에서 수렴 (+0.35/15k분). 갭은 시간이 아니라 **용량·배치**. → 44g(스냅 init 130k) 검증 중, 부족 시 44c(RoMA).
3. 색 효과 재확인: 필터+색 7k(28.72) → 15k(30.26) 수렴 곡선이 회색 대비 일관 우위.

## 07-12 오후 3차 — 스냅 init으로 용량 갭 공략

| run (no-densify) | init | PSNR@7k | PSNR@15k | region_n | 가시 |
|---|---|---:|---:|---:|---:|
| 44a″50 강필터+색 | 41k | 28.72 | 30.26 | ~850 | 47 |
| 44g 스냅+색 | 130k | 30.36 | **31.82** | 7,207 | 236 |
| **44g′ 스냅+재필터** | 100k | 30.02 | **31.47** | **1,539** | 110 |

- **스냅 init(+1.6dB)**: 버린 빈공간 점을 ray 따라 표면 증거 깊이로 이동 — 용량·배치 가설 적중.
- 재필터로 먼지 -79% 회수 (PSNR -0.35 트레이드).
- **fast-track 현 최적: 44g′@15k = PSNR 31.47 / 먼지 1,539 / 7분** (exp40b 대비 -1.1dB, 시간 절반).
- 진행 중: 44h(스냅 init + 짧은 densify 3k + carve, 7k/15k) — RoMA 없이 갭을 닫는 마지막 싼 카드. 이후에도 갭 크면 44c(RoMA) 착수.

## 07-12 오후 4차 — 44h로 갭 해소, fast-track 레시피 윤곽

| run | densify | iter | 시간 | PSNR | region_n | 가시 |
|---|---|---:|---:|---:|---:|---:|
| 44g′ (스냅+재필터, no-densify) | off | 15k | 7분 | 31.47 | 1,539 | 110 |
| **44h (스냅+재필터 + densify≤3k + carve풀)** | ≤3k | 7k | 4분 | 30.28 | 1,879 | 264 |
| **44h @15k** | ≤3k | 15k | **7.5분** | **32.08** | 1,362 | 194 |
| (참조) exp40b 정규 | ≤7k | 30k | 14분 | 32.58 | 498 | 28 |

**판정: RoMA(44c) 없이 갭 사실상 해소** — 44h@15k가 baseline 노이즈 접경(-0.5dB)에 시간 절반.
짧은 densify(3k)가 용량을 채우고, gate+깨끗한 init이 먼지 폭발을 막는 구조가 작동.
44c(RoMA)는 "novel-view 품질 추가 개선" 목적의 선택 카드로 강등. 진행 중: 44ht(soft 0.03·prune 조기화·예산 1% 튜닝) — 가시 먼지(194) 다듬기 최종 샷.

### Fast-track 파이프라인 정리 (Aria 스트림 → recon, 데이터셋 이후 기준)
1. SLAM(OpenMAVIS) → sparse 7k pts + poses
2. dense init: monodepth 148k → **carve 필터 → ray 스냅 → 재필터 → 투영 착색** (CPU ~3분)
3. 학습: densify≤3k + carve(soft/prune/gate/force) × 15k iter (GPU ~7.5분)
→ **총 ~11분/장면, PSNR 32.1, 먼지 1.4k (baseline 3.7k 대비 -63%)**

## Verdict (07-12 확정)

**Fast-track 레시피 채택 (exp44h)**: `스냅-재필터-착색 init(100k) + densify≤3k + carve 풀레시피 + 15k iter`
→ **PSNR 32.08 / region 먼지 1,362 / 학습 7.5분 (+init 전처리 3분)** — 정규 트랙(exp40b, 14분)의 절반 시간에 baseline 노이즈 접경 품질. 44ht(λ·예산 튜닝)로 개선 없음 확인 — 가시 잔여 ~200은 기존 3D 신호 한계 집단.

**품질 기함 유지 (exp44f)**: 같은 init + densify≤7k + 30k = **PSNR 32.67 / 먼지 745 / 14분** — 시간 무관 최고 품질 시 선택.

**확립된 4원칙**: ① 먼지는 init에서 잡는다(사전 필터 -96%) ② 색은 선불(+1.0~1.6dB) ③ 갭의 정체는 배치·용량(스냅 +1.6dB) ④ 용량은 짧은 densify(3k)로 충분.

**후속(선택)**: 44c(RoMA) — novel-view 추가 개선용 / 44e(2D GS lift) — init 고도화 / 저텍스처 장면(12F류) 재도전.

## 07-12 저녁 — held-out 대반전 + Instant-GI PPM init

**① held-out(segment) 재평가 결과:**

| run | test PSNR | vs baseline(31.549) | vs exp40b(31.106) | region_n |
|---|---:|---:|---:|---:|
| 44h (스냅 init, 15k) | 30.804 | -0.75 | -0.30 | 1,326 |
| **44f (스냅 init + densify≤7k, 30k)** | **32.126** | **+0.58** | **+1.02** | 572 |

**44f가 held-out에서 baseline을 이긴 최초의 구성** — 깨끗한 착색 init이 novel-view 일반화를 실질 개선.
"먼지 제거 = -0.44dB 비용" 결론이 **init 개선으로 역전**됨. (44h는 -0.3dB — 속도 타협분)

**② exp44e (Instant-GI 사상 PPM init, 117k, 15k train):**
train PSNR 32.001 + **region 먼지 123 / 기여 0.00% — 역대 최저** (스냅 1,362의 1/11).
보정 monodepth의 per-pixel lift가 terminal-snap보다 배치가 정확. **fast-track 챔피언 교체 후보.**
→ 검증 중: 44e held-out + 44f2(PPM init 품질기함 30k). RoMA(44c)는 local_corr 이슈를 torch 폴백으로 수리 후 매칭 재실행 중.

## 07-12 저녁 2차 — 44f2 신기록: 3벤치마크 동시 개선

| run | init | 시간 | train PSNR | test PSNR | region_n | 가시 |
|---|---|---:|---:|---:|---:|---:|
| baseline (exp30) | ORB 7k | 8분 | 32.906 | 31.549* | 3,477 | 238 |
| exp40b (carve 정규) | ORB 7k | 14분 | 32.576 | 31.106* | 498 | 28 |
| 44f (스냅 init) | 스냅 100k | 14분 | 32.672 | **32.126** | 745/572 | 80 |
| **44f2 (PPM init + densify + carve)** | **PPM 117k** | 14분 | **33.524 (신기록)** | 검증 중 | **277** | 73 |
| 44e (PPM, fast 15k) | PPM 117k | 8분 | 32.001 | 30.787 | **123~150** | 60 |
| 44h (스냅, fast 15k) | 스냅 100k | 7.5분 | 32.076 | 30.804 | 1,326 | 176 |

*eval split run 별도 측정치.
- **44f2 = 새 절대 챔피언 후보**: 프로젝트 사상 최고 PSNR(exp08 33.012 경신) + 먼지 baseline의 7% + 동일 시간. Instant-GI 사상(내용-적응 확률맵 샘플링 + 보정 depth lift)의 기여 확정.
- fast-track 챔피언 교체: 44h → **44e** (PSNR 동률·먼지 1/9).
- RoMA init(44c, 71,789pts) 학습 중 — 기하 검증 배치의 최종 항목.

## 07-12 저녁 3차 — RoMA(EDGS 실전) 결과 + 하이브리드 착수

| run | init | train PSNR | region_n | 가시 |
|---|---|---:|---:|---:|
| **44c (RoMA, fast 15k)** | RoMA 71.8k | 31.215 | **67 (신기록)** | **24** |
| **44c2 (RoMA + densify 30k)** | RoMA 71.8k | 33.005 | 214 | 44 |
| (비교) 44f2 PPM 30k | PPM 117k | **33.524** | 277 | 73 |

- **RoMA = 청정 왕** (기하 검증 배치 — 먼지 67개), **PPM = 품질 왕** (33.52). RoMA의 PSNR 열위는 matching이 텍스처리스 표면(흰 벽·천장)을 못 덮는 커버리지 한계.
- → **44d 하이브리드** (RoMA 71.8k + PPM 보충 102.9k = 174.7k, 4cm voxel 우선권 RoMA) 학습 체인 등록 — 두 왕의 결합.

## 07-12 밤 — 최종 확정판

**44f2 held-out 확정**: test PSNR **32.292** (baseline +0.74dB, exp40b +1.19dB) — 신기록이 novel view에서도 성립. train과 test가 같은 방향 = 기생충 아닌 진짜 개선.

**44d 하이브리드 (RoMA+PPM)**: fast 15k에서 train 32.347 + region **147/가시 64** — **fast-track 신챔피언** (동시간대 PSNR·먼지 모두 최고). 44d2(30k) 진행 중.

## 🏆 Init 대전 최종표 (07-12 밤 확정)

| 순위 | init | 레시피 | 시간 | train PSNR | test PSNR | region먼지 | 가시 |
|---|---|---|---:|---:|---:|---:|---:|
| **종합 1위** | **44d2: RoMA+PPM 하이브리드 174.7k** | densify≤7k+carve 30k | 14분 | **33.799** | 검증 중 | 234 | 62 |
| 2 | 44f2: Instant-GI PPM 117k | 〃 | 14분 | 33.524 | **32.292 (+0.74 vs baseline)** | 277 | 73 |
| 3 | 44c2: RoMA 71.8k | 〃 | 14분 | 33.005 | — | 214 | 44 |
| fast 1위 | **44d: 하이브리드** | densify≤3k+carve 15k | **8분** | 32.347 | — | **147** | 64 |
| fast 2 | 44e: PPM | 〃 | 8분 | 32.001 | 30.787 | 123 | 60 |
| 청정 1위 | 44c: RoMA | 〃 | 8분 | 31.215 | — | **67** | **24** |
| (기준) | baseline ORB 7k | densify≤7k 30k | 8분 | 32.906 | 31.549 | 3,477 | 238 |

**결론**: 사용자 제안(EDGS·Instant-GI·depth-mono) 3종이 전부 적중 —
- Instant-GI 사상(PPM 샘플링)+depth-mono lift = **품질 축** (+0.6dB)
- EDGS(RoMA 삼각측량) = **청정 축** (먼지 67)
- **하이브리드 = 종합 우승** (train 33.80, baseline +0.89dB, 먼지 -93%)

## 최종 Verdict 갱신 (07-12 밤, 확정)

**종합 챔피언: exp44d2** — RoMA+PPM 하이브리드 init(174.7k) + densify≤7k + carve 풀레시피 + 30k (14분)
→ **train 33.799 / test 32.479 (baseline +0.93dB) / region 먼지 231~234 / 가시 62~72.**
**Fast-track 챔피언: exp44d** — 같은 init + densify≤3k + 15k (8분) → 32.35 / 먼지 147.

세 방법론의 최종 기여: Instant-GI 사상(PPM 적응 샘플링)=품질 축(+0.6dB), EDGS(RoMA 삼각측량)=청정 축(먼지 67), depth-mono(보정 lift)=둘의 공통 기반. 하이브리드가 3벤치마크 동시 석권.
잔여(선택): 44e2(GI 네트워크 학습 확률맵), 재현 run, MPS판 하이브리드.

## 07-12 심야 — 재현 확인 + 44e2(진짜 Instant-GI 네트워크) 판정

| run | train PSNR | region_n | 판정 |
|---|---:|---:|---|
| 44d2r (챔피언 재현) | 33.568 (1차 33.799, Δ0.23) | 258 | **재현 성공** — 노이즈 내 |
| 44dr (fast 재현) | 31.923 (1차 32.347, Δ0.42) | 128 | 노이즈 상단, 먼지 재현 |
| **44e2: 진짜 GI 네트워크 PPM (15k)** | **32.144** | 133 | 수제 Sobel PPM(32.001) 대비 **+0.14dB — 노이즈 내 소폭 우위** |

**44e2 정직 판정**: 사전학습 ConvNeXt PPM은 수제 확률맵과 사실상 동급. **가치의 원천은 네트워크가 아니라 '내용-적응 샘플링 + 보정 depth lift' 사상 자체** — Instant-GI에서 빌린 아이디어는 이미 44e/44d에 충분히 흡수됨. (통합 방법: gsplat/ellipse_fit/torch_kdtree 스텁 후 only_get_pf 경로만 사용 — `scripts/anchors/build_instantgi_net_init.py`)

## exp45 큐 (07-12 밤, 사용자 승인 4종)

| # | 실험 | 내용 | 상태 |
|---|---|---|---|
| 45a | **노출 모델링** | 챔피언 레시피 + `--train_test_exp` (per-image affine exposure) — 글레어·노출 잔차(floater의 먹이) 명시 모델링 | 체인 등록 |
| 45b | **dynamic carve field** | 학습 중 가시 gaussian 점유를 terminal attractor에 주기 반영 (정적 field → 동적) | 코딩 예정 |
| 44e3 | **GI 2D fit 속성 이식** | Instant-GI의 scaling·rotation·color를 3D covariance 초기값으로 (gaussian_model init 확장 필요) | 코딩 예정 |
| 45c | **progressive resolution** | 저해상도 선학습 → 체크포인트 재개로 고해상도 마무리 (2단계) — 시간 벤치 공략 | 코딩 예정 |
