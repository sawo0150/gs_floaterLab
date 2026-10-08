# Selective low-opacity births — PREREG (2026-10-09, user approved; aria1253, 1 run)

Birth count and positions unchanged (unlike exp98–100, which removed covered candidates and lost 34–58% of Gaussians,
−2.0/−2.5 dB). At each KF birth (not the first of a generation) the map is rendered from the birth KF before adding;
new points on pixels already explained (Gaussian-SLAM rule: alpha ≥ 0.6 and no positive depth residual > 40×median)
start at opacity 0.12, others at 0.5. Base: online uniform with replacement; birth probe installed on top.
Read-out: final-map PSNR vs online 24.66, uniform lowop 25.13, D2 26.65; immediate covered-view damage vs −0.21 dB
(probe baseline); covered-point share.
