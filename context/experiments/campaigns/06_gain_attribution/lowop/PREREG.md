# Low-opacity births (diagnostic) — PREREG (2026-10-09, user approved; aria1253, 1 run)

**Question.** Do untrained new Gaussians degrade already-trained regions by covering them? Births start at opacity 0.5
in the B mapper. Earlier evidence against this hypothesis was indirect (frustum-only overlap statistic; local-birth
suppression shows births are needed, not that they are harmless; repair replay starved the pool).

**Arm `lowop_iid`** (`lowop_patch.py`): online uniform with replacement; every KF birth after the first of a
generation starts at opacity 0.12 (just above the protected-prune threshold 0.1); everything else unchanged.
aria1253, seed 0, 1 run. Compare with online uniform_iid (24.66) and D2 (26.65), final-map held-out views. A clear
gain supports "new Gaussians cover trained regions"; no change weakens it.
