# exp78 C — Aria-specific assumption audit

Classify each candidate as one of: active literal Aria dependency, active but
dataset-generic mechanism only tuned on Aria, opt-in/dead path, or inactive.

Audit targets include the `aria1253_content_curve.json` path, absolute frame
boundaries, tracker parameters, point-cloud density and PPM growth, global-view
count, map/IMU initialization timing, FPS/length-dependent replay admission,
GPU reserve/queue sizes, and PGBA/rematuration/topology policy.

The existing matched test already shows that simply disabling the Aria content
curve is not a fix: RPNG `table_06` changes by -0.337 dB PSNR on average and
worsens SSIM/LPIPS.  The curve nevertheless extrapolates strongly on RPNG, so
the replacement candidates are normalized causal content statistics, online
percentile calibration, and scene-independent point budgets.

The active-path source/config classification is recorded in
[`source_path_audit.md`](source_path_audit.md).  It confirms that the literal
Aria curve is live, whereas old absolute freeze/PGBA boundaries and terminal
rematuration/pruning are inactive in the current sensor-EOS arm.  Several other
choices are dataset-generic code but remain Aria-tuned, especially fixed birth,
view, initialization and wall-clock admission budgets.
