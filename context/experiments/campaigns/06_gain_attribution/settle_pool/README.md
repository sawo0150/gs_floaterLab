# Settle-aware pool management — result (2026-10-09)

PREREG: [PREREG.md](PREREG.md). 18 runs (6 scenes × set_kf5 / set_kf15 / set_pose), seed 0, all valid.
Mean PSNR on final-map held-out views, difference vs online ERVS K16 seed 0: set_kf5 −0.141 (0/6), set_kf15 −0.255
(0/6), set_pose −0.212 (0/6). **Rejected:** restricting replay pools to settled regions does not recover the
stream-time loss; the later the admission, the worse.
