# Live operating point of the adopted B mapper on RTX 5070 Ti (2026-10-02)

Status: **EVIDENCE — descriptive measurement**, single run per cell, sampler ERVS (= B). Not a quality ablation.

Actual RGB+IMU tracking and B mapping run concurrently; frames are fed at sensor timestamps × {1, 1.2, 1.5}; every
frame is tracked (overdue frames run late, none skipped); the mapper stops at the scaled sensor deadline with zero
optimizer updates afterwards; ordinary mapping packets are evicted oldest-first beyond a queue of 2; models load
before the stream clock. B loss checked per run (`w_plain` 0.25, D3 terms 0); renders/KF cap 40.

- Driver `benchmarks/online_gs/campaigns/gain_attribution/run_live_b_operating_point.py`; probe
  `measure_fifo_live_b.py` (copy of the live FIFO probe with a sampler option and a sha-only extension check).
- **v2_trt (main):** TensorRT engines previously built on this machine (TensorRT 10.13; omnidata 512 + per-resolution
  DroidNet fnet/update/PGBA, all verified to deserialize and match resolution); a run fails if any runner falls back.
- v1: TensorRT disabled (PyTorch tracking), 1× only (the 1.2/1.5× no-TRT sweep was stopped to switch to TRT).
- Raw: `results/campaigns/gain_attribution/live_operating_point_5070ti/{v2_trt,v1}/`.

## Results (TensorRT)

"Tracking KFs" = keyframes produced by the tracker; "admitted" = keyframe admissions that reached the mapper.

| Scene | Speed | PSNR | Renders / admitted KF | Admitted / tracking KFs | Renders / tracking KF | Tracking overrun | End lag p95 |
|---|---:|---:|---:|---:|---:|---:|---:|
| aria1253 | 1× | 23.29 | 39.8 | 81 / 115 (70%) | 28.0 | 7.1 s | 8.0 s |
| aria1253 | 1.2× | 23.33 | 39.7 | 83 / 115 (72%) | 28.6 | 4.8 s | 6.0 s |
| aria1253 | 1.5× | 23.00 | 39.5 | 87 / 115 (76%) | 29.9 | 1.9 s | 3.8 s |
| aria1253rot | 1× | 22.19 | 40.0 | 95 / 176 (54%) | 21.6 | 32.6 s | 31.1 s |
| aria1253rot | 1.2× | 23.29 | 39.9 | 111 / 176 (63%) | 25.2 | 24.8 s | 24.4 s |
| aria1253rot | 1.5× | 24.48 | 39.9 | 124 / 176 (70%) | 28.1 | 11.6 s | 12.9 s |
| table_06 | 1× | 23.82 | 40.0 | 88 / 211 (42%) | 16.7 | 61.7 s | 63.0 s |
| table_06 | 1.2× | 23.74 | 40.0 | 104 / 211 (49%) | 19.7 | 49.1 s | 52.0 s |
| table_06 | 1.5× | 24.03 | 40.0 | 130 / 211 (62%) | 24.6 | 31.3 s | 37.9 s |
| square-1 | 1× | 20.87 | 40.0 | 51 / 69 (74%) | 29.6 | 0.6 s | 3.3 s |
| square-1 | 1.2× | 20.83 | 40.0 | 51 / 69 (74%) | 29.6 | 0.4 s | 1.9 s |
| square-1 | 1.5× | 20.84 | 40.0 | 51 / 69 (74%) | 29.6 | 0.2 s | 1.1 s |

TensorRT vs PyTorch tracking at 1× (PSNR / admitted KFs / overrun): aria 23.29 vs 23.11 / 81 vs 76 / 7.1 vs 16.2 s;
rot 22.19 vs 21.34 / 95 vs 83 / 32.6 vs 48.0 s; table_06 23.82 vs 22.75 / 88 vs 76 / 61.7 vs 82.1 s;
square-1 20.87 vs 17.93 / 51 vs 40 / 0.6 vs 11.9 s.

## Reading

- **Every admitted keyframe receives the full 40-render cap.** The real-time constraint does not reduce renders per
  admitted keyframe; it reduces how many keyframes reach the mapper (tracking lag → bounded queue eviction, plus the
  mapper deadline arriving before late keyframes are tracked).
- Expressed per tracking keyframe, the live budget at 1× is **≈17–30 renders/KF** (table_06 16.7, rot 21.6, aria 28.0,
  square-1 29.6), rising to ≈25–30 at 1.5×.
- Tracking is the bottleneck on this machine: table_06 and rot lag by 30–60 s at 1× even with TensorRT; square-1 keeps
  up (its admitted set is identical at all speeds, so it is not time-limited).
- PSNR follows admitted-keyframe coverage where tracking lags (rot +2.3 dB from 1× to 1.5×); where it keeps up,
  extra time changes nothing (square-1). Single runs; live spread appears to be a few tenths of a dB (aria 1.5×).

## Consequences for the sampler question

The live operating point is "full 40 renders per admitted keyframe, but fewer admitted keyframes", not "few renders per
keyframe". The fixed-work regime where ERVS showed a signal (budget 5) does not occur live; at 40 renders/KF the
fixed-work ERVS−RR results were mixed. A live ERVS vs RR comparison is therefore not expected to favour ERVS, and the
dominant live lever on this machine is tracking throughput / keyframe admission.

## Live ERVS vs RR on aria1253 and square-1 (PREREG_ERVS_RR.md, committed `15a8ebe`)

Same live setup (TensorRT, queue 2, credit 40, sensor deadline). 1× has two runs per arm (`_r2`).

| Scene | Speed | ERVS | RR | ERVS−RR | Admitted KFs ERVS/RR | Recent-third Δ |
|---|---:|---:|---:|---:|---:|---:|
| aria1253 | 1× | 23.287, 23.262 | 22.766, 23.432 | +0.175 (mean) | 81, 81 / 76, 81 | +0.71 |
| aria1253 | 1.2× | 23.325 | 23.640 | −0.315 | 83 / 83 | −0.23 |
| aria1253 | 1.5× | 22.997 | 23.570 | −0.572 | 87 / 86 | +0.28 |
| square-1 | 1× | 20.870, 20.876 | 20.840, 20.833 | +0.037 (mean) | 51 / 51 | +0.04 |
| square-1 | 1.2× | 20.825 | 20.791 | +0.034 | 51 / 51 | +0.01 |
| square-1 | 1.5× | 20.836 | 20.800 | +0.036 | 51 / 51 | +0.03 |

Live run-to-run noise (max |run1 − run2| at 1×): aria1253 **0.666 dB** (one RR run admitted 76 instead of 81 KFs after
a larger tracking lag), square-1 **0.007 dB**.

Reading: aria1253 — no cell resolved (all |Δ| < 0.666; RR higher at 1.2× and 1.5×). square-1 — ERVS higher by
+0.03…+0.04 dB at all three speeds, resolved against its very small noise but negligible in size. The preregistered
"ERVS helps live" criterion (resolved-positive in both scenes at ≥2 speeds) is **not met**. On aria1253 live variance
is dominated by tracking lag and keyframe admission, not by the sampler.
