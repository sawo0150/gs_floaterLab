# Exp121 — source-backed topology direction and cost profile

Date: 2026-09-24

## Question

Before replacing the current global densify/prune path with a more invasive
local implementation, determine whether topology mutation is actually the
mapping-time bottleneck. At the same time, inspect downloaded author code—not
paper prose—to decide which local-topology primitives are compatible with the
strict RGB/causal/fixed-work contract.

## Profiling method

The frozen Exp119/120 unified LPM-mass normalized arm was replayed on UTMM
`square-1` and RPNG `table_01`. `VIGS_TIMING_LOG` enables CUDA-synchronized
section timing around the existing mapper operations. It does not change the
render/Adam schedule, but synchronization perturbs wall time; these runs are
therefore profiling artifacts, not quality comparisons.

The first manual launch inherited a stale `PYTHONPATH` and stopped before any
mapping work. It is retained at
`results/experiments/exp121_topology_cost_profile/`. The corrected runs use the
same environment construction as the official benchmark runner and live at
`results/experiments/exp121_topology_cost_profile_v2/`.

## Results

| Scene | Mapping wall | Render | Adam | Final GS | Topology calls timed | Densify/prune total | Max call | Share of mapping wall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| UTMM square-1 | 40.590 s | 9,345 | 757 | 120,708 | 3 | 69.575 ms | 55.108 ms | **0.171%** |
| RPNG table_01 | 170.247 s | 38,302 | 3,030 | 418,927 | 4 | 58.666 ms | 40.334 ms | **0.034%** |

Section totals provide the same diagnosis:

| Scene | Backward | Loss compute | Rasterize | Optimizer step | Densify/prune |
|---|---:|---:|---:|---:|---:|
| UTMM square-1 | 8,181.1 ms | 5,465.0 ms | 2,165.9 ms | 528.6 ms | **69.6 ms** |
| RPNG table_01 | 79,620.3 ms | 21,473.5 ms | 18,495.2 ms | 2,166.4 ms | **58.7 ms** |

The profile still records very large mutation churn: 89,296 regular lifetime
row mutations on UTMM and 114,143 on RPNG. Thus global topology is a quality
and mechanism-interpretability concern, but it is not the current average
throughput bottleneck. A 40--55 ms event spike may still matter in strict live
execution and should remain in the C-track latency ledger.

## Downloaded-source audit

| Author implementation | Exact code finding | Decision |
|---|---|---|
| LPM `7c060267` | In triangulated 3D error zones it lowers the native gradient threshold by a fixed 0.5 ratio, then compensates extra additions by pruning the same number of lowest-opacity points. Building those zones requires LightGlue/SuperPoint matching and multi-view triangulation. | Keep the already ported exact 16x16 error-zone primitive. Do not claim or copy the full offline topology pipeline into strict online mapping. |
| TileGS `7f109a40` | Its custom CUDA rasterizer increments per-Gaussian appearance counters for every touched tile, increments/decrements hit counters at SSIM below 0.5/above 0.9, and later uses hard ratios plus an `appear_times > 500` gate. It allocates extra tile buffers in the render path and densifies every qualifier. | Do not transplant the CUDA fork now: fixed offline thresholds, unbounded mutation, and extra hot-path state do not solve the measured bottleneck. |
| Taming 3DGS `fd0f7d9e` | The reusable primitive is weighted `torch.multinomial(..., replacement=False)` under an explicit point budget. Its full score recomputes multiple camera renders and its evaluation script uses scene-specific final budgets. | Retain the bounded sampling primitive already used by the generation-scoped ticket; reject the extra-render score and scene budgets. |
| RTG-SLAM `49dada14` | The mapper uses a top-40% 16x16 color-error tile mask, but stable/unstable state also depends on RGB-D depth, normals, index maps, confidence 200, and a 50-frame lifetime. The checkout is GPL-3.0. | Useful context only. Do not copy its fixed-frame RGB-D lifecycle into the strict RGB mapper or mix GPL code into the current tree without a separate licensing decision. |

## Verdict

**PASS as a profiling/decision gate.** The evidence rejects a speed-motivated
TileGS CUDA port at this stage. The defensible implementation path remains:

1. LPM author code supplies the exact causal error-zone evidence;
2. normalized-variance ERCB decides which admitted dense view receives service;
3. Taming author code supplies bounded weighted-without-replacement mutation;
4. our contribution is the causal, transactional, fixed-render composition.

No new hard pruning is introduced before the 27 dB quality milestone. The next
isolation should determine whether RPNG's Exp120 loss comes from replacing a
historical RGB-D keyframe gradient or from allowing the dense replacement to
enter native densification statistics. That single-factor result is needed
before changing the mutation rule.
