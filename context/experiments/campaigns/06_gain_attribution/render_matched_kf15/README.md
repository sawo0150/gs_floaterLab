# KF당 총 15회 렌더링 비교

2026-09-25 사용자 지시로 30k 렌더링 실험을 중단하고 저예산으로 변경.

## 사전 프로토콜

- Aria1253, RPNG table_06, UTMM square-1, seed0. 기존 구조/mixed+Growth와 새 paired 구조/immediate를 비교.
- map generation에서 새 training KF가 등록될 때마다 **총 15 camera render**를 부여한다. reset 이후 재등록은 새 KF 학습으로 계산하며 총 admissions와 고유 uid 수를 따로 보고한다. Held-out은 제외.
- 초기화·native mapping·추가 KF·dense 모두 위 예산을 공유. 기본 mapper는 입력당 최대 1 multi-view step, 기존 max_viewpoints 제한을 잔여 budget으로 낮춘다. 기존 구조의 window+과거6 후보가 15장을 넘으면 기존 mapper의 무작위 batch 축소가 적용된다. 새 구조는 window만 대상으로 동일 제한 적용.
- native 실행 후 남은 credit을 각 구조의 추가 trainer로 모두 소비. 예: native local window11장이면 나머지4회는 추가 KF/dense 학습이다. 초기화의 대량 반복도 예외 없음.
- pose/depth 보정은 계속 적용하지만 새로운 KF가 없으면 추가 credit은 없다. 새 topology freeze/cutoff는 도입하지 않는다. 낮아진 native iteration에 따라 topology event 빈도도 달라질 수 있음.
- 동일 causal tracker packet과 RGB/IMU prefix 사용. 각 입력 시점마다 양쪽 누적 render=15×그때까지 KF admissions 확인. terminal frame 이후 update0.
- 실제 worker를 사용하되 fixed-work 진단이므로 1.5× wall-clock 제한은 적용하지 않는다. 실제 시간이 실시간 예산 내인지 별도 보고.
- renderer forward/backward/service 세 계측 대조. 배치 호출도 카메라별로 계산. no-grad 보조 렌더와 평가 렌더는 학습 budget과 별도 집계.
- 각 구조 loss/ERVS/Growth는 그대로. 한 step당 영상 수와 optimizer 횟수도 여전히 다르므로 sampler 단독 ablation 아님.
- 실행 후 held-out 평가 2회. source snapshots 보존. 실제 production/runtime 파일은 수정하지 않음.

## 결과

6run 완료. 독립 source/cohort/trajectory/render-prefix 검증 PASS. 각 run 평가2회 일치, seed0 탐색 결과.

**2026-09-25 (15-render-per-KF / aria / legacy_growth / seed0):** 20.465558dB, mapping 12.870s.

```json
{
  "dataset": "aria",
  "scene": "aria1253",
  "arm": "legacy_growth",
  "seed": 0,
  "output": "/home/intern/gs_floaterLab/results/campaigns/gain_attribution/render_matched_kf15/v1/aria/legacy_growth/seed0",
  "returncode": 0,
  "valid": true,
  "psnr": 20.46555753518607,
  "mapping_seconds": 12.870090618962422,
  "final_map": {
    "keyframes": 91,
    "dense_admitted": 0,
    "role_commits": null,
    "native_steps": 78
  },
  "checks": {
    "common_commits_match_adam": true,
    "photometric_counts_match_adam": true,
    "recent_counts_match_committed_history": true,
    "whole_pool_growth_capacity": true,
    "render_backward_matches": true,
    "render_service_matches": true,
    "no_render_errors": true,
    "exact_kf_credit": true,
    "prefix_budget_matches": true,
    "per_kf_budget": true
  },
  "renders": {
    "all": 1901,
    "no_grad": 116,
    "training": 1785,
    "backward": 1785
  },
  "native_steps": 87,
  "additional_steps": 534,
  "clock_budget": 97.64999836950005
}
```

**2026-09-25 (15-render-per-KF / aria / paired / seed0):** 20.725142dB, mapping 22.322s.

```json
{
  "dataset": "aria",
  "scene": "aria1253",
  "arm": "paired",
  "seed": 0,
  "output": "/home/intern/gs_floaterLab/results/campaigns/gain_attribution/render_matched_kf15/v1/aria/paired/seed0",
  "returncode": 0,
  "valid": true,
  "psnr": 20.725141954785993,
  "mapping_seconds": 22.322169485036284,
  "final_map": {
    "keyframes": 91,
    "dense_admitted": 924,
    "role_commits": {
      "keyframe": 254,
      "dense": 253
    },
    "native_steps": 78
  },
  "checks": {
    "common_commits_match_adam": true,
    "photometric_counts_match_adam": true,
    "recent_counts_match_committed_history": true,
    "whole_pool_growth_capacity": true,
    "full_available_pools": true,
    "paired_turns": true,
    "role_recent_counts": true,
    "native_window_only": true,
    "final_map_dense_used": true,
    "render_backward_matches": true,
    "render_service_matches": true,
    "no_render_errors": true,
    "exact_kf_credit": true,
    "prefix_budget_matches": true,
    "per_kf_budget": true
  },
  "renders": {
    "all": 1901,
    "no_grad": 116,
    "training": 1785,
    "backward": 1785
  },
  "native_steps": 87,
  "additional_steps": 839,
  "clock_budget": 97.64999836950005,
  "delta_psnr": 0.25958441959992484
}
```

**2026-09-25 (15-render-per-KF / rpng / legacy_growth / seed0):** 20.499256dB, mapping 49.875s.

```json
{
  "dataset": "rpng",
  "scene": "table_06",
  "arm": "legacy_growth",
  "seed": 0,
  "output": "/home/intern/gs_floaterLab/results/campaigns/gain_attribution/render_matched_kf15/v1/rpng/legacy_growth/seed0",
  "returncode": 0,
  "valid": true,
  "psnr": 20.49925581442343,
  "mapping_seconds": 49.87507279403508,
  "final_map": {
    "keyframes": 186,
    "dense_admitted": 0,
    "role_commits": null,
    "native_steps": 173
  },
  "checks": {
    "common_commits_match_adam": true,
    "photometric_counts_match_adam": true,
    "recent_counts_match_committed_history": true,
    "whole_pool_growth_capacity": true,
    "render_backward_matches": true,
    "render_service_matches": true,
    "no_render_errors": true,
    "exact_kf_credit": true,
    "prefix_budget_matches": true,
    "per_kf_budget": true
  },
  "renders": {
    "all": 3628,
    "no_grad": 223,
    "training": 3405,
    "backward": 3405
  },
  "native_steps": 185,
  "additional_steps": 783,
  "clock_budget": 138.367005944252
}
```

**2026-09-25 (15-render-per-KF / rpng / paired / seed0):** 22.278183dB, mapping 66.374s.

```json
{
  "dataset": "rpng",
  "scene": "table_06",
  "arm": "paired",
  "seed": 0,
  "output": "/home/intern/gs_floaterLab/results/campaigns/gain_attribution/render_matched_kf15/v1/rpng/paired/seed0",
  "returncode": 0,
  "valid": true,
  "psnr": 22.27818327895156,
  "mapping_seconds": 66.37421674001962,
  "final_map": {
    "keyframes": 186,
    "dense_admitted": 1810,
    "role_commits": {
      "keyframe": 444,
      "dense": 443
    },
    "native_steps": 173
  },
  "checks": {
    "common_commits_match_adam": true,
    "photometric_counts_match_adam": true,
    "recent_counts_match_committed_history": true,
    "whole_pool_growth_capacity": true,
    "full_available_pools": true,
    "paired_turns": true,
    "role_recent_counts": true,
    "native_window_only": true,
    "final_map_dense_used": true,
    "render_backward_matches": true,
    "render_service_matches": true,
    "no_render_errors": true,
    "exact_kf_credit": true,
    "prefix_budget_matches": true,
    "per_kf_budget": true
  },
  "renders": {
    "all": 3628,
    "no_grad": 223,
    "training": 3405,
    "backward": 3405
  },
  "native_steps": 185,
  "additional_steps": 1399,
  "clock_budget": 138.367005944252,
  "delta_psnr": 1.7789274645281274
}
```

**2026-09-25 (15-render-per-KF / utmm / legacy_growth / seed0):** 16.828925dB, mapping 24.509s.

```json
{
  "dataset": "utmm",
  "scene": "square-1",
  "arm": "legacy_growth",
  "seed": 0,
  "output": "/home/intern/gs_floaterLab/results/campaigns/gain_attribution/render_matched_kf15/v1/utmm/legacy_growth/seed0",
  "returncode": 0,
  "valid": true,
  "psnr": 16.828924755991242,
  "mapping_seconds": 24.50879096100107,
  "final_map": {
    "keyframes": 71,
    "dense_admitted": 0,
    "role_commits": null,
    "native_steps": 62
  },
  "checks": {
    "common_commits_match_adam": true,
    "photometric_counts_match_adam": true,
    "recent_counts_match_committed_history": true,
    "whole_pool_growth_capacity": true,
    "render_backward_matches": true,
    "render_service_matches": true,
    "no_render_errors": true,
    "exact_kf_credit": true,
    "prefix_budget_matches": true,
    "per_kf_budget": true
  },
  "renders": {
    "all": 1437,
    "no_grad": 87,
    "training": 1350,
    "backward": 1350
  },
  "native_steps": 67,
  "additional_steps": 398,
  "clock_budget": 80.71412551403046
}
```

**2026-09-25 (15-render-per-KF / utmm / paired / seed0):** 18.420765dB, mapping 29.606s.

```json
{
  "dataset": "utmm",
  "scene": "square-1",
  "arm": "paired",
  "seed": 0,
  "output": "/home/intern/gs_floaterLab/results/campaigns/gain_attribution/render_matched_kf15/v1/utmm/paired/seed0",
  "returncode": 0,
  "valid": true,
  "psnr": 18.42076500845544,
  "mapping_seconds": 29.60573420196306,
  "final_map": {
    "keyframes": 71,
    "dense_admitted": 1133,
    "role_commits": {
      "keyframe": 193,
      "dense": 193
    },
    "native_steps": 62
  },
  "checks": {
    "common_commits_match_adam": true,
    "photometric_counts_match_adam": true,
    "recent_counts_match_committed_history": true,
    "whole_pool_growth_capacity": true,
    "full_available_pools": true,
    "paired_turns": true,
    "role_recent_counts": true,
    "native_window_only": true,
    "final_map_dense_used": true,
    "render_backward_matches": true,
    "render_service_matches": true,
    "no_render_errors": true,
    "exact_kf_credit": true,
    "prefix_budget_matches": true,
    "per_kf_budget": true
  },
  "renders": {
    "all": 1437,
    "no_grad": 87,
    "training": 1350,
    "backward": 1350
  },
  "native_steps": 67,
  "additional_steps": 633,
  "clock_budget": 80.71412551403046,
  "delta_psnr": 1.5918402524641984
}
```

## 최종 비교 — 2026-09-25

| Scene | KF admissions (reset 재등록 포함) | 학습 렌더링/각 arm | 보조 포함 총 렌더링/각 arm | 기존 PSNR | 새 paired PSNR | 차이 | 기존/새 처리시간(s) |
|---|---:|---:|---:|---:|---:|---:|---:|
| aria | 119 | 1785 | 1901 | 20.465558 | 20.725142 | +0.259584 | 12.870/22.322 |
| rpng | 227 | 3405 | 3628 | 20.499256 | 22.278183 | +1.778927 | 49.875/66.374 |
| utmm | 90 | 1350 | 1437 | 16.828925 | 18.420765 | +1.591840 | 24.509/29.606 |

- 세 장면 평균 +1.210117dB. 세 장면 모두 양수지만 seed0이며 반복 안정성은 미검증.
- 매 입력 prefix마다 학습 renders뿐 아니라 no-grad 보조 렌더를 포함한 전체 렌더 수도 같음. renderer/backward/service 카운터 동일. 실제 renderer budget 계측 테스트2개 + KF credit/cap/reset/heldout 테스트3개 PASS.
- 기존 30k 실험과 다르게 초기화도 15/KF에 포함하고 native는 입력당1step으로 제한함. 기본 topology policy를 교체하지 않았지만 optimizer 횟수 감소에 따라 topology 실행 기회가 감소함. 이전 고예산 PSNR과 절대값 직접 비교 금지.
- 과거 full-time 실패는 새 구조 자체/ERVS/full pool의 보편적 열세를 증명하지 않는다. 이번 저예산 구조 비교에서 새 구조는 더 높은 PSNR이나 시간은 더 듦.
- 기존 Growth는 이 저예산에서 모든 장면 dense admission0. 새 paired는 dense를 실제 학습. 따라서 native grouping/loss 변경, admission/dense 유무, 선택 방식이 결합된 비교이고 ERVS 또는 dense 단독 효과는 미분리.
- Native 대비 추가 렌더링 배분: Aria 기존1251+534 / 새946+839; RPNG2622+783 /2006+1399; UTMM952+398 /717+633.
- 새 paired pose 준비비용 Aria6.176s/RPNG11.109s/UTMM4.807s. KF-only 원인 대조나 같은 loss 대조는 이번 사용자 요청 범위에서 추가 실행하지 않음.
- 실제 mapper worker의 causal packet replay. 동시 tracking/실시간 arrival pacing 실험 아님. 동일 wall-clock 성능 유지나 strict streaming 목표 달성으로 판정하지 않음.
- production worktree 변경 없음. 실험 종료 후 compute GPU job 없음.

검증 파일: `results/campaigns/gain_attribution/render_matched_kf15/v1/verified_summary.json`

재현:
```bash
python3 benchmarks/online_gs/campaigns/gain_attribution/run_kf15_render_panel.py --output /ABS/FRESH_OUTPUT --seeds 0
python3 benchmarks/online_gs/campaigns/gain_attribution/analyze_kf15_render_panel.py --panel /ABS/FRESH_OUTPUT
```

## Vanilla 비교 추가 — 사전 프로토콜

2026-09-25 사용자 추가 요청. `/home/intern/VIGS-SLAM-official-exp78` commit22ffe24 원본 mapper + 공식 RPNG/UTMM config와 기존 Aria calibration adapter 사용. native window+과거2KF·loss·birth·topology 보존, ERVS/dense 도입 없음.
기존 공식 benchmark의 D1RenderBudgetAdapter를 재사용하여 매 input prefix마다 위 15/KF 비교와 **정확히 같은 render credit**을 native KF mapping으로 소비한다. 마지막에 예산을 몰아 소비하지 않는다.
공통 heldout 제외에 따른 first birth UID0 문제는 기존 공식 benchmark adapter로 교정. RGBD loss는 비교군과 동일한 masked inverse-depth 안전 계산만 프로세스 안에서 적용(유효픽셀 목적함수/gradient 불변). 원본 파일은 수정하지 않는다.
기존6run은 source/eval provenance가 보존된 fixed-work reference로 사용. Vanilla3run 새 실행 후 renderer forward/backward·prefix·same heldout·same trajectory·이중평가 검증. 실제 concurrent tracking 실험 아님.

**2026-09-25 (15 renders/KF vanilla / aria):** 18.906699dB, 1785 training renders.

```json
{
  "dataset": "aria",
  "scene": "aria1253",
  "arm": "vanilla",
  "seed": 0,
  "output": "/home/intern/gs_floaterLab/results/campaigns/gain_attribution/render_matched_kf15/vanilla_v1/aria/vanilla/seed0",
  "returncode": 0,
  "valid": true,
  "psnr": 18.906698667366086,
  "mapping_seconds": 15.570825533010066,
  "renders": {
    "all": 1901,
    "no_grad": 116,
    "training": 1785,
    "backward": 1785
  },
  "legacy_growth_minus_vanilla": 1.558858867819982,
  "paired_minus_vanilla": 1.8184432874199068
}
```

**2026-09-25 (15 renders/KF vanilla / rpng):** 21.228337dB, 3405 training renders.

```json
{
  "dataset": "rpng",
  "scene": "table_06",
  "arm": "vanilla",
  "seed": 0,
  "output": "/home/intern/gs_floaterLab/results/campaigns/gain_attribution/render_matched_kf15/vanilla_v1/rpng/vanilla/seed0",
  "returncode": 0,
  "valid": true,
  "psnr": 21.22833673975489,
  "mapping_seconds": 58.87559876090381,
  "renders": {
    "all": 3628,
    "no_grad": 223,
    "training": 3405,
    "backward": 3405
  },
  "legacy_growth_minus_vanilla": -0.7290809253314592,
  "paired_minus_vanilla": 1.0498465391966683
}
```

**2026-09-25 (15 renders/KF vanilla / utmm):** 15.875981dB, 1350 training renders.

```json
{
  "dataset": "utmm",
  "scene": "square-1",
  "arm": "vanilla",
  "seed": 0,
  "output": "/home/intern/gs_floaterLab/results/campaigns/gain_attribution/render_matched_kf15/vanilla_v1/utmm/vanilla/seed0",
  "returncode": 0,
  "valid": true,
  "psnr": 15.875981327928143,
  "mapping_seconds": 28.163778629968874,
  "renders": {
    "all": 1437,
    "no_grad": 87,
    "training": 1350,
    "backward": 1350
  },
  "legacy_growth_minus_vanilla": 0.9529434280630991,
  "paired_minus_vanilla": 2.5447836805272974
}
```

## Vanilla 포함 최종 비교 — 2026-09-25

공식 vanilla 새3run 완료. 기존 검증된 custom6run과 source/heldout/trajectory/render-prefix 비교 PASS.

| Scene | 학습 renders/arm | 보조 포함 renders/arm | Vanilla | 기존 내부구조 | 새 paired | 새−vanilla | vanilla 처리시간(s) |
|---|---:|---:|---:|---:|---:|---:|---:|
| aria | 1785 | 1901 | 18.906699 | 20.465558 | 20.725142 | +1.818443 | 15.571 |
| rpng | 3405 | 3628 | 21.228337 | 20.499256 | 22.278183 | +1.049847 | 58.876 |
| utmm | 1350 | 1437 | 15.875981 | 16.828925 | 18.420765 | +2.544784 | 28.164 |

- 새 paired−vanilla 평균 **+1.804358dB**, 3/3 양수. 기존 내부구조−vanilla 평균+0.594240dB이나 RPNG는−0.729081dB.
- 동일 input prefix마다 training/보조포함total 렌더 일치. 3scene evaluator2회일치, 평가 cohort/trajectory hash동일. 미래/heldout 학습입력0, EOS후optimizer0.
- Vanilla는 official commit22ffe24의 KF window+과거2 random 및 원래 loss/birth/topology 사용. shared heldout first-birth UID correction, 동일 valid-depth loss의 안전 reciprocal 처리, per-prefix render budget adapter만 프로세스 안에서 적용. ERVS/dense 미추가. 원본 source 파일 미수정.
- Vanilla optimizer steps Aria226/RPNG445/UTMM181. 같은 render count여도 custom의 단일영상 추가 Adam과 batch grouping은 다름. 차이를 sampler 단독 효과로 귀속하지 않는다.
- Seed0 fixed-work mapping 진단. 초기화도 저예산에 포함해 절대품질이 낮음. concurrent tracking/strict realtime 성능·반복안정성은 이 결과로 입증하지 않는다. 기존 broader goal은 미완료.
- 완료 후 GPU compute job 없음.

검증: `results/campaigns/gain_attribution/render_matched_kf15/vanilla_v1/verified_summary.json`

재현:
```bash
python3 benchmarks/online_gs/campaigns/gain_attribution/run_kf15_vanilla_panel.py --output /ABS/FRESH_VANILLA_OUTPUT --reference-panel /ABS/KF15_REFERENCE_PANEL
python3 benchmarks/online_gs/campaigns/gain_attribution/analyze_kf15_vanilla.py --panel /ABS/FRESH_VANILLA_OUTPUT --reference-panel /ABS/KF15_REFERENCE_PANEL
```
