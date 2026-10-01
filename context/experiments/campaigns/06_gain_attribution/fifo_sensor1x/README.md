# Sensor-clock 1x bounded FIFO — 2026-09-30

User confirmed pending-packet eviction only; retain full-history learning pools and ERVS.
User confirmed actual sensor timestamp 1x, **not** a budget equal to prior vanilla mapping time.

- Frozen causal tracker replay: tracking is NOT computed concurrently.
- Same raw arrival clock for official vanilla and main + D3/fixed raster/warp.
- Keep 40 renders per admitted KF, per-image Adam for ours, 3:3:6, kappa16/tau4, birth.8, pruning.1/300.
- Queue capacity 2 pending ordinary mapping envelopes; active work is not evicted.
- Reset/rescale/PGBA envelopes are protected FIFO barriers, excluded from droppable capacity.
- Source timestamps causal; no new optimization after EOS, no tail queue drain.
- Common .5-second deadline admission reserve, no scene-specific tuning.
- Four requested scenes, seed0. Each saved map evaluated twice. Failed timing/causality runs remain failures.
- Zero-tail may leave unused KF credit; report completed updates and dropped packets rather than force an exact render count.

2026-09-30 FIFO sensor1x aria/d3: PSNR=25.778139150779666, pass=True; results/campaigns/gain_attribution/fifo_sensor1x/gpu_v1/aria/d3

2026-09-30 FIFO sensor1x aria/vanilla: PSNR=None, pass=False; results/campaigns/gain_attribution/fifo_sensor1x/gpu_v1/aria/vanilla
