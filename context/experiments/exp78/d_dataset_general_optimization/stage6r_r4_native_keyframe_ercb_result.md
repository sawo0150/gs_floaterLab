# exp78-D Stage 6R R4 — native historical-keyframe ERCB

- 날짜: 2026-09-15
- 판정: **개발 gate PASS, R4를 paper Full candidate로 승격**
- paper 실행 source: `eb5fa99fecab4a85408bfb1baa8db197857ea231`
- paper result commit: `e62cd6b18d42207c21f89d8af6b1b8cd37ff1d4d`
- official vanilla source: `22ffe24`
- 장면/seed: RPNG `table_01`, mapper seed 0
- 평가: fixed held-out 502 views, causal mapping-disjoint, zero-tail

## 문제와 변경 범위

R3에서는 ERCB(C2)가 dense view 269회와 별도 keyframe appearance 269회에
들어갔지만, 더 큰 native historical-keyframe 학습은 계속 outside-window
pool에서 최대 6장을 `torch.randperm`으로 골랐다. 따라서 ERCB가 실제
mapper의 주 keyframe 학습을 통제하지 않는다는 contribution-scope 문제가
남았다.

R4는 다음 한 축만 바꾼다.

- FRONTIER와 local window는 원형 그대로 둔다.
- BALANCED/REPLAY의 native outside-window historical slot에만 causal full
  pool global-residue ERCB를 적용한다.
- 파라미터는 기존 C2와 같은 `K=8`, `rho=0.75`, `gamma=log(1.5)`다.
- control은 기존 `torch.randperm`을 그대로 쓴다. Candidate도 동일 uniform
  shadow draw를 소비해 Torch RNG state를 맞추고 ERCB는 독립 CPU RNG를 쓴다.
- ERCB proposal은 native Adam 성공 뒤에만 commit한다.
- Adam, 물리 render, local/frontier, dense C1+C2, auxiliary-KF C1+C2, birth,
  topology, loss는 바꾸지 않는다.

## 결과

| Arm | PSNR | SSIM | LPIPS | Adam | Physical render | GS |
|---|---:|---:|---:|---:|---:|---:|
| R3 uniform native-history control | 25.580154 | .848709 | .153402 | 3,030 | 38,302 | 417,658 |
| **R4 native-history ERCB** | **25.624315** | .848183 | .153554 | 3,030 | 38,302 | 417,618 |
| fresh native vanilla render-match | 23.929422 | .793429 | .199396 | 3,027 | 38,302 | 182,825 |

- R4 - control: **+0.044161 dB**, SSIM `-0.000526`, LPIPS `+0.000152`.
- R4 - vanilla: **+1.694893 dB**, SSIM `+0.054754`, LPIPS `-0.045842`.
- control-hard Q1: `+0.025094 dB`.
- temporal thirds: `+0.052928 / +0.025779 / +0.053724 dB`.

따라서 selector-only PSNR gate는 양수이고 기존 Full의 vanilla 대비 큰
이득도 유지된다. 다만 control 대비 SSIM/LPIPS는 극미세하게 나빠졌으므로
ERCB 단독으로 모든 perceptual metric을 개선한다고 주장하지 않는다.

## 구조·공정성 검증

- 동일 commit/archive/config, event signature 283, tracking KF 210.
- native selection ledger 1,610행 정렬 exact.
- FRONTIER 210행은 변경 없음. BALANCED/REPLAY 1,400행 모두 ERCB active.
- BALANCED/REPLAY의 historical keyframe service는 **8,400회**다. ERCB가 이제
  538회의 dense+auxiliary 고정 기회뿐 아니라 많은 native KF 학습을 직접
  통제하므로 auxiliary-only contribution 문제를 해소한다.
- dense 269회와 auxiliary-KF 269회의 selected UID trace는 exact 동일.
- control/candidate 모두 Adam 3,030, physical render 38,302, post-EOS update 0.
- historical unique는 uniform 197장, R4 199장(정렬된 eligible union 199장).
- stable anchor 33장의 service min/max가 `75/109 -> 90/91`, spread가
  `34 -> 1`, CV가 `0.09694 -> 0.00493`으로 감소했다.
- global-residue epoch 90회 완료, terminal residue 133. residue 소진 전 반복,
  batch 내 duplicate, pending proposal, future/dataset/horizon 의존은 모두 0.
- R4 final gate 10/10, fresh native render-match 10/10 PASS.

## 사전 검증 정정 이력

첫 structural-only verifier는 wall EMA와 미세 float recovery telemetry까지
fixed-work invariant로 잘못 비교해 invalid였다. 품질 열람 전이었으며, 고정
dense/aux trace와 exact work만 비교한 `v2`는 PASS했다. 또 control unique
197장을 전체 pool로 오독해 gate를 잠시 fairness-only로 바꾼 amendment가
있었으나, 정렬 ledger의 pool union이 199장임을 확인해 품질 열람 전에 원래
`R4 unique > control unique` gate로 복구했다. 최초 report와 정정 문서는
provenance로 보존한다.

## 해석과 다음 gate

R4는 ERCB의 적용 범위를 논문 contribution에 맞게 보강했고, native 주 학습
경로에서 service 균형과 작은 양의 PSNR 효과를 동시에 확인했다. 따라서 R4를
Full candidate로 사용한다.

아직 `table_01` 단일 개발 장면/seed 결과이므로 dataset-general claim은 하지
않는다. 다음은 이미 본 `table_01/table_02`를 제외한 untouched cohort에 대해
R4 파라미터를 전혀 바꾸지 않는 새 cross-sequence 계약을 먼저 고정하고
실행한다. End-to-end strict live Track C는 mapping-isolation B와 별도로 둔다.

## Evidence

- control:
  `results/experiments/exp78/paper_full_staged_v1/stage6r_r4_native_global_keyframe/rpng/table_01/r3_uniform_audited_s0/`
- candidate:
  `results/experiments/exp78/paper_full_staged_v1/stage6r_r4_native_global_keyframe/rpng/table_01/r4_native_global_keyframe_ercb_s0/`
- vanilla:
  `results/experiments/exp78/paper_full_staged_v1/stage6r_r4_native_global_keyframe/rpng/table_01/native_vanilla_render_matched_r4_s0/`
- corrected structural report:
  `results/experiments/exp78/paper_full_staged_v1/stage6r_r4_native_global_keyframe/rpng/table_01/verification/r4_structural_prequality_v2.json`
- final gate:
  `results/experiments/exp78/paper_full_staged_v1/stage6r_r4_native_global_keyframe/rpng/table_01/verification/r4_final_gate.json`
- render match:
  `results/experiments/exp78/paper_full_staged_v1/stage6r_r4_native_global_keyframe/rpng/table_01/verification/r4_render_match.json`
- 사전 정정 기록:
  `context/experiments/exp78/d_dataset_general_optimization/stage6r_r4_prequality_amendment.md`
