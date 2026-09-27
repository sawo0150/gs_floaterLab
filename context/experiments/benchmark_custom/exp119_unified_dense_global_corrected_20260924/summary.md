# Exp119 — corrected exact-render unified dense global slot

Control-equivalent global cardinality is frozen before one actual
historical slot is reassigned to the unified LPM-mass dense pool.

| Arm | PSNR | Delta | SSIM | LPIPS | Dense renders/share | Renders | Adam | GS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| mass_normalized_control | 21.220422 | +0.000000 | 0.716066 | 0.341520 | 142 / 1.52% | 9345 | 757 | 120132 |
| unified_mass_normalized | 21.208358 | -0.012064 | 0.716294 | 0.341234 | 625 / 6.69% | 9345 | 757 | 120736 |
| unified_mass_rr | 21.182736 | -0.037685 | 0.715337 | 0.344014 | 625 / 6.69% | 9345 | 757 | 120684 |

Normalized/RR unified global trace differences: **70 rows**.
Gate: **PASS**.
