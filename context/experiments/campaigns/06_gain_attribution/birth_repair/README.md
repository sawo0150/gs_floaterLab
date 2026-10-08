# Birth-triggered repair replay — result (2026-10-09)

PREREG: [PREREG.md](PREREG.md). 2 runs (square-1, aria1253), seed 0, valid; 63 / 79 repair events, repair views took
~55% of KF-role and ~32–45% of dense-role draws. Mean PSNR (final-map views): square-1 21.31 (ERVS 21.98, −0.67),
aria1253 23.58 (ERVS 24.85, −1.27). **Rejected.** Concentrating replay on views that see new Gaussians starves the
rest of the pool. Follow-up checks: D2 prunes more and keeps fewer Gaussians than online yet is better (pruning /
capacity is not the D2 advantage); mean KF rotation change after first appearance is 0.2–1.5 px of image shift in
these scenes, not ordered with the D2 gain — an oracle-pose arm (D3) is the remaining direct test.
