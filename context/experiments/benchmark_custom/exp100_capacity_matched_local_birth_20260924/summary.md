# Exp100 — capacity-matched official-code local birth

The low-alpha/positive-depth-residual seed mask and current-frustum
radius rejection come from the downloaded Gaussian-SLAM author code
at `eaec10d7` (MIT). Birth work is adapted to VIGS by preserving R4's
full-view causal allocation instead of imposing Exp99's arbitrary
1,024-point cap. VIGS source: `1721e3cc`.

Candidate PSNR: **23.581536 dB**.
Candidate−Exp95 normalized R4: **-2.003482 dB**.
Candidate−fresh vanilla: **-0.382728 dB**.
Double evaluation: **PASS**.
Structural/quality gate: **FAIL**.
Full-view causal density trace parity: **PASS**.

Birth events/eligible/offered/accepted/duplicate-rejected: 235/4,628,859/351,624/314,590/37,034.
Topology events candidate/control: 2/2.
Work: 38,302 renders, 3,030 Adam, 276,837 GS, 128.42 s.

This is a one-scene isolation gate. A loss greater than 0.5 dB versus
Exp95 stops the track before dense/ERCB topology coupling.

## Interpretation

The matched adapter recovers +0.509392 dB over Exp99 and proves that the
full-view causal density trace is identical to R4. It still accepts only
314,590 local births and ends with 276,837 Gaussians, 33.7% below Exp95's
417,656. The residual mask is therefore unsuitable as a drop-in replacement
for blanket PPM birth under VIGS's global-map/online-depth assumptions.
The quality stop fired, so no dense/ERCB topology coupling was run.
