# D3 — online training with end-of-stream poses (diagnostic) — PREREG (2026-10-09, user approved; 2 runs)

**Why.** gap_ladder: training after the stream (D2) is +1 dB over the same online updates. Ruled out since: order,
births-into-seen-space (no correlation; suppression costs 2 dB), repair replay (worse), pruning/capacity (D2 prunes
more). Remaining direct candidate: the pose a view has when it is trained vs its final pose (0.2–1.5 px rotation-only
estimate in these scenes).

**Arm `oracle_iid`** (`pose_oracle_patch.py`, non-causal diagnostic): online uniform with replacement (same as the
online reference), but every training view is rendered/supervised with its end-of-stream pose (KF: final mapper pose of
the reference run; dense: current pose corrected by its left anchor's correction). Mapper state, births and packets
unchanged. Scenes aria1253, square-1; seed 0; 2 runs.

**Read-out.** PSNR on final-map held-out views vs online uniform_iid and D2 (seq). D3 ≈ D2 → poses explain the
stream-time loss; D3 ≈ online → they do not.
