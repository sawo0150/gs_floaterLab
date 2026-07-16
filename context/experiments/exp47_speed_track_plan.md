# exp47 (계획) — 속도 최적화 트랙: incremental을 위한 per-chunk 레시피 확정

- 상태: **계획** (2026-07-15 수립, 사용자 방향 지시)
- 배경: exp46에서 품질/floater는 확보(305 35.84dB·먼지4, 12F 35.07·243, rot +1.37dB — 사용자 "충분" 판정). 그러나 학습 시간 **26~72분**으로 실시간 목표와 거리 멂.
- **목적: 품질을 하한선으로 고정하고 속도만 최적화 → incremental(스트리밍 갱신)의 per-chunk 학습 예산 확정.**
- 전제: incremental은 "새 keyframe 몇 장을 기존 모델에 빠르게 추가"가 핵심 → 지금 batch 속도 최적화가 그 per-chunk 비용/품질을 그대로 알려줌.

## 품질 하한선 (유지 목표, 이 아래로 떨어지면 실패)

| 장면 | PSNR 하한 | free-space 먼지 상한 |
|---|---|---|
| 305 | ≥ 34.5 (baseline 이상) | ≤ 30 |
| 12F | ≥ 33.5 | ≤ 300 |
| (참고 현재) 305 35.84/4 · 12F 35.07/243 | | |

## 현재 병목 (exp46 timing 분석)

1. **iterations 30k** — fast-track은 15k로 절반 (44d 8분 실증)
2. **dense init 300~600k** — 매 iter 비쌈 + carve _refresh_score(전체 N KDTree)가 N 비례. 12F 66분의 주범.
3. **data_device cpu** — 이미지 매 iter CPU→GPU 전송. cuda면 제거되나 메모리 한계.
4. **전체 프레임(2000+장) 학습** — 실시간은 keyframe만. 최대 감속 여지.
5. **carve field build + refresh 빈도** — cam_stride·refresh_interval로 조절 가능(축B가 coarse화로 66→29분 실증).

## 속도 축 (우선순위: 무료 이득 → Pareto → incremental 정렬)

### 축 S1 — data_device cuda (무료 이득, 품질 0 손실)
- 이미지를 GPU 상주 → 매 iter CPU→GPU 전송 제거. 예상 -20~40% 시간.
- 제약: 2194장×1024²×3 ≈ 6.7GB → dense gaussian과 합쳐 OOM 위험. **keyframe subset(축 S4)과 결합 시 성립.**

### 축 S2 — carve 비용 절감 (무료 이득 근접)
- `refresh_interval` ↑(현 매회→10~20 iter마다), `cam_stride` ↑, carve를 densify 구간(≤7k)에만. _refresh_score의 전체 N KDTree가 12F 느림의 핵심 → 빈도만 낮춰도 큼.
- 품질 영향 최소 예상(score는 천천히 변함). 12F 66분의 상당분 회수 기대.

### 축 S3 — iterations sweep (품질-시간 Pareto)
- 30k → 15k → 10k → 7k. 어디서 품질 하한 깨지나. fast-track 15k가 유력 후보.

### 축 S4 — keyframe subset (incremental 최정렬, 최대 이득)
- 전체 2194장 → keyframe 500/300/150장 학습. 이미지 로드·iter 수 동시 감소 + **data_device cuda 성립**(메모리 여유).
- **incremental의 본질과 일치**: 실시간은 keyframe만 씀. 품질 하한 지키는 최소 keyframe 수 = incremental 청크 크기 힌트.

### 축 S5 — 중간 budget init (axis A 후속, 품질-무게 knee)
- init N ∈ {586k(full), 400k, 300k, 200k}. axis A(122k)에서 +3dB 소실 확인 → knee가 어디인지. 품질 지키는 최소 N = per-chunk 메모리 예산.

### 축 S6 (선택) — 해상도 축소
- 단일 저해상도(r=1.5~2) 전 구간 학습. 45c(2단계 재개)는 기각됐으나 단일 저해상은 별개 — 이미지 로드·rasterize 비용 감소. 품질 리스크 있어 후순위.

## 목표 레시피 (수렴점)
**중간 budget(~300k) + keyframe subset(~300장) + data_device cuda + carve refresh 저빈도 + 15k iter**
→ 목표: **5분 이내에 품질 하한 유지.** 이게 성립하면 incremental per-chunk 예산 = 이 설정.

## 평가 프로토콜
- 지표: **wall time(init 전처리 + 학습 분리 계측)** + PSNR + free-space 먼지(원거리 분할). train PSNR 금지, 기존 region GT 사용.
- 장면: 305(선명·(a)형 대표) + 12F(느림·최악). rot는 품질 확인용 참고.
- 위생: 각 축 단독 효과 격리, 먼지는 재현 런 병행(exp43 분산 교훈).

## 실행 순서 (제안)
1. **S1+S2 무료 이득 먼저** (품질 0 손실 예상) — 12F 66분이 얼마나 주는지 실측.
2. **S4 keyframe subset** — cuda 성립 + 최대 감속. 품질 하한 유지되는 최소 keyframe.
3. **S3·S5 Pareto sweep** — iter·N knee.
4. 목표 레시피 조합 실측 → incremental per-chunk 예산 확정 → exp48(incremental) 착수.

## 연결
- 다음 트랙 exp48(incremental): 여기서 확정한 per-chunk 레시피로 keyframe 청크 단위 depth-lift init + 로컬 갱신.
- 품질 방법론(carve·hybrid init)은 [exp46](exp46_basin_reframe_plan.md) 확정분 그대로 사용.

## 실행/결과 관리 관례 (2026-07-15 도입)

- 런 원본은 `results/experiments/`에 flat 유지(모든 glob 경로 보존).
- **폴더뷰(브라우징)**: `results/by_exp/<expNN>/` symlink 인덱스 — `python scripts/experiments/index_runs_by_exp.py`로 재생성(멱등, gitignored).
- **앞으로**: 새 실험 배치 끝에 인덱서 재실행 → 새 런이 자동으로 exp 번호별 폴더뷰에 반영. exp47 런 스크립트에 인덱서 호출 포함.

## 실행 결과 (12F, 07-15)

| 축 | 시간 | PSNR | 먼지(s>0.5/가시) | 판정 |
|---|---:|---:|---:|---|
| 기준 hybrid+carve (ctrl) | 66분 | 35.07 | 243 (free-space) | — |
| **S2 cheapcarve** | **26.8분** | **35.116** | 22,585 / 1,963 | ✅ **성공 (화질 무손실 + 시간 60% 단축)** |
| S3 15k iter | 39.9분 | 32.801 | 24,896 / 1,707 | ❌ PSNR 하한 미달 |
| S4 kf300 | 53.8분 | 34.397 | 20,369 / 2,438 | ⚠️ 화질OK·시간 단축 소폭 |
| S5 budget235k | 63.2분 | 34.400 | 7,354 / 640 | ⚠️ 화질OK·시간 이득 없음 |
| S6 r2 | 56.1분 | 35.553 | 19,347 / 1,870 | ⚠️ 화질OK·속도 개선 미비 |
| S1S4 (kf300 + cuda) | 53.8분 | 34.470 | 19,947 / 2,332 | ⚠️ 화질OK·시간 이득 없음 (CUDA 이득 소폭) |
| **TARGET** (budget+kf+cuda+cheap+15k) | **12.6분** | **32.943** | 9,691 / 818 | ❌ **기각** (화질 하한선 33.5dB 미달 및 먼지 초과) |

- **startup 고정비 ~13분**(carve 빌드+2194장 로드) — iter만 줄여선 분 단위 불가.
- **S2 cheapcarve의 초대형 성과**: `voxel: 0.20`, `cam_stride: 40`, `refresh_interval: 500` 조치만으로 화질 손실 없이 **40분가량 단축** (CPU EDT/KDTree 병목 제거).
- **GPU 상주화(CUDA) 속도 한계 규명**: S4(CPU 로딩)와 S1S4(GPU 상주)의 실행 속도가 53분대로 사실상 동일한 것으로 확인되었습니다. 즉, CPU-to-GPU 이미지 전송 오버헤드는 3DGS 전체 루프에서 미미하며, 병목의 핵심은 오로지 Carve Loss 연산에 집중되어 있습니다.
- **TARGET 기각 분석 및 최종 속도-품질 Pareto 최적 레시피 도출**:
  - `TARGET`은 15k iterations 감축(`S3`)과 keyframe 300장 제한(`S4`)이 병합되면서 복합 화질 하락이 일어나 최종 PSNR이 **32.943 dB**로 떨어져 하한선(33.5 dB)을 충족하지 못했습니다.
  - **대안 권장 레시피 (예상 21~23분, PSNR ~34.4 dB)**: 
    - `S2_cheapcarve` (속도 60% 단축) + `S4_kf300` (Keyframe 300) + `S5_budget235k` (먼지 청소)를 적용하되, **Iterations는 30k를 유지**합니다.
    - cheapcarve가 CPU 병목을 거의 없애주기 때문에, 30k iterations 전체를 돌아도 **21~23분대**에 도달하면서 화질 하한선을 아늑하게 지킬 수 있습니다.
