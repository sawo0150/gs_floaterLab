# Does keyframe depth supervision mask the sampler effect? (2026-10-02)

Status: **EVIDENCE — complete, 32 runs**, seed 0. **Diagnostic only** (B with keyframe depth weight 0 is not the
paper system).

[PREREG](PREREG.md) (committed `d113883` before any run). All runs went through `per_pool_selector.py` with
`B_KF_DEPTH_W=0`; every run recorded `w_plain = 0`, and ER/RE runs passed the per-pool draw gate.
Depth-on comparison: [ervs_per_pool](../ervs_per_pool/README.md). Raw: `results/campaigns/gain_attribution/ervs_depth_off/v1/`.

## Results (whole-cohort held-out PSNR, dB; `*` above the scene's noise reference)

| Scene | Budget | D0-EE | D0-RR | Joint ERVS−RR (depth off) | Joint (depth on) | Keyframe-pool effect | Dense-pool effect | Recent-third joint |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| aria1253rot | 15 | 23.55 | 23.49 | +0.05 | +0.13 | −0.07 | +0.12 | +0.18 |
| table_06 | 15 | 24.01 | 23.48 | **+0.53*** | +0.44 | **+0.24*** | **+0.29*** | +0.18 |
| aria1253 | 15 | 22.97 | 22.41 | **+0.56*** | +0.14 | +0.01 | **+0.55*** | −0.25 |
| square-1 | 15 | 20.83 | 21.11 | **−0.28*** | −0.21 | **−0.24*** | −0.04* | +0.03 |
| aria1253rot | 25 | 24.47 | 24.58 | −0.11 | −0.06 | −0.05 | −0.06 | −0.04 |
| table_06 | 25 | 24.61 | 24.39 | **+0.22*** | +0.27 | +0.05* | **+0.17*** | +0.11 |
| aria1253 | 25 | 23.86 | 24.81 | **−0.95*** | −0.41 | **−0.51*** | **−0.43*** | +0.07 |
| square-1 | 25 | 21.67 | 21.83 | **−0.16*** | −0.05 | **−0.13*** | −0.03* | −0.19 |

Removing the keyframe depth term (EE / RR vs depth-on): table_06 +0.23/+0.14 (15), +0.18/+0.23 (25);
square-1 +0.06/+0.13, +0.30/+0.41; aria1253 −0.48/−0.90, −0.65/−0.12; rot −0.26/−0.19, −0.06/−0.02.

## Reading against the PREREG

- **H rejected:** no joint or pool effect is a positive signal at either budget (budget 15: positive above noise in
  2/4 scenes; budget 25: mixed with large negatives).
- Removing depth **amplifies** the scene-dependent swings rather than making them consistent: aria1253 moves from
  +0.14/−0.41 to +0.56/−0.95 (budget 15/25); square-1 stays negative; table_06 stays positive; rot stays within noise.
- aria1253 at budget 25 again shows EE alone far below the other three arms (interaction −0.66), as with depth on.

## Exploratory (not preregistered)

- On RPNG table_06 and UTMM square-1 the keyframe depth term lowers held-out PSNR by 0.06–0.41 dB; on the Aria scenes
  it raises it. This is appearance only; geometry was not measured, and the depth term was adopted for geometry
  (dense-depth four-scene experiment).

## Conclusion

Keyframe depth supervision does not hide a consistent sampler effect. Together with the per-pool and earlier tests,
the ERVS/RR difference on B is scene- and budget-dependent in sign under every tested condition.
