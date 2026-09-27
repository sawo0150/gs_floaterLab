# 동일 렌더링 작업량: 기존 mapper vs paired mapper

2026-09-25. 사용자 요청: 총 렌더링 수를 같게 하여 새 구조를 비교한다.

## 사전 고정 프로토콜

- Aria1253, RPNG table_06, UTMM square-1, seed0. 기존 v2와 같은 runtime/source/loss, 새 Carve·prune 없음.
- 기존 구조와 paired 구조를 모두 다시 실행. 시간 제한은 제거한 **원인 분석용 causal fixed-work replay**이며 strict/live 성능 판정이 아니다.
- 기존 v2 legacy의 추가 optimizer 완료 시각을 그 시점까지 도착한 마지막 RGB uid에 배분하여 기준선 추가 작업량을 정한다. 품질이나 장면별 knob로 예산을 선택하지 않는다.
- 모든 causal tracker packet은 도착 uid에서 동기적으로 worker 처리. 다음 입력 전에 정해진 작업을 완료. 미래 frame/pose/depth, 평가 RGB는 학습에 사용하지 않는다.
- 기준선에서 각 입력 uid 처리 후의 누적 **학습 camera render**를 기록. paired는 같은 uid에서 native work를 끝낸 뒤 추가 학습으로 그 수에 정확히 도달한다. 초과하면 실패 처리하며 native를 중간 잘라 맞추지 않는다.
- 렌더링 budget에는 초기화·reset 이전·native KF window/global·추가 KF/dense 학습을 모두 포함한다. 배치 renderer 1호출도 camera N장이면 N회로 계산.
- renderer forward 계측, 실제 backward 도달 여부, committed training service의 영상 수를 독립 비교한다. no-grad 보조 렌더는 별도 보고하며 held-out 평가는 종료 후만 수행한다.
- 최종 입력에서 종료. 마지막 입력 후 optimizer update 0회. 실제 처리 시간·pose 비용·optimizer steps를 함께 보고한다.
- Loss, native view grouping, Growth/immediate, ERVS role 분리는 각 기존/new 버전 그대로 유지하므로 ERVS 단독 ablation은 아니다.
- 학습 호출은 원래 VIGS worker/runtime. 실험 runner에서 unsolicited idle을 끄고 FIFO counted-work packet을 추가한다. production/runtime source 수정 없음.
- 유효 실행 후 동일 held-out harness 독립 2회 평가. per-prefix budget 동등성·source lock 검증.

## 결과

진행 중. 기존 fixed-time PSNR과 직접 혼합하지 않는다.

**2026-09-25 (render-matched / aria / legacy_growth / seed0):** 27.708641dB, mapping 97.725s.

```json
{
  "dataset": "aria",
  "scene": "aria1253",
  "arm": "legacy_growth",
  "seed": 0,
  "output": "/home/intern/gs_floaterLab/results/campaigns/gain_attribution/render_matched/v1/aria/legacy_growth/seed0",
  "returncode": 0,
  "valid": true,
  "psnr": 27.708641176005358,
  "mapping_seconds": 97.72547180799302,
  "final_map": {
    "keyframes": 91,
    "dense_admitted": 132,
    "role_commits": null,
    "native_steps": 799
  },
  "checks": {
    "common_commits_match_adam": true,
    "photometric_counts_match_adam": true,
    "recent_counts_match_committed_history": true,
    "whole_pool_growth_capacity": true,
    "render_backward_matches": true,
    "render_service_matches": true,
    "no_render_errors": true,
    "no_unused_quota": true,
    "prefix_budget_matches": true,
    "reference_extra_count_matches": true
  },
  "renders": {
    "all": 30197,
    "no_grad": 116,
    "training": 30081,
    "backward": 30081
  },
  "native_steps": 1016,
  "additional_steps": 15384,
  "clock_budget": 97.64999836950005
}
```

**2026-09-25 (render-matched / aria / paired / seed0):** 27.348867dB, mapping 138.726s.

```json
{
  "dataset": "aria",
  "scene": "aria1253",
  "arm": "paired",
  "seed": 0,
  "output": "/home/intern/gs_floaterLab/results/campaigns/gain_attribution/render_matched/v1/aria/paired/seed0",
  "returncode": 0,
  "valid": true,
  "psnr": 27.348866593746738,
  "mapping_seconds": 138.7258913529804,
  "final_map": {
    "keyframes": 91,
    "dense_admitted": 924,
    "role_commits": {
      "keyframe": 8760,
      "dense": 8759
    },
    "native_steps": 799
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
    "no_unused_quota": true,
    "prefix_budget_matches": true,
    "reference_extra_count_matches": true
  },
  "renders": {
    "all": 30197,
    "no_grad": 116,
    "training": 30081,
    "backward": 30081
  },
  "native_steps": 1016,
  "additional_steps": 19461,
  "clock_budget": 97.64999836950005,
  "delta_psnr": -0.3597745822586198
}
```

## 사용자 지시에 따른 중단

2026-09-25: Aria 2arm 완료(30,081 training renders), RPNG baseline 실행 도중 사용자 지시로 coordinator와 해당 mapper만 SIGTERM. 미완료 panel이며 15 renders/KF 실험으로 대체한다. 기존 산출물은 보존.
