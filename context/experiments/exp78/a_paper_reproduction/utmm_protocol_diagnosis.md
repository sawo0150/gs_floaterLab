# exp78 A2 — UTMM paper/public-source protocol diagnosis

## Question

Why does clean official VIGS reproduce RPNG `table_06` within the preregistered
PSNR/SSIM tolerance while UTMM `fast-straight` and `slow-straight-1` miss the
paper's pre-refinement rendering values?

This card diagnoses the reproduction path.  It does **not** tune VIGS or
gsSLAM, and it does not treat the weaker local vanilla result as evidence that
gsSLAM wins.

## Frozen inputs

- Official repository: `/home/intern/VIGS-SLAM-official-exp78`
- Commit: `22ffe24c6df81d0bf63bd20057565c00c51d2996`
- Official config: `config/utmm.yaml`, `IMU_poseinit_after=15`
- ETH-preprocessed UTMM archive and its native `rgb_timestamp`, `imu_ours`,
  `groundtruth.txt`, and `intrinsics_ours.txt` inputs
- No TensorRT; official PyTorch path and weights
- Map state: before final visual BA and final color refinement
- Paper target, `fast-straight`: 21.98 / .685 / .458
- Paper target, `slow-straight-1`: 20.66 / .669 / .482

## Public-artifact contradictions

The currently published batch runner is not an executable recipe for the
paper's UTMM rendering table:

1. `eval_utmm_mono.py:14` sets `gsmapping = False`; its generated command only
   adds `--gsmapping` when that variable is manually changed.  As published,
   the UTMM batch script produces tracking results but no Gaussian map.
2. `vigs/gaussian/utils/eval_utils.py:39` evaluates
   `stride-5 OR VIGS-keyframe OR final`.  The actual keyframe exclusion at line
   66 is commented out, contrary to the paper's non-keyframe/mapping-disjoint
   description.
3. The paper's union of keyframes from every compared method is not published,
   so its exact rendering UID set cannot be recovered from this repository.
4. `vigs/vigs.py:212-235` performs visual BA, a `final=True` mapping update and
   `gs.finalize()` before its built-in rendering evaluation.  Its comment says
   the current paper result includes that step, while the paper text labels the
   primary rendering result as preceding final global BA/color refinement.
5. The official README itself warns that refactoring, cleaning, optimization,
   environment and GPU differences can change the paper results.  The public
   Git history contains no earlier paper-state implementation to pin instead.

Accordingly, the exact paper-native UTMM rendering invocation is
underdetermined by the public artifacts.  We retain a separate nearest
reproducible arm: clean current official source, mapping explicitly enabled,
and the map captured before `terminate()`.

## Results

### Pre-final current-public source

| Sequence/run | Views | KF overlap | PSNR | SSIM | LPIPS | Paper PSNR gap |
|---|---:|---:|---:|---:|---:|---:|
| fast, seed 0, official-public split | 78 | 17 | 18.0244 | .6740 | .4552 | -3.9556 |
| fast, seed 1, official in-process | 78 | 17 | 18.0311 | .6735 | .4571 | -3.9489 |
| fast, seed 2, official in-process | 78 | 17 | 18.0045 | .6734 | .4567 | -3.9755 |
| **fast, three-seed mean** | 78 | 17 | **18.0200** | **.6737** | **.4563** | **-3.9600** |
| slow-1, seed 0, official-public split | 86 | 12 | 19.1459 | .6083 | .4982 | -1.5141 |

The fast-sequence seed range is only 0.0265 dB.  Its paper-compatible
self-non-KF value is 17.3652 dB for seed 0, so excluding this method's own
keyframes does not close the gap.  The predeclared fixed UID result remains
post-hoc only because 7/68 selected fast views and 6/80 selected slow-1 views
were used by native mapping.

### Cause-isolation checks

| Candidate cause | Evidence | Verdict |
|---|---|---|
| PLY save/load, preprocessing, pose inversion, or metric reimplementation | Fast seed 1 official in-process PSNR 18.031059497 vs reloaded evaluator 18.031059742; absolute difference 0.000000245 dB. SSIM/LPIPS also agree within numerical noise. | Excluded |
| Random seed | Fast seeds 0/1/2 span 18.0045–18.0311 dB. | Excluded as the multi-dB cause |
| Tracking failure | Fast Sim(3) ATE is .9422 cm with 100% Recall@10 cm, better than the paper's 1.20 cm. Slow-1 is .8853 cm/100%, close to the paper's .81 cm. | Not the primary fast rendering cause |
| Stale mapping-view poses | Fast seed 2 tracker↔cached-map pose difference before final BA: .000695 m mean camera-center error and .00247° mean rotation error. | Excluded as the multi-dB cause |
| Missing final visual BA/update | On fast seed 2, visual BA plus the source's 20-step `final=True` map update raises 18.0045→19.1058 dB (+1.1013), but remains 2.8742 dB below the paper target. This state is not the paper-stated pre-final protocol. | Contributes, but insufficient and protocol-mismatched |
| Initialization timing | Fast creates its first map at frame 161/332 and initializes IMU at 259/332; only 16 mapping views receive 115 iterations before capture. Slow-1 ends with 12 KFs, below the official UTMM IMU-init threshold 15. | Real short-sequence stressor; whether the hidden paper implementation handled it differently is unresolvable from public artifacts |
| Exact paper evaluation split | All-method keyframe union/UID list is absent. Early fast views are extremely poor, so an unpublished split can materially change a short-sequence mean. | Unresolved external input, not safe to guess |

The after-BA-before-color diagnostic improves SSIM/LPIPS to .7018/.4131 while
PSNR is still only 19.1058 dB.  This metric-direction mismatch further argues
against forcing a paper match by silently changing the finalization state.

## Decision and next action

- RPNG `table_06` remains a qualified paper-reproduction gate pass.
- Exact UTMM paper-table reproduction is **not proven** by the public release;
  the missing executable mapping recipe and exact evaluation manifest are now
  preserved as source-level limitations.
- Continue all UTMM/RPNG sequences under the explicit label
  `public-source mapping-enabled pre-final`, retaining official-public,
  self-non-KF, and post-hoc fixed-manifest values separately.
- Check the longer frozen UTMM development sequence `ego-drive` next.  It tests
  whether the short-sequence late-initialization effect explains a substantial
  part of the gap without changing any parameter.
- Lane B will not reuse these post-hoc views.  It must prevent every fixed UID
  from entering mapping before running either method.

## Evidence

- Machine-readable summary: `evidence/utmm_protocol_diagnosis.json`
- Fast seed 0 and slow-1 seed 0:
  `results/experiments/exp78/a_paper_reproduction/native_official_22ffe24/utmm/`
- Fast seed 1 exact evaluator parity:
  `results/experiments/exp78/a_paper_reproduction/diagnostics/utmm_fast_straight_seed1_inprocess/`
- Fast seed 2 pose/final-BA isolation:
  `results/experiments/exp78/a_paper_reproduction/diagnostics/utmm_fast_straight_seed2_after_ba_before_color/`

