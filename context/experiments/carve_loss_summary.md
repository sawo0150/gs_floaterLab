# CPU 분석 실험 총정리 — Plateau의 사망 진단과 Carve Loss의 탄생 (2026-07-11)

> 학습(GPU) 없이 순수 분석만으로 진행한 하루치 실험의 종합 요약.
> 상세 로그는 [carve_loss_design.md](carve_loss_design.md) (Round 1~10), [exp32_lineage_diag.md](exp32_lineage_diag.md) §3 참조.
> **핵심 자산**: 사용자가 SuperSplat으로 직접 지운 floater 2,817개 = 사람이 라벨링한 ground truth. 모든 후보 방법을 학습 없이 이 채점표로 즉시 평가할 수 있었다.

---

## 1. 출발 질문: "내 plateau loss로 저 floater들을 잡을 수 있나?"

**답: 원리적으로 불가능. 4가지 독립적인 구조적 실패가 겹쳐 있다.**

실제 학습에 쓰인 plateau field(DepthPro anchor 7,108개 + ellipsoidal 적응형 tau)를 그대로 재구성해서 확인한 결과:

| # | 실패 | 수치 근거 |
|---|---|---|
| 1 | **사각지대**: floater의 66%가 plateau "안"에 있어 gradient가 수학적으로 0 | 학습 로그와 교차검증 — inside 판정 floater의 90.4%가 30k 내내 plateau grad ≡ 0 |
| 2 | **판별 불능**: 정규화 거리 D로 floater와 표면을 구별 못함 | AUC 0.511 = 동전 던지기. λ를 키우면 표면도 똑같이 맞음 (exp20~26 PSNR 하락의 원인) |
| 3 | **작용 대상 오류**: xyz만 밀 수 있고 opacity 경로가 없음 | floater를 "삭제"하지 못하고 경계까지 "이동"만 시킴. 경계 gap 중앙값 5.8cm — 옮겨봤자 그대로 보임 |
| 4 | **타이밍**: floater 100%가 densify 종료(7k) 전 출생 | plateau 시작은 5k, split 출생은 RGB gradient가 주도 — 출생 자체를 못 막음 |

**반전 포인트**: λ 크기는 애초에 문제가 아니었다 (경계 도달 필요 λ 중앙값 0.034 — 쉬움). 그리고 **신호 자체는 살아 있었다** — raw 유클리드 거리는 AUC 0.93. 적응형 tau(kNN spacing 비례)가 anchor 희소 지역의 plateau를 부풀려 그 신호를 파괴한 것.

또 하나의 정정: floater들은 "opacity>0.5로 버티는 강자"가 아니라 **중앙값 0.044의 한계 생존자**였다 (표면은 0.194). prune 임계(0.01) 바로 위에서 간신히 사는 먼지 무리 — 이 발견이 새 설계의 지렛대가 된다.

---

## 2. 새 설계: Carve Loss (조각 손실)

### 2-1. 직관

카메라에서 SLAM 포인트로 ray를 쏘면, **ray가 통과한 허공은 "비어 있다고 관측된 공간"**이다.
조각가가 돌을 깎아내듯, 수천 개의 ray가 지나간 공간에는 아무것도 있으면 안 된다.

```
ρ(x) = transit(x) / (transit(x) + 3·terminal(x))   ← "이 위치가 빈 공간일 확률"
        (통과한 ray 수)      (여기서 끝난 ray 수 = 표면 증거)

w(x) = ρ(x) · min(d_SLAM5NN(x)/0.25m, 1)           ← 빈 공간이면서 anchor에서도 먼 곳

score = w(x) · (1 − 이웃 5cm 내 최대 opacity)        ← + 주변에 단단한 지지점도 없는 곳
```

**추가 입력이 전혀 필요 없다** — plateau가 쓰던 것과 같은 SLAM 포인트 + 카메라 포즈뿐 (DepthPro anchor 생성도 불필요).

### 2-2. 성적표 (라벨 2,817개 기준)

| 판별 신호 | AUC |
|---|---:|
| plateau 정규화 D (기존) | 0.511 |
| SLAM 거리 단독 | 0.930 |
| carve 단독 | 0.841 |
| **최종 score (w × 이웃op부재)** | **0.976~0.980** |
| 이론 상한 (oracle logistic) | 0.983 |

이론 상한에 0.005 차이까지 접근 — 3D 기하 신호로 뽑을 수 있는 건 거의 다 뽑았다.

### 2-3. 안전 프레임: "임계값"이 아니라 "예산"

사용자 질문("표면에 해 안 가?")이 잡아낸 핵심 설계 원칙:

- **피해 지표를 교체**: "지운 점 개수"가 아니라 **시각 기여량**(opacity × 투영면적 × 노출 프레임수). 저opacity 점 수만 개의 합은 유의미하기 때문 — 초기 규칙(공간 가변 임계)은 이 지표로 3.83% 손실이라 폐기됐다.
- **임계값으로 자르면 위험** (score>0.5 → recall 95%지만 손실 6%): 대신 **score 내림차순으로 지우되 누적 기여량이 예산에 닿으면 멈추는 top-K 방식** — 피해가 수학적으로 상한됨.
- 캘리브레이션: 런타임 예산의 ~30%는 (지우려는) floater 기여가 소모 → **런타임 예산 0.75% = 실제 표면 손실 ~0.5%, floater 55% 제거**.
- 게다가 패치 증거(아래 §4)에 따르면 "표면 손실"로 센 것의 상당수가 실은 안 지운 먼지 — **실제 피해는 이 수치보다도 낮다**.

### 2-4. 세 개의 작용점 (모두 같은 field 공유)

| 구성요소 | 무엇을 하나 | 근거 수치 |
|---|---|---|
| **soft loss** `λ·Σ score·op` | opacity에 직접 하강 압력 (plateau에 없던 "소멸" 경로). 진짜 표면은 RGB gradient가 저항해 자가 교정 | 선택성 7.2:1, floater 억제에 필요한 bias는 gradient RMS의 0.25%뿐 |
| **예산 prune** (7k부터 1k마다) | score 상위를 예산 한도 내에서 삭제 | 7k 시점 조기 검출 AUC 0.957 확인 — densify 끝나자마자 잡을 수 있음 |
| **출생 게이트** (densify 직후) | score>0.95 위치에 태어난 신생아 즉시 삭제 | floater 출생의 91% 차단 (표면 밀집화 차단은 7.7%) |

---

## 3. 기각된 아이디어들 (재시도 방지용 — prior가 얼마나 틀렸는지)

| 아이디어 | 직관 | 실측 | 왜 틀렸나 |
|---|---|---|---:|
| 평면성 (이웃 PCA) | "표면은 판, floater는 덩어리" | AUC 0.64 | floater는 split 산물이라 표면 조각과 모양이 같음 |
| 법선 정렬 | "표면끼리는 법선이 맞음" | AUC 0.64 | 〃 |
| SH 고차 에너지 | "floater는 뷰마다 색을 속임" | AUC **0.49** | 오히려 역방향 |
| scale 등방성 | "floater는 둥글다" | AUC 0.51 | 무신호 |
| 멀티뷰 색 일관성 | "floater 뒤 배경은 뷰마다 다름" | AUC **0.33 (역상관!)** | 이 방은 흰 벽/천장 지배적 — 먼지 배경이 어느 뷰에서나 하얗고, 표면은 텍스처+포즈오차로 더 흔들림 |
| 연결성 (신뢰 구조에서 graph 도달성) | "floater는 고립됨" | recall은 최강(99.1%) | 표면도 21.7%가 도달불가(먼지 편재) → 예산 효율 열세 |
| occlusion 보정 carve | "가림 무시는 부정확" | AUC 변화 0.0001 | 근사로 충분 |
| 가시 floater 자동 prune (tier-2) | "고op 무리도 자동으로" | floater 114개당 표면 3,600개 | 가시 무리와 "feature-poor 실표면"은 3D 기하로 분리 불가 (§4) |

교훈 두 줄:
1. **모양 prior는 전멸, 위치·맥락 신호만 작동한다** (빈 공간 + anchor 거리 + 지지 부재).
2. **평가 지표가 설계를 결정한다** — "점 개수 FP"로 보면 좋아 보이던 규칙이 "기여량 손실"로 보면 위험했다.

---

## 4. 패치 증거: 애매한 점들의 정체 (렌더링 없이 눈으로 판정)

score는 높은데 사용자가 안 지운 점들을 서로 다른 3개 카메라의 GT 이미지에 투영해 패치로 비교
(`results/experiments/exp32_lineage_diag/patch_evidence/`):

- **가시 애매군 (op>0.3)**: 3뷰에서 같은 물체가 보임 = **진짜 표면**. 광택 천장·균일 벽·책상 물체·케이블 — SLAM feature가 안 잡히는 곳이라 anchor가 없어서 score가 높았을 뿐. **지우면 안 되는 것들** → 자동 처리 기각이 옳았음을 시각적으로 확인.
- **저op 애매군 (op<0.1)**: 다수가 뷰마다 배경이 다름 = **사용자가 귀찮아서 안 지운 진짜 먼지**. 즉 라벨은 저op 먼지에 불완전하고, 우리가 "표면 오삭제"로 센 것 일부는 사실 정당한 제거였다.

---

## 5. 부수 발견: 기존 결론에 대한 경고 2건

1. **exp37(dense init, 현 1순위)이 챔피언 score 기준으로는 최다 먼지** — score>0.5가 58,510개로 exp30/32의 4.5배, 가시 후보 1,558개. 기존 지표(|Z|>4m, unseen-voxel)는 **카메라 frustum 안에 떠 있는 먼지를 못 본다**. exp37 "최고 억제" 결론은 재평가 필요.
2. **MPS semidense anchor의 7.6%(47,411개)는 표면 증거가 없는 outlier** — MPS 트랙에서 carve를 쓸 땐 terminal-검증 필터가 필수 (ORB에선 불필요했음).

---

## 6. 산출물 (바로 쓸 수 있는 것들)

| 종류 | 경로 |
|---|---|
| **학습 코드** (soft+prune+gate 통합) | `3dgs-custom/eval/carve_loss.py` + `train.py` 훅 4개 |
| **실행** — ORB 트랙 exp38a/b | `scripts/experiments/run_exp38_carve.sh` (config: `3dgs-custom/configs/carve_loss/exp38_carve.yaml`, `exp38_prunegate_only.yaml`) |
| **실행** — MPS 트랙 exp39 | `3dgs-custom/configs/carve_loss/exp39_carve_mps.yaml` (field: `results/diagnostic/mps_carve_field.npz`) |
| 채점 도구 (먼지 부하 표준 지표) | `scripts/analysis/eval_carve_load.py` (ORB), `eval_mps_carve_load.py` (MPS) |
| 렌더 A/B 검증 (GPU 뜨면 ~10분) | `scripts/analysis/carve_psnr_check.py` + `carve_prune_variants/{A_safe,A_mid,A_orig,user_cleaned}` |
| plateau 사망 진단 | `scripts/analysis/verify_plateau_capability.py` → `plateau_capability_report.json` |
| 리그전 스크립트/결과 | `design_floater_loss_candidates.py`, `design_floater_loss_round2.py` → `loss_candidate_*.json` |
| 시각 증거 | `patch_evidence/patches_{A,B,C}*.png` |

**성공 기준은 결과를 보기 전에 카드에 사전 등록해 둠** (carve_loss_design.md "사전 등록" 섹션):
렌더 A/B는 A_safe 하락 ≤0.05dB, exp38은 PSNR ≥32.7 + 먼지 부하 절반 + 예산 준수.

## 7. 남은 리스크 (정직하게)

- 모든 수치는 **한 장면(exp32) 재대입 평가**이고, 임계값 일부는 그 라벨로 튜닝됨.
- **학습 동력학은 미검증** — 재밀집화 상호작용, soft λ 과대 여부, gate의 표면 밀집화 부작용(차단 영역이 기여량 13.75% 보유)은 exp38이 판정.
- 가시 floater 142개 중 ~36개는 3D 신호의 원리적 한계 밖 — 렌더-GT 잔차(photometric) 축이 다음 후보.
