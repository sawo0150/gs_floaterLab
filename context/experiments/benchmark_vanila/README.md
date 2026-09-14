# benchmark_vanila

원본 VIGS-SLAM `origin/main@22ffe24c` 기준선을 실행 조건별로 분리한다.
tracking/frontend/PGBA/GS loss와 dataset 파라미터는 동일하게 유지하고, GPU와
입력/budget 계약이 다른 결과를 같은 표로 덮어쓰지 않는다.

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
  각각 audit한다. 새 custom 비교의 vanilla 기준은 이 폴더다.
- [`paper_reference/`](paper_reference/README.md): VIGS-SLAM 논문 Table 18/19의
  장면별 PSNR/SSIM/LPIPS 원문 전사와 protocol 주의.

폴더 이름의 `1.5x`는 source timestamp 간격을 1.5배로 재생한다는 뜻이다.
`pure_online`은 offline BA/color refinement 제거 여부이고, streaming budget과는
별개의 축이다.

완료된 조건의 장면별 PSNR은 [`summary.md`](summary.md)에 한 표로 모은다.
strict 실행 중간 결과는 strict 폴더의 `evidence/summary.{json,csv}`와
`summary.md`에만 갱신하며, 20-scene queue가 끝난 뒤 상위 표에 합친다.
