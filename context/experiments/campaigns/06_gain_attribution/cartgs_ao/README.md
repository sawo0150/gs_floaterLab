# CaRtGS adaptive optimization as a drop-in sampler — UTMM seed 0 (2026-10-06)

PREREG: [PREREG.md](PREREG.md) (+ Amendments 1-3). Patch `cartgs_ao_patch.py` mirrors the released scheduler
(github.com/DapengFeng/cartgs 547c905, `useOneRandomSlidingWindowKeyframe`), per KF and dense pool. Results
`results/campaigns/gain_attribution/cartgs_ao/v1/`. 8 runs, all valid; borrow share (views taken out of the uses rule
because every view with uses left was already in the batch) 13–27% (short sequences highest: fast-straight 26%,
slow-straight-1 27%).

UTMM 8 scenes, seed 0, held-out views from the final map's first trained view, gaps vs offline seed 0:

| arm | mean PSNR | gap first 15% | gap 30–90% | gap MAD | front-loading | dense count CV |
|---|---:|---:|---:|---:|---:|---:|
| uniform_iid | 20.588 | −1.17 | −0.75 | 0.654 | 0.191 | 0.89 |
| uniform_k16 | **20.841** | **−0.23** | −0.70 | **0.478** | 0.218 | 0.75 |
| CaRtGS-AO | 20.748 | −1.02 | **−0.59** | 0.775 | **0.189** | **0.64** |
| ERVS τ=4 | 20.725 | −0.98 | −0.62 | 0.671 | 0.210 | 0.71 |

CaRtGS-AO − uniform_iid +0.160 (7/8), − uniform_k16 −0.094 (3/8), − ERVS +0.023 (5/8).
**Reading (seed 0, 8 scenes).** CaRtGS-AO and ERVS behave alike: both balance per-view counts (CaRtGS-AO more strongly),
both lift the 30–90% stretch and both lose the earliest views; mean PSNR is indistinguishable (+0.02). Neither beats
the same-batch uniform group sampler, which keeps the earliest views closest to offline. The borrow share means the
CaRtGS rule is only partly in force on short sequences.
