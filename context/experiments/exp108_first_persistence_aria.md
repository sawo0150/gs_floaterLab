# exp108 — first-persistence ticket transfers unchanged to Aria

- Date: 2026-09-24
- Status: Aria `aria1253` quality/structure/fresh-pair gate **PASS**
- VIGS code source: `f6a90853` (`afbfe52f` adds documentation only)
- Lab source lock: `d8b5a0a` plus the new Exp108 runner
- Runner: `benchmarks/online_gs/run_exp108_first_persistence_aria.py`
- Results: `results/experiments/exp108_first_persistence_aria/`
- Summary: [metrics](benchmark_custom/exp108_first_persistence_aria_20260924/summary.md)

## Frozen method

No Aria-specific parameter was introduced. The run uses exactly the Exp106/107
rule: normalized-variance ERCB dense renders nominate generation-scoped point
IDs; evidence must recur for at least two distinct dense view UIDs; the first
qualifying event in a map generation may spend one top-1,024 weighted
without-replacement small-clone ticket. The clone implementation is adapted
from the pinned Taming 3DGS author code and preserves all existing VIGS native
densification statistics.

## Result

| Run | PSNR | SSIM | LPIPS | Physical renders | Adam steps | Final GS |
|---|---:|---:|---:|---:|---:|---:|
| Exp108 first-persistence | **25.755865** | **0.824987** | **0.319630** | 13,620 | 1,055 | 177,207 |
| Exp108 fresh vanilla | 23.979334 | 0.779900 | 0.408106 | 13,620 | 1,071 | 175,878 |
| Exp94 normalized R4 | 25.775702 | — | — | 13,620 | 1,055 | 177,099 |

Candidate−fresh vanilla is **+1.776532 dB**, SSIM **+0.045087**, and LPIPS
**−0.088476**. Candidate−exact R4 is **−0.019837 dB**, far inside the
predeclared −0.5 dB stop threshold. It is also +0.032121 dB over Exp105's
native-event-only precursor, though this small single-run delta is not treated
as a quality claim.

The contribution is active: the first persistent event in map generation 2
had 148 repeated candidates, 70 standard small-scale eligible candidates, and
performed 70 clones. It added zero render and zero Adam step. Candidate and
vanilla saved-map double evaluation, exact physical-render matching, frozen
archive/config, dense/keyframe opportunity parity, held-out disjointness, and
zero-tail checks all pass.

## Decision

The unchanged common rule has now passed one development scene in each dataset
family. UTMM shows that it activates when native topology events finish early;
RPNG preserves the core +1.6 dB R4 advantage; Aria preserves +1.78 dB against
a fresh vanilla pair. Freeze this configuration for the 17-valid-scene
B-track panel. The panel must use new candidate/vanilla pairs and stop on any
scene below exact R4 by more than 0.5 dB. These mapping-only results still do
not prove strict-live latency or that the ticket itself improves over R4.
