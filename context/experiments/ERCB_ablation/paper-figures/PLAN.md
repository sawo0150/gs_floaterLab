# paper-figures — 논문 본문에 들어갈 표 2개 + 그림 2개

> 시작: 2026-09-20
> 목적: ERCB_ablation에서 이미 수행한 실험들을 논문 본문용 산출물 4개로 고정한다.
> 상태: **Phase 1 실행 중** (view-ordering densify-on 격자)

이 폴더는 실험을 새로 설계하는 곳이 아니라, `benchmark-B/`와 `dense-supervision/`에서
나온 결과를 논문 산출물로 확정하는 곳이다. 학습 계약은 전부 benchmark-B에서 상속한다.

---

## 1. 산출물 구조

| # | 뒷받침하는 주장 | 형태 | 조건 |
|---|---|---|---|
| **Table 1** | supervision source — keyframe만 vs keyframe + 중간 프레임 | 19장면 집계 | keyframe당 **60** update 고정 |
| **Figure 1** | 위 주장의 수렴 과정 | 3패널 = 데이터셋 3개 | 동일 |
| **Table 2** | view ordering — random reshuffling vs ERCB | 19장면 집계, **예산 15/30/60을 열로** | Phase 2에서 정하는 regime |
| **Figure 2** | 위 주장의 수렴 과정 | 3패널 = **예산 15/30/60** | 동일 |

**표와 그림은 같은 측정을 공유한다.** 각 곡선의 마지막 점이 곧 해당 표의 값이다.

### 그림 공통 규격 (HAMMER Fig. 5 idiom)

HAMMER (arXiv:2501.14147) Fig. 5를 따른다. 그 논문 §IV-B2: *"the average PSNR of each
method on the held-out evaluation dataset, comprised of 10 held-out frames per device"*,
*"evaluation views span the entire scene"*.

| 항목 | 값 |
|---|---|
| x축 | `Map Optimization Step` — 누적 optimizer step, **절대값** (정규화 금지) |
| y축 | `Evaluation PSNR` |
| 평가 집합 | llffhold-8. trajectory 전체를 덮고, **모든 arm이 미학습**. 장면당 42~1,061장 |
| 측정 | 각 checkpoint 지도로 고정 집합 전체를 렌더링 → 평균 PSNR |
| checkpoint | run당 **24개** (run 길이의 1%~100%) |
| 선 | 패널당 **2개**. 굵게, 주석·화살표·target선·에러밴드 **없음** |
| 라벨 | 장면 이름은 패널 안 회색 배지, 범례는 맨 아래 공유 |

### 장면 선정 규칙 (캡션에 명시 — cherry-picking 방지)

- **Figure 1**: 데이터셋별로 최종 Δ가 그 데이터셋의 **중앙값**인 장면.
- **Figure 2**: 예산 60에서 ERCB−RR Δ가 19장면 중 **중앙값**인 장면 하나.
- 나머지 장면 곡선은 부록.

---

## 2. 왜 이 구조인가 (기각한 대안)

- **fraction-of-run x축** — 장면을 평균내려다 강제된 정규화. 이 분야는 수렴 곡선을
  평균내지 않는다 (3DGS², SIGGRAPH 2025, Fig. 4: 6개 장면 small multiples, 절대 iteration).
  평균을 포기하면 정규화가 필요 없다. → **절대 step 축으로 확정.**
- **age-aligned 축** (도착 후 경과 interval) — 자기 주장에 유리한 평가축을 새로 정의한
  것으로 읽힌다. → 기각.
- **forgetting 패널**, **그림 안의 예산별 subplot**, **6패널 small multiples** → 기각.

---

## 3. 데이터 인벤토리 (예산은 keyframe interval당 update 수)

| 자산 | 위치 | regime | 보유 |
|---|---|---|---|
| kf_only / kf_dense @60, 5 checkpoint | `dense-supervision/evidence/manifest.json` | densify on | 38/38 |
| kf_only / kf_dense @60, **24 checkpoint** | `dense-supervision/evidence/manifest_curve.json` | densify on | 38/38 |
| kf_only / kf_dense @120 (+SSIM/LPIPS) | `dense-supervision/evidence/manifest_budget.json` | densify on | 38/38 |
| RR / ERCB @15/30/60, 5 checkpoint, PSNR만 | `benchmark-B/evidence/manifest.json` | **fixed topology** | 완비 |
| RR / ERCB @15/30/60, **24 checkpoint** | `paper-figures/evidence/manifest_view_ordering.json` | densify on | **Phase 1 진행 중** |

`manifest_curve.json`의 `kf_dense@60`이 곧 densify-on RR@60이므로 재학습하지 않고 재사용한다
(114 job 중 19개).

### 재현성 (2026-09-20 실측)

`manifest.json` → `manifest_curve.json` 재실행은 학습 인자가 바이트 단위로 동일한데
최종 PSNR이 **최대 0.24dB** 어긋났다. CUDA rasterizer backward의 atomicAdd 순서
비결정성이며, 프로젝트 기존 실측치 ±0.33dB와 일치한다. **paired Δ에서는 상쇄된다**:
평균 Δ +0.333 → +0.332, 승률 15/19 → 15/19. 단일 seed로도 arm 간 차이는 재현된다.

---

## 4. Phase 계획

| Phase | 내용 | 비용 | 상태 |
|---|---|---|---|
| **1** | view-ordering densify-on 격자 (RR/ERCB × 15/30/60 × 19장면, 24 checkpoint). 95 job 학습 + 19 job 재사용 | ~3.3h | **실행 중** |
| **2** | regime 판정 — densify-on vs benchmark-B fixed topology | 5분 | 대기 |
| **3** | Table 2 / Figure 2 생성. fixed topology가 이기면 Figure 2용 대표 장면 1개만 24 checkpoint 재실행 (6 job, 20분) | — | 대기 |
| **4** | SSIM/LPIPS 렌더링 — Table 1 (38 run) + Table 2 (114 run) | ~3~6h | 대기 |
| **5** | Table 1 / Figure 1 생성 | — | 대기 |

### Phase 2 판정 기준 (미리 고정)

**held-out PSNR이 더 높은 regime을 고른다.** "ERCB 우위 폭이 큰 쪽"으로 고르면
cherry-picking이다. 우위 폭은 결과로 함께 보고하되 선택 기준으로 쓰지 않는다.

---

## 5. 미결

- **Table 2의 데이터셋 분해** — 예산 3열 × 데이터셋 3분해는 본문에 너무 넓다.
  본문 All-19 집계 + 부록 분해를 제안했고, 사용자가 Phase 2 이후에 결정하기로 함.
- Table 1의 운영점을 60으로 확정함(실시간성). 예산 120 결과(+1.11dB, 18/19)는
  `dense-supervision/README.md`에 참고로 남긴다.

---

## 6. 파일

| 파일 | 역할 |
|---|---|
| `prepare_view_ordering.py` | Phase 1 manifest 생성 (114 job) |
| `run_panel_view_ordering.py` | 순차 실행/재개 |
| `evidence/manifest_view_ordering.json` | job 원장 + 계약 + sha256 |
