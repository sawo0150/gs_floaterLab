# exp109 — frozen first-persistence topology, full 17-scene B-track panel

- Date: 2026-09-24
- Status: **PASS** (minimum acceptance and Exp94 stretch target)
- VIGS code source: `f6a90853`; head at source lock `51ad7285` adds docs only
- Lab source at start: `3ddd720` plus source-locked Exp109 runner
- Mapping runner: `benchmarks/online_gs/run_exp109_first_persistence_panel.py`
- Artifact-only reporter: `benchmarks/online_gs/report_exp109_first_persistence_panel.py`
- Results: `results/experiments/exp109_first_persistence_panel/`
- Official summary: [17-scene table](benchmark_custom/exp109_first_persistence_panel_20260924/summary.md)

## Frozen method and code provenance

All 17 valid scenes use the same method without dataset/scene-specific tuning:

1. Preserve normalized R4 birth, recent-keyframe floor, normalized-variance
   ERCB service, prune, and observation-driven native topology.
2. Read per-Gaussian `f_dc` gradient evidence from already-paid dense renders;
   add no render and invent no dense depth.
3. Scope identities by `(map_generation, point_id)` and require nomination by
   at least two distinct dense view UIDs.
4. At the first qualifying persistence event in each map generation, spend at
   most one top-1,024 small-Gaussian clone ticket.
5. Preserve existing native densification accumulators across the mid-cycle
   append.

The bounded weighted-without-replacement operator is adapted from Taming 3DGS
author code pinned at `fd0f7d9edfe135eb4eefd3be82ee56dada7f2a16`, rather than
reconstructed from paper prose. TileGS author code at
`7f109a403ed522ba5ec7610f3d4778c363b68b11` informed the repeated-evidence
concept, but its offline tile/CUDA path was not copied. Methods without public
author code remain paper-only context and were not presented as ports.

## Main result

Every row is a newly executed candidate/official-vanilla pair in the Exp109
root. Both saved maps were evaluated twice and all pair-verifier checks pass.

| Dataset | Scenes | Candidate PSNR | Vanilla PSNR | delta PSNR | Wins | delta R4 | SSIM C/V | LPIPS C/V |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| RPNG | 8 | 24.0927 | 22.4762 | **+1.6165** | 8/8 | -0.0000 | 0.8055/0.7455 | 0.1786/0.2428 |
| UTMM | 7 | 19.2631 | 18.6888 | **+0.5743** | 7/7 | +0.0117 | 0.6634/0.6445 | 0.4121/0.4206 |
| Aria | 2 | 25.4067 | 22.9447 | **+2.4620** | 2/2 | -0.0374 | 0.8328/0.7829 | 0.3465/0.4580 |
| **Overall** | **17** | **22.2586** | **20.9718** | **+1.286809** | **17/17** | **+0.000426** | **0.7502/0.7083** | **0.2945/0.3414** |

The predeclared minimum acceptance (mean at least +0.5 dB, majority wins,
every fairness/R4-floor check) passes. The Exp94 stretch target of +1.253787 dB
and 17/17 wins also passes. Mean SSIM improves by +0.041866 and LPIPS decreases
by 0.046840.

## Work and resource accounting

- Every candidate/vanilla pair has exactly matched physical renders; all
  held-out disjointness and zero-tail checks pass.
- The ticket itself adds **zero render and zero Adam step**.
- It executes 6,782 bounded clones across the panel. The summed final map size
  is 5,644,613 versus exact R4's 5,642,198: only **+2,415 (+0.043%)**, because
  unchanged downstream native topology absorbs most inserted rows.
- Total candidate mapping wall is 2,618.0 s versus historical exact R4's
  2,724.8 s (-3.92%). This is cross-run timing variation, not a speed claim.
  Per-scene wall, final GS, and peak CUDA allocation are in the official
  summary.

## Reporting incident

All 17 mapping/evaluation pairs completed before the source-locked runner's
inline summary raised `KeyError: candidate_renders`: the inherited Exp106
compact `pair_result.json` intentionally omitted work fields. No mapping or
metric artifact was lost. The separate artifact-only reporter reconstructs
the table from immutable pair-verifier, quality-gate, evaluation-consistency,
and runtime JSON files. The executed runner is kept unchanged so its source
lock remains auditable.

## Decision and claim boundary

Adopt this as the current B-track custom composition. It demonstrates that
dense/ERCB evidence actively controls bounded topology on every tested family
while reproducing the full R4 quality advantage. It does **not** yet show that
the new ticket is causally better than ticket-off R4: mean delta R4 is only
+0.000426 dB. The next method ablation must compare this frozen version against
ticket-off R4 and ERCB-to-RR under scarce work. Strict-live tracking+mapping
deadline compliance is also still pending; do not convert this B-track result
into a realtime claim.
