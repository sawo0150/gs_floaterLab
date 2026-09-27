# Exp99 — corrected official Gaussian-SLAM local birth

Implementation basis: Gaussian-SLAM author repository commit
`eaec10d73ce7511563882b8856896e06d1f804e3` (MIT). VIGS source
is `d00e2263`: lineage cap registration now follows the final explicit
birth ticket; the no-ticket R4 path retains its historical arithmetic.

Candidate PSNR: **23.072144 dB**.
Candidate−Exp95 normalized R4: **-2.512874 dB**.
Candidate−fresh vanilla: **-0.892119 dB**.
Double evaluation: **PASS**.
Structural/quality gate: **FAIL**.

Birth events/eligible/ticketed/accepted/duplicate-rejected: 235/4,573,626/198,697/185,508/13,189.
Topology events candidate/control: 2/2.
Topology cap diagnostic: 0 rows removed; 185,508 local births accepted over the run.
Work: 38,302 renders, 3,030 Adam, 173,415 GS, 116.36 s.

This is a one-scene method gate, not a full-panel result and not yet a
dense/ERCB topology contribution. A loss greater than 0.5 dB versus the
Exp95 control stops the track before any dense-topology coupling work.

## Failure diagnosis

The cap-order bug is fixed: both final-generation topology events report zero
cap deletion. The fixed 1,024 adapter ticket is instead too small for this R4
mapping regime. It accepted 185,508 births over 235 events (789/event after
the radius test), leaving 173,415 final Gaussians versus Exp95's 417,656
(−58.5%) under identical optimizer/render work. The downloaded official
Gaussian-SLAM configs use 30k, 100k, or unlimited new-frame samples, so 1,024
must not be described as an official implementation detail.

The current adapter also zero-masks depth before VIGS computes its causal
full-view Sobel rank. That changes the density allocation trace in addition to
the intended candidate mask. A valid next test must preserve R4's full-view
causal target and apply the official seed mask/radius only within that target.
