# Exp114 — official-LPM behavior-neutral repeat

Two fresh no-probe controls bracket one probe run. Exact PLY byte
identity is reported but is not a gate because Exp113 and prior
same-command controls established CUDA/topology run variation.

| Arm | PSNR | SSIM | LPIPS | Renders | Adam | GS | Wall (s) |
|---|---:|---:|---:|---:|---:|---:|---:|
| control_a | 21.223234 | 0.715732 | 0.340931 | 9345 | 757 | 120137 | 40.475 |
| lpm_probe | 21.225550 | 0.715801 | 0.341525 | 9345 | 757 | 120195 | 40.328 |
| control_b | 21.223577 | 0.716448 | 0.340719 | 9345 | 757 | 120235 | 39.936 |

Control PSNR spread / probe minus control mean: **0.000343 / +0.002144 dB**.
LPM GPU fraction / mapping-wall overhead: **0.187% / +0.306%**.
Error-zone score min/mean/max/std: **0.103583/0.242299/0.368564/0.059700**.
Probe GS deviation / predeclared tolerance: **9.0/121**.
Gate: **PASS**.
