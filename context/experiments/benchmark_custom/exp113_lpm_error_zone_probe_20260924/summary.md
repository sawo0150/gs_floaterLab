# Exp113 — official-LPM error-zone telemetry gate

This experiment ports only the downloaded author implementation's
`lpm/utils.py::get_errormap(diff)` operator at commit
`7c060267cf55df76992e9ef2b6df42133ba9349f`. It runs on an already-paid causal dense replay
render/GT pair and performs no LightGlue matching, triangulation,
additional render/Adam step, selection change, or map mutation.

| Arm | PSNR | SSIM | LPIPS | Renders | Adam | GS | Wall (s) |
|---|---:|---:|---:|---:|---:|---:|---:|
| control | 21.218693 | 0.716176 | 0.341625 | 9,345 | 757 | 120,105 | 40.148 |
| LPM probe | 21.225969 | 0.715884 | 0.340801 | 9,345 | 757 | 120,110 | 41.322 |

The probe changed neither completed work nor the dense selection trace. Its
PSNR difference was **+0.007276 dB**, its measured GPU share was **0.211%**,
and its mapping-wall overhead was **+2.924%**. The score was non-degenerate:
142 calls over 72 views, range 0.105992--0.369768, standard deviation 0.059340,
with 36 views observed more than once.

Status: **FAIL under the predeclared exact-PLY-SHA gate**. The two PLY hashes
differed and final counts were 120,105/120,110. Exp114 subsequently showed
that two untouched controls also produce different PLY hashes and a 98-row
count spread, so byte identity was an invalid behavior-neutrality criterion.
Exp113 is not relabeled; Exp114 is the corrected, independently archived gate.
