# Exp112 — active normalized-variance dense temperature

`gamma=16` was selected before image-quality evaluation on UTMM
`square-1`: it is the smallest tested constant with at least 10%
repeat-trace divergence and 10% final-generation count-CV reduction
versus RR. The implemented law remains
`p_i proportional exp(-gamma*n_i/(T+1))`; gamma is never scaled by
`T`, and native/auxiliary keyframe queues retain `log(1.5)`.

| Scene | R4 | repeat log1.5 | repeat gamma16 | repeat RR | g16-R4 | g16-log1.5 | g16-RR | trace diff | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| utmm/square-1 | 21.215443 | 21.229589 | 21.230649 | 21.225112 | +0.015206 | +0.001060 | +0.005537 | 9 | PASS |
| rpng/table_01 | 25.581778 | 25.570648 | 25.550914 | 25.576560 | -0.030864 | -0.019734 | -0.025646 | 17 | PASS |
| aria/aria1253 | 25.733551 | 25.718779 | 25.708201 | 25.715842 | -0.025350 | -0.010578 | -0.007642 | 10 | PASS |

Completed scenes: **3/3**.
Mean gamma16 minus R4: **-0.013669 dB**.
Mean gamma16 minus log1.5: **-0.009751 dB**.
Mean gamma16 minus RR: **-0.009250 dB**.
