# exp97 — shadow-count regular filter-prune isolation

- Date: 2026-09-24
- Status: RPNG `table_01` PASS; single-scene diagnosis only
- VIGS source: `f0e7f7a68f88e7277083995b9f367e7eafec17f5`
- Runner: `benchmarks/online_gs/run_exp97_shadow_filter_prune_isolation.py`
- Results: `results/experiments/exp97_shadow_filter_prune_isolation/`
- Summary: [metrics and accounting](benchmark_custom/exp97_shadow_filter_prune_isolation_20260924/summary.md)

## Why Exp97 was needed

Exp96 showed that physically skipping filter-prune changes R4's future
topology cadence because the observation controller consumes the actual
post-prune count.  Exp97 retains prune candidates in the trainable tensor but
feeds the controller the counterfactual post-filter count.  It fails closed if
the independent KF cap also deletes rows, because overlap would make that
counterfactual ambiguous.

## Result

| Run | PSNR | SSIM | LPIPS | Renders | Adam | GS |
|---|---:|---:|---:|---:|---:|---:|
| Exp97 shadow no-filter | **25.680925** | **0.851117** | **0.149576** | 38,302 | 3,030 | 463,543 |
| Exp95 normalized R4 | 25.585018 | 0.847780 | 0.153816 | 38,302 | 3,030 | 417,656 |
| Fresh vanilla | 23.964263 | 0.794350 | 0.198004 | 38,302 | 3,027 | 183,283 |

Exp97 is **+0.095907 dB** over Exp95 R4 and **+1.716662 dB** over fresh
vanilla.  Both independent saved-map evaluations are exactly 25.680925 dB.
All isolation checks pass: same archive/config/event stream, exact physical
renders and Adam work, identical dense and keyframe opportunity skeletons,
zero-tail, held-out disjointness, normalized ERCB, and final-generation
topology event count 2/2 versus control.

Across all recorded mapper generations, 86,782 ordinary filter candidates
were withheld and zero physically removed; clone/split still added 31,527 rows
and removed 4,780 split parents.  In the final generation, 57,770 filter
candidates were retained.  Generation accounting is now explicit rather than
inferred by summing reset logs.

## Cost and interpretation

The final map has 45,887 more Gaussians than Exp95 (+11.0%).  Peak allocated
CUDA memory rises 5.092→5.454 GB (+7.1%), peak reserved memory
8.670→10.100 GB (+16.5%), and mapping wall time 165.90→176.08 s (+6.1%).
Therefore aggressive ordinary pruning is not the source of R4's quality gain;
on this scene it slightly hurts all three rendering metrics.  Removing it
entirely is nevertheless not the final method because it spends meaningful
memory and time and has only been tested on one development scene.

The next method experiment should replace global add/remove turnover with a
bounded current-view local birth operator derived from public author code,
then reintroduce evidence-based bounded cleanup separately.  It must preserve
the same 2-event controller trace and fixed physical render budget.
