# Exp115 — source-backed LPM dense-view utility

The LPM author-code error-zone coverage is an explicit bounded base
measure; normalized-variance ERCB remains a separate energy term.
No extra render, Adam update, topology mutation, or scene knob is allowed.

| Arm | PSNR | Delta | SSIM | LPIPS | Trace rows changed | Renders | Adam | GS | Wall (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| normalized_control | 21.234035 | +0.000000 | 0.715966 | 0.340895 | 0 | 9345 | 757 | 120199 | 40.340 |
| lpm_probe_control | 21.228204 | -0.005831 | 0.716566 | 0.341203 | 0 | 9345 | 757 | 120212 | 41.229 |
| lpm_normalized_utility | 21.214362 | -0.019673 | 0.715712 | 0.341833 | 0 | 9345 | 757 | 120108 | 39.925 |
| lpm_utility_rr | 21.236992 | +0.002957 | 0.716184 | 0.340900 | 9 | 9345 | 757 | 120129 | 40.039 |

Normalized utility: `p_i proportional to (1+e_i)*exp(-16*n_i/(T+1))`.
Utility-only RR control: `p_i proportional to 1+e_i`.
Gate: **FAIL**.
