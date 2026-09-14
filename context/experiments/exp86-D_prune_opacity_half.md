# exp86-D — native opacity pruning 0.5× control

날짜: 2026-09-15
상태: **2-scene × 2-selector 완료; fixed held-out PSNR이 장면에 따라 갈려 미채택**

## 질문

exp86-C처럼 birth를 2배로 만들지 않고, 같은 1× birth에서 기존 Gaussian을 덜
지우면 fixed-time 수렴이 좋아지는가? Online native topology의 opacity prune
threshold만 `0.7 -> 0.35`로 낮췄다.

## 단일 변인 계약

- UTMM `fast-straight`: vanilla map-done matched budget 30.905821초
- UTMM `ego-centric-1`: vanilla map-done matched budget 91.405114초
- selector: RR와 original view-count ERCB(`beta=.02`, `K=128`)
- single unified KF+dense loop, cycle work-credit `r=4`, physical batch 1, seed 0
- birth downsample multiplier는 `1.0`으로 유지
- **online native opacity prune threshold만** `gaussian_th * 0.5 = 0.35`
- initialization prune(`0.005`), size prune, densify, loss, scheduling은 그대로
- background polish 및 frame/iteration/fraction/topology cutoff 없음
- 4개 run 모두 matched budget 및 zero-tail 통과

## 결과

판정 지표는 `fixed_eval_mean_*`이다. 괄호 안 PSNR은 같은 장면·selector의 기본
prune threshold `0.7` 대비 변화량이다. `raw capacity`는 최초 Gaussian과 모든
causal keyframe birth를 합한 수이며 densify 이전 기준이다.

| scene | selector | opacity threshold | raw capacity | final GS | Adam | KF/dense | held-out PSNR | SSIM | LPIPS |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| fast-straight | RR | 0.70 | 35,912 | 30,112 | 612 | 426/186 | 17.6622 | 0.66934 | 0.47401 |
| fast-straight | RR | 0.35 | 35,915 | 44,579 | 375 | 287/88 | 17.8869 (**+0.2247**) | 0.67995 | 0.44723 |
| fast-straight | ERCB K128 | 0.70 | 35,910 | 29,671 | 621 | 450/171 | 17.8764 | 0.67420 | 0.46488 |
| fast-straight | ERCB K128 | 0.35 | 35,913 | 44,945 | 371 | 296/75 | 17.8920 (**+0.0156**) | 0.67805 | 0.44988 |
| ego-centric-1 | RR | 0.70 | 142,180 | 114,923 | 4,058 | 2,849/1,209 | 19.7069 | 0.68104 | 0.37961 |
| ego-centric-1 | RR | 0.35 | 142,181 | 142,548 | 2,444 | 2,002/442 | 19.2341 (**-0.4728**) | 0.66617 | 0.38839 |
| ego-centric-1 | ERCB K128 | 0.70 | 142,199 | 117,377 | 3,894 | 2,890/1,004 | 19.4853 | 0.67348 | 0.38605 |
| ego-centric-1 | ERCB K128 | 0.35 | 142,196 | 143,934 | 2,393 | 2,019/374 | 19.3485 (**-0.1368**) | 0.66372 | 0.39070 |

## 판정

- pruning 완화 자체는 확실히 작동했다. Final GS는 기본값 대비
  `1.23--1.51×`가 됐고, fast의 첫 topology action은 약 35.9k에서 25k로
  감소하던 기본값과 달리 약 42.2k로 증가했다.
- 그러나 커진 map의 step 비용 때문에 같은 wall-time의 Adam service가
  `38.5--40.3%` 감소했다. Dense update도 fast `171--186 -> 75--88`,
  ego-centric `1004--1209 -> 374--442`로 줄었다.
- held-out PSNR은 2승 2패이고 평균 변화는 **-0.0923dB**이다. Fast에서는
  LPIPS도 개선됐지만 ego-centric에서는 PSNR/SSIM/LPIPS가 모두 악화했다.
- 따라서 **고정 prune multiplier 0.5는 production 기본값으로 채택하지 않는다.**
  “Gaussian을 더 남기면 항상 더 빨리 수렴한다”는 가설도 성립하지 않는다.
  짧은 장면에는 여유 capacity가 도움이 될 수 있지만, 긴 장면에서는 per-step
  비용과 supervision service 손실이 더 크다.
- 다음 capacity 실험을 한다면 장면별 시점/개수 cutoff가 아니라 관측 기반
  service debt와 실제 measured step cost로 opacity threshold 또는 birth를
  적응시키는 단일축이어야 한다.

## 구현 및 증거

- VIGS commit: `424ecd87` (`--mapping_prune_opacity_multiplier`, 기본값 `1.0`)
- 실험값: `--mapping_prune_opacity_multiplier 0.5`
- panel: `benchmark_custom/5070ti_vanilla_matched_time/run_prunehalf_panel.sh`
- summary: `benchmark_custom/5070ti_vanilla_matched_time/evidence/exp86d_prunehalf_summary.json`
- raw: `results/benchmarks/benchmark_custom/5070ti_vanilla_matched_time/utmm/{fast-straight,ego-centric-1}/`
