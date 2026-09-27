# Local window + paired full-pool refinement

2026-09-25 user-directed architecture change. The immediate target is paper-aligned execution and checking whether quality is maintained on Aria1253, RPNG table_06 and UTMM square-1. Do not presume an improvement. Earlier broader goal comparisons/repeats/convergence remain outstanding.

- Native mapping: current keyframe window, original RGB/depth/normal losses and observation-based topology; historical six slots removed in candidate only.
- Additional refinement: alternate one KF RGB/depth/normal Adam and one dense RGB Adam; independent full-role ERVS, recent role selection counts, entropy tau=1/N. Native steps do not consume turns; cancellations do not advance turns. When no causal dense exists, KF-only refinement is allowed and logged as unpaired.
- Dense membership: all arrived non-held-out views bracketed by current training KFs. Old whole_pool capacity gate disabled for candidate. CPU history retained, bounded GPU image cache, pose prepared only on selection. Map reset starts a fresh generation and pair.
- Causal input/pose preparation, setup-inclusive 1.5x clock, 100ms admission reserve, zero optimizer tail. Frozen causal tracking inputs through actual mapper worker, not concurrent tracking validation.
- Controls: legacy_growth worker with original native global slots; paired_kf_only to expose dense contribution in the new local+global geometry structure. All run with identical new source bytes and selected native extensions.
- Initial seed0 panel; final repeats must precede an equivalence claim. Report actual PSNR differences rather than retroactively choose a tolerance.
- Added preparation-finally accounting and explicit normal deadline-cancellation handling. Unexpected early close/worker failure remains fatal; transfer completion counts against budget.

Reproduce: `python3 benchmarks/online_gs/campaigns/gain_attribution/run_paired_worker_panel.py --output /home/intern/gs_floaterLab/results/campaigns/gain_attribution/paired_full_pool/v1 --seeds 0`

CPU checks before GPU: paired scheduler5, boundary handling3; broader existing checks pending. Paper is not changed yet; full-pool immediate admission and recent role counts differ from old Growth/lifetime-count wording.

Pre-run verification:49 tests passed (39 existing online tests,5 paired scheduler/loss-routing tests,3 producer-boundary tests,2 masked-depth tests). Executing the existing RGBD loss on zero target/render depths reproduced NaN from masked inverse-depth division; mask-before-reciprocal repair applied identically to candidate and controls. Valid-depth loss values/gradients unchanged; masked-zero gradients finite and zero. This repair is numerical correctness, not a new geometry loss.

**2026-09-25 (paired full-pool / aria / paired / seed0):** 26.555117dB, mapping 97.575s.

```json
{
  "dataset": "aria",
  "scene": "aria1253",
  "arm": "paired",
  "seed": 0,
  "output": "/home/intern/gs_floaterLab/results/campaigns/gain_attribution/paired_full_pool/v1/aria/paired/seed0",
  "returncode": 0,
  "valid": true,
  "psnr": 26.555117366878132,
  "mapping_seconds": 97.57523306505755,
  "final_map": {
    "keyframes": 91,
    "dense_admitted": 924,
    "role_commits": {
      "keyframe": 3353,
      "dense": 3352
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
    "worker_and_preparation_within_budget": true
  }
}
```

## Implementation and interpretation

Entry: `VIGS(args, online_mapping={"schedule":"paired_kf_dense", "membership":"immediate", "selector":"ervs", "deadline":deadline})`, with existing pure-online parallel mapping enabled. Deadline is a monotonic clock timestamp. Current benchmark runner creates the same runtime and calls the actual VIGS mapper worker, with frozen causal tracker packets.

`OnlineMapperRuntime` disables historical native slots and selects the paired policy. `PairedTrainingSet` retains all current-generation KF and all admitted causal dense, applies ERVS within each role, and keeps the pending turn across native work. `OnlinePhotometricTrainer` dispatches KF samples to the existing frontier RGBD/normal loss and dense samples to RGB L1/SSIM. Additional steps share the Gaussian optimizer but do not trigger an independent topology cycle; native window mapping continues to own the existing topology behavior. Service logs retain the historical `photometric` label for all additional steps, including the new geometry-supervised KF steps; `role` disambiguates them.

The local window's design role is immediate refinement of recently observed/newly initialized geometry while topology evolves. This is a rationale, not an ablation proving the window necessary. Full-pool KF refinement revisits old geometry; dense refinement uses additional appearance observations. Ratios refer to additional Adam steps, not all rendered images or wall time. The protocol changes several aspects jointly, so an overall quality difference is not evidence for ERVS alone.

Paper alignment remains a separate editing task: immediate full-pool admission does not implement the former kappa-based View Set Growth claim; recent per-role counts are not lifetime cumulative counts. Do not silently retain those old descriptions when presenting this implementation.

## v1 review and v2 correction

Aria paired v1 completed at26.555117dB with exact double evaluation, but is **not accepted as the requested architecture**: PGBA recovery passed all corrected KFs to map(), and native_window_only mistakenly checked that supplied list rather than the actual current window. Four recovery calls had76/79/84/91candidates. v1 artifact and contract_review.json preserved; coordinator stopped after its in-flight legacy control finished mapping, before any source mutation. v2 forces every paired native call (including PGBA recovery) to the actual current window; all pose/depth corrections still apply. Independent audit compares the actual window and selected UIDs. An added test executes the actual map routing prefix with100PGBA KFs and3recent KFs, and checks the legacy path remains unchanged;6paired tests pass. Initial v2 panel prioritizes paired/legacy across all3scenes; paired KF-only and repeat comparisons follow.

Test-record correction: the first new PGBA routing test invocation failed because its fixture omitted required `iters`; mapper code was not the failing component. The premature6-pass note above is superseded by the corrected fixture artifact in `v2/test_paired_view_training_corrected.py` and its explicit six-test log. Active locked test/source files were not changed; the fixture will be corrected in the worktree after the panel. An initial dynamic loader invocation discovered0tests and is not counted.

**2026-09-25 (paired full-pool / aria / paired / seed0):** 26.442868dB, mapping 97.551s.

```json
{
  "dataset": "aria",
  "scene": "aria1253",
  "arm": "paired",
  "seed": 0,
  "output": "/home/intern/gs_floaterLab/results/campaigns/gain_attribution/paired_full_pool/v2/aria/paired/seed0",
  "returncode": 0,
  "valid": true,
  "psnr": 26.442867810489567,
  "mapping_seconds": 97.55123843695037,
  "final_map": {
    "keyframes": 91,
    "dense_admitted": 924,
    "role_commits": {
      "keyframe": 4008,
      "dense": 4007
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
    "worker_and_preparation_within_budget": true
  }
}
```

**2026-09-25 (paired full-pool / aria / legacy_growth / seed0):** 27.787554dB, mapping 97.553s.

```json
{
  "dataset": "aria",
  "scene": "aria1253",
  "arm": "legacy_growth",
  "seed": 0,
  "output": "/home/intern/gs_floaterLab/results/campaigns/gain_attribution/paired_full_pool/v2/aria/legacy_growth/seed0",
  "returncode": 0,
  "valid": true,
  "psnr": 27.787553925550622,
  "mapping_seconds": 97.55327673803549,
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
    "worker_and_preparation_within_budget": true
  }
}
```

**2026-09-25 (paired full-pool / rpng / paired / seed0):** 23.920891dB, mapping 138.276s.

```json
{
  "dataset": "rpng",
  "scene": "table_06",
  "arm": "paired",
  "seed": 0,
  "output": "/home/intern/gs_floaterLab/results/campaigns/gain_attribution/paired_full_pool/v2/rpng/paired/seed0",
  "returncode": 0,
  "valid": true,
  "psnr": 23.920890660328908,
  "mapping_seconds": 138.27634711004794,
  "final_map": {
    "keyframes": 186,
    "dense_admitted": 1810,
    "role_commits": {
      "keyframe": 773,
      "dense": 772
    },
    "native_steps": 2118
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
    "worker_and_preparation_within_budget": true
  }
}
```

**2026-09-25 (paired full-pool / rpng / legacy_growth / seed0):** 24.538978dB, mapping 138.277s.

```json
{
  "dataset": "rpng",
  "scene": "table_06",
  "arm": "legacy_growth",
  "seed": 0,
  "output": "/home/intern/gs_floaterLab/results/campaigns/gain_attribution/paired_full_pool/v2/rpng/legacy_growth/seed0",
  "returncode": 0,
  "valid": true,
  "psnr": 24.538977559407552,
  "mapping_seconds": 138.27694323495962,
  "final_map": {
    "keyframes": 186,
    "dense_admitted": 0,
    "role_commits": null,
    "native_steps": 2118
  },
  "checks": {
    "common_commits_match_adam": true,
    "photometric_counts_match_adam": true,
    "recent_counts_match_committed_history": true,
    "whole_pool_growth_capacity": true,
    "worker_and_preparation_within_budget": true
  }
}
```

**2026-09-25 (paired full-pool / utmm / paired / seed0):** 22.385100dB, mapping 80.614s.

```json
{
  "dataset": "utmm",
  "scene": "square-1",
  "arm": "paired",
  "seed": 0,
  "output": "/home/intern/gs_floaterLab/results/campaigns/gain_attribution/paired_full_pool/v2/utmm/paired/seed0",
  "returncode": 0,
  "valid": true,
  "psnr": 22.38510031759003,
  "mapping_seconds": 80.6142272070283,
  "final_map": {
    "keyframes": 70,
    "dense_admitted": 1126,
    "role_commits": {
      "keyframe": 2419,
      "dense": 2419
    },
    "native_steps": 542
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
    "worker_and_preparation_within_budget": true
  }
}
```

**2026-09-25 (paired full-pool / utmm / legacy_growth / seed0):** 23.269436dB, mapping 80.639s.

```json
{
  "dataset": "utmm",
  "scene": "square-1",
  "arm": "legacy_growth",
  "seed": 0,
  "output": "/home/intern/gs_floaterLab/results/campaigns/gain_attribution/paired_full_pool/v2/utmm/legacy_growth/seed0",
  "returncode": 0,
  "valid": true,
  "psnr": 23.269435847247088,
  "mapping_seconds": 80.63938171206973,
  "final_map": {
    "keyframes": 70,
    "dense_admitted": 116,
    "role_commits": null,
    "native_steps": 542
  },
  "checks": {
    "common_commits_match_adam": true,
    "photometric_counts_match_adam": true,
    "recent_counts_match_committed_history": true,
    "whole_pool_growth_capacity": true,
    "worker_and_preparation_within_budget": true
  }
}
```

**2026-09-25 (paired v2 3scene 완료):** 동일소스/예산/평가 검증PASS. paired−기존 Aria-1.3447,RPNG-0.6181,UTMM-0.8843dB, 평균-0.9490; 성능유지 실패. 모든최종지도 dense실사용/최근window/1:1교대검증PASS. KF-only 분리대조 진행.

`results/campaigns/gain_attribution/paired_full_pool/v2/verified_summary.json` contains cross-arm source/cohort/trajectory/budget verification. No 3-seed equivalence claim is made from this failed seed0 candidate. The test-fixture correction is now committed to the working file after the panel;6tests pass. Runtime source bytes remain unchanged for the following KF-only diagnostic.

**2026-09-25 (paired full-pool / aria / paired_kf_only / seed0):** 26.496855dB, mapping 97.552s.

```json
{
  "dataset": "aria",
  "scene": "aria1253",
  "arm": "paired_kf_only",
  "seed": 0,
  "output": "/home/intern/gs_floaterLab/results/campaigns/gain_attribution/paired_full_pool/v2_kf_control/aria/paired_kf_only/seed0",
  "returncode": 0,
  "valid": true,
  "psnr": 26.49685524074176,
  "mapping_seconds": 97.5515993500594,
  "final_map": {
    "keyframes": 91,
    "dense_admitted": 0,
    "role_commits": {
      "keyframe": 16227,
      "dense": 0
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
    "worker_and_preparation_within_budget": true
  }
}
```

**2026-09-25 (paired full-pool / rpng / paired_kf_only / seed0):** 24.584378dB, mapping 138.276s.

```json
{
  "dataset": "rpng",
  "scene": "table_06",
  "arm": "paired_kf_only",
  "seed": 0,
  "output": "/home/intern/gs_floaterLab/results/campaigns/gain_attribution/paired_full_pool/v2_kf_control/rpng/paired_kf_only/seed0",
  "returncode": 0,
  "valid": true,
  "psnr": 24.58437829576097,
  "mapping_seconds": 138.27589405700564,
  "final_map": {
    "keyframes": 186,
    "dense_admitted": 0,
    "role_commits": {
      "keyframe": 6125,
      "dense": 0
    },
    "native_steps": 2118
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
    "worker_and_preparation_within_budget": true
  }
}
```

**2026-09-25 (paired full-pool / utmm / paired_kf_only / seed0):** 22.126928dB, mapping 80.639s.

```json
{
  "dataset": "utmm",
  "scene": "square-1",
  "arm": "paired_kf_only",
  "seed": 0,
  "output": "/home/intern/gs_floaterLab/results/campaigns/gain_attribution/paired_full_pool/v2_kf_control/utmm/paired_kf_only/seed0",
  "returncode": 0,
  "valid": true,
  "psnr": 22.126927970368186,
  "mapping_seconds": 80.63912756403442,
  "final_map": {
    "keyframes": 70,
    "dense_admitted": 0,
    "role_commits": {
      "keyframe": 12507,
      "dense": 0
    },
    "native_steps": 542
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
    "worker_and_preparation_within_budget": true
  }
}
```

## Final v2 seed0 result — execution implemented, quality maintenance failed

All9runs (three scenes x paired/legacy_growth/paired_kf_only) passed runtime, common runtime-source, cohort, trajectory and budget checks plus independent double saved-map evaluation. Tests:50unique cases passed across existing online39, paired6, input-boundary3 and masked-depth2. No GPU job remains after this panel. Production worktree remains clean.

| Scene | Legacy worker | New KF-only | New KF+dense paired | Paired minus legacy | Paired minus new KF-only |
|---|---:|---:|---:|---:|---:|
| aria | 27.787554 | 26.496855 | 26.442868 | -1.344686 | -0.053987 |
| rpng | 24.538978 | 24.584378 | 23.920891 | -0.618087 | -0.663488 |
| utmm | 23.269436 | 22.126928 | 22.385100 | -0.884336 | +0.258172 |

The requested role alternation and actual recent-window restriction are verified, including PGBA recovery. The paired candidate fails the requested quality-maintenance target: mean delta legacy -0.949036dB. No repeated-seed equivalence or fast-convergence claim. It remains an opt-in development branch, not a promoted production recipe.

Interpretation: Aria and UTMM remain below legacy even when the new additional path trains KFs only. RPNG KF-only approximately matches legacy in this seed, while adding dense reduces quality. Dense preparation costs17-22s in the paired runs; however the KF-only controls demonstrate that pose cost alone is not a sufficient general explanation. Window/global allocation, batch-vs-single-view optimization and the changed additional-KF RGB/depth/normal objective remain confounded.

Next evidence needed: isolate additional-KF RGB objective (legacy common RGB L1/SSIM versus reused native masked RGB+geometry loss) and geometry weighting before concluding full-pool ERVS is responsible. Any follow-up retains current scene set, roles and clock, and must not tune by scene. A paired Growth admission ablation, final repeats, stream quality and paper alignment remain open. Immediate membership in this candidate is not the old optimization-guided Growth claim.

Reproduce all three arms with a fresh output directory: `python3 benchmarks/online_gs/campaigns/gain_attribution/run_paired_worker_panel.py --output /home/intern/gs_floaterLab/results/campaigns/gain_attribution/paired_full_pool/reproduce_seed0 --seeds 0`. Exact executed source snapshots and commands are under v2/implementation and v2_kf_control/implementation. Combined verified result: `results/campaigns/gain_attribution/paired_full_pool/v2/verified_summary.json`.
