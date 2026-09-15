# exp78 A4 — clean official VIGS pre-final reproduction, all 16 + TensorRT probes

Date: 2026-09-11

## Question

How closely does the only released official VIGS source reproduce the paper's
pre-final RPNG 8-sequence and UTMM 8-sequence rendering/tracking tables on the
paper's RTX 5090 class hardware, before using vanilla VIGS as a gsSLAM
baseline?

## Frozen conditions

- Official source: `/home/intern/VIGS-SLAM-official-exp78`, commit
  `22ffe24c6df81d0bf63bd20057565c00c51d2996`.
- Official source/config modules were not patched.  A separate driver stops
  before `terminate()` so final global BA and final color refinement are both
  absent.
- Official processed ETH RPNG/UTMM inputs, official calibration/config and
  official pretrained weights.
- Official published RTX5090 environment versions: PyTorch `2.8.0+cu128`,
  CUDA `12.8`, torchmetrics `1.8.2`, OpenCV `4.12.0`, NumPy `2.1.2`.
- The all-16 rendering table is the **PyTorch inference** arm.  TensorRT is
  isolated in a separate runtime root and tested on four representative
  probes because the paper runtime section explicitly says TensorRT was
  deployed.
- Rendering parity uses the released evaluator condition
  `idx % 5 == 0 OR VIGS keyframe OR final`.  The self-non-KF diagnostic removes
  VIGS's own keyframes, but cannot reconstruct the paper's unpublished union of
  every method's non-keyframes.

Runner and machine evidence live under
`results/experiments/exp78/a_paper_reproduction/native_official_22ffe24/`.
Machine-readable audits are
`evidence/all16_seed0_analysis.json` and
`evidence/all16_seed0_with_table08_valid_retry.json`.  TensorRT evidence is
`evidence/trt_readme_dynamic_validation.json` and
`evidence/trt_readme_dynamic_probe_analysis.json`; raw runs are under
`results/experiments/exp78/a_paper_reproduction/native_official_22ffe24_trt_readme_dynamic/`.

## Rendering results

The primary table below is the released public evaluator result.  Deltas are
local minus paper; lower LPIPS is better.  `table08` shows both the failed
seed0 and the valid seed1 retry instead of silently selecting one.

| Dataset | Sequence | Paper PSNR | Local PSNR | Δ dB | Local SSIM | Local LPIPS | Paper ATE cm | Local ATE cm | Recall@10cm |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| RPNG | table01 | 23.41 | 24.358 | +0.948 | .8072 | .1879 | 1.31 | 1.300 | 100% |
| RPNG | table02 | 20.84 | 21.507 | +0.667 | .7231 | .2495 | 1.57 | 1.578 | 100% |
| RPNG | table03 | 20.71 | 21.571 | +0.861 | .7087 | .2697 | 1.22 | 1.206 | 100% |
| RPNG | table04 | 21.97 | 20.927 | -1.043 | .7102 | .2044 | 1.75 | 1.875 | 100% |
| RPNG | table05 | 21.44 | 21.608 | +0.168 | .6721 | .2861 | 1.28 | 1.561 | 100% |
| RPNG | table06 | 23.47 | 23.038 | -0.432 | .7622 | .2603 | 1.38 | 1.547 | 100% |
| RPNG | table07 | 24.81 | 25.486 | +0.676 | .8446 | .1742 | 1.08 | 1.064 | 100% |
| RPNG | table08 seed0 | 21.05 | 22.429* | +1.379 | .7728* | .3076* | 3.86 | 151.155 | 5.12% |
| RPNG | table08 seed1 | 21.05 | 22.186 | +1.136 | .7621 | .2760 | 3.86 | 3.413 | 100% |
| UTMM | ego1 | 20.05 | 17.534 | -2.516 | .5885 | .3796 | 1.81 | 4.443 | 100% |
| UTMM | ego2 | 20.39 | 19.350 | -1.040 | .6552 | .3200 | .93 | 2.238 | 100% |
| UTMM | ego-drive | 21.54 | 20.325 | -1.215 | .6647 | .3772 | 1.45 | 5.176 | 100% |
| UTMM | fast | 21.98 | 18.024 | -3.956 | .6740 | .4552 | 1.20 | .942 | 100% |
| UTMM | slow1 | 20.66 | 19.146 | -1.514 | .6083 | .4982 | .81 | .885 | 100% |
| UTMM | slow2 | 21.92 | 19.173 | -2.747 | .6809 | .4680 | .93 | .915 | 100% |
| UTMM | square1 | 19.98 | 20.667 | +.687 | .7014 | .3489 | 2.17 | 8.811 | 84.34% |
| UTMM | square2 | 20.42 | 20.764 | +.344 | .6948 | .3637 | 16.61 | 11.995 | 73.97% |

`*` The table08 seed0 map is not a valid paper reproduction.  Its tracker pose
first jumps from a normal meter-scale trajectory to a `32.1 km` seed-to-seed
translation difference at input frame 7930, then grows to roughly `1e9 m`.
The cached map and final tracker state disagree by mean/max
`2195.7/38992.1 m`, so the superficially good image metric cannot be used.

Dataset means:

| Dataset/selection | Local PSNR/SSIM/LPIPS | Paper | Parity tolerance result |
|---|---|---|---|
| RPNG raw seed0 | 22.615 / .7501 / .2425 | 22.21 / .723 / .314 | PSNR pass; SSIM/LPIPS symmetrically outside but better direction |
| RPNG with only failed table08 retried as seed1 | **22.585 / .7488 / .2385** | 22.21 / .723 / .314 | PSNR `+0.375 dB`, pass; SSIM/LPIPS outside but better direction |
| UTMM seed0 | **19.373 / .6585 / .4013** | 20.87 / .687 / .441 | PSNR `-1.497 dB` fail; SSIM `-.0285` fail; LPIPS better but outside symmetric parity |

The self-non-KF best-effort means are RPNG
`22.687/.7510/.2409` for raw seed0 and UTMM
`19.195/.6541/.4066`.  These do not repair the UTMM gap and are not an exact
paper split.

## Tracking, KF, runtime and memory findings

- RPNG Table 9 was previously easy to misread: `211,389,...,227` is the
  ORB-SLAM3 row.  The VIGS row is
  `250,349,525,427,341,232,223,579`.  Local seed0 matches exactly on
  table01/02/04/05/06/07, differs by one on table03, and failed at 646 on
  table08.  The valid table08 seed1 is exactly 579.
- Valid table08 seed1 agrees with seed0 to millimeters until the failed seed0's
  sudden frontend/VI state jump.  It ends at ATE `3.413 cm`, Recall 100%, map
  pose mean/max error `2.03/28.46 mm`, and `579 KF`; this proves the seed0
  failure is an official long-sequence numerical/concurrency instability, not
  a dataset/config-wide KF policy mismatch.
- RPNG PyTorch mapping FPS is below the paper on every sequence by
  `0.59–3.55 FPS`; table08 seed0 is excluded from this interpretation.  The
  missing TensorRT runtime arm is therefore necessary before runtime parity is
  judged.
- RPNG peak allocated memory is within roughly `-0.64 to +0.45 GiB` of Table 9
  on table01–07.  Valid table08 seed1 allocates `10.38 GiB`, about `+0.50 GiB`
  over the paper's 9.88 GiB.
- UTMM is not a mapping-only failure claim: ego1/ego2/ego-drive/square1 have
  material ATE gaps, and square1/2 have incomplete Recall.  Fast/slow1/slow2
  show that rendering can still miss by `1.5–4.0 dB` even when ATE is close,
  isolating a map initialization/supervision deficit on short sequences.

## Official README TensorRT arm

Five dynamic FP16 engines were built with the official README profiles in a
separate runtime root.  Direct module validation against the official PyTorch
weights gives maximum relative RMSE `0.236%` for fnet, `0.286%/0.300%` for the
frontend/PGBA update outputs, `0.092%` for Omnidata depth and `0.043%` for
normal; every tested output has cosine at least `.9999956` and is finite.
Engine identities, ONNX hashes and profiles are frozen in the runtime-root
README.

The sequence probes below use seed0 except that the valid PyTorch table08
control is seed1.  This exception is explicit: PyTorch seed0 is the invalid
trajectory described above, so comparing its wall time or image metric would
reward a failed tracker.

| Sequence | PT→TRT PSNR | PT→TRT ATE cm | PT→TRT KF | PT→TRT seconds | Speedup | Allocated Δ GiB |
|---|---:|---:|---:|---:|---:|---:|
| UTMM fast | 18.024→18.050 | .942→.936 | 17→17 | 23.37→18.63 | 1.254× | -0.861 |
| UTMM ego-drive | 20.325→20.273 | 5.176→5.178 | 85→85 | 102.12→92.05 | 1.109× | -1.272 |
| RPNG table06 | 23.038→23.076 | 1.547→1.554 | 232→232 | 299.06→281.13 | 1.064× | -1.626 |
| RPNG table08 valid PT seed1→TRT seed0 | 22.186→22.124 | 3.413→3.401 | 579→579 | 875.92→804.56 | 1.089× | -1.282 |

Across these probes the absolute PSNR change is at most `.061 dB`; SSIM at
most `.0030`, LPIPS at most `.0054`, and ATE at most `.0121 cm`.  Thus
TensorRT cannot explain the UTMM paper gap of `1.5 dB` mean or the individual
`1.2–4.0 dB` gaps.  It does recover `6.4–25.4%` sequence-level speed and saves
`0.86–1.63 GiB` peak allocated memory.

Most importantly, table08 TensorRT seed0 crosses the exact frame-7930 failure
point, finishes with the paper's exact `579 KF`, ATE `3.401 cm`, Recall 100%,
and map/tracker center error mean/max `2.00/28.60 mm`.  Because PyTorch seed1
also succeeds with essentially the same result, this is evidence of
execution-path-sensitive numerical/concurrency instability in the released
long-sequence pipeline, not evidence that TensorRT deterministically fixes a
defined algorithmic bug.

## Source-level reproducibility limitation

Exact paper-state UTMM reproduction cannot be reconstructed from the released
artifact alone:

1. Git history contains only the initial license, one large post-paper code
   import, and a README-only commit; there is no paper-state source commit.
2. The official README explicitly warns that large refactoring, cleanup,
   optimization, environment and GPU differences can change paper results.
3. The released `eval_utmm_mono.py` has `gsmapping=False`, so it contains no
   invocation capable of producing paper Table 19.
4. The released evaluator includes VIGS mapping keyframes, whereas the paper
   says rendering uses frames that are not keyframes of any compared method and
   were unused for mapping.  The all-method KF union is not published.
5. The released `terminate()` performs final BA, map pose propagation and final
   color updates, while the paper tables are described as pre-final.  The clean
   driver has to intercept this state because the official batch scripts do not
   expose it.

These limitations do not license a weak vanilla baseline.  The closest public
source result is preserved in full, and the TensorRT probes are kept separate.
Fair gsSLAM claims use the predeclared mapping-disjoint Lane-B
manifests and identical frozen tracker packets, not these paper-table splits.

## Decision

- **RPNG rendering/tracking reproduction:** sufficiently restored for the
  goal's paper-value gate after disclosing the table08 failure/retry and metric
  direction.  PSNR average is within `±0.5 dB`, and TensorRT table06/table08
  retain the exact paper KF counts with valid tracking.
- **UTMM exact reproduction:** not restored by the public PyTorch path; the
  source-level missing invocation/split/paper-state limitations are confirmed,
  and TensorRT changes the representative results by only `-.051/+0.026 dB`,
  ruling it out as the missing paper-result explanation.
- **Lane-A verdict:** complete as a qualified public-artifact reproduction:
  RPNG passes the stated PSNR tolerance; UTMM is an honestly recorded
  non-reproduction whose exact paper state/split/invocation is absent from the
  only public artifact.  It must not be relabelled as exact parity.
- **Next:** freeze identical tracker packets for mapping-only Lane B.  Do not
  tune gsSLAM against the invalid table08 seed0 trajectory or present the weak
  UTMM public-source run as the paper's exact baseline.
