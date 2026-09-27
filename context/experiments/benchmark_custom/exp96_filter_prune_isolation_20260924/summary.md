# Exp96 — naive regular filter-prune isolation (stopped)

- Scene: RPNG `table_01`
- Status: **STOPPED before completion; no PSNR claim**
- Output: `results/experiments/exp96_filter_prune_isolation/`

The candidate disabled only the physical regular opacity/size filter deletion,
while leaving initialization pruning, clone/split, split-parent replacement,
ERCB, and the fixed render scheduler enabled.  This was intended as a pruning
isolation, but the experiment violated that isolation before evaluation.

Exp95 control transitions away from topology after two final-generation
events.  The no-filter candidate had already opened a third event at frame
657.  Its first three final-generation transactions were:

| Frame | Input | Added | Split parents removed | Filter removed | Output | Net |
|---:|---:|---:|---:|---:|---:|---:|
| 286 | 38,202 | 6,219 | 962 | 0 | 43,459 | +5,257 |
| 482 | 92,087 | 13,085 | 1,888 | 0 | 103,284 | +11,197 |
| 657 | 147,733 | 15,551 | 2,393 | 0 | 160,891 | +13,158 |

The reason is structural: `TopologyReplayController.observe_topology(before,
after)` treats a net-pruning event as the capacity-recovery certificate that
moves R4 from FRONTIER toward BALANCED.  With physical pruning removed, every
event is net growth, the certificate never appears, and topology remains open.
Thus the naive candidate changes both deletion and future topology cadence.

The run was interrupted immediately after detecting the third event.  It has
no final PLY, held-out metrics, or success result.  The partial directory is
retained as failure evidence and must not be resumed or mixed into a panel.
The corrected test needs a shadow/counterfactual post-prune count for the
controller while retaining the physically unpruned tensor for optimization.
