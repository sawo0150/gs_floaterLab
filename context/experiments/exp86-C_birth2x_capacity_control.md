# exp86-C — causal Gaussian birth 2× capacity control

날짜: 2026-09-15
상태: **2-scene × 2-selector pilot 완료; raw birth는 정확히 2×였으나 held-out PSNR 이득은 일관되지 않아 미채택**

## 질문

ERCB ablation에서 Gaussian 수가 많을수록 더 빨리 수렴하는 것처럼 보인 현상이
실제 birth density의 인과 효과인가? Scheduler, loss, matched wall-time budget을 고정하고
모든 causal keyframe birth의 PPM/uniform downsample 간격만 `1.0 -> 0.5`로 바꿔
raw birth point를 약 2배로 만들었다.

## 계약

- UTMM `fast-straight`: vanilla map-done matched budget 30.905821초
- UTMM `ego-centric-1`: vanilla map-done matched budget 91.405114초
- selector: RR와 original view-count ERCB(`beta=.02`, `K=128`)
- single unified KF+dense loop, cycle work-credit `r=4`, physical batch 1, seed 0
- KF RGBD+normal+native topology, dense RGB appearance+opacity
- background polish 0, phase/frame/fraction/topology cutoff 0
- birth 1×와 2× 모두 동일한 fixed held-out evaluator를 사용
- 2× 4개 run 모두 matched budget/counter/zero-tail 통과

## 결과

판정 지표는 `fixed_eval_mean_*`이다. 괄호 안 PSNR은 같은 selector의 birth 1× 대비
변화량이다.

| scene | selector | birth | raw born | final GS | Adam | KF/dense | held-out PSNR | SSIM | LPIPS |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| fast-straight | RR | 1× | 35,912 | 30,112 | 612 | 426/186 | 17.6622 | 0.66934 | 0.47401 |
| fast-straight | RR | 2× | 71,826 | 49,306 | 394 | 305/89 | 17.6436 (**-0.0186**) | 0.68072 | 0.43433 |
| fast-straight | ERCB K128 | 1× | 35,910 | 29,671 | 621 | 450/171 | 17.8764 | 0.67420 | 0.46488 |
| fast-straight | ERCB K128 | 2× | 71,837 | 49,103 | 398 | 318/80 | 17.7519 (**-0.1245**) | 0.68307 | 0.42463 |
| ego-centric-1 | RR | 1× | 142,180 | 114,923 | 4,058 | 2,849/1,209 | 19.7069 | 0.68104 | 0.37961 |
| ego-centric-1 | RR | 2× | 284,351 | 136,234 | 2,572 | 2,117/455 | 19.7793 (**+0.0724**) | 0.67841 | 0.36885 |
| ego-centric-1 | ERCB K128 | 1× | 142,199 | 117,377 | 3,894 | 2,890/1,004 | 19.4853 | 0.67348 | 0.38605 |
| ego-centric-1 | ERCB K128 | 2× | 284,412 | 138,621 | 2,503 | 2,122/381 | 19.8264 (**+0.3411**) | 0.68306 | 0.36538 |

2× arm은 raw birth가 4/4에서 1×의 `1.9999--2.0005×`로 의도대로 바뀌었다.
그러나 prune/densify 뒤 final GS는 fast에서 `1.64--1.65×`, ego-centric에서
`1.18×`만 남았다. Gaussian이 많아져 각 step이 비싸졌기 때문에 동일 wall-time에서
Adam service는 `35.6--36.6%` 감소했고, topology event도 fast `3->2`, ego-centric
`19->14`로 줄었다.

## 판정

- **“Gaussian을 2배 birth하면 PSNR 수렴이 빨라진다”는 가설은 현재 결과로 확인되지
  않았다.** Held-out PSNR 변화는 2승 2패, 평균 `+0.0676dB`이며 장면·selector에
  따라 부호가 갈렸다.
- perceptual 품질 신호는 있다. LPIPS는 4/4 개선했고 SSIM은 3/4 개선했다. 특히 긴
  ego-centric ERCB는 PSNR도 `+0.3411dB`였다.
- 동시에 optimizer service가 약 36% 줄었으므로 이 실험은 **같은 시간에서 capacity와
  update 수가 자연스럽게 경쟁하는 실제 시스템 효과**를 측정한 것이다. Birth만 늘린
  것이 최종 Gaussian 수만 독립적으로 바꾼 실험은 아니다.
- 따라서 2×를 production 기본값으로 채택하지 않는다. 다음에 이 축을 계속 본다면
  장면별 iteration cutoff가 아니라 관측당 service debt 또는 measured step cost로
  birth를 제한하는 적응형 capacity control 한 축만 검증한다.

## 구현 및 증거

- VIGS commit: `c5269eac` (`--mapping_birth_downsample_multiplier`, 기본값 `1.0`)
- 2× 값: `--mapping_birth_downsample_multiplier 0.5`
- panel: `benchmark_custom/5070ti_vanilla_matched_time/run_birth2x_panel.sh`
- summary: `benchmark_custom/5070ti_vanilla_matched_time/evidence/exp86c_birth2x_summary.json`
- raw: `results/benchmarks/benchmark_custom/5070ti_vanilla_matched_time/utmm/{fast-straight,ego-centric-1}/`
- 첫 실행은 새 worktree에 Omnidata asset이 없어 학습 전에 실패했다. 실패 output은
  `.failed_asset_path_20260914`로 보존했고, runner가 검증된 main-integration asset을
  read-only로 참조하도록 수정한 뒤 동일 panel을 재실행했다.
