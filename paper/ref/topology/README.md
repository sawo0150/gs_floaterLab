# Local and budgeted topology references

Last reviewed: 2026-09-24

This directory holds the papers used to design a causal local-topology service
for the online mapper.  The selection criterion is practical relevance to at
least one of: local candidate discovery, bounded growth, safe removal, online
validity, or mutation cost.  A paper being listed here does not mean that its
protocol is directly comparable with our strict streaming benchmark.

## Local copies

| File | Primary source | SHA-256 | Main reason to keep it |
|---|---|---|---|
| `lpm_cvpr2025_arxiv_2406.04251.pdf` | [LPM, CVPR 2025](https://openaccess.thecvf.com/content/CVPR2025/html/Lee_LPM_Localized_Point_Management_for_Improving_Gaussian_Splatting_CVPR_2025_paper.html) | `469ee09cccbdd3aba84881d892ecb36d56b67cb2741725ab70b46164505f693a` | Multi-view error zones and local candidate management |
| `tilegs_aaai2026.pdf` | [TileGS, AAAI 2026](https://ojs.aaai.org/index.php/AAAI/article/view/37997) | `ccb7bbed88e30c3ae9cc28372aa36705d39a1289a2328ff7dd3b9be6ec4b02e0` | Persistent tile-quality evidence assigned to visible Gaussians |
| `splatmap_2501.07015.pdf` | [SplatMAP](https://arxiv.org/abs/2501.07015) | `a1ee00e9ef132de7814c2051e176797800d650687053dd0af6608073466e4d0a` | Online valid/invalid point transitions for birth and removal |
| `geometry_aware_online_mapping_2608.14902.pdf` | [Geometry-Aware Online Mapping](https://arxiv.org/abs/2608.14902) | `f390962687703b5c75190d917147f5e43bd6e707c61c0d6b39351a90ea5f6769` | Camera-footprint initialization, clone opacity correction, residual-backed birth under an online mapping budget |
| `taming_3dgs_2406.15643.pdf` | [Taming 3DGS](https://arxiv.org/abs/2406.15643) | `ebb0fc193915f8455b8784c47e33d034df548e9c1b8dfddaf62dcbd113c44a04` | Exact constructive growth budget without prune-induced memory peaks |

Related PDFs already stored elsewhere in the repository:

- `paper/ref/view_selection/gaussian_slam_2312.10070v1.pdf`
- `paper/ref/view_selection/rtg_slam_2404.19706v1.pdf`
- `paper/ref/convergence/edgs_cvpr2026.pdf`

Additional primary sources inspected online:

- [GAD-SLAM: Active densification and visibility culling](https://doi.org/10.1016/j.displa.2026.103476)
- [Real-Time LiDAR Gaussian Splatting SLAM via Geometry-Aware Covariance Coupling](https://arxiv.org/abs/2607.04127)

## Official implementation snapshots

Paper reading is used to assess the idea and protocol.  Any code port must be
based on an inspected author implementation, not reconstructed from prose.
The following repositories are cloned outside the working repositories so
their licenses and histories stay separate:

| Method | Local clone | Pinned inspected commit |
|---|---|---|
| LPM | `/home/intern/gs_topology_references/lpm` | `7c060267cf55df76992e9ef2b6df42133ba9349f` |
| TileGS | `/home/intern/gs_topology_references/tilegs` | `7f109a403ed522ba5ec7610f3d4778c363b68b11` |
| LiDAR GS-SLAM | `/home/intern/gs_topology_references/lidar_gs_slam` | `04b916180926878fc6b474970b38d6c12eb84ec3` |
| Taming 3DGS | `/home/intern/gs_topology_references/taming_3dgs` | `fd0f7d9edfe135eb4eefd3be82ee56dada7f2a16` |
| Gaussian-SLAM | `/home/intern/gs_topology_references/gaussian_slam` | `eaec10d73ce7511563882b8856896e06d1f804e3` |
| RTG-SLAM | `/home/intern/gs_topology_references/rtg_slam` | `49dada148551961e2dee38040a4f760fa1b0f01d` |

No public author implementation was found on 2026-09-24 for SplatMAP,
GAD-SLAM, or Geometry-Aware Online Mapping.  Their ideas may motivate an
experiment, but their algorithms will not be presented as code-derived or
ported until an official implementation is available.  In particular, the
Geometry-Aware Online Mapping paper says that code will be released; that is
not the same as code being available now.

## Conclusions relevant to this repository

1. **Local score is not automatically local computation.** LPM and TileGS
   select local candidates, but their public implementations still create
   map-wide masks/buffers or rebuild global tensors.  We must measure optimizer
   mutation and compaction separately from candidate selection.
2. **Residual birth is not monotonically beneficial.** Geometry-Aware Online
   Mapping reports lower averages after adding its Error-guided Densification
   to TPD+CS: TUM RGB-D `21.91 -> 21.85 dB` and Replica `34.72 -> 34.39 dB`.
   The useful first controls are camera-footprint scale and transmittance-
   preserving clone opacity; residual birth needs a bounded ticket and its own
   ablation.
3. **A fixed early/late phase is incompatible with an unknown stream horizon.**
   GAD-SLAM and several offline methods use a fixed densification period.  We
   may reuse their evidence signals, but transitions must depend on repeated
   observations and relative capacity/service state rather than a scene-tuned
   frame or iteration cutoff.
4. **The closest opportunity is a causal topology service.** Couple
   under-served online views to persistent local evidence, bound mutations per
   service opportunity, preserve the recent-keyframe floor, and log exact
   clone/split/prune churn and latency.  This is more specific than claiming
   local error-driven densification alone.

The implementation and experiment sequence is frozen in
`/home/intern/VIGS-SLAM-paper-full/docs/LOCAL_TOPOLOGY_TWO_TRACK_PLAN.md`.
