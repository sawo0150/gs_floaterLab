# exp105 — dense topology ticket no-retuning transfer pilot

- Date: 2026-09-24
- Status: 2-scene cross-dataset pilot complete; all-scene expansion deferred
- VIGS source: `913b9da2`
- Lab source: `9cd0402` plus source-locked runner
- Runner: `benchmarks/online_gs/run_exp105_dense_ticket_transfer.py`
- Results: `results/experiments/exp105_dense_ticket_transfer/`
- Summary: [2/17 pilot table](benchmark_custom/exp105_dense_ticket_transfer_20260924/summary.md)

## Result

Exp104's rule was frozen without scene tuning. Unlike a historical-number
comparison, each pilot scene created a fresh dense-ticket candidate and fresh
render-matched vanilla run, and evaluated both saved maps twice.

| Scene | Ticket | Fresh vanilla | Δ vanilla | Δ Exp94 R4 | Actual mutation | Verdict |
|---|---:|---:|---:|---:|---:|---|
| UTMM `slow-straight-2` | 17.246139 | 17.281727 | −0.035588 | +0.022695 | 0 | fairness PASS; ticket inactive |
| Aria `aria1253` | 25.723744 | 23.960097 | **+1.763647** | −0.051958 | 1,453 | fairness PASS; ticket active |

Both pairs preserve exact physical-render matching, the normalized R4 Adam
work, fixed held-out disjointness, zero-tail, and saved-map evaluation
consistency. Neither scene approaches the predeclared −0.5 dB R4 stop line.

## Finding and decision

Aria confirms that the author-code-based ticket transfers across datasets and
keeps the existing R4 advantage with only a noise-scale change from R4. The
short UTMM scene exposes a more important scheduling problem: four dense
updates produce 619 repeated final-generation candidates, but all native
topology events occur before that evidence matures, so the controller performs
zero mutation. Its small fresh-vanilla loss therefore cannot support an ERCB
topology contribution.

Do not spend the full 17-scene panel on this native-event-only scheduler yet.
The next isolated experiment should add at most one observation-triggered
bounded service per map generation when repeated evidence first becomes
available. A mid-cycle clone must preserve existing native
`xyz_gradient_accum`, `denom`, and `max_radii2D`; otherwise it silently changes
the later regular densification rule. Test the short UTMM failure case first,
then recheck RPNG `table_01` before any all-scene expansion.
