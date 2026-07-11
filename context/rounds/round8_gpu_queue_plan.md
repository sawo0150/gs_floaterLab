# GPU 작업 큐 계획 (2026-07-12 수립, 실행 전)

> 목적: GPU를 무인 루프로 돌리며 carve loss 검증 + gradient flow 규명 + 3D force 부활 가능성 판정.
> 각 단계는 이전 단계 결과로 게이트됨. 성공 기준은 [round8_carve_loss_design.md](round8_carve_loss_design.md) "사전 등록" 섹션에 고정 (결과 보고 변경 금지).

## 큐 요약

| # | 작업 | 시간 | 게이트 | 산출물 |
|---|---|---:|---|---|
| ① | 렌더 A/B (6 변형 PSNR) | ~15분 | — (최우선) | 예산=무해 실증, 청소본 검증 |
| ② | Gradient-flow 프로브 | ~1시간 | — | 정착 메커니즘 + 3D force 판정 데이터 |
| ③ | 계측 심기(CPU) → exp38a 학습 | ~5시간 | ①PASS | carve 검증 + 출생/정착 계측 |
| ④ | exp38b 학습 | ~5시간 | ③완료(성패 무관) | soft loss 순기여 분리 |
| ⑤ | 아침 결정: exp30 재현 or exp39 or exp40 | ~5시간 | ①~④ 결과 | 지표 노이즈 or MPS 확장 or 3D force |

## ① 렌더 A/B 검증 (최우선, ~15분)

`scripts/analysis/carve_psnr_check.py` — 변형 6종 PSNR(GT) + PSNR(원본렌더 대비):
원본 / A_safe / A_mid / A_orig(폐기 후보 대조군) / user_cleaned / **룰베이스 balanced 청소본** / **영역(GT region) 청소본** (뒤 2종은 variants 디렉토리에 추가 필요 — CPU 5분).

- **판정 기준(사전 등록)**: A_safe 하락 ≤0.05dB → PASS. user_cleaned의 ΔPSNR = "floater 제거 이득"의 참조 상한.
- **게이트**: A_safe FAIL 시 exp38 착수 보류 — 기여량 예산 가정이 틀렸다는 뜻이므로 재캘리브레이션 먼저.
- 부수 판정: A_orig(기여 3.8% 삭제)의 하락폭 → harm 지표의 dB 환산 계수 획득.

### ① 결과 (07-12 실행) — FAIL이지만 게이트의 전제가 틀렸음을 발견

| 변형 | ΔPSNR(GT, train views) | vs원본렌더 |
|---|---:|---:|
| A_safe | **-1.82dB** (기준 ≤0.05 FAIL) | 36.5dB |
| A_mid | -2.83 | 32.7 |
| **user_cleaned (수동 정답)** | **-3.71** | 31.7 |
| rulebase_balanced | -3.21 | 31.8 |
| region_cleaned | -4.38 | 30.0 |
| A_orig (폐기 대조군) | -5.66 | 27.6 |

**핵심 발견: 사용자의 수동 편집(시각적 정답)조차 train PSNR -3.7dB** → **floater는 train-view PSNR의 기생충** — 학습 뷰 잔차(글레어·노출)를 흡수해 지표를 올림. 시각 기여량 proxy는 "픽셀을 얼마나 바꾸나"는 맞혔지만(A_safe vs원본렌더 36.5dB) "그 픽셀이 GT-fit을 얼마나 지고 있나"를 못 봄.

**수정 해석 (amendment — 결과 확인 후 기록임을 명시):**
1. **train PSNR은 floater 품질 지표로 부적합** — 오히려 역방향 선택압. 품질 판단은 region GT 지표 + (향후) held-out 뷰로.
2. **사후 삭제 비용 ≠ 학습 중 삭제 비용**: 학습 중 prune은 최적화가 잔차를 표면에 재분배 (exp13 = -0.16dB 선례). A_safe -1.8dB가 exp38의 예상 손실이 아님.
3. 게이트 판단: "A_safe FAIL → exp38 보류" 조항은 전제 오류로 무효화. **exp38 예정대로 진행** — in-training 흡수가 실제로 일어나는지가 exp38의 검증 대상 (PASS 1 기준 PSNR ≥32.7 유지 — 이제 진짜 정보량 있는 관문).
4. 부수 확인: 하락 순서 = harm 지표 순서 (A_safe < rulebase ≈ user < region < A_orig) — 지표의 순서 보존성 유효.

## ② Gradient-flow 프로브 (~1시간) — "3D force 부활 가능성" 판정 포함

exp32 30k 체크포인트 로드, 뷰 전수(or stride 2)로 개별 backward를 돌려 **라벨 floater 2,817개의 gradient를 뷰 단위로 분해** (누적이 아니라 뷰별 벡터 보존):

측정 항목:
1. **coherence ratio** ‖Σ_views g‖ / Σ_views ‖g‖ (xyz·opacity 각각) — 진동 가설(≈0) vs 줄다리기 가설(>0.3) 판정
2. **뷰별 줄다리기 지도**: 어느 뷰가 floater opacity를 올리는가(부양 뷰) / 내리는가. 부양 뷰가 소수·특정 패턴(글레어·specular)인지
3. **평형 강성**: floater를 ε만큼 인위 변위 후 gradient 변화 → RGB가 얼마나 강하게 제자리로 되끄는지
4. 표면 대조군 동일 측정

**이 데이터가 판정하는 것 — 3D force 부활 두 갈래** (아래 "exp40 후보" 참조):
- coherence 낮음(진동) → 약한 일관 힘이 장기적으로 이김 → **A안(carve-potential force) 유리**
- 부양이 소수 뷰에 집중 → 힘을 더하는 대신 **부양 gradient를 빼는 B안** 유리
- 평형 강성 큼(강한 되끌림) → xyz 이동 계열 전체 불리 → opacity 소멸 경로(현 carve loss) 유지가 정답

### ② 결과 (07-12 실행, stride 2 = 652뷰, `gradient_probe.npz`)

| 측정 | floater | surface |
|---|---:|---:|
| xyz coherence ‖Σg‖/Σ‖g‖ p50 | 0.257 | 0.205 |
| opacity 순부양 비율 | 42.1% | 41.9% |
| 부양/억압 질량비 p50 | 0.76 | 0.75 |
| 부양 상위10뷰 집중도 p50 | 73.2% | 58.9% |

**판정: 진동 가설 승** — floater를 잡아두는 건 강한 일관된 핀이 아니라 상쇄되는 노이즈 평형 (gradient 크기의 ~74%가 서로 상쇄). 표면과 통계적으로 거의 구별 안 됨 → 판별은 오직 w(x) 몫.
→ **A안(carve-potential force) 청신호**: 평형 위에 약한 일관 편향만 얹으면 drift 방향을 지배. B안(뷰 게이트)은 집중도 차이(73 vs 59%)가 중간 수준이라 후순위.
→ A안 설계 시 주의: potential φ의 attractor를 terminal 증거로만 잡으면 feature-poor 표면(anchor 없는 천장)이 밀려남 — attractor = terminal ∪ 현재 가시 gaussian 점유로 확장 필요.

## ③ exp38a — carve loss 첫 학습 (soft+prune+gate, ~5시간)

착수 전 CPU 작업 (~30분):
- `gaussian_model.py`에 `accum_rgb_grad_vec`(방향 벡터 누적) 추가 — coherence를 학습 전체에서 공짜로 획득
- `densify_and_split`에 출생 이벤트 로그(부모 id·scale·viewspace grad) — "허공에 걸친 큰 부모" 가설 검증
- 계측 추가 후 문법 체크 + 짧은 스모크(500 iter)

완료 즉시 자동 채점:
- PASS 1: PSNR@30k ≥ 32.7
- PASS 2: eval_carve_load score>0.5 < 5,800, 가시 < 450
- PASS 2': **표준 GT 지표** region_n < 1,750 / region_visible < 120 / region_contrib < 1.15%
- PASS 3: harm_spent ≤ 0.0075, gate 차단량 < 신생아 15%

### ③④ 결과 (07-12 새벽) — 학습이 회당 ~10분임이 판명, 다회전 모드 전환

| | PSNR@30k | region_n(<1,750) | region가시(<120) | 먼지기여 | N |
|---|---:|---:|---:|---:|---:|
| exp30 기준 | 32.906 | 3,477 | 238 | 2.27% | 147,620 |
| **exp38a (soft+prune+gate)** | 32.266 (PASS1 ✗ -0.64dB) | **559** ✓ | **27** ✓ | **0.54%** ✓ | 134,554 |
| **exp38b (prune+gate)** | 32.663 (노이즈 경계) | 1,744 ✓ | 187 ✗ | 1.39% ✗ | 147,117 |

판정:
- **exp38a = floater 억제 압도적** (region -84%, carve-load 가시 905→9). PSNR -0.64dB — 단 ① amendment 기준으로 보면 **in-training 흡수 증명**: 같은 청정도를 사후 삭제로 얻으면 -3.2dB.
- **soft loss가 가시 먼지의 주역** (a/b 분리). 시너지 발견: soft가 opacity를 낮춰 같은 기여 예산으로 더 많은 점 prune 가능 (a가 b보다 12.6k 더 삭제).
- exp38c(λ 0.05→0.02, score_min 0.5)로 PSNR 회복 여지 탐색 중.

### 계측 수확 (exp38a split_events + gvec)

- **split 출생의 29.5%가 허공(w>0.5)** — 76%는 5k 이전. 가설 수정: 허공 부모는 크지 않고(scale 0.122 vs 0.115) **저op 반투명**(0.165 vs 0.245) — **"먼지가 먼지를 낳는" 연쇄**. gate+soft 처방의 사후 정당화.
- 전 학습 coherence(30k 누적): region 잔존 0.049 vs 표면 0.018 — 진동 지배 재확인.

## ④ exp38b — prune+gate만 (~5시간)

exp38a 성패와 무관하게 진행 (soft loss 분리가 목적). a PASS + b PASS이고 차이가 노이즈 내면 **더 단순한 b 레시피 채택**.

### 배치2 결과 (07-12 새벽): exp38c = 사실상 전 기준 PASS

| | PSNR@30k | region_n | region가시 | carve가시 |
|---|---:|---:|---:|---:|
| exp30r (baseline 재현) | 32.579 | 3,749 | 180 | 860 |
| **exp38c (softlite λ0.02/smin0.5 + prune+gate)** | **32.557** | **946** | **33** | **18** |

- **baseline run-to-run 노이즈 ±0.33dB 실측** (exp30 32.906 vs exp30r 32.579; region 지표 노이즈 ~8%/±25%가시) → exp38c PSNR은 baseline과 통계적 구별 불가.
- **exp38c = PSNR 무손실 + 가시 먼지 -98% (860→18) + region 먼지 -73%.** 사전 등록 PASS 1·2·2' 충족. **현 최종 후보 레시피.**
- λ 트레이드오프 확인: λ0.05(exp38a)는 억제 최강(region 559)이나 -0.3dB 추가 비용, λ0.02가 스위트스팟.

### exp39 (MPS 전이) 결과: 전이 성공

PSNR 32.666 (exp08 33.012 대비 -0.35dB — full soft λ0.05 사용, exp38a와 같은 패턴), **가시 먼지 96→2, 먼지 기여 6.42→1.34%**. MPS에도 carve가 그대로 작동. softlite(λ0.02) MPS 변형이면 PSNR 갭도 닫힐 전망.

### exp40a (carve-potential force) 결과: **3D force 부활 성공**

exp38b(prune+gate) 대비 force만 추가: PSNR 32.663→32.667(무비용), region_n 1,744→**1,309**, region가시 187→**134**, carve가시 905→**503**. 프로브의 진동 가설 예측("평형 위 약한 일관 힘이 drift를 지배")이 학습으로 실증. plateau의 실패 요인(사각지대·판별·경계 소멸·희석)을 모두 고친 형태의 xyz-force가 실제로 작동. exp40b(force+softlite)가 exp38c 대비 결합 이득이 있는지 확인 중.

## ⑤ 아침 결정 (택1)

| 옵션 | 조건 | 내용 |
|---|---|---|
| exp30 재현 | 지표 신뢰구간 필요 시 | region 지표의 run-to-run 노이즈 측정 (exp38 채점 신뢰도) |
| exp39 | exp38 PASS 시 | MPS 트랙 carve (config 준비됨) |
| exp40 | ② 프로브가 유리 판정 시 | 3D force 부활 실험 (아래) |

## exp40 후보: 3D force 부활 두 갈래 (프로브 ② 결과로 택1)

plateau의 4중 실패 중 1(사각지대)·2(판별)는 carve field로 이미 해결 가능. 남은 문제는 3(이동≠삭제)·경쟁 gradient였고, 이를 각각 우회하는 두 설계:

**A안 — Carve-potential force (힘을 더하기):**
`L = λ Σ w_i·φ(x_i)`, φ = free-space voxel의 표면까지 distance transform.
- plateau와의 차이: ① 겨냥이 carve field(AUC 0.98) ② **경계에서 힘이 멈추지 않음** — 표면 도달까지 연속 견인 (plateau는 D=1 껍질에서 gradient 소멸) ③ per-point 직접 적용(λ/N 희석 없음, score>0.5 게이트) ④ 표면 위에선 φ≈0이라 자연 소멸.
- 도착 후: 잘못된 색으로 표면에 붙지만 색·opacity는 RGB가 재최적화 — "먼지의 표면 재활용". 이동 실패해도 opacity 경로(기존 carve loss)와 병행 가능.
- 리스크: 오분류 점(feature-poor 표면)도 끌려감 — 단 그런 점은 φ가 작아 힘도 약함.

**B안 — 부양 gradient 차단 (힘을 빼기):**
프로브에서 "floater를 살려두는 부양 뷰/gradient"가 특정 패턴(소수 뷰, opacity-상승 성분)으로 확인되면, **high-w 점에 한해 그 성분을 감쇠** — 새 힘을 더하지 않고 존재의 근거를 제거해 자연 소멸(opacity가 스스로 prune 임계 아래로).
- plateau 실패 요인과 정반대 접근: 힘의 크기 경쟁 자체를 회피.
- 리스크: gradient 조작은 PSNR 부작용 예측이 어려움 — 반드시 w-게이트 하에서만.

## 운영 규칙

- 각 단계 완료 시 자동 채점 → 사전 등록 기준 대조 → 카드 기록 → 다음 단계.
- FAIL 시: 다음 학습은 진행하되(정보 가치) 원인 가설을 기록, ⑤에서 진단 우선으로 전환.
- GPU 점유 확인 후 착수 (다른 프로세스 있으면 대기).
