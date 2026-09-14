# exp78 A — clean paper-native VIGS reproduction

## Frozen source and first gate

- Official source: `/home/intern/VIGS-SLAM-official-exp78`
- Commit: `22ffe24c6df81d0bf63bd20057565c00c51d2996`
- First gate: RPNG `table_06`, seed 0, official `config/rpng.yaml`, official
  calibration and DROID/Omnidata weights, PyTorch inference, no TensorRT.
- Output: `results/experiments/exp78/a_paper_reproduction/`
- Runner: `benchmarks/online_gs/run_exp78a_vigs_paper_native.sh`
- Driver: `benchmarks/online_gs/exp78_vigs_native_driver.py`
- Evaluation: `benchmarks/online_gs/exp78_evaluate_vigs_ply.py`

The driver saves `3dgs_before_final.ply` and trajectories before calling
`VIGS.terminate()`.  Thus final global BA and final color refinement are not
performed.  Full-trajectory filling is run after the final input only to obtain
poses for Lane-A rendering evaluation and is explicitly recorded in telemetry.

## Evaluation-definition discrepancy

The paper says rendering evaluation excludes every frame used as a keyframe by
any compared method and every mapping view.  The public implementation instead
uses this inclusion condition in `vigs/gaussian/utils/eval_utils.py`:

```python
if idx % 5 != 0 and idx not in kf_idx and i != len(gtimages) - 1:
    continue
```

Its subsequent keyframe exclusion is commented out.  Therefore the public code
evaluates `stride-5 OR VIGS-keyframe OR final`, including VIGS mapping views.
The union of all competing methods' keyframes is not published, so the exact
paper split cannot currently be reconstructed from the repository alone.

Each saved map is consequently reported under three labels:

1. `official_public`: public implementation exactly, including keyframes.
2. `paper_compatible_self_non_kf`: `(stride-5 OR final) AND NOT VIGS-keyframe`;
   a best effort that cannot exclude unpublished other-method keyframes.
3. `predeclared_fixed_manifest_posthoc`: the Lane-B fixed UID list.  For a
   native Lane-A run this is diagnostic only because those views were not
   prevented from entering mapping.

## Paper targets and gate

| Scope | PSNR | SSIM | LPIPS | Reproduction tolerance |
|---|---:|---:|---:|---:|
| RPNG `table_06` | 23.47 | 0.775 | 0.304 | ±0.5 dB / ±0.02 / ±0.03 |
| RPNG mean | 22.21 | 0.723 | 0.314 | same |
| UTMM mean | 20.87 | 0.687 | 0.441 | same |

## Run log

- Attempt 0 processed through frame 2,766/2,767 but failed while deserializing
  the last queued tensor after the producer exited.  This was a driver IPC
  lifetime race, not an official VIGS failure; no map/result was saved.  The log
  is preserved as `run_attempt0_ipc_failed.log`.
- The driver now keeps the producer alive until the consumer acknowledges the
  last tensor.  The same gate reran successfully without modifying official
  source.

## RPNG `table_06`, seed 0 result

| Evaluation label | Views | VIGS KF overlap | PSNR | SSIM | LPIPS |
|---|---:|---:|---:|---:|---:|
| Paper target | — | 0 by definition | 23.470 | 0.7750 | 0.3040 |
| Official public source | 742 | 232 | 23.038 | 0.7622 | 0.2603 |
| Paper-compatible self-non-KF | 510 | 0 | 23.006 | 0.7646 | 0.2564 |
| Predeclared fixed, post-hoc diagnostic | 555 | 45 | 22.971 | 0.7633 | 0.2571 |

PSNR is -0.432/-0.464 dB and SSIM is -0.0128/-0.0104 from the paper target,
inside the preregistered tolerances.  LPIPS is 0.044–0.048 lower (better) than
the paper but outside the symmetric ±0.03 reproduction band.  Because the
paper's union-of-all-methods keyframe split is unavailable, this is a qualified
first-gate pass, not a claim of exact table reproduction.

The run produced 232 keyframes and 174,349 Gaussians.  Visual inspection of the
paper's runtime Table 9 confirms that VIGS also has 232 keyframes on `table_06`
(238 belongs to the preceding ORB-SLAM3 row), so the keyframe count reproduces
exactly.  Sim(3) ATE is 1.5473 cm over 231 matched poses with 100% Recall@10 cm,
versus the paper's 1.38 cm entry.

Native tracking+mapping took 299.063 seconds, or 9.252 FPS.  Peak CUDA allocated
and reserved memory were 8,583,615,488 and 10,976,493,568 bytes.  The current
machine has an RTX 5090 and i9-12900; the paper reports an RTX 5090 and
i7-14700K, so native throughput is descriptive rather than hardware-matched.

Evidence is under
`results/experiments/exp78/a_paper_reproduction/native_official_22ffe24/rpng/table_06/seed0/`.

## UTMM protocol diagnosis

The first two UTMM pilots do not reproduce the paper despite good tracking:
`fast-straight` is 18.024/.6740/.4552 versus 21.98/.685/.458 and
`slow-straight-1` is 19.146/.6083/.4982 versus 20.66/.669/.482.  Three
`fast-straight` seeds have a 0.0265 dB range, and the unmodified official
in-process evaluator agrees with the saved-PLY evaluator within 0.00000025 dB.
Visual BA plus the source's 20-step final mapping update recovers 1.101 dB but
still leaves a 2.874 dB gap and is not the paper-stated pre-final state.

The published UTMM batch runner has `gsmapping=False`, the public renderer
includes mapping keyframes, the paper's all-method keyframe union is absent,
and the current `terminate()` evaluation order conflicts with the paper's
pre-final description.  Exact paper-native UTMM rendering is therefore
underdetermined by the public artifacts.  We continue with the explicitly
labelled clean public-source, mapping-enabled, pre-final arm instead of hiding
the discrepancy.  See
[A2 diagnosis](utmm_protocol_diagnosis.md) and
[machine-readable evidence](evidence/utmm_protocol_diagnosis.json).

The frozen longer-sequence check `ego-drive` starts mapping/IMU much earlier
and narrows the rendering gap, but two seeds remain at 20.351 dB mean versus
the paper's 21.54 dB.  More importantly, pre-final ATE is 5.176/5.219 cm versus
the paper's 1.45 cm; final BA improves it only to 3.328 cm and worsens rendering
by .214 dB.  This sequence requires tracking-parity or mapping-only isolation
before any mapping optimization is interpreted.  See
[A3 `ego-drive`](utmm_ego_drive_reproduction.md).

## All-16 closure and TensorRT

The clean public-source PyTorch arm is complete on RPNG 8 + UTMM 8.  With the
only invalid trajectory (`table_08` seed0) replaced by the disclosed seed1
retry, RPNG is `22.585/.7488/.2385` versus the paper
`22.21/.723/.314`: PSNR passes the preregistered ±0.5 dB tolerance.  UTMM is
`19.373/.6585/.4013` versus `20.87/.687/.441`: PSNR and SSIM do not reproduce.

Official-README-profile TensorRT engines were independently built and
numerically validated, then probed on UTMM fast/ego-drive and RPNG
table06/table08.  Their PSNR differs from valid PyTorch controls by at most
`.061 dB`, so TensorRT cannot explain the UTMM paper gap.  It speeds the four
sequences by `1.064–1.254×`; table08 seed0 also completes with the exact paper
`579 KF`, ATE `3.401 cm`, and no catastrophic pose jump.  The official source
contains no paper-state commit, UTMM mapping invocation, or all-method
non-keyframe union, so Lane A closes as a **qualified public-artifact
reproduction**, not an exact UTMM restoration.

Full card: [A4 all-16 + TensorRT](vigs_all16_pytorch_reproduction.md).
