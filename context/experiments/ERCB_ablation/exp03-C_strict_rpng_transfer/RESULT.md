# exp03-C — strict VIGS ERCB RPNG transfer

날짜: 2026-09-15
상태: **중단 — RR tracking 붕괴로 selector pair 성립 전 실패**

## 질문

`exp03-B`의 causal fixed-arrival strict 1.5x 계약을 숫자 변경 없이 RPNG `table_01`에
전이했을 때 ERCB의 저예산 이득이 관측되는가?

## 고정 계약

- `exp03-B`와 같은 unified B1, fixed-arrival stride5/offset2/max1
- RR vs relative-floor ERCB K8/rho.5/gamma=log3
- online tracking/native topology, KF RGBD+normal, dense appearance+opacity
- fixed 1.5x sensor budget, fixed held-out mapping 제외, zero-tail
- 장면별 phase/topology cutoff와 background polish 없음

첫 gate는 table_01 seed 0 pair다.

## 결과

RR은 2,506장 중 약 60%를 처리한 뒤 online pose의 회전행렬이 비정상화됐다.
`submit_depth_anchors -> _export_depth_anchors -> Rotation.from_matrix`에서
`numpy.linalg.LinAlgError: SVD did not converge`가 발생했고, 예외 뒤 남은 process는
해당 실행 세션에 Ctrl-C를 보내 정리했다. 사용자나 다른 GPU process는 건드리지 않았다.

그 전부터 replay 1.5x의 sensor mapping deadline 약 83초를 tracking wall time이 크게
넘겼고, Gaussian 수는 6,622에서 멈췄다. 즉 후반 stream은 mapping service를 받지 못한
상태였다. 완성된 held-out 결과와 zero-tail audit가 없으므로 이 run은 품질 표에 넣지
않고, ERCB arm과 seed 확장도 실행하지 않는다.

## 판정

**RPNG table_01 strict 1.5x에서는 scheduler보다 frontend/pose 안정성과 처리량이 선결
병목이다.** 실패를 숨기기 위해 matched-time이나 scene-specific cutoff로 바꾸지 않는다.
원본 실패 log는
`results/ERCB_ablation/exp03-C_strict_rpng_transfer/rpng/table_01/1p5x/rr_arrival_s0/`
에 보존한다.
