# exp104 — active dense/ERCB bounded topology ticket

- Date: 2026-09-24
- Status: RPNG `table_01` quality/structure gate **PASS**; transfer pending
- VIGS source: `913b9da2`
- Runner: `benchmarks/online_gs/run_exp104_dense_topology_ticket.py`
- Results: `results/experiments/exp104_dense_topology_ticket/`
- Summary: [metrics and ticket events](benchmark_custom/exp104_dense_topology_ticket_20260924/summary.md)
- Author-code basis: Taming 3DGS
  `fd0f7d9edfe135eb4eefd3be82ee56dada7f2a16` weighted multinomial sampling
  without replacement; TileGS `7f109a403ed522ba5ec7610f3d4778c363b68b11`
  persistent per-Gaussian evidence concept

## Method

Exp104 keeps normalized R4 birth, pruning, observation-driven phase state, and
native topology cadence. Every paid normalized-ERCB dense backward nominates
the top 1,024 finite positive `f_dc`-gradient rows. Point identities are scoped
to the active map generation, and a point becomes eligible only after
nomination by at least two distinct dense UIDs.

At an existing native topology event, the mutation ticket is not a scene-sized
constant: it equals that event's ordinary clone+split additions. The ported
Taming operator samples eligible small-Gaussian parents with count weights and
`replacement=False`. Selected parents are cloned with fresh stable point IDs
and optimizer state. Dense RGB contributes no depth, no new render, and no
extra Adam step. Hard pruning is not introduced.

## Result

| Run | PSNR | Renders | Adam | Final GS | Mapping wall |
|---|---:|---:|---:|---:|---:|
| Exp104 dense ticket | **25.595663** | 38,302 | 3,030 | 419,366 | 168.42 s |
| Exp95 normalized R4 | 25.585018 | 38,302 | 3,030 | 417,656 | 165.90 s |
| Fresh vanilla | 23.964263 | 38,302 | 3,027 | 183,283 | — |

Candidate−R4 is **+0.010645 dB** and candidate−vanilla is **+1.631399 dB**.
Saved-map double evaluation and all archive/config/event/opportunity/render/
Adam/topology-count/disjoint/zero-tail checks pass.

The controller observed all 269 dense opportunities and all four lifetime
topology events. The first three events had no two-view persistent candidate
and correctly performed no extra mutation. At the final-generation second
event, 2,250 repeated candidates existed, 1,706 passed the standard small-scale
clone qualifier, and all 1,706 were selected without replacement. Final GS is
only 1,710 (+0.41%) above R4. Mapping wall is +2.51 s (+1.52%), peak allocated
memory +0.54%, and peak reserved memory −0.82% (allocator noise included).

## Decision

This is the first implementation in which dense views and normalized ERCB
materially control topology while the historical R4 quality advantage remains.
The +0.0106 dB over R4 is noise-scale on one scene, so it is a preservation and
activation result—not evidence that the ticket improves quality. Freeze this
common rule and transfer it without scene tuning. Stop and diagnose if any
scene falls more than 0.5 dB below its R4 paired control. Do not add hard prune
or a denser ticket before transfer establishes the sign and cost distribution.
