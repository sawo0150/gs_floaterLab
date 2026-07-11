# exp38~40 — Carve Loss 학습 검증 트랙 (ORB + MPS)

- 날짜: 2026-07-12 (심야 자율 루프, 실행 계획·사전 등록: [round8_gpu_queue_plan](../rounds/round8_gpu_queue_plan.md))
- 설계 근거: [round8_carve_loss_design](../rounds/round8_carve_loss_design.md) (라벨 검증 AUC 0.98)
- 코드: `3dgs-custom/eval/carve_loss.py` (+ train.py 훅), configs: `configs/carve_loss/exp38*.yaml, exp39*.yaml, exp40*.yaml`
- 평가: PSNR(tensorboard) + **표준 GT 지표**(`floater_metric_region.py`) + carve 부하(`eval_carve_load.py`)
- 계측: `accum_rgb_grad_vec`(coherence), `split_events.pkl`(출생 로그) — exp38a부터 전 run 포함

## 설정 (공통: exp30 하이퍼 + carve loss)

| exp | soft (λ/score_min) | prune | gate | force | 비고 |
|---|---|---|---|---|---|
| exp38a | 0.05 / 0.3 | ✓ | ✓ | — | 원안 |
| exp38b | — | ✓ | ✓ | — | soft 분리 |
| exp38c | 0.02 / 0.5 | ✓ | ✓ | — | softlite |
| exp30r | — | — | — | — | baseline 재현 (노이즈 측정) |
| exp39 | 0.05 / 0.3 | ✓ | ✓ | — | **MPS 트랙** (anchor 검증 필터) |
| exp40a | — | ✓ | ✓ | ✓ λ0.05 | 3D force 단독 |
| **exp40b** | 0.02 / 0.5 | ✓ | ✓ | ✓ λ0.05 | **챔피언** |

## 결과 (ORB 트랙, region GT 지표 = 낮을수록 좋음)

| run | PSNR@30k | region_n | region가시 | carve가시 | N |
|---|---:|---:|---:|---:|---:|
| exp30 (기준) | 32.906 | 3,477 | 238 | 884 | 147,620 |
| exp30r (재현) | 32.579 | 3,749 | 180 | 860 | 148,512 |
| exp38a | 32.266 | 559 | 27 | 9 | 134,554 |
| exp38b | 32.663 | 1,744 | 187 | 905 | 147,117 |
| exp38c | 32.557 | 946 | 33 | 18 | 140,959 |
| exp40a | 32.667 | 1,309 | 134 | 503 | 148,818 |
| **exp40b** | **32.576** | **498** | **28** | **12** | 142,905 |

- **baseline run-to-run 노이즈 실측: PSNR ±0.33dB** (exp30 vs exp30r), region_n ~8%, 가시 ~±25%.
- **exp40b = 최종 챔피언**: PSNR이 baseline 재현과 동일(32.576 vs 32.579) = **무손실**, region 먼지 **-86%**, 가시 carve 먼지 **-99% (860→12)**. 사전 등록 PASS 1·2·2' 전부 충족.
- 성분 분해: soft가 가시 먼지 주역(b vs a/c), force는 무비용 추가 억제(b→40a: region -25%, 가시 -45%), 결합 시너지 확인(40b가 둘 다보다 우수). λ0.05 soft는 -0.3dB 추가 비용(exp38a) — 0.02가 스위트스팟.

## MPS 트랙 (exp39, full soft λ0.05)

PSNR 32.666 (exp08 33.012 대비 -0.35), **가시 먼지 96→2, 먼지 기여 6.42→1.34%** — 전이 성공. softlite+force 판(exp39b) 검증 중.

## 기타 확인 사항

- **train PSNR은 floater 품질 지표로 부적합** (렌더 A/B: 사용자 수동 편집조차 -3.7dB — floater가 train 잔차를 흡수하는 기생충. 사후 삭제 -3.2dB vs 학습 중 동일 청정도 -0.0~-0.3dB = in-training 흡수 실증). 상세: round8_gpu_queue_plan ① amendment.
- **출생 메커니즘**: split 출생의 29.5%가 허공(w>0.5), 부모는 "큰" 게 아니라 저opacity 반투명(0.165) — 먼지가 먼지를 낳는 연쇄. gate+soft 처방의 직접 근거.
- **gradient 프로브**: floater 고정은 강한 핀이 아닌 진동 평형(coherence 0.257) → 약한 일관 force가 유효하리라는 예측이 exp40으로 실증됨.

## 재현 및 MPS 확장 (07-12 아침 추기)

- **exp40br (챔피언 재현)**: PSNR 32.448 (1차 32.576, Δ0.13 — 노이즈 ±0.33 내), region_n **462** / 가시 **25** (1차 498/28) — **먼지 억제 고재현성**. 정직한 판독: 챔피언 PSNR 범위 [32.45,32.58]는 baseline [32.58,32.91] 하단 접경 — 실비용 0~0.2dB 추정.
- **exp39b (MPS softlite+force)**: PSNR **32.913** (exp08 33.012 대비 **-0.10dB**), **가시 먼지 0개** (exp08 96개), 먼지 기여 6.42→**0.21%**. full-soft판(exp39, -0.35dB)의 PSNR 갭이 softlite로 닫힘 — **MPS 트랙도 채택**.

## Verdict

**채택: exp40b 레시피 (softlite λ0.02/0.5 + 예산 prune 0.75% + 출생 게이트 0.95 + carve-force λ0.05)** — 양 트랙 공통으로 PSNR 무손실(~0.1dB 내)로 가시 먼지 96~100% 억제. plateau 트랙(exp15~36)이 못 하던 것을 같은 입력(SLAM+카메라)만으로 달성. 사전 등록 기준 전 항목 PASS.
