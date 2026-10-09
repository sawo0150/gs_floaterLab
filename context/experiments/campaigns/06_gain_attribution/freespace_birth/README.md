# Multi-view free-space birth gate — result (2026-10-09, 2 valid runs, seed 0)

Flagged (start at 0.02): aria 19,705 / 282,107 points (7.0%), square-1 20,524 / 203,315 (10.1%), with 1,201 / 782 old-KF
renders for the checks. Selective births (current-view rule) flag ~81%.
| scene | arm | PSNR | first 70% | last 30% | old-KF birth Δ / training Δ (whole stream) |
|---|---|---:|---:|---:|---|
| aria1253 | A adopted (clamp 0.1) | 24.85 | 25.56 | 23.22 | |
| aria1253 | B clamp off, 0.5 births | 25.32 | 26.24 | 23.19 | |
| aria1253 | selective 0.5/0.02 | 25.72 | 26.87 | 23.05 | −0.98 / +12.01 |
| aria1253 | **free-space gate** | **25.67** | 26.75 | 23.20 | −4.05 / +14.56 |
| aria1253 | D2 (clamp off) | 26.52 | 27.92 | 23.30 | |
| square-1 | A adopted | 21.98 | 22.67 | 20.37 | |
| square-1 | B clamp off | 21.92 | 22.68 | 20.18 | |
| square-1 | selective 0.5/0.02 (uniform) | 21.72 | 22.42 | 20.11 | −0.37 / +8.13 |
| square-1 | **free-space gate** | **21.96** | 22.75 | 20.13 | −4.59 / +12.09 |
| square-1 | D2 (clamp off) | 21.85 | 22.58 | 20.16 | |
**Reading.** Making only the ~7–10% of new points that fall in an old KF's known free space start transparent gives
the same gain as the current-view selective rule on aria1253 (+0.35 vs B; selective +0.40) without its loss on
square-1 (+0.04 vs B; selective −0.20 with a different sampler). Most of the selective rule's 81% transparent births
were unnecessary. Single seed per scene.
