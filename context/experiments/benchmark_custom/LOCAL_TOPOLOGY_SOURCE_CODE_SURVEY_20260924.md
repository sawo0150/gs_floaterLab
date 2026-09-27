# Local topology source-code survey

Date: 2026-09-24

## Working rule

Papers establish the idea, assumptions, and comparison context. Production
experiments use an author implementation downloaded locally at a pinned
commit. A paper-only description is not copied as if it were verified code.
When the author code depends on unavailable modalities or violates the causal
online contract, only the incompatibility is recorded; a superficially
similar reimplementation is not attributed to that work.

All checkouts are under `/home/intern/gs_topology_references`.

| Work / local checkout | Pinned commit | What the code actually does | Decision for VIGS |
|---|---|---|---|
| LPM (`lpm`) | `7c060267` | Normalizes render/GT by image mean, thresholds channel-summed absolute error at quantile 0.4, and marks 16x16 zones whose error coverage exceeds 0.85. The full pipeline also uses CPU camera/ray preparation, LightGlue/SuperPoint all-pair matching, connected components, triangulation, and map-wide masks. | Port only the exact error-zone operation on an already-paid dense render. Do not port the offline matching/triangulation pipeline. |
| TileGS (`tilegs`) | `7f109a40` | A custom CUDA rasterizer accumulates per-tile grayscale SSIM evidence into per-Gaussian hit/appearance counters; refinement uses fixed score thresholds/cadence and render-hot-path buffers. | Useful evidence-counter precedent, but too invasive to port before the LPM utility gate; CUDA implementation requires an independent correctness audit. |
| Taming 3DGS (`taming_3dgs`) | `fd0f7d9e` | Performs constructive, budgeted sampling/densification with explicit point selection. | Already used as the source for bounded weighted topology tickets; retain pinned attribution. |
| RTG-SLAM (`rtg_slam`) | `49dada14` | Uses a top-40% 16x16 color-error tile mask during global optimization, while stable/unstable lifecycle and error removal depend on RGB-D depth, normals, Gaussian index maps, confidence 200, and a 50-frame lifetime. The checkout is GPL-3.0. | Code-level context only. Do not copy its fixed-frame RGB-D lifecycle or GPL implementation into the current tree without a separate license decision. |
| Gaussian-SLAM (`gaussian_slam`) | `eaec10d7` | Adds Gaussians from low-silhouette/positive depth residual regions in an RGB-D/submap pipeline. | Previously ported and rejected as a replacement birth rule; residual supplement is safe but far too costly. |
| SplatMAP (`splatmap`) | `909cde62` | Checkout contains project-page/web assets, not an executable mapper implementation. | Paper context only; no implementation may be claimed as a source port. |
| LiDAR-GS-SLAM (`lidar_gs_slam`) | `04b91618` | Selective densification/pruning uses LiDAR depth, normals, validity, and planar geometry. | Modality mismatch with the strict RGB+online-state contract; do not port the exact score. |
| VAD-GS (`vad_gs`) | `77e27686` | Uses voxel visibility plus LiDAR/monocular depth, normals, segmentation, and MVS-style propagation. | Offline/sensor-heavy mismatch; do not port. The inspected checkout also lacks a root license file, so copying is inappropriate. |
| SplaTAM (`splatam`) | `da6bbcd2` | Uses rendered silhouette and GT RGB-D depth, backprojecting new points in under-modelled regions. | Strong local-birth precedent but an exact port would violate the input contract because GT depth is required. |

No usable official implementation was found for GaussianFlow-SLAM (repository
announces code as forthcoming) or GAD-SLAM during this audit. They remain
literature context only.

## Code-level conclusion

The smallest implementation-compatible primitive is LPM's image-space
error-zone extraction. Exp113/114 show that it can run on a dense render that
was already budgeted, with no additional rendering, Adam update, or map
mutation. The next implementation should therefore use the detached zone
coverage as a bounded *view-service utility*, not immediately as a topology
or pruning trigger:

\[
p_i \propto (1+e_i)\exp[-\gamma n_i/(T+1)],
\]

where `e_i` is the most recently completed LPM error-zone coverage and the
normalized-variance ERCB term remains unchanged. The `1+e_i` base measure is
bounded in [1,2], adds no scene-specific knob, and preserves the first-service
floor. Updating `e_i` only after a successful Adam step is required so a
deadline-rejected draw cannot alter later probabilities.

This formula is our scheduler composition, not a claim that the LPM authors
implemented ERCB. It must be ablated against identical-work normalized ERCB
and RR controls before any contribution claim.

## Post-Exp120 exact-code audit

Exp121 revisited the topology implementations themselves after the unified
dense path became active:

- LPM's `lpm_densify_and_clone/split` lowers the native gradient threshold by
  `grad_ratio=0.5` only inside LightGlue-matched, triangulated 3D zones. Its
  `lpm_densify_and_prune` then selects the same number of lowest-opacity rows as
  the extra additions. The exact topology path therefore cannot be represented
  by an image mask alone, and the hard prune is disallowed before our quality
  milestone.
- TileGS updates `appear_times` for every Gaussian touching a tile, changes
  `hit_times` when grayscale tile SSIM is below 0.5 or above 0.9, then applies
  hard ratio gates and an `appear_times > 500` clone gate. Its CUDA render path
  allocates auxiliary image/tile buffers and its mutation is not bounded.
- Taming's exact bounded primitive is
  `torch.multinomial(score, budget, replacement=False)`. The full author score
  performs additional camera renders, and `full_eval.py` contains scene-specific
  final budgets; only the sampling primitive is suitable for this benchmark.
- RTG-SLAM's RGB-only-looking `colorerror2tilemask` is embedded in a mapper whose
  state transitions and cleanup consume depth, normals, transmission, and
  per-pixel Gaussian indices. Copying only its top-40% mask would not reproduce
  the author method.

The synchronized UTMM/RPNG profile measured densify/prune at only 0.171% and
0.034% of mapping wall time. Therefore a TileGS rasterizer transplant is not
justified as a speed optimization. Local topology remains useful for bounded,
interpretable mutation, not because the current global mutation kernel is the
dominant runtime cost.

## Post-Exp122/123 supervision diagnosis

Source-backed local topology is not the remedy for the unified dense-slot
loss. Exp122 removed only dense-origin native densification statistics: churn
returned almost exactly to control, but PSNR recovered just +0.0141 dB.
Exp123 then preserved aggregate depth/normal loss mass on every replacement;
PSNR changed another -0.0218 dB. The missing signal is the historical
keyframe's view-specific RGB-D coverage, not topology cost or a scalar geometry
weight.

Accordingly, no downloaded local-pruning implementation will be used to make
the aggressive replacement appear viable. The accepted source-backed path is
limited to LPM evidence on already-paid dense work and Taming's bounded
sampling ticket while all geometry-bearing native keyframe renders remain in
the quality base. Any future paper mechanism is first checked against its
downloaded executable code, modality assumptions, license, and fixed-work
contract before an implementation experiment is opened.
