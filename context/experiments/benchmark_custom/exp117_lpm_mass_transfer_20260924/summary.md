# Exp117 — frozen LPM mass-prior transfer

Exp116's formula and gamma are transferred without retuning.
A failure or a normalized-arm drop below -0.5 dB stops later scenes.

| Dataset / scene | Arm | PSNR | Delta | Trace rows changed | Renders | Adam | GS |
|---|---|---:|---:|---:|---:|---:|---:|
| rpng / table_01 | normalized_control | 25.586171 | +0.000000 | 0 | 38302 | 3030 | 417928 |
| rpng / table_01 | lpm_mass_normalized | 25.575404 | -0.010767 | 34 | 38302 | 3030 | 417980 |
| rpng / table_01 | lpm_mass_rr | 25.583380 | -0.002790 | 40 | 38302 | 3030 | 417873 |
| aria / aria1253 | normalized_control | 25.726881 | +0.000000 | 0 | 13620 | 1055 | 177273 |
| aria / aria1253 | lpm_mass_normalized | 25.757892 | +0.031011 | 9 | 13620 | 1055 | 177202 |
| aria / aria1253 | lpm_mass_rr | 25.749919 | +0.023038 | 15 | 13620 | 1055 | 177123 |

Completed scenes: **2/2**.
Gate: **PASS**.
