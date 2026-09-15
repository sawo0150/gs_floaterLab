# exp78 C1 — active-path Aria overfit audit

Date: 2026-09-11

## Question

Which parts of the current gsSLAM benchmark recipe are literal Aria
dependencies, which are dataset-generic mechanisms tuned only on Aria, and
which apparently suspicious frame/finalization paths are actually inactive in
the current strict benchmark arm?

This is a source/config audit, not a quality experiment.  The active arm audited
here is the exp77-E2 fixed-1x, sensor-EOS zero-tail runner with reserve `0 ms`.
The repository is intentionally dirty and was not modified or reverted for the
audit.

## Classification

| Candidate | Active classification | Evidence and consequence |
|---|---|---|
| `aria1253_content_curve.json` | **Active literal Aria dependency** | Both RPNG and UTMM configs set `adaptive_density: true` and name the Aria-1253 curve. The source loads that file inside the PPM birth path and uses its Sobel anchors to scale birth count and per-lineage caps. |
| Resolution/contrast dependence of the curve | **Active transfer defect** | The statistic is the raw mean of 8-bit Sobel magnitude: it is not normalized by image scale, contrast distribution, or online scene statistics. The Aria fit uses p10/p90 `22.361/44.043`; 181 unique RPNG table06 mapping frames have Sobel min/mean/max `29.495/68.652/106.913`. Their inferred multiplier is min/mean/max `1.127/2.291/3.0`, with 20 frames at the hard `3x` cap. |
| PPM sampling | **Active generic method, Aria-only empirical validation** | PPM itself is causal and uses only the current arrived RGB/depth. It is not a literal Aria branch, but its adoption evidence and sampling budget were selected on Aria. Do not remove it together with the bad curve: the matched table06 ablation already worsened PSNR by about `0.337 dB` when adaptive density was disabled. |
| `pcd_downsample=256`, init `64`, growth allowance `2` | **Active generic constants, Aria-tuned** | They directly control every keyframe's birth budget. They differ from official VIGS `64/32` and are not normalized by pixel count, observed surface area, sequence duration, or available wall-clock budget. |
| `n_global_views=6`, Gaussian window `10` | **Active generic constants, Aria-tuned** | They determine views rasterized per frontier map call. `6` was selected as an Aria speed/quality improvement; it is not a dataset name check, but cost and revisit coverage change with FPS, resolution, KF density, and sequence length. |
| `init_itr_num=600` and `--mapping_after_imu_init` | **Active generic policy, Aria-tuned** | Initial mapping work is reduced from official `1050` and all Gaussian birth is delayed until online metric IMU initialization. The latter avoids creating a map that is discarded at the scale reset, but on short UTMM sequences it also leaves little post-init time. It must be expressed against causal initialized duration/work capacity, not a fixed Aria success assumption. |
| Tracker overrides | **Active generic constants, Aria-tuned** | The final-v7 runner overrides config with frontend window `15`, radius `2`, motion threshold `2.6`, and frontend iterations `2/0`. These differ from the paper-native tracker and confound mapping conclusions until the frozen-packet lane is used. |
| Dense replay scheduler | **Active generic mechanism, capacity-sensitive** | Pose-active/archive plus work-credit admission, dense-only replay, adaptive viewset, trajectory-filler poses, and a fixed replay seed are active. The logic is causal, but its realized service depends on KF interval statistics and available GPU idle time. |
| GPU tracking reserve | **Active hardware/time constant** | The 5090 profile defaults to `40 ms`; exp77-E2 explicitly overrides it to `0 ms`. `40 ms` is longer than a 30 FPS benchmark frame interval and previously eliminated overlap admission, while it did not do so on 20 FPS Aria. An absolute reserve is therefore an FPS-conditioned transfer defect, even though the current E2 value is neutralized to zero. |
| Replay batch/iteration/queue sizes | **Active hardware-tuned constants** | RTX5090 uses 4 replay iterations, batch 1, idle batch 1, dedicated stream, and packed slack; mapping config queue size is 2. These are not literal scene checks but must be normalized or profiled per hardware/frame deadline. |
| Absolute freeze/start/PGBA cutoffs | **Implemented but inactive in current E2** | The parser supports absolute and fractional boundaries, but the current final-v7 runner passes none; defaults resolve freeze, PGBA-disable, and late-map start to `-1`. Earlier Aria freeze800 recipes are real overfit evidence, but must not be attributed to this current benchmark arm. |
| Terminal pose rematuration/dust prune | **Requested upstream, forcibly inactive in current strict arm** | The 5090 profile and v7 alias add these terminal paths, but `VIGS_SENSOR_EOS_ZERO_TAIL=1` explicitly clears both before execution. They cannot explain current E2 PSNR and must stay out of the strict claim. |
| PGBA quaternion/moment correction | **Active general correctness fix** | The v7 alias transforms optimizer moments and uses corrected Gaussian quaternion order. This has no Aria literal and repairs coordinate consistency after PGBA; retain unless a matched packet experiment finds a regression. |
| TensorRT | **Inactive in the current matched benchmark baselines** | exp77-F explicitly disables fnet/update TRT. RPNG `344x616` engines exist and passed numerical validation, but remain opt-in. Any TRT comparison must enable the same module set and shape-compatible engines in both vanilla and gsSLAM arms. |

## Direct source evidence

- `benchmarks/online_gs/config/vigs_final_v7_rpng.yaml:1-79` activates the
  curve, PPM, density constants, `n_global_views=6`, `init_itr_num=600`, parallel
  queueing and kernel batch rendering.
- `vigs/gaussian/scene/gaussian_model.py:231-305` applies downsampling, raw
  Sobel PPM sampling, curve-based birth multiplication, and growth caps on the
  live path.
- `vigs/gaussian/utils/content_budget.py:1-45` says the curve was fitted from
  roughly 100–130 calibration keyframes and linearly extrapolates before a
  `[0.35, 3.0]` clamp.
- `exp69_axes/run_decoupled_geometry.sh:20-45,410-440,669-709` resolves v7 to
  pose-active/archive work-credit scheduling and supplies the actual CLI
  overrides.
- `demo.py:73-125` resolves unspecified frame boundaries to disabled `-1`;
  `demo.py:3445-3452` disables terminal rematuration/pruning under the
  sensor-EOS contract.
- The table06 curve measurement is reproducible from
  `results/experiments/exp77f_density_curve_20260911/run0_neutral/rpng/table_06/seed0/kf_content.csv`.

Audited hashes:

```text
run_exp77e_reserve.sh                 6a8d10b38cff1eb8eb46e4ab83318731f92c822973bce0854e254b8f9141f38f
vigs_final_v7_rpng.yaml               138fdd26a99be125fab900ba9e731d38660ee7d2dd8e5f6833496a16045ccf54
vigs_final_v7_utmm.yaml               b68693bf2d91291af1b5bd8cbd5489427445b7ff6048722f5736d14e1a6516c4
run_decoupled_geometry.sh             1c1cfb7a20677b91593759cd55b0192460769681cc3e6df028fe45241b752ff1
hardware_profiles.sh                  1cc4f12049f16beedaa89ae7290767e243bffe8612ee89123b351d5edfb524e5
content_budget.py                     00bbb17c9acd503ac3391e7b3b8d655345c82a67a73ae5950508fb375c905aa1
gaussian_model.py                     9e42b1c100817ee9a01672cbbcc3b7fb2a97ac42ddc6e7a50e4fd14369e6ed2a
```

## Decision

The current benchmark regression is not explained by one dormant freeze800
constant.  The strongest live transfer defects are the raw, Aria-fitted Sobel
curve; fixed per-frame birth/revisit budgets; initialization opportunity on
short streams; and wall-clock admission expressed in absolute milliseconds.
The first dataset-general replacement should therefore preserve PPM while
replacing its curve with a causal scale/contrast-normalized statistic and a
budget derived from arrived pixels/surface coverage and remaining work capacity.

Before tuning that replacement, use identical saved tracker packets so changes
in tracker thresholds, IMU initialization, PGBA and map supervision cannot be
mistaken for mapper improvement.
