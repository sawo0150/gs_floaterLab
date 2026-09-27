# Official-code audit for online local topology

Date: 2026-09-24

This note records what the downloaded implementations actually do.  It is the
implementation source of truth; paper descriptions are kept in `README.md` for
method context.  Line numbers refer to the pinned commits in that file and may
move if a reference clone is updated.

## Porting rule

- Read a paper to decide whether an idea is relevant.
- Read the author repository to determine the executed operator, defaults,
  allocations, and edge cases.
- Port only the minimal mechanism into VIGS-SLAM, with an attribution comment
  and license check.  Do not copy a paper-only algorithm whose author code is
  unavailable.
- Keep each imported mechanism behind an independent switch until its
  render-matched held-out ablation passes.

## Code-derived findings

### Gaussian-SLAM — best first reference for bounded residual birth

Source: `/home/intern/gs_topology_references/gaussian_slam`, commit
`eaec10d73ce7511563882b8856896e06d1f804e3`, MIT.

- `src/entities/mapper.py:48-71` builds a current-view seeding mask from low
  rendered alpha or a large positive depth residual.
- `mapper.py:89-108` back-projects observed depth and caps a normal frame to
  `new_frame_sample_size` samples.
- `mapper.py:185-196` restricts duplicate checking to the current camera
  frustum, then rejects candidate points within `new_points_radius` using the
  existing map.
- It does not use ADC clone/split in its online `Mapper`.  It grows by explicit
  observed-depth births and prunes low-opacity rows at the middle and end of
  each submap optimization (`mapper.py:153-159`).
- The released dataset configs do **not** use a 1,024-point normal-frame cap:
  ScanNet/TUM use 30,000, ScanNet++ uses 100,000, and Replica uses unlimited
  eligible pixels.  Any smaller VIGS ticket is an adapter choice, not an
  implementation detail that can be attributed to Gaussian-SLAM.

This is the cleanest code base for an initial VIGS experiment: replace blanket
birth expansion with a **bounded under-coverage/depth-residual birth mask**,
while retaining VIGS pose/depth provenance.  The fixed submap schedule and
mid/end prune cadence are not portable to our unknown-horizon stream.

Execution corrected that initial replacement recommendation. Exp99's 1,024
ticket lost 2.51 dB versus R4; Exp100 matched R4's full-view causal target and
still lost 2.00 dB because residual-only replacement removed useful blanket
capacity. Exp101 preserved the R4 birth/RNG and added the author-code operator
as a separate residual supplement: it retained quality (+0.024 dB versus R4,
+1.645 dB versus vanilla) but cost +52% final Gaussians and +11% mapping wall
time. The evidence-backed composition rule is therefore **supplement, not
replacement**, followed by explicit evidence/budget rationing.

### RTG-SLAM — reference for maturity state and partial rendering

Source: `/home/intern/gs_topology_references/rtg_slam`, commit
`49dada148551961e2dee38040a4f760fa1b0f01d`, GPL-3.0.

- `SLAM/multiprocess/mapper.py:714-794` adds points at high transmission
  (uncovered pixels) and at color/depth residual pixels, with sample counts
  proportional to the eligible population.
- `mapper.py:797-826` rejects candidates already covered by unstable
  Gaussians using a KNN/radius test.
- `mapper.py:143-208` renders masks/tiles occupied by unstable Gaussians and
  optimizes a separate unstable point cloud.
- `mapper.py:252-271` promotes sufficiently observed rows into a stable point
  cloud.  `mapper.py:297-333` removes over-large or long-unstable rows.

The useful mechanism is persistent per-Gaussian maturity, not the exact code:
GPL code should not be copied into a differently licensed project, and the
reference relies on RGB-D maps and two physically separate point clouds.  A
clean-room VIGS implementation can reproduce the high-level state machine
using existing `n_obs`, stable point IDs, and causal service counts.

### LPM — local candidate logic, but still global mutation

Source: `/home/intern/gs_topology_references/lpm`, commit
`7c060267cf55df76992e9ef2b6df42133ba9349f`, research-only 3DGS license.

- `lpm/lpm.py:48-54` precomputes paired training views with feature matching;
  this is not causal and is too heavy for the online path.
- `lpm.py:71-77` converts a current rendering error and matched regions into
  3D zones.
- `lpm.py:81-129` keeps normal ADC candidates and relaxes the gradient
  threshold to 0.5x only inside those zones.
- `lpm.py:131-154` adds an equal-count global low-opacity removal on top of the
  ordinary global prune, then calls the ordinary optimizer-tensor mutation.
- `lpm.py:179-203` constructs a full-length map mask for every zone.

Thus LPM supports the scientific claim that persistent local errors may define
candidate regions, but its implementation is not a real-time local mutation
service and must not be dropped into VIGS unchanged.

### TileGS — evidence counters are useful; the released CUDA path is not

Source: `/home/intern/gs_topology_references/tilegs`, commit
`7f109a403ed522ba5ec7610f3d4778c363b68b11`, research-only 3DGS license.

- `submodules/diff-gaussian-rasterization/cuda_rasterizer/forward.cu:511-535`
  increments per-Gaussian appearance and low-SSIM hit counters for the
  Gaussians contributing to a tile, and decrements hits above SSIM 0.9.
- The CUDA implementation uses SSIM 0.5 as the low-quality boundary, which is
  not the paper's stated 0.6 setting.
- `forward.cu:564-604` allocates and frees two full-resolution grayscale arrays
  plus a tile SSIM array on every analysis call.
- The released kernel launch/indexing at `forward.cu:560-582` uses a 2D grid
  while `compute_ssimCUDA` derives the tile index from x only; its contributor
  loop at `forward.cu:526` uses a comma expression in the condition.  These
  details require independent validation before any reuse.

We will not port this CUDA code.  The transferable part is a small persistent
evidence record updated from outputs already produced by the VIGS rasterizer.

### Taming 3DGS — reference for explicit mutation tickets

Source: `/home/intern/gs_topology_references/taming_3dgs`, commit
`fd0f7d9edfe135eb4eefd3be82ee56dada7f2a16`, MIT additions over upstream
3DGS components.

- `utils/taming_utils.py:40-91` re-renders a list of offline cameras and builds
  an all-view, all-Gaussian importance matrix; this is not an online hot-path
  operator.
- `scene/gaussian_model.py:459-505` samples clone/split parents without
  replacement from an explicit budget.
- `gaussian_model.py:505-546` divides the requested population increment
  between clone and split candidates and prunes only a sampled portion of the
  ordinary prune mask.
- `utils/taming_utils.py:100-117` derives a complete offline growth trajectory
  from a final count/multiplier and known densification horizon.  The supplied
  benchmark script also contains scene-specific budgets.

We can reuse the **bounded without-replacement parent selection** structure.
We cannot reuse the final scene capacity schedule because our stream horizon
is unknown and scene-specific capacity is forbidden.

### LiDAR GS-SLAM — current-view bounded pixel birth

Source: `/home/intern/gs_topology_references/lidar_gs_slam`, commit
`04b916180926878fc6b474970b38d6c12eb84ec3`, MIT.

- `mp_Mapper.py:186-260` selects valid low-alpha pixels, samples a fixed
  percentage using normalized depth-gradient probabilities, back-projects
  them, and appends Gaussians.
- `mp_Mapper.py:535-560` still combines that operator with periodic global ADC
  and a hard-coded plane-management start/frequency of 300 iterations.
- The plane-aware selection/removal depends on LiDAR covariance geometry and
  is not directly meaningful for current Aria RGB supervision.

The low-alpha candidate path is another executable precedent for bounded
current-view birth.  Its fixed percentage and hard-coded phase are not carried
over.  If used, candidate count must be controlled by the common physical-work
budget and online evidence, not image size or elapsed iteration.

## Initial implementation choice

After Exp95 establishes the unchanged R4 topology ledger, the first code
change is a small, independently switched operator based on the MIT
Gaussian-SLAM/LiDAR patterns:

1. use the current causal render's under-coverage and trustworthy positive
   depth-residual mask;
2. sample at most a common per-opportunity ticket without replacement;
3. back-project with VIGS's online depth and pose only;
4. reject births already covered by a current-frustum radius check;
5. append rows, but do not enable a new hard-prune policy in the same test.

Exp98--101 completed that isolation. ERCB and dense views should now be
connected by allowing a serviced historical view to nominate existing
Gaussian candidates from gradients already produced by its paid render. Since
dense RGB has no trustworthy depth, it must not back-project new geometry.
The implementation precedent is TileGS's persistent per-Gaussian low-quality
evidence plus Taming 3DGS's explicit without-replacement mutation ticket; the
released TileGS CUDA kernel itself is not reused. This keeps the source of a
quality change identifiable and avoids inventing dense depth.
