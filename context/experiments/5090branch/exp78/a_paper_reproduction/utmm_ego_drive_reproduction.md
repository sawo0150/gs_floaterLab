# exp78 A3 — UTMM `ego-drive` longer-sequence reproduction

## Question

Does the multi-dB `fast-straight` paper gap primarily come from its map and IMU
initializing near the end of a very short sequence?  `ego-drive` is the frozen
longer UTMM development check; no parameter was changed from A2.

## Protocol

- Clean official VIGS commit `22ffe24c6df81d0bf63bd20057565c00c51d2996`
- Official `config/utmm.yaml`, `IMU_poseinit_after=15`, PyTorch, TensorRT off
- ETH-preprocessed official-format RGB+IMU/calibration/GT
- Mapping explicitly enabled because the published UTMM batch runner defaults
  to `gsmapping=False`
- Primary state captured before final visual BA and color refinement
- Official-public evaluator run in process; saved PLY audit run separately
- Paper targets: rendering 21.54/.696/.399 before final color refinement;
  tracking ATE 1.45 cm without final BA and 2.13 cm with final BA

## Repeated pre-final result

| Seed | Frames | First map | IMU init | KF | Mapped views / iters | PSNR | SSIM | LPIPS | ATE cm | Recall@10cm |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 1,399 | 54 | 131 | 85 | 84 / 835 | 20.3246 | .6647 | .3772 | 5.1759 | 100% |
| 1 | 1,399 | 54 | 131 | 85 | 84 / 835 | 20.3772 | .6664 | .3766 | 5.2188 | 100% |
| **Mean** | — | — | — | 85 | — | **20.3509** | **.6656** | **.3769** | **5.1974** | **100%** |
| Paper | — | — | — | — | — | **21.5400** | **.6960** | **.3990** | **1.4500** | — |

The two-seed PSNR range is .0526 dB and ATE range is .0429 cm.  The mean gaps
are -1.1891 dB PSNR, -.0304 SSIM, and +3.7474 cm ATE.  LPIPS is .0221 lower
(better) than the paper.  This is a stable current-public-source mismatch, not
a lucky/unlucky seed.

Seed 0 native tracking+mapping took 102.123 s (13.699 FPS), used 130,448
Gaussians, and peaked at 8.246 GB allocated / 11.333 GB reserved CUDA memory.
Seed 1 took 99.979 s (13.993 FPS) and captured 129,566 Gaussians.

## Split and finalization diagnostics

For seed 0:

| Evaluation label | Views | KF overlap | PSNR | SSIM | LPIPS |
|---|---:|---:|---:|---:|---:|
| Official-public | 349 | 85 | 20.3246 | .6647 | .3772 |
| Self-non-KF best effort | 264 | 0 | 20.2485 | .6611 | .3842 |
| Fixed UID post-hoc diagnostic | 281 | 17 | 20.3003 | .6629 | .3811 |

The fixed result is not Lane-B evidence because 17 selected views entered
native mapping.  Removing this method's keyframes also does not restore the
paper result.

On seed 1, final visual BA plus the source's 20-step `final=True` mapping update
changes rendering from 20.3772/.6664/.3766 to
20.1630/.6540/.4127.  It therefore **reduces** PSNR by .2142 dB and worsens all
three rendering metrics.  Tracking ATE improves from 5.2188 to 3.3283 cm, but
still misses the paper's with-final-BA value of 2.13 cm by 1.1983 cm.

## Interpretation

Earlier initialization clearly removes part of the short `fast-straight`
failure: `ego-drive` starts mapping at 3.86% and IMU initialization at 9.36% of
the stream, versus 48.49% and 78.01% on fast, and its PSNR gap shrinks from
3.960 to 1.189 dB.  That does not establish mapping parity because `ego-drive`
itself fails the paper tracking gate by 3.75 cm before final BA.

The next fair causal test is therefore mapping-only isolation using frozen
tracking packets/poses, not gsSLAM mapping tuning against this weak end-to-end
trajectory.  Lane-A all-sequence collection may continue for coverage, but
`ego-drive` cannot be called an exact vanilla reproduction.

## Evidence

- Machine-readable: `evidence/utmm_ego_drive_reproduction.json`
- Seed 0 main output:
  `results/experiments/exp78/a_paper_reproduction/native_official_22ffe24/utmm/ego-drive/seed0/`
- Seed 1 pre/post-BA isolation:
  `results/experiments/exp78/a_paper_reproduction/diagnostics/utmm_ego_drive_seed1_after_ba_before_color/`

