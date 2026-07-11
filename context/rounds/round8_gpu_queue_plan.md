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

## ④ exp38b — prune+gate만 (~5시간)

exp38a 성패와 무관하게 진행 (soft loss 분리가 목적). a PASS + b PASS이고 차이가 노이즈 내면 **더 단순한 b 레시피 채택**.

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
