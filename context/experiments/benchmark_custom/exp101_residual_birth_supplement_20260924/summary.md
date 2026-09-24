# Exp101 — R4-preserving official residual-birth supplement

R4 blanket PPM birth and its RNG stream are preserved first. A separate
RNG stream then applies the low-alpha/positive-depth-residual mask and
current-frustum radius rejection ported from Gaussian-SLAM author code
`eaec10d7` (MIT), using one matched-R4 supplemental allocation. VIGS
source: `96de04b3`.

Candidate PSNR: **25.609319 dB**.
Candidate−Exp95 normalized R4: **+0.024301 dB**.
Candidate−fresh vanilla: **+1.645055 dB**.
Double evaluation: **PASS**.
Structural/quality gate: **PASS**.
Full-view causal density trace parity: **PASS**.

Birth events/baseline births/residual offered/residual accepted/duplicate-rejected: 235/498,627/324,428/286,549/37,879.
Topology events candidate/control: 2/2.
Work: 38,302 renders, 3,030 Adam, 634,950 GS, 184.53 s.

This is a one-scene isolation gate. It does not yet establish a dense/
ERCB topology contribution or strict-live feasibility.

## Cost

Against Exp95 R4, final GS increases 417,656→634,950 (**+52.0%**), mapping
wall time 165.90→184.53 s (**+11.2%**), peak CUDA allocated 5.092→6.419 GB
(**+26.1%**), and peak reserved 8.670→16.008 GB (**+84.6%**). The surviving
generation's regular topology churn rises 68,517→91,652 rows (**+33.8%**).
The +0.024 dB quality gain does not justify this cost, so 1× supplement is a
safe mechanism proof, not the final method. Dense/ERCB evidence must ration
the service before broader evaluation.
