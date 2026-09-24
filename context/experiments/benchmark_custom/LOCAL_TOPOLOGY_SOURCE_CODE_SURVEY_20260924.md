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
