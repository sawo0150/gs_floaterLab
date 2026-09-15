# exp78 B — matched strict-streaming comparison

The method-independent evaluation UID manifests were locked before exp78 model
tuning.  They select zero-based frame indices divisible by five plus the final
frame.  Every listed UID must be excluded from Gaussian supervision and birth;
tracking may still observe it.

- Manifest index: `manifests/manifest_index.json`
- Development sequences: RPNG `table_01`, `table_06`; UTMM `ego-drive`,
  `square-2`
- Validation sequences: the remaining six RPNG and six UTMM sequences
- Historical exp77 work has already exposed all sequences.  “Validation” here
  means untouched by tuning after the exp78 manifest lock, not globally unseen.

Required per-arm telemetry is PSNR/SSIM/LPIPS, ATE/Recall, wall time/FPS, input
lag, peak memory, Adam steps, rasterized view-updates, unique mapped views and
Gaussian count.  Results at 1× and 1.5× are reported separately, with identical
input/preprocessing/hardware/TensorRT state and zero optimizer work after EOS.

The mapper-independent frozen archive schema v2 and common timeline scheduler
are operational. The pinned one-arm runner is
`benchmarks/online_gs/run_exp78b_matched_mapping.sh`; it validates archive
hashes/causality/split isolation, refuses output overwrite, checks zero-tail,
and evaluates the predeclared held-out manifest. The current 1.5× RPNG paired
result is recorded in [Lane D1](../d_dataset_general_optimization/rpng_mapping_only_ablation.md).
