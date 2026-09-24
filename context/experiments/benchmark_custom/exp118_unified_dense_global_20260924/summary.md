# Exp118 — unified dense global-slot development gate

One of six flexible historical-keyframe renders is replaced by a
transactional draw from the same LPM-mass dense ERCB pool. The recent
keyframe window, total physical renders, and Adam steps stay fixed.

| Arm | PSNR | Delta | SSIM | LPIPS | Dense renders/share | Renders | Adam | GS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| mass_normalized_control | 21.231306 | +0.000000 | 0.716141 | 0.340861 | 142 / 1.52% | 9345 | 757 | 120029 |
| unified_mass_normalized | 21.197972 | -0.033335 | 0.716625 | 0.342482 | 625 / 6.65% | 9394 | 757 | 120734 |
| unified_mass_rr | 21.179603 | -0.051703 | 0.715617 | 0.343416 | 625 / 6.65% | 9394 | 757 | 120693 |

Normalized/RR unified global trace differences: **70 rows**.
Gate: **FAIL**.
