# exp110 — normalized ERCB / RR / topology-ticket isolation

- Date: 2026-09-24
- Status: **PASS as mechanism isolation; quality causality NOT established**
- Lab source lock: `38eb193f270f7241945781a1ccc99c62688faa3e`
- VIGS source lock: `e248b6133af512eebbb0170cbd8c62432443d464`
- Runner: `benchmarks/online_gs/run_exp110_rr_ticket_ablation.py`
- Results: `results/experiments/exp110_rr_ticket_ablation/`
- Official summary: [three-scene table](benchmark_custom/exp110_rr_ticket_ablation_20260924/summary.md)

## Question and controls

Exp109 preserved the complete R4 gain over vanilla, but its dense topology
ticket changed quality by only `+0.000426 dB` versus historical exact R4. This
experiment separates two mechanisms under scarce work:

1. normalized-variance ERCB versus an explicit RR control in dense,
   auxiliary-keyframe, and native historical-keyframe selectors;
2. normalized ERCB with the first-persistence ticket on versus off.

RR preserves the same causal growing pool, global no-repeat epochs, admission,
block size, RNG ownership, proposal/commit protocol, birth, pruning, physical
renders, and Adam steps. It changes only the Gibbs energy to zero. The
normalized arm uses

\[
\Phi(\mathbf n)=\operatorname{Var}(\mathbf n)/\bar n,\qquad
p_i\propto\exp[-\log(1.5)n_i/(T+1)].
\]

No scene-specific parameter or phase cutoff is used. Every saved map is
evaluated twice on the frozen held-out manifest.

## Results

| Scene | Normalized+ticket | RR+ticket | Normalized no-ticket | N-RR | Ticket-off | D/A/N differing rows |
|---|---:|---:|---:|---:|---:|---:|
| UTMM ego-centric-2 | 19.483852 | 19.489788 | 19.495748 | -0.005936 | -0.011896 | 0/0/9 |
| UTMM fast-straight | 16.389484 | 16.411041 | 16.370305 | -0.021557 | +0.019179 | 0/0/0 |
| UTMM square-1 | 21.226980 | 21.222601 | 21.225575 | +0.004379 | +0.001405 | 0/0/16 |
| **Mean** | — | — | — | **-0.007705** | **+0.002896** | — |

All 9 arms pass equal-render, equal-Adam, identical frozen archive/config/event,
identical admission/opportunity, held-out disjointness, double-evaluation, and
zero-tail checks. Render/Adam counts are 6,655/559, 1,348/172, and 9,345/757
per arm for the three scenes.

## Mechanism finding

The dense selector registered/selected 50/48, 5/3, and 72/70 unique views,
and no selected dense view had count above one. It never completed a growing
no-repeat epoch. Auxiliary-KF service was also effectively single-pass. Thus
normalized ERCB and RR generated identical dense and auxiliary traces by
construction: the current scheduler gives the Gibbs term no choice to make.

Native historical-KF service did repeat (1,771 and 2,723 services with 29 and
47 full epochs in the active scenes), so normalized ERCB changed 9 and 16
opportunity rows. The quality deltas are still below the `fast-straight`
negative-control variation, where the selection trace was identical but PSNR
differed by 0.021557 dB.

The ticket performed 455/332/470 clones in normalized arms and added no render
or Adam step. Its mean quality effect is `+0.002896 dB`, also noise-level.

## Decision and claim boundary

Exp109 remains valid evidence that the dense-evidence topology path is active
and preserves the full 17-scene R4 gain. Exp110 shows that the current gain
cannot honestly be attributed to normalized ERCB, and the ticket has not yet
shown causal quality improvement. ERCB should not be advertised as a main
quality contribution from this configuration.

The next safe Track-A experiment will preserve one causal first service for
new views and spend only a common, fixed fraction of already-existing flexible
historical work on repeat dense service selected by normalized ERCB. It must
add no physical render, retain the recent-keyframe floor, use no scene-specific
cutoff, and pass the same R4 quality/fairness gate before a panel expansion.
