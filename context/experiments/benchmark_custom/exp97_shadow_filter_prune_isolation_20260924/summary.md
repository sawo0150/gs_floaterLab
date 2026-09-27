# Exp97 — shadow-count regular filter-prune isolation

This is a single-scene causal diagnosis, not a method or full-panel claim.
The physical tensor retains ordinary opacity/size prune candidates, while
the existing R4 phase controller receives the counterfactual count it would
have observed after deleting them. Initialization, clone/split, split-parent
replacement, ERCB, render work, and zero-tail remain unchanged.

| Candidate | PSNR | SSIM | LPIPS | vs Exp95 R4 | vs fresh vanilla | Renders | Adam | GS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| shadow no-filter-prune | 25.680925 | 0.851117 | 0.149576 | +0.095907 | +1.716662 | 38,302 | 3,030 | 463,543 |

Double evaluation: **PASS**.
Isolation gate: **PASS**.
Final-generation topology events candidate/control: **2/2**.
Lifetime regular mutations: added 31,527, split-parent removed 4,780, filter candidates/physically removed/withheld 86,782/0/86,782.
Completed mapper generations recorded: **6**.

Compared with Exp95 R4, the candidate retains 45,887 more final Gaussians
(+11.0%), raises peak CUDA allocated memory from 5.092 to 5.454 GB (+7.1%) and
peak reserved memory from 8.670 to 10.100 GB (+16.5%), and increases mapping
wall time from 165.90 to 176.08 s (+6.1%).  The run is fixed-work B-track, so
the wall-time difference is diagnostic rather than a strict-live result.

Any failed invariant or >0.5 dB loss stops the track before local births.
