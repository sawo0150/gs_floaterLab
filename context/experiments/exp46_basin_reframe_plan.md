# exp46 (계획) — Floater = 분지(basin) 재프레임: 압력에서 basin 설계로

- 상태: **계획** (2026-07-14 수립, 사용자와의 방향 토론에서 도출)
- 배경: exp43에서 "탐지≠제거" 간극 확정 (vr AUC 0.908이지만 학습 통합 무효, 12F carve -1dB). 사용자 통찰로 한 단계 더 깊은 재프레임에 도달.

## 재프레임: floater는 '점'이 아니라 photometric loss의 '분지(basin)'다

- **핵심 관찰 (사용자)**: 이미지가 뭉개진 게 아니라 **장소 특성상 "먼지 하나 띄워 잔차 흡수"가 "올바른 geometry 세우기"보다 loss가 더 낮거나 더 가까운 분지**다. floater는 photometric loss의 **정당한 local minimum(숏컷)**.
- 따라서 carve로 누르면(pressure) photo gradient가 다시 그 분지로 끌어내림 → **압력으론 근본적으로 못 이김** (12F carve -1dB가 증거).
- **이기는 방법 = 더 세게 누르기가 아니라, 올바른 geometry를 floater보다 가깝고/깊은 분지로 만들기.**
- 최적화 관점: 이는 round8 이래의 문제의식("저차원 gaussian → local minima 지배 → landscape smoothing 필요")의 연장선. carve force(φ 견인)가 continuation의 일종이었으나 underfit 장면에선 부족.

## 원인 이분법: (a) 도달 불가 vs (b) 환원 불가 — 처방이 갈린다

| 유형 | 정의 | 왜 floater가 더 가까운가 | 처방 |
|---|---|---|---|
| **(a) 도달 불가형** | 올바른 표면이 **씨앗 없음** (init에 없고, 시차 부족으로 photo gradient가 삼각측량도 못 함) | floater가 잔차를 줄이는 **유일한 길** | **좋은 init** — 표면을 불투명 gaussian으로 미리 심으면 그 자리 잔차가 낮아 floater 채용 이유 소멸 |
| **(b) 환원 불가형** | 잔차가 **어떤 geometry로도 안 사라짐** (fog·글레어·노출 = 시점의존, 완벽한 표면으로도 픽셀 안 맞음) | floater가 시점의존 잔차를 흡수하는 게 **실제로 유용** | **appearance 채널** — non-geometric 합법적 흡수구(per-image affine 노출/view-dependent embedding) 제공 = "숏컷의 먹이 뺏기" |

- **진단이 곧 실험**: "좋은 init을 줬는데도 floater가 돌아오는가?"
  - 돌아옴 → (b) 환원 불가 → appearance 모델링이 답
  - 죽음 → (a) 도달 불가 → init이 답
- **장면별 예상 병명** (슬라이드 27 이미지 특성 분석 기반):
  - 1253/305: 이미지 선명(대비 39) → **(a)형 유력** — init으로 해결 가능
  - 12F: fog(대비 25.6, 시점의존) → **(b)형 유력** — init으로 안 되고 appearance 필요 (미검증)
  - rot: 시차 부족 → (a)의 특수 케이스 (init +1.37dB 실증, 단 시차 자체 부족으로 잔여)

## 개선안 7축 (carve/vr을 '압력'에서 'basin 설계'로 승격)

> 선결 확인: 커스텀 렌더러가 이미 depth를 출력함(`gaussian_renderer/__init__.py` "depth") → 축 7 옵션 (a) per-pixel 깊이 가중 즉시 구현 가능.

### 축 1 — 305 hybrid init + carve (가장 확실, 재료 준비됨)
- 근거: 305는 이미지 밝고 선명(대비 39, PSNR 34.5) → RoMA·depth가 잘 먹히는 **(a)형 후보**. 지금까지 305는 depth-anchor carve만 했고 **hybrid init은 미투입**.
- 가설: hybrid init(RoMA+PPM, `build_hybrid_init_scene.py`)을 넣으면 carve 압력 없이도 floater가 depth-carve보다 더 줄어든다 = "init이 압력보다 낫다"를 다른 방에서 확증.
- 비교선: 305 depth-carve(먼지 994~1,184) vs 305 baseline(6,888) vs 305 hybrid+carve(?).
- 실행: `scripts/anchors/build_hybrid_init_scene.py --scene 301_305` (depth 캐시·보정 depth 이미 있음) → carve 학습. ~30분.

### 축 2 — 12F 좋은 init 진단 (병명 확정)
- 근거: 12F가 (a)냐 (b)냐를 판별하는 결정적 실험. hybrid/depth-lift init + carve 학습 1회.
- 예측: fog가 supervision을 굶기므로(시점의존 잔차) **천장(~32) 거의 안 오름** → 맞으면 "fog=(b)형, init 무효" 확정 → 축 4로. 틀리면 (a) 재해석.
- 재료: 12F depth_anchors.npz, 보정 depth(depth_pro_calib) 이미 준비됨. ~15분.

### 축 3 — 표면-확신 불투명 init (init 시점 carve/vr 활용 강화)
- 현재: carve로 빈 공간 init 점을 **제거**만 함 (수동적).
- 개선: depth+carve가 "여기 표면"이라고 **합의하는 voxel은 불투명·고신뢰 gaussian으로 시작** → 잔차를 floater보다 먼저 선점. floater가 태어나기 전에 표면이 그 자리를 차지.
- 구현 스케치: init 점의 opacity를 carve score 반비례로 초기화(표면 확신 점은 σ⁻¹(0.9), 빈 공간 의심 점은 낮게) + 색 선불. `CARVE_INIT_ATTRS` 경로(exp44e3에서 쓴 per-point 속성 주입) 재활용 가능.
- 검증: 44e3 attrs 이식이 먼지 4배였던 원인(무분별 이방성)과 구분 — 여기선 opacity/신뢰도만 조정.

### 축 4 — appearance/노출 채널 재설계 ((b)형 전용 처방)
- 근거: 45a 노출 모델링은 **개념이 아니라 프로토콜 때문에 기각**(train_test_exp가 eval-split 전용 설계 → 전체이미지 PSNR 27.79). 개념(시점의존 잔차의 합법적 흡수구)은 유효.
- 재설계: 전체이미지 학습 경로에 **per-image affine 노출항만** 추가(마스킹·eval 프로토콜 제거). fog·글레어 잔차를 노출항이 흡수 → floater 채용 필요 소멸 가설.
- 확장 후보: 작은 view-dependent appearance embedding (NeRF-W/GS appearance 사상) — per-image latent + tiny MLP.
- 검증: 12F에서 축 2가 (b) 확정 시 착수. floater(먼지)가 노출항 도입으로 줄어드는지.

### 축 5 — densification을 carve-aware하게 재유도 (억제→방향전환)
- 근거: floater는 3k–7k split에서 태어남(계보 실증). 현재 gate는 나쁜 출생을 **죽이기만** 함(capacity 낭비).
- 개선: φ(표면 거리장)을 써서 **split 자식의 위치/방향을 표면 쪽으로 편향** → 같은 capacity가 floater 대신 표면 보강에 쓰임. "먼지가 먼지를 낳는 연쇄"를 "먼지가 표면을 낳도록" 전환.
- 구현 스케치: `densify_and_split`에서 자식 xyz에 φ의 -∇ 방향 오프셋 추가 (score>문턱인 부모 한정).
- 리스크: split은 photo gradient 방향이 근거라 강제 편향이 품질 해칠 수 있음 → 약한 편향부터.

### 축 6 (보조) — (b)형 운영점: no-densify + 좋은 init
- 반직관적 방어: fog 장면에선 **densify를 꺼 capacity를 묶으면** floater를 만들 여분 gaussian이 없음 → 고정 예산을 표면에 강제.
- 좋은 init(표면 씨앗) + no-densify 결합 = "fog는 PSNR 살짝 포기하고 깨끗하게" 운영점.
- 축 2/4 결과에 따라 fog 장면 표준 레시피 후보.

### 축 7 — 원거리 photometric 감쇠 (distance-attenuated photometric loss, 사용자 제안)
- **근거**: [round9](../rounds/round9_pixel_frustum.md) — 원거리 1px가 물리적으로 큼(12F Q3 footprint 18.6mm = 1253의 3.1×, p95 28.7mm). 원거리 영역은 ① 픽셀 수 적고 깊이 모호해 supervision이 약하고 ② floater가 부피·시각 피해를 가장 크게 내는 곳. **먼 곳의 photometric 보상을 줄이면 그곳의 floater 숏컷이 얕아짐** → basin 재프레임의 "숏컷 보상 제거"에 직결.
- **가설**: 렌더 깊이가 큰 픽셀(또는 카메라-공간 깊이가 큰 gaussian)의 photometric gradient를 감쇠하면, 먼 free-space floater가 잔차를 흡수해도 이득이 줄어 carve/기하 prior가 이김. 특히 12F·305처럼 footprint가 큰 장면에서 효과 클 것으로 예상.
- **구현 옵션**:
  - (a) **per-pixel 깊이 가중**: `L = Σ_p w(z_render_p)·‖I_p−Î_p‖`, w는 깊이 증가 시 감소. 렌더러의 depth 출력 필요(커스텀 rasterizer depth map 확인).
  - (b) **per-gaussian gradient 스케일**: rasterizer backward에서 카메라 깊이로 gradient 감쇠 — 더 외과적, 렌더러 수정 필요.
  - (c) **간단 프록시**: w(z)=1/(1+(z/z0)^k) 또는 z_far 초과 hard cutoff. z0/z_far는 **장면별 round9 분위수로 스케일**(예 Q3·p90) — 하드코딩 미터값 금지(1253 얕음 vs 12F 깊음 불일치).
- **리스크·주의**:
  - **먼 진짜 표면도 supervision 손실** → 원거리 벽/천장이 과소복원·흐려질 수 있음. Pareto = "원거리 디테일 ↔ 원거리 floater". 감쇠 강도 튜닝 필수.
  - carve와 상보: carve는 free-space 먼지를 제거(위치), 축 7은 먼지 생성 유인을 제거(잔차) — **결합 실험**. 축 4(노출/appearance)와도 같은 계열("숏컷의 먹이 뺏기").
  - 관련 선행: mip-NeRF 360 distortion loss·배경 모델링이 원거리 floater 억제로 알려짐 — 이론적 근거 있음.
- **지표**: region GT 먼지(특히 **원거리 먼지 = 깊이 Q3 초과 분할**), held-out PSNR(원거리 열화 감시), 그리고 원거리/근거리 먼지 비율 변화.
- **진단 가치**: 원거리 감쇠로 12F floater가 PSNR 무손실로 줄면 → "원거리 photometric 숏컷" 메커니즘 확증. PSNR이 크게 떨어지면 → 원거리 supervision이 load-bearing이었다는 반증.

## 실행 우선순위 (사용자 합의)

1. **축 1 (305 hybrid init)** — (a)형에서 "init > 압력" 확증. 가장 근거 확실, 재료 완비.
2. **축 2 (12F 좋은 init 진단)** — (a)/(b) 병명 확정.
3. 축 2가 (b) → **축 4 (노출 재설계)**, 축 1 성공 → **축 3 (표면-확신 init)** 로 심화.
4. **축 7 (원거리 photometric 감쇠)** — round9로 근거 확보됨. footprint 큰 12F/305에서 효과 예상 → 축 2와 묶어 검증(둘 다 원거리 floater 대책). 렌더러 depth 출력 확인이 선결.
5. 축 5(densify 재유도)·축 6(no-densify 운영점)은 위 결과 본 뒤 판단.

## 한 줄 요약

**carve는 "floater를 지우는 압력 도구"에서 "올바른 basin을 init으로 심고 densify를 그쪽으로 유도하는 basin 설계 도구"로 승격돼야 한다.** 압력(soft/prune)은 clean 장면 마무리용으로 잔존. 단 fog((b)형)만은 init으로도 안 되고 appearance 채널이 필요하며, 그 갈림을 12F 실험(축 2)이 판정한다.

## 실행 결과

### 축 1 — 305 hybrid init + carve: **(a)형에서 "init > 압력" 결정적 확증** (07-14)

| 305 30k | PSNR | N | region_n | 가시 | **free-space 먼지(진짜 부유물)** |
|---|---:|---:|---:|---:|---:|
| baseline | 34.51 | 112k | 6,888 | 708 | 461 |
| depth-carve (압력 위주) | 34.48 | 98k | 1,184 | 173 | 29 |
| **hybrid init + carve (축1)** | **35.84** | 586k | 5,517 | 647 | **4** |

- **좋은 init이 품질·청정 둘 다 이김**: PSNR **35.84 = 305 최고**(baseline +1.33dB, depth-carve +1.36dB), 진짜 free-space 먼지 **461→29→4**로 hybrid가 가장 깨끗. "먼 표면을 미리 불투명하게 심으면 floater가 잔차를 흡수할 이유가 사라진다"는 basin 가설의 직접 증거.
- **지표 해석 주의**: region_n 5,517은 **조밀 init(586k) 아티팩트** — 라벨 볼륨 안에 정상 표면점이 대량 들어감(free-space 비율 0.01 = 99%가 표면 부착). **공정 지표는 free-space 먼지 개수**(4). region GT는 dense init에서 과대계상되므로 free-space split 병기 필수.
- **비용**: N 586k(depth 앵커 1.4M 상속)로 무거움 — 실용화하려면 init dedupe/budget 필요. 품질·청정 결론과는 별개.
- **판정**: (a)형(선명한 방)에서 **carve는 압력이 아니라 init 재료로 쓸 때 최강.** 305는 (a)형 확정. → 축 3(표면-확신 불투명 init)으로 심화 가치 높음.

### 축 2 — 12F 좋은 init 진단: **예측(b) 반박, 그러나 지표 함정 주의** (07-14)

- 12F hybrid init(carve 없음): **train PSNR 35.441 = baseline(32.034) 대비 +3.41dB.** 예측("fog=(b) 환원불가, init 무효")이 **train PSNR로는 반박됨** — 좋은 init이 12F도 크게 개선.
- **그러나 판정 보류**: free-space 먼지 **1,289**(carve 없어 높음), N 454k. **+3.41dB가 진짜 기하 개선인지, 조밀 init의 floater 인플레이션인지 train PSNR로는 구분 불가**(floater=train PSNR 기생충 교훈 — 2,817 삭제가 -3.7dB였던 것과 규모 유사, 경계 필요).
- **판별 런 발사**: 12F hybrid init + **carve**(exp46_ax2b) — 먼지를 청소한 뒤에도 PSNR이 유지되면 → **12F는 (a)형, init이 답**(예측 최종 반박) / 청소하니 PSNR이 baseline으로 떨어지면 → 인플레이션이었고 (b) 유지.
- **함의(잠정)**: 305(축1)에 이어 12F도 좋은 init에 강하게 반응 → "fog=원리적 환원불가"보다 "저텍스처=init으로 해결 가능한 (a)형"일 가능성. self-diagnosis 규칙3("둘 다 실패→carve off")도 "좋은 init 먼저" 재해석 여지. **축2b 결과가 확정**.
