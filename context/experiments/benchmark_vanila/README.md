# benchmark_vanila

원본 VIGS-SLAM `origin/main@22ffe24c` 기준선을 실행 조건별로 분리한다.
tracking/frontend/PGBA/GS loss와 dataset 파라미터는 동일하게 유지하고, GPU와
입력/budget 계약이 다른 결과를 같은 표로 덮어쓰지 않는다.

논문의 `online` 정의, Table 18/19 metric split, baseline별 저자 수정, 공개 코드와
paper protocol의 차이, 우리 1.0×/1.5× 계약 선택지는
[`paper_online_metric_protocol_and_baseline_modifications.md`](paper_online_metric_protocol_and_baseline_modifications.md)에
정리한다.

실제 논문에서 실행할 B(mapping-only isolation)와 C(strict streaming system)의 세부 제약,
KF 처리, work ledger, metric 표와 실행 순서는
[`bc_metric_comparison_plan.md`](bc_metric_comparison_plan.md)에 고정한다.

## 디렉터리

- [`synchronous_unbounded/`](synchronous_unbounded/README.md): RTX 5070 Ti,
  `--pure_online`, keyframe별 map 호출을 기다리는 기존 18-scene 품질 reference.
- [`5070ti_1.5x_streaming/`](5070ti_1.5x_streaming/README.md): RTX 5070 Ti,
  timestamp 1.5x pacing target + 원본 async GS worker로 완료한 UTMM/RPNG 16-scene
  streaming 품질 baseline. ingress backpressure로 16/16 tracking deadline은 늦었으므로
  literal 1.5x throughput 성공과는 구분한다.
- [`5070ti_1.5x_strict/`](5070ti_1.5x_strict/README.md): RTX 5070 Ti,
  Aria/UTMM/RPNG 20-scene hard-deadline 재측정. final capture deadline 뒤 Gaussian
  optimizer와 topology update를 0회로 강제하고, map strict와 tracking deadline을
  각각 audit한다. 다만 harness의 drop-oldest ingress로 완료 16개 기준 RGB의 69.74%가
  버려졌고 end-to-end strict pass는 0/20이므로, live-drop stress 진단으로 사용하되
  동일-input gsSLAM 품질 비교의 유일한 vanilla 기준으로 사용하지 않는다.
- [`paper_reference/`](paper_reference/README.md): VIGS-SLAM 논문 Table 18/19의
  장면별 PSNR/SSIM/LPIPS 원문 전사와 protocol 주의.

폴더 이름의 `1.5x`는 source timestamp 간격을 1.5배로 재생한다는 뜻이다.
`pure_online`은 offline BA/color refinement 제거 여부이고, streaming budget과는
별개의 축이다.

완료된 조건의 장면별 PSNR은 [`summary.md`](summary.md)에 한 표로 모은다.
strict 실행 중간 결과는 strict 폴더의 `evidence/summary.{json,csv}`와
`summary.md`에만 갱신하며, 20-scene queue가 끝난 뒤 상위 표에 합친다.
