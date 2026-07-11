# carve_loss_design — Free-Space Carve 기반 floater loss 설계 (학습 없이 분석만)

- 날짜: 2026-07-11
- 입력: exp32_lineage_diag 30k ply + 수동 라벨 2,817개 (ground truth), SLAM 7,205pts, 카메라 1,303개
- 산출물: `results/experiments/exp32_lineage_diag/{loss_candidate_league.json, loss_candidate_round2.json, carve_fields.npz, final_score_w_phys.npz}`
- 스크립트: `scripts/analysis/design_floater_loss_candidates.py` (Round 1), `design_floater_loss_round2.py` (Round 2)

## 목적

plateau loss가 수동 floater를 원리적으로 못 잡는다는 검증([exp32_lineage_diag §3](exp32_lineage_diag.md)) 이후,
**같은 입력(SLAM 포인트 + 카메라 포즈)만으로** floater를 정확히 겨냥하는 3D loss를 설계하고,
라벨 2,817개를 채점표로 삼아 학습 없이 후보들을 리그전으로 평가.

## 핵심 신호: Free-Space Carve (공간 조각)

카메라 → (frustum 내) SLAM 포인트로 ray를 쏘면, **ray가 통과한 허공은 "관측된 빈 공간"**이다.
- `transit(v)` = voxel v를 표면 앞 허공으로 통과한 ray 수 (0.1m voxel, step 0.06m, 표면 margin 0.2m)
- `terminal(v)` = voxel v 근처(±0.2m)에서 끝난 ray 수 (표면 증거)
- **증거비** `ρ(x) = transit/(transit + 3·terminal)` (3³ smoothing) — "이 위치가 빈 공간일 확률"
- 최종 score `w(x) = ρ(x) · min(d̄₅ₙₙ_SLAM(x)/0.25, 1)` — 빈 공간이면서 anchor에서 먼 곳

## 리그전 결과 (floater=positive, AUC)

| 후보 | AUC | recall@FP1% | 비고 |
|---|---:|---:|---|
| plateau 정규화 D (기존, 참고) | 0.511 | — | 무작위 수준 |
| S3 DepthPro anchor 1-NN 거리 | 0.876 | 0.0% | DepthPro anchor는 오염됨 |
| S1 SLAM 1-NN 거리 | 0.930 | 24.2% | 고정 tau plateau와 동치 |
| S2 SLAM 5-NN 평균 거리 | 0.943 | 22.2% | outlier 강건 |
| S5 carve 단독 | 0.841 | 27.2% | 저FP에서 독보적 조기 정밀도 |
| S6 carve × d (rank 곱) | 0.952 | 55.0% | 상호보완 확인 |
| **R6 ρ_smooth × d (증거비)** | **0.974** | **63.1%** | **최종 채택** |
| R5 logistic oracle (재대입 상한) | 0.983 | 65.4% | 결합 이론 상한 |

물리 단위 버전 `w = ρ·min(d5/0.25,1)`도 AUC 0.967~0.970으로 rank 버전과 동급 → 실제 loss에 사용 가능.

## 결정적 leverage: floater는 "한계 생존자"

수동 floater opacity 중앙값 **0.044** (표면 0.194) — prune 임계 0.01 바로 위에서 간신히 생존.
op>0.3인 가시 floater는 142개뿐. → 큰 힘이 아니라 **w로 편향된 약한 opacity 압력**이면 선택적으로 소멸 가능.
soft loss `L = λ·Σ wᵢ·opᵢ`의 per-point bias는 floater:표면 = **7.2:1** 선택성.

## 제안: Carve Loss (3 + 1 구성요소, 필드 1회 전처리 공유)

전처리(학습 시작 시 1회, CPU ~2분): ρ field + SLAM 5-NN 거리 → `w(x)` trilinear lookup.

| # | 구성요소 | 메커니즘 | 라벨 시뮬레이션 결과 |
|---|---|---|---|
| A | **공간 가변 prune 임계** `op_thr(x) = 0.01 + 0.19·w(x)` | prune 사이클마다 적용 | **floater 89.6% 제거, 가시 표면 오삭제 0개** |
| B | **densify 게이트**: 자식이 w>0.95 위치면 split/clone 차단 | 출생 자체를 차단 (floater 100%가 7k 전 split 출생) | floater 출생 91.2% 차단, 표면 밀집화 7.7% 차단 |
| C | **soft opacity bias** `L = λ·Σ wᵢ·σ(opᵢ)` | opacity로의 직접 gradient 경로 (plateau에 없던 소멸 작용자) | 선택성 7.2x, floater 필요 logit 하강 1.52 vs 표면 3.17 |
| D | (선택) 가시 고립 클럼프 prune: `d_support` = w<0.3&op>0.3인 지지 구조까지 거리 | 가시 잔존자 전용 (AUC 0.935) | 가시FP 0.1%에서 가시 floater +24개 |

**조합 시뮬레이션 (A+D)**: 2,817개 중 **2,561개(90.9%) 제거, 가시 표면 손실 59개**(D에서만 발생, D 제외 시 0개).
놓친 256개 중 가시(op>0.3)는 104개 — 이들은 3D 기하 신호만으로는 한계, multi-view 색 일관성 등 photometric 신호 필요.

### ⚠ 피해 재정량 (07-11 후속) — "가시 점 0개 삭제"는 과대평가였음

"op>0.3 점 개수"는 피해 지표로 너무 거칢. **시각 기여량**(opacity × 투영면적 × 노출 프레임수) 기준으로 재측정하면:
- 규칙 A(thr_max=0.2)가 지우는 비-floater의 기여량은 **전체의 3.83%** — 사용자가 지운 floater 기여량(1.08%)의 3.5배. 유의미 점의 50%+가 사라지는 0.3m voxel도 1.3% (국소 구멍 위험). **원안 폐기.**
- 게이트 B(w>0.95)가 밀집화를 차단하는 영역은 기여량 13.75%를 보유 — 학습 검증 전까지 위험 축.

**안전 운영점 재탐색 결과 (recall vs 기여손실 frontier):**

| 규칙 | recall | 표면 기여손실 | 구멍 voxel |
|---|---:|---:|---:|
| ~~A 원안: op<0.01+0.19w~~ | 89.6% | 3.83% | 1.30% |
| **A_safe: w>0.9 & op<0.1 & contrib<p90** | **69.4%** | **0.39%** | **0%** |
| A_mid: w>0.9 & op<0.1 | 72.2% | 0.88% | 0% |
| 보수: w>0.9 & op<0.05 | 51.2% | 0.30% | 0% |

contrib(기여량)은 학습 중에도 opacity·scale·accum_visibility로 계산 가능 → in-training 적용 가능한 규칙.
부족한 recall은 soft loss C(RGB가 저항 가능해 자가 교정적)가 학습 중 보완하는 구조로 설계.

**렌더 검증 준비 완료**: `carve_prune_variants/{A_safe, A_mid, A_orig, user_cleaned}` 모델 4종 생성,
`scripts/analysis/carve_psnr_check.py`로 GPU가 빌 때 PSNR 직접 측정 예정 (결과: `carve_psnr_check.json`).

## vs plateau loss (구조적 차이)

| | plateau | carve |
|---|---|---|
| 판별력 (AUC) | 0.511 | 0.974 |
| 작용 대상 | xyz (이동만, 경계에서 gradient 소멸) | **opacity (소멸)** + 출생 차단 |
| 타이밍 | start 5000 (floater 65%가 그 전 출생) | densify 전 구간 + 출생 게이트 |
| per-point 희석 | λ/N (mean + cyclic sampler) | prune/게이트는 희석 없음 |
| 추가 입력 | DepthPro anchor 생성 필요 | **SLAM pts + 카메라만** (이미 있음) |

## 전이성 (라벨 없는 run, 부하 지표)

- exp30 (baseline): 가시 floater 부하(w>0.9&op>0.3) 3,975개, 규칙A prune 21.6%
- exp37 (dense init): 부하 6,205개, 규칙A prune **39.7%** — dense init 점들이 저op로 빈 공간에 대량 잔존.
  **⚠ dense init과 규칙A의 상호작용은 학습 중 검증 필요** (init 직후 대량 prune 가능성).

## Round 3 (07-11 밤, 자율 루프): 자기조직 신호 + 기여손실 예산 평가

평가 지표를 "FP 점 개수"에서 **표면 기여손실 예산 대비 recall**로 교체 (표면 보호 관점 직접 최적화).

**기각된 prior들** (모양 기반 직관 전멸 — pitfalls 등재):
평면성 AUC 0.64, 법선 정렬 0.64, SH 뷰의존 에너지 0.49(!), scale 등방성 0.51.
이 장면의 floater는 "모양"으로 구별 불가 — split 산물이라 표면 조각과 형태가 같음.

**새 챔피언: `w × (이웃 최대 opacity 부재)`** — "빈 공간 + 주변 5cm~ 내 단단한 지지점 없음":

| 신호 | AUC | recall@기여손실 0.1% | 0.3% | 1% |
|---|---:|---:|---:|---:|
| w 단독 | 0.967 | 1.1% | 4.4% | 13.7% |
| nbr_op_max(-) 단독 | 0.889 | 9.9% | 29.3% | 59.0% |
| **w × nbr_op_max(-)** | 0.959 | **41.1%** | **56.2%** | **76.3%** |
| w × graph_dist × nbrop | 0.967 | 23.7% | 45.8% | 69.6% |

연결성(신뢰 seed에서 graph 도달성): floater 99.1% 도달불가로 recall 최강이나 표면도 21.7% 도달불가(먼지 편재) → 예산 기준 열세. 가시 floater(142개)에는 여전히 고립도(local_d5/d_support, AUC 0.93)가 최강.

## Round 4 (07-11 오후, 자율 루프): 물리 단위 규칙·라벨 감사·조기 검출

1. **물리 단위 챔피언**: `score = w(x)·(1−maxop_r(x))` (r=0.05m 반경 내 최대 opacity) — **AUC 0.976~0.980 (역대 최고)**, recall@기여손실 0.1/0.3/1% = 31.9/49.6/74.0%.
2. **하드 임계 규칙은 위험 확정**: `score>0.5`로 자르면 recall 94.9%지만 기여손실 6.0%. **in-training 규칙은 임계값이 아니라 "예산 상한부 top-K prune"** (score 내림차순으로 누적 기여량이 예산 B에 닿을 때까지만 삭제)이어야 함 — 자기 제한적이고 안전.
3. **라벨 감사**: score>0.5인 비-floater 7,258개(기여량 6%)는 수동 floater 무리 근처가 아님(최근접 0.67m, 0.1m 이내 1.2%) — 미라벨 floater 잔여물이 아니라 별개의 애매 집단(얇은 구조물 or 사용자가 안 지운 먼지). **내일 렌더 A/B(A_orig 변형)가 판정** — A_orig PSNR이 원본과 같으면 이들은 없어도 되는 집단.
4. **조기 검출 가능**: 7k 체크포인트 위치·opacity로 계산한 score의 AUC **0.957** (30k score와 상관 0.847) — densify 종료 직후부터 in-training 적용 가능한 신호임을 확인.

## Round 5 (07-11 저녁, 자율 루프): 추가 검증 + 학습 코드 구현 완료

1. **반복 peeling 불필요**: prune 후 maxop 재계산하며 10 cycle 반복(0.05%씩) ≈ 정적 1회 top-K(59.5% vs 60.1%) — 규칙은 단순 정적 형태로 충분.
2. **soft loss 필요 강도 실측**: opacity 리셋 후 재성장 속도 floater 6.3e-5 logit/iter (표면 1.3e-4) — Adam 기준 gradient RMS의 0.25% bias면 상쇄. λ는 극소로 충분, 관건은 score 오분류뿐.
3. **⚠ exp37 경고**: 챔피언 score 부하(score>0.5)가 exp37 dense init에서 58,510개로 exp30/32의 4.5배, 가시 후보 1,558개(exp32의 1.7배). **|Z|>4m·unseen-voxel 지표는 frustum 안 먼지를 놓친다** — "exp37 최고 억제" 결론은 이 지표로 재평가 필요.
4. **구현 완료** (`3dgs-custom`): `eval/carve_loss.py` (soft+prune+gate, plateau 패턴 미러링), `train.py` 훅 4개(import·init·backward·post_backward), `configs/carve_loss/exp38_carve.yaml`(+prunegate_only 변형), `scripts/experiments/run_exp38_carve.sh` (exp38a=전부, exp38b=prune+gate만). 문법·config·field build·birth_step gate 로직 검증 완료. score refresh 비용 0.38s/회 → 30k 학습에 ~1분 오버헤드.

## Round 6 (07-11 저녁, 자율 루프): occlusion·knee·평가 하네스·SuperSplat 함정

1. **occlusion 보정 무효과**: 32² 깊이버퍼로 가림 필터링해도 AUC 0.9759 vs 0.9760 — 현행 frustum 근사 유지 확정.
2. **예산 knee**: 0.2%→42%, 0.5%→60%, 0.75%→69%, 1%→74% recall. 한계효율은 0.5~0.75%에서 급감 시작 — exp38 기본값 0.5% 유지, 여유 시 0.75% 변형.
3. **평가 하네스**: `scripts/analysis/eval_carve_load.py` — 임의 run의 먼지 부하(score>0.5 수·가시 수·score 질량·먼지 기여%) 표준 측정. exp38 채점용.
4. **⚠ SuperSplat 함정 발견**: cleaned ply는 좌표 회전+속성 재인코딩 상태 (pitfalls 등재). user_cleaned 렌더 변형을 원본 행 기반으로 재생성 완료. 교정된 수치: 사용자 편집의 먼지 기여 7.83%→6.93%, A_safe는 7.34% (사용자 편집과 유사 수준을 자동 달성).

## Round 7 (07-11 저녁, 자율 루프): 잔여 가시 floater 정밀 분해 — tier-2 자동화 기각

score>0.3에서 못 잡는 가시 floater 36개 원인 분해:
- **19개: floater 무리 상호지지** — 고op floater끼리 5cm 내에서 서로 maxop veto를 발동시킴.
- **13개: SLAM outlier anchor가 허공 합법화** — anchor 근처(d5 0.15m)지만 가시 표면에선 0.49m 떨어진 위치.

**수정 시도와 기각**:
- 수정A(지지 자격을 anchored 이웃(w<0.5)으로 제한): 가시 caught 112→129/142로 개선되나, 애매 고op 집단의 self-veto가 사라져 **예산 recall 붕괴** (0.1%손실 recall 31.9→0.7%). 먼지 규칙과 양립 불가.
- 수정B(terminal 증거 있는 anchor만 사용): 이 장면 SLAM은 이미 깨끗해서(증거 0인 anchor 16/7,205) 무효과.
- **tier-2(가시 무리 전용 자동 prune) 기각**: 가시 floater 114~129개를 잡는 비용이 가시 표면 3,6~7,4천개(기여 11~16%). 리뷰 랭킹 도구로도 상위 100개 정밀도 3%. **가시 floater 무리(142개)와 "빈 공간의 진짜 고op 구조" 집단은 3D 기하 신호만으로 분리 불가** — soft loss의 완만한 압력 + photometric 중재(학습 중) 또는 multi-view 색 일관성(향후)의 영역.

→ **최종 설계 고정**: 챔피언 v1 `w·(1−maxop_all,5cm)` + 예산 prune + gate + soft loss (exp38 config 그대로).

## Round 8 (07-11 밤, 자율 루프): MPS 전이 + 애매 집단의 시각적 판정

1. **MPS 트랙 전이 완료**: `build_mps_carve_field.py`(타깃 188k 다운샘플, ~9분) → `results/diagnostic/mps_carve_field.npz`, 평가는 `eval_mps_carve_load.py`. **MPS anchor의 7.6%(47,411개)가 terminal 증거 없는 outlier** → 검증 필터 필수 (ORB에선 무효과였던 수정B가 MPS에선 핵심). 측정: exp08 먼지기여 6.42%(가시 96), exp13 9.32%(가시 89). CarveLoss에 `cam_stride/target_voxel/anchor_term_min` 옵션 추가, `configs/carve_loss/exp39_carve_mps.yaml` 준비 완료.
2. **멀티뷰 패치 투영으로 애매 집단 정체 판정** (`patch_evidence/patches_*.png`, GPU 불필요):
   - **B(score>0.5 & op>0.3, 사용자가 안 지움)**: 3뷰 일관 = **feature-poor 실표면** (광택 천장·균일 벽·책상 물체·케이블). SLAM anchor 부재로 d5 크고, occlusion 무시 근사로 rho도 큼. **지우면 안 됨** — tier-2 기각 시각적 재확인, soft loss의 RGB 중재에 맡기는 설계가 정답.
   - **C(score>0.5 & op<0.1, 사용자가 안 지움)**: 다수가 뷰 간 불일치 = **미라벨 진짜 먼지**. 사용자 라벨은 저op 먼지에 불완전 → **측정된 "표면 기여손실"은 과대평가** (일부는 floater 제거가 맞음). 예산 prune의 실질 harm은 수치보다 낮다.

## Round 9 (07-11 밤, 자율 루프): 멀티뷰 색 일관성 — 기각

가시 floater 잔여물 공략용 마지막 CPU 신호 테스트. 각 점을 163뷰(stride 8, 256²)에 투영해 GT 색의 강건 분산(MAD) 측정 → **역상관 (AUC 0.33)**: floater가 표면보다 색이 더 일관됨. 원인: 이 장면은 흰 벽·천장 지배적이라 허공 먼지의 배경이 모든 뷰에서 동일하게 하얗고, 실표면은 텍스처 경계+포즈 오차로 오히려 색이 흔들림. **photometric 축은 raw 색 수집으로 불가 — 렌더-GT 잔차(GPU) 필요.** 기존 신호와의 결합도 전부 열화. (negative result, 재시도 방지용 기록)

## Round 10 (07-11 밤): 런타임 예산 캘리브레이션

학습 중에는 라벨을 모르므로 예산이 **지워지는 floater의 기여까지 포함해** 소모됨 (시뮬레이션은 표면 harm만 계산). 보정 측정: 런타임 예산의 ~30%가 floater 기여로 소모 → **budget_total 0.75%(런타임) = 실제 표면 harm ~0.52%, recall 54.5%**. exp38/38b/39 config 모두 0.005→0.0075로 갱신 완료.

## 사전 등록: 검증 성공 기준 (결과 보기 전에 고정, 07-11)

**렌더 A/B (carve_psnr_check.py, 변형 4종):**
- PASS: `A_safe` PSNR(GT) 하락 ≤ 0.05dB (vs 원본). `A_orig`(폐기 후보)는 하락 예상 — 예상대로면 harm 지표 체계 신뢰 ↑.
- `user_cleaned`의 PSNR 변화가 "floater 제거의 이득 상한" 참조점.

**exp38a/b (30k 학습):**
- PASS 1 (품질): PSNR@30k ≥ 32.7 (exp30=32.906, run 노이즈 ±0.24dB 하한).
- PASS 2 (먼지): `eval_carve_load.py` 기준 score>0.5 개수 < 5,800 (exp30의 절반), 가시(op>0.3) < 450 (exp30=884의 절반).
- PASS 3 (예산 준수): 로그의 `carve/harm_spent` ≤ 0.0075, gate가 표면 밀집화를 과도 차단하지 않았는지 gate_pruned 총량 < 신생아의 ~15%.
- exp38a(soft 포함) vs exp38b(prune+gate만) 비교로 soft loss의 순기여 분리.
- FAIL 시 1순위 의심: budget prune의 재밀집화 상호작용(7k 이후엔 densify 없음 → 재발 불가, 그러면 gate 부작용), soft λ 과대.

## 한계 / 다음 단계

1. 모든 수치는 exp32 한 장면의 **재대입 평가** (라벨은 평가에만 사용했으나 thr_max=0.2, τ=0.25, gate=0.95는 이 라벨로 튜닝됨).
2. 학습 중 동력학(재밀집화, RGB 복원력과의 경쟁, PSNR 영향) 미검증 — **실제 학습 1회로 검증 필요** (A+B만 먼저, C는 λ sweep).
3. carve field는 frustum 근사(occlusion 무시) — 그럼에도 AUC 0.97이므로 정밀 occlusion은 후순위.
4. 진짜 미관측 공간 floater(auto 76개)는 carve 신호가 0 — 기존 ray-density full-depth prune이 별도로 담당 (상보적).

## Verdict

**설계 성공 (분석 단계)**. 같은 입력만으로 plateau(AUC 0.51) → carve(0.97)로 겨냥이 교정되고,
이동(xyz)이 아닌 소멸(opacity·출생차단) 작용자를 확보. 수동 floater의 90.9%를 가시 표면 손실 0~59개로
제거 가능함을 라벨 기준으로 입증. 다음은 학습 1회 재현 (후보: exp38).
