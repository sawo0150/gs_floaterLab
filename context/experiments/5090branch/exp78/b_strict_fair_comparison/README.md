# exp78 B — matched strict-streaming comparison

The method-independent evaluation UID manifests were locked before exp78 model
tuning.  They select zero-based frame indices divisible by five plus the final
frame.  Every listed UID must be excluded from Gaussian supervision and birth;
tracking may still observe it.

- Manifest index: `manifests/manifest_index.json`
- Development sequences: RPNG `table_01`, `table_06`; UTMM `ego-drive`,
  `square-2`
- Validation sequences: the remaining six RPNG and six UTMM sequences
- Historical exp77 work has already exposed all sequences.  “Validation” here
  means untouched by tuning after the exp78 manifest lock, not globally unseen.

Required per-arm telemetry is PSNR/SSIM/LPIPS, ATE/Recall, wall time/FPS, input
lag, peak memory, Adam steps, rasterized view-updates, unique mapped views and
Gaussian count. B primary uses the fixed-work causal contract. Mapper-only 1x
and 1.5x results are secondary throughput diagnostics; C is the end-to-end
strict-streaming result. All use identical input/preprocessing/hardware state
and zero optimizer work after the final snapshot.

The mapper-independent frozen archive schemas v2/v3 and common timeline
scheduler are operational. The pinned one-arm runner is
`benchmarks/online_gs/run_exp78b_matched_mapping.sh`; it validates archive
hashes/causality/split isolation, refuses output overwrite, checks zero-tail,
and evaluates the predeclared held-out manifest. The current 1.5× RPNG paired
result is recorded in [Lane D1](../d_dataset_general_optimization/rpng_mapping_only_ablation.md).

## 2026-09-14 — frozen causal input lock complete

All 16 seed-0 tracker archives now exist under
`results/experiments/exp78/b_strict_fair_comparison/frozen_tracker/official_22ffe24_trt/`
and pass `exp78b_frozen_tracker_validation_v2`. They were captured with the
official VIGS tracker at commit `22ffe24c6df81d0bf63bd20057565c00c51d2996`
and the RTX 5090 TensorRT runtime profile
`results/experiments/exp78/a_paper_reproduction/trt_profiles/official_readme_dynamic_rtx5090`.
Capture used an archive sink with no Gaussian optimizer.

| Dataset / sequence | Role | Schema | Frames | Events | Dense unique | Eval held-out | Archive manifest SHA-256 prefix |
|---|---|---|---:|---:|---:|---:|---|
| RPNG `table_01` | dev | v2 | 2,506 | 283 | 1,728 | 502 | `cb7e31db582d` |
| RPNG `table_02` | validation | v2 | 2,914 | 396 | 1,999 | 584 | `e08428c63c97` |
| RPNG `table_03` | validation | v3 | 7,006 | 614 | 5,105 | 1,402 | `307eef0076da` |
| RPNG `table_04` | validation | v3 | 6,068 | 494 | 4,467 | 1,215 | `1f56dd70b341` |
| RPNG `table_05` | validation | v3 | 6,164 | 387 | 4,626 | 1,234 | `3c85628754e6` |
| RPNG `table_06` | dev | v2 | 2,767 | 258 | 1,989 | 555 | `4cca088609e3` |
| RPNG `table_07` | validation | v3 | 4,784 | 250 | 3,624 | 958 | `bfa9c64c323e` |
| RPNG `table_08` | validation | v3 | 8,484 | 679 | 6,292 | 1,698 | `1a65a6e3baa9` |
| UTMM `ego-centric-1` | validation | v3 | 1,535 | 48 | 1,146 | 308 | `77b8b9a843a8` |
| UTMM `ego-centric-2` | validation | v3 | 1,298 | 57 | 979 | 261 | `9697429d3c54` |
| UTMM `ego-drive` | dev | v3 | 1,399 | 86 | 998 | 281 | `b76d81746d8e` |
| UTMM `fast-straight` | validation | v2 | 332 | 12 | 226 | 68 | `1162b1659a92` |
| UTMM `slow-straight-1` | validation | v3 | 393 | 3 | 288 | 80 | `7843e9df6b15` |
| UTMM `slow-straight-2` | validation | v3 | 597 | 13 | 406 | 121 | `b213977e13cb` |
| UTMM `square-1` | validation | v3 | 1,614 | 79 | 1,219 | 324 | `db5de0b9d08c` |
| UTMM `square-2` | dev | v3 | 1,219 | 70 | 913 | 245 | `93eeca4b273d` |

Aggregate audit: **16/16 valid**, 49,080 frames, 3,729 tracker events,
36,005 unique causally available dense views and 9,836 held-out views.
Filtered held-out mapping overlap, dense held-out overlap, future-order
violations, geometry tensor hash mismatches, capture-time Gaussian updates and
post-EOS Gaussian updates are all **zero**. The four v2 archives and twelve v3
archives have the same causal replay contract; v3 stores repeated geometry by
content-addressed split tensors to reduce duplication. Full hashes and every
payload check are retained in each archive's `validation.json`.

This lock freezes the tracker-side input only. It does **not** freeze the final
gsSLAM mapper. The current `gsslam` runner arm is a D1-style candidate backbone
(causal dense RGB, online-rank birth density, adaptive topology maturation and
dense/KF replay), not the final C1+C2+C3 model.

## Fairness correction before final B runs

The existing D1 evidence remains useful transfer evidence, but it used a
50 ms deadline reserve for vanilla and 20 ms for gsSLAM. Therefore its reported
mean `+1.598 dB` is **not** promoted as the final fair B result. Every new
B0/B1/B2/B3 primary run must use the same frozen archive hash, timeline,
1.5× mapper-service deadline, deadline reserve and zero-tail rule. Exact-work
matching is retained as a secondary mechanism ablation, not as the primary
real-time comparison.

The runner now defaults both methods to the common 50 ms reserve and records
`protocol=exp78b_matched_mapping_runner_v3_common_reserve`. A non-default
`EXP78B_COMMON_DEADLINE_RESERVE_MS` changes both arms together. Reproducing the
historical D1 split requires the explicit compatibility switch
`EXP78B_LEGACY_D1_RESERVE_SPLIT=1`; outputs produced with that switch cannot be
entered into the final B0--B3 primary table.

## Superseded time-matched parity gate and fixed-work correction

The first UTMM `square-2` 1.5x mapper-only pair failed the prospectively fixed
parity gate. Official/custom fixed-manifest metrics were respectively
20.3068/19.9218 dB, 0.67858/0.66300 SSIM and 0.38389/0.39589 LPIPS. Custom was
therefore -0.3850 dB, -0.01558 SSIM and +0.01201 LPIPS. More importantly,
official/custom work was 908/529 optimizer steps and 9,993/6,414 rasterized
view-updates; completed packets were 63/65. Both used archive SHA
`93eeca4b...`, 245 fixed views, zero mapping overlap and zero post-EOS updates.

First-divergence inspection found a concrete cause: the custom backend's
ordinary frontier branch had been changed from official 10 iterations to a
hard-coded 7 during earlier speed optimization. Thus an equal mapper-only
wall-clock does not hold work constant, and freezing the tracker also removes
the real tracker--mapper resource competition. Per user decision, B primary is
now fixed-work causal mapping isolation: official event-level initialization,
PGBA and 10-iteration regular mapping credit plus exact gradient-bearing view
credits. Mapper-only 1.5x/1.0x becomes a secondary throughput diagnostic, and
only C may support the end-to-end real-time claim. The failed pair is retained
as evidence for this protocol correction, not entered into B0--B3.

The replacement parity gate still uses UTMM `square-2` plus RPNG `table_01`,
with every custom contribution disabled and official YAML/policy restored.
Each fixed-work pair must have exact event/UID, optimizer-step and rasterized
view-update equality, no drop/preemption, zero future/held-out/EOS violations,
and metric deltas within 0.15 dB PSNR, 0.005 SSIM and 0.01 LPIPS. Final
Gaussian count may differ by at most 5%; failure triggers first-divergence
diagnosis before B0--B3.

## 2026-09-14 — fixed-work cross-dataset vanilla parity complete

The corrected `official_event_credit_v1` pair passed on the predeclared UTMM
`square-2` and RPNG `table_01` development scenes. The sequential scheduler
processed one causal event at a time; all packets completed and drop,
preemption, pending work, held-out supervision and tail updates were zero.
The custom path explicitly restored official frontier10, isotropic loss and
PGBA behavior while disabling dense replay, custom density, adaptive topology
and carving.

| Scene | Path | Fixed PSNR | SSIM | LPIPS | Adam step | View-update | Mapped UID | GS | Mapper wall |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| UTMM `square-2` | official | 20.6260 | 0.69125 | 0.36789 | 832 | 9,858 | 58 | 126,701 | 36.018s |
|  | custom vanilla | 20.6140 | 0.69116 | 0.36825 | 832 | 9,858 | 58 | 126,711 | 41.361s |
|  | custom-official | **-0.0121** | -0.00008 | +0.00036 | **0** | **0** | **0** | +10 | +5.343s |
| RPNG `table_01` | official | 24.1523 | 0.80187 | 0.19146 | 3,305 | 41,675 | 210 | 191,020 | 216.363s |
|  | custom vanilla | 24.1209 | 0.80145 | 0.19196 | 3,305 | 41,675 | 210 | 190,453 | 207.276s |
|  | custom-official | **-0.0313** | -0.00042 | +0.00050 | **0** | **0** | **0** | -567 | -9.087s |

Both machine-readable verifier outputs report `valid=true`; all event-level
step/view ledgers and mapped UID lists are exact matches. They are stored at
`parity_fixed_work_v2/{utmm/square-2,rpng/table_01}/parity_verification.json`.
The earlier fixed-work v1 official pilot is invalid because the first
unbounded scheduler version still preempted event 7 at a future reset. In v2,
unbounded sequential replay makes later controls unavailable until the current
packet completes, giving 67/67 and 279/279 packet completion respectively.

**Decision:** goal item 2 is complete. B0 official and B1 custom-vanilla paths
are equivalent under fixed work. The next gate is to define B2/B3 and the
pre-carve Full recipe on development scenes without looking at validation
metrics.

## 2026-09-14 — B primary corrected from exact-view to fixed-iteration

The first B2 implementation interpreted “fixed work” as exact equality of
both Adam steps and rasterized views. Dense RGB therefore replaced an existing
historical KF slot. The corrected v2 ledger was valid on UTMM `square-2`
(832/832 Adam, 9,858/9,858 total view-updates), but quality fell from B1
20.6140 to **20.4804 dB** (-0.1336); SSIM changed by -0.00025 and LPIPS by
+0.00765. The invalid v1 precursor had accidentally filled otherwise empty
global slots and produced 9,878 rather than 9,858 views; it is retained but
excluded.

This agrees with exp85-W/N: dense appearance is not a useful replacement for
the vanilla KF RGB-D/normal gradient. Per user decision, B primary is now
**fixed physical Adam iteration**, not exact view/FLOP matching. Every
candidate preserves the full B1 regular KF gradient and may add an explicitly
counted auxiliary dense render/backward inside the same Adam step. It may not
add another optimizer `step()`. B therefore isolates quality at the paper's
event-level mapping-iteration schedule; auxiliary views, mapper wall/GPU time,
peak VRAM and the 15/30/60 curve expose its additional compute. Only C can
support a real-time claim. Exact-view replacement remains a diagnostic
control, not B2.

Evidence:

- valid exact-view control:
  `development_fixed_work_v2/utmm/square-2/b2_rr_s0/`
- verifier: `fixed_work_verification_vs_b1.json` (`valid=true`)
- excluded over-budget precursor:
  `development_fixed_work_v1/utmm/square-2/b2_rr_s0/`

## 2026-09-14 — fixed-iteration B2 RR pilot

B2 preserves the official frontier10 KF RGB-D/normal backward and adds one
RR-scheduled dense batch of four, appearance-only, in the final regular
iteration. Each parameter group uses PCGrad with a 0.25 norm cap; dense
geometry ratio is zero. No idle replay or additional Adam step is allowed.

| Arm | PSNR | SSIM | LPIPS | Adam | Regular views | Auxiliary dense views | Total views | Mapper wall | GS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| B1 custom vanilla | 20.6140 | .69116 | .36825 | 832 | 9,858 | 0 | 9,858 | 41.361s | 126,711 |
| B2 RR | **20.6456** | **.69208** | **.36608** | 832 | 9,858 | 240 | 10,098 | 44.584s | 126,529 |
| B2−B1 | **+0.0316** | +.00092 | -.00217 | 0 | 0 | +240 | +240 | +3.223s | -182 |

The v2 verifier reports `valid=true`: every event has the same physical Adam
count, B2 never removes a B1 view, the 240-view difference exactly equals the
replay queue draw count, all 70 archive events and 62 post-metric packets
complete, and drop/preemption/pending/held-out overlap/future/tail violations
are zero. This confirms the comparison mechanism, but +0.0316 dB is not enough
to freeze the recipe.

The pilot intentionally used `dense_rr`, so the separately validated raw-IMU
dense rotation shaper was **not** active (`dense_pose_shaper=null`). The
official tracker-side IMU initialization was active and frozen in the common
archive. B3 will test the complete pre-carve candidate with strict-causal IMU
dense-pose shaping, global-seed/compute-paced C1 admission, ERCB ordering,
online-rank birth density and adaptive topology. C3 stays off until the
27 dB gate is met.

Evidence:

- run: `development_fixed_iteration_v1/utmm/square-2/b2_rr_s0/`
- verifier: `fixed_iteration_verification_vs_b1.json` (`valid=true`)
- fixed metrics: PSNR `20.6455698052`, SSIM `0.6920843207`, LPIPS
  `0.3660795619`

## 2026-09-14 — D1-style Full does not retain its old gain under fixed iterations

The first B3 pilot was protocol-valid for C1/IMU/ERCB but invalid as a test of
the complete D1 birth recipe. It reported UTMM `square-2` **21.0267 dB**
(B1 +0.4127), but `online_density_summary.unique_frames=0`: enabling
`adaptive_density` on the official YAML was a silent no-op because the
multiplier is called only inside the PPM birth branch. This v1 result remains a
diagnostic for C1/IMU/ERCB plus early topology freeze and is excluded from the
Full comparison.

The replay now pins the dataset-independent D1 birth bundle whenever
`density-policy=online_rank`: PPM sampling, regular/init downsample 256/64,
causal online rank mean 2.5/span 2.0 and growth allowance 2.0. It aborts if the
causal multiplier observes zero birth frames. Verifier v3 additionally checks
the complete bundle and nonzero causal observations. The corrected v2 Full
was then run without per-scene tuning on the two parity scenes:

| Scene / arm | PSNR | SSIM | LPIPS | Adam | Regular + aux views | Mapper wall | GS |
|---|---:|---:|---:|---:|---:|---:|---:|
| UTMM `square-2` B1 | 20.6140 | .69116 | .36825 | 832 | 9,858 + 0 | 41.361s | 126,711 |
| UTMM `square-2` corrected Full | 20.6070 | .68415 | .38970 | 832 | 9,858 + 144 | 42.085s | 98,606 |
| Full−B1 | **-0.0069** | -.00701 | +.02145 | 0 | 0 + 144 | +0.724s | -28,105 |
| RPNG `table_01` B1 | 24.1209 | .80145 | .19196 | 3,305 | 41,675 + 0 | 207.276s | 190,453 |
| RPNG `table_01` corrected Full | 24.0568 | .79535 | .20984 | 3,305 | 41,675 + 824 | 227.887s | 151,000 |
| Full−B1 | **-0.0641** | -.00610 | +.01788 | 0 | 0 + 824 | +20.611s | -39,453 |

Both verifier outputs are `valid=true`: event/Adam ledgers and all B1 regular
views are preserved, auxiliary dense work is exactly accounted, all packets
complete, and held-out overlap/future access/tail updates are zero. C1 admitted
7 of 913 dense candidates on square-2 and 38 of 1,728 on table_01; the latter
produced 824 ERCB auxiliary views. Online density observed 58 and 210 causal
birth frames respectively.

**Decision:** the historical D1 result (+1.135 dB on table_01, +1.598 dB mean,
up to +2.282 dB) does **not** survive the new fixed-iteration comparison on
either tested scene. The old result combined asymmetric 50/20 ms reserves,
method-dependent completed Adam work and a much larger dense-service regime;
it remains historical evidence, not the current gsSLAM claim. Do not freeze
this B3 recipe or proceed to validation. The next development step must recover
quality under the new ledger, starting from a contribution ablation that
separates early topology freeze/birth allocation from C1+IMU+ERCB rather than
increasing dense work indiscriminately.

Evidence:

- excluded density-no-op diagnostic:
  `development_fixed_iteration_v1/utmm/square-2/b3_precarve_s0/`
- corrected runs and `fixed_iteration_verification_vs_b1.json`:
  `development_fixed_iteration_v2/{utmm/square-2,rpng/table_01}/b3_precarve_s0/`

## 2026-09-14 — birth × dense interaction audit under legal topology

The historical D1 gain was re-audited before attributing its disappearance to
deadline reserve alone. On old `table_01`, vanilla and D1 completed almost the
same Adam work (1,910/1,908 steps), while D1 used 536 unique dense views and
retained 437,702 GS versus vanilla's 183,765. On old `table_02`, D1 even used
fewer Adam steps (1,685 versus 2,234) yet gained +2.282 dB. A same-gs-config
`table_06` reserve 0/20 ms control changed PSNR by only +0.051 dB. Thus reserve
and completed-work asymmetry make the old comparison non-final, but they do not
by themselves explain the full +1--2 dB signal. The stronger common signature
was broad causal dense coverage plus substantially retained map capacity after
a cadence-dependent global topology stop.

To test the user's concrete hypothesis, three fixed-iteration arms were run on
RPNG `table_01` seed 0 from the parity B1. All preserve B1's 3,305 Adam steps,
41,675 regular RGB-D/normal view-updates, event/packet order, zero-tail rule and
normal frontier densify/prune. They use no global topology freeze or absolute
phase cutoff.

| Arm | PSNR | delta vs B1 | SSIM | LPIPS | Aux dense | Unique dense | Final GS | Wall delta |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| B1 custom vanilla | 24.1209 | -- | .80145 | .19196 | 0 | 0 | 190,453 | -- |
| dense RR only | **24.1717** | **+0.0507** | .80266 | .19357 | 920 | 920 | 190,527 | +14.639s |
| online-rank birth only | 24.1064 | -0.0145 | .79638 | .20693 | 0 | 0 | 152,084 | +8.119s |
| online-rank birth + dense RR | 24.1122 | **-0.0088** | .79597 | .20877 | 920 | 920 | 151,727 | +20.762s |

The measured interaction is negative: the additive expectation from the two
single arms is +0.0362 dB, but the joint arm is -0.0088 dB, an interaction of
**-0.0450 dB**. Dense adds only +0.0058 dB on top of birth and does not retain
the newborn capacity because its projected auxiliary gradient is
appearance-only while ordinary topology pruning remains active. The joint arm
therefore ends at essentially the same reduced capacity as birth-only.

Frame-bin evidence also rejects a purely late-tail explanation. Old D1 minus
old vanilla was +1.240/+1.260/+1.323/+1.240/+0.630 dB over successive 500-frame
bins, whereas corrected Full minus B1 was
+0.015/-0.103/-0.045/-0.050/-0.140 dB. The historical benefit was global; it
was not reproduced by the legal two-way birth+dense combination.

**Decision:** the general idea that useful births need later dense
consolidation remains plausible, but the current `birth + appearance-only
dense` implementation is insufficient and is not the recovered D1 mechanism.
The next admissible mechanism is observation-conditioned newborn
consolidation: keep normal topology running, but make each newborn's prune
eligibility depend on causal repeated-view support/maturity, and direct dense
service toward visible under-supported newborn cohorts. This must use the
final-v7 unknown-horizon observation state, expose no scene/frame/count cutoff,
and be evaluated first on development scenes under the same fixed-iteration
ledger. No carve is added before the 27 dB gate.

Evidence:

- runs: `results/experiments/exp78/b_strict_fair_comparison/development_fixed_iteration_v3/rpng/table_01/{b2_rr_s0,b2_birth_s0,b2_birth_rr_s0}/`
- per-run verifier: `fixed_iteration_verification_vs_b1.json` (`valid=true`)
- historical D1 telemetry: `../d_dataset_general_optimization/rpng_mapping_only_ablation.md`

## 2026-09-14 — observation-conditioned newborn protection pilot

The next legal birth+dense coupling was implemented without restoring the old
global topology freeze.  Each keyframe-origin lineage is temporarily excluded
from clone/split, opacity/size pruning and the adaptive per-lineage cap until
two distinct, already-selected causal dense observations touch one of its
interval endpoints.  Normal frontier densify/prune continues for every mature
lineage.  The fallback maturity clock is final-v7's two completed replay
opportunity passes; it was not reached in these growing unbounded pools.  The
controller reads no dataset name, frame/iteration boundary, stream horizon or
Gaussian-count threshold.

Both valid seed-0 runs preserve every B1 Adam step and regular RGB-D/normal
view, add the same RR projected-dense batch4/last1/cap0.25 service as the prior
birth+dense arm, and pass the fixed-iteration verifier including zero-tail,
zero held-out overlap, no drop/preemption and no global freeze.

| Scene / arm | PSNR | delta vs B1 | SSIM delta | LPIPS delta | Adam | Regular + aux views | Final GS | Mapper wall delta |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| UTMM `square-2` B1 | 20.6140 | -- | -- | -- | 832 | 9,858 + 0 | 126,711 | -- |
| protected birth+dense | **20.7506** | **+0.1366** | -.00092 | +.00810 | 832 | 9,858 + 240 | 110,872 | +0.274s |
| RPNG `table_01` B1 | 24.1209 | -- | -- | -- | 3,305 | 41,675 + 0 | 190,453 | -- |
| protected birth+dense | **24.2187** | **+0.0977** | +.00059 | +.00870 | 3,305 | 41,675 + 920 | 181,927 | +42.290s |

The protection changes the interaction sign on both development scenes.  It
improves the previous unprotected birth+dense arm by +0.1435 dB on square-2
and +0.1065 dB on table_01.  However, it still does not reproduce historical
D1's +1--2 dB: final capacity remains below B1, and LPIPS regresses on both
scenes.  Table_01 observed 920 unique RR draws and 23 topology queries, with
12--22 lineages protected per query and 17 still protected at the final
topology event.  Endpoint selection is therefore a useful retention signal
but not yet proof that the newborn rows were visible or received effective
appearance updates.

**Decision:** birth and dense need to be coupled, but the current evidence says
that coupling is necessary rather than sufficient.  Do not freeze this recipe
or run validation.  The next development step is to replace endpoint-draw
maturity with measured newborn-row visibility/gradient service and prioritize
the already-arrived dense observations that actually supervise unsupported
lineages.  The number of Adam iterations, B1 regular views and global topology
behavior remain unchanged.

Evidence:

- valid runs and verifier outputs:
  `results/experiments/exp78/b_strict_fair_comparison/development_fixed_iteration_v5/{utmm/square-2,rpng/table_01}/b2_birth_rr_consolidation_s0/`
- excluded wiring pilot: `development_fixed_iteration_v4/utmm/square-2/`
  (`topology_queries=0` after the mapper reset; no metric is used)

## 2026-09-14 — dense strength and fixed-iteration allocation diagnosis

Two square-2 controls isolate whether the remaining D1 gap is simply too weak
a dense gradient or too little dedicated dense work.  Both retain the same
online-rank birth and observation-conditioned newborn protection as the pilot,
use the frozen causal tracker archive, and pass the machine fixed-iteration
contract with 832 Adam steps, zero held-out overlap and zero tail update.

| Arm | PSNR | delta vs B1 | SSIM delta | LPIPS delta | Adam | Regular + dense views | Final GS |
|---|---:|---:|---:|---:|---:|---:|---:|
| B1 custom vanilla | 20.6140 | -- | -- | -- | 832 | 9,858 + 0 | 126,711 |
| protected projected dense, cap 0.25 | 20.7506 | +0.1366 | -.00092 | +.00810 | 832 | 9,858 + 240 | 110,872 |
| protected projected dense, cap 1.0 | **20.7844** | **+0.1705** | -.00051 | +.00818 | 832 | 9,858 + 240 | 110,445 |
| protected dedicated dense allocation | 20.3630 | **-0.2510** | -.01713 | +.03906 | 832 | 7,527 + 180 | 106,732 |

Removing the projected appearance-gradient cap adds only **+0.0339 dB** over
the cap-0.25 protection arm and retains fewer Gaussians.  Dense gradient
magnitude is therefore not the missing one-decibel mechanism.  Allocating
three of each event's fixed Adam iterations exclusively to appearance-only
dense replay removes 2,331 regular RGB-D/normal view-updates and is strongly
harmful despite 180 dedicated dense views.  The regular keyframe geometry and
normal service must not be traded away in B.

**Decision:** keep B1's complete regular work and the full-cap projected dense
gradient, but make newborn maturity depend on actual Gaussian-row visibility
and committed appearance gradient rather than causal-interval endpoint draws.
This tests whether premature lineage release, not dense gradient strength or
iteration count, is what prevents D1's large map capacity from surviving.

Evidence:

- full-cap valid run:
  `results/experiments/exp78/b_strict_fair_comparison/development_fixed_iteration_v6/utmm/square-2/b2_birth_rr_consolidation_fullcap_s0/`
- dedicated-allocation valid retry:
  `results/experiments/exp78/b_strict_fair_comparison/development_fixed_iteration_v7/utmm/square-2/b2_birth_rr_consolidation_dedicated_s0_retry1/`
- excluded first dedicated launch:
  `development_fixed_iteration_v7/utmm/square-2/b2_birth_rr_consolidation_dedicated_s0/`
  (pre-run validator wiring rejected it; no metric was produced)

## 2026-09-14 — row-visible evidence with lineage-level release is too coarse

The first committed-service implementation replaced endpoint draws with actual
visibility plus a non-zero projected `f_dc` gradient and published evidence
only after the shared Adam step.  It is protocol-valid, but still released an
entire keyframe-origin lineage as soon as any row in that lineage accumulated
two dense UIDs.  On square-2 the number of protected lineages consequently
collapsed from 10 at initialization to 1 at the next topology event.

The fixed-iteration verifier is valid (Adam 832, regular 9,858 + dense 240,
no drop/overlap/freeze/tail), but fixed held-out quality is only **20.6704 dB**
(B1 **+0.0564 dB**, prior full-cap lineage protection **-0.1140 dB**) with
100,622 final GS.  SSIM/LPIPS deltas versus B1 are -.00577/+.01834.  The run
therefore isolates a granularity error rather than disproving service-based
protection: one visible old row must not certify every unobserved newborn row
sharing its origin.

**Decision:** reject lineage-wide release.  The next implementation keys
maturity by stable Gaussian `point_id`, permits at most one service certificate
per point per committed Adam step, and protects each immature point from
clone/split, opacity/size pruning, non-visible opacity reset, and the
content-adaptive cap.  It retains the same no-cutoff, unknown-horizon two-pass
fallback.

Evidence:

- valid run and verifier:
  `results/experiments/exp78/b_strict_fair_comparison/development_fixed_iteration_v8/utmm/square-2/b2_birth_rr_consolidation_rows_s0/`

## 2026-09-14 — uniform Gaussian birth 2x control

At the user's request, a simpler birth-only arm removes Sobel-rank allocation
and assigns every causal keyframe the same PPM birth multiplier 2.0
(`mean=2.0`, `span=0.0`).  Dense replay and newborn protection are both off;
the normal frontier topology and B1's exact 832 Adam / 9,858 regular view work
remain unchanged.

The fixed-iteration verifier is valid, but fixed held-out quality is
**20.3848 dB**, or **-0.2292 dB** versus B1.  SSIM/LPIPS also regress by
-.01838/+.04562.  Although birth is doubled, the final map contains only
86,648 GS versus B1's 126,711: ordinary prune/cap removes enough immature
births that the system ends with 40,063 fewer points.

**Decision:** reject uniform 2x as a standalone recipe.  Birth quantity is not
the missing D1 mechanism; survival after causal supervision is.  Continue the
predeclared point-ID service protection, and only revisit a fixed multiplier
inside a successful birth+dense survival coupling rather than sweeping birth
counts.

Evidence:

- valid run and verifier:
  `results/experiments/exp78/b_strict_fair_comparison/development_fixed_iteration_v9/utmm/square-2/b2_birth_uniform2_s0/`

## 2026-09-14 — stable point-ID direct service does not recover capacity

The follow-up replaced lineage-wide maturity with a stable Gaussian
`point_id`.  A point could receive at most one certificate per committed Adam
step and required visible, non-zero projected appearance gradients from two
distinct dense UIDs.  Immature points were protected individually from
clone/split, opacity/size pruning, non-visible opacity reset, and the adaptive
cap.  It uses no frame, iteration, stream-horizon, or Gaussian-count cutoff and
does not freeze normal frontier topology.

The square-2 fixed-iteration verifier is valid (Adam 832, regular 9,858 + dense
240, zero drop/overlap/freeze/tail), but held-out quality is **20.6189 dB**, only
**+0.0050 dB** versus B1.  SSIM/LPIPS regress by -.00569/+.01744 and final GS
falls from B1's 126,711 to 101,464.  Direct service matured 119,741 points; only
3,421 points remained protected by the third topology query and 11,050 by the
last.  Thus the finer identifier fixed the lineage granularity bug, but the
two-view appearance criterion certifies most visible points too quickly and
still does not preserve D1-scale capacity.

**Decision:** reject direct two-view point maturity as the missing D1
mechanism and pause further protection-controller invention.  Return to a
forensic reconstruction of the historical D1 source/state and identify the
first topology/capacity divergence under the fixed event ledger before changing
another rule.

Evidence:

- valid run and verifier:
  `results/experiments/exp78/b_strict_fair_comparison/development_fixed_iteration_v10/utmm/square-2/b2_birth_rr_consolidation_points_s0/`

## 2026-09-15 — D1 state-replay reconstruction v1: contract valid, allocation too dense

The historical source audit recovered the exact D1 mapper components rather
than approximating them from the card: backend and scheduler are Git object
`9c1e2767`, the Gaussian model is object `b05e981d`, the content-budget file is
object `362dcf67`, and the currently retained `demo.py` has the exact runtime
SHA-256.  The historical final-v7 RPNG YAML also still matches its recorded
SHA-256.  The prior "corrected D1-style Full" was therefore not an exact D1
execution problem: its projected auxiliary gradient and compute-paced 36-view
admission did not reproduce D1's independent appearance-only replay steps.

The first legal reconstruction keeps the fixed event Adam ledger, online-rank
birth and causal IMU-shaped RR dense input, but replaces the deprecated global
freeze with final-v7's observation-only unknown-horizon topology state.  On
square-2 it is verifier-valid: Adam 832/832, identical event/KF/origin ledger,
drop/preemption/overlap/tail 0, auto-freeze 0, and two native topology events.
It then allocates 510/832 Adam steps (61.3%) to one-view dense replay and keeps
114,030 GS.

Held-out quality is **20.2397 dB**, **-0.3743 dB** versus B1; SSIM/LPIPS deltas
are -.01447/+.06661.  This does not reject the historical D1 mechanism.  It
isolates an adapter error: final-v7 pressure handling converted every remaining
event iteration to replay, whereas historical table_01 used 535/1,908 (28.0%)
dense steps and retained frontier work.  The next arm executes the controller's
already-defined BALANCED allocation (`sqrt(window)` frontier, remaining fixed
credit replay) instead of an all-replay branch; no threshold or scene knob is
introduced.

Evidence:

- valid run and verifier:
  `results/experiments/exp78/b_strict_fair_comparison/development_fixed_iteration_v11/utmm/square-2/d1_fixed_state_rr_imu_s0/`

## 2026-09-15 — D1 state-replay reconstruction v2: balanced allocation still loses capacity

The second reconstruction uses the controller's pre-existing BALANCED rule
instead of sending all post-transition work to replay.  Each fixed event keeps
the exact B1 physical Adam credit; in BALANCED, `sqrt(window)` iterations use
the normal multi-view frontier objective and the remaining iterations use
independent one-view appearance replay without advancing the native topology
clock.  No scene-dependent threshold, automatic freeze, post-stream work, or
extra Adam credit is used.

The machine verifier passes every fixed-iteration-allocation requirement:
Adam 832/832, exact event/KF/origin ledger, mapping/evaluation disjointness,
causal IMU shaping, non-zero online-density observations, and zero
drop/preemption/overlap/tail.  The run performs 350 replay steps (42.1% of
Adam work) and 5,658 total view updates.

Quality nevertheless falls to **20.2245 dB**, **-0.3895 dB** versus B1;
SSIM/LPIPS deltas are -.02256/+.06715.  The decisive divergence is structural:
the controller remains BALANCED while the causal dense pool keeps growing, so
a third native topology event at frame 1042 prunes 104,059 Gaussians to 70,375.
The final map has only **80,335 GS**, versus B1's 126,711 and historical D1's
single topology event followed by 437,702 retained GS.  The v1 allocation
diagnosis was therefore incomplete: balanced frontier work is necessary, but
the current adapter still fails to transfer final-v7's observation-certified
topology state into the backend's topology cadence.

**Decision:** reject v2 as a quality recipe.  Before changing another birth or
dense parameter, audit the final-v7 controller tests and Git history to decide
whether BALANCED is intended to close topology while retaining frontier
optimization.  Any correction must be driven only by the existing repeated
topology/capacity state and must not reintroduce an absolute frame, iteration,
stream-fraction, event-count, or Gaussian-count cutoff.

Evidence:

- valid run and verifier:
  `results/experiments/exp78/b_strict_fair_comparison/development_fixed_iteration_v12/utmm/square-2/d1_fixed_state_rr_imu_balanced_s0/`

## 2026-09-15 — D1 state-replay reconstruction v3: final-v7 topology state is now effective

The controller/source audit found a missing state connection rather than a
missing historical D1 artifact.  `TopologyReplayController` documented
BALANCED as the post-topology overlap phase, but the backend still allowed its
sublinear frontier iterations to advance into another native densify/prune.
Earlier wall-paced final-v7 runs usually completed replay epochs and reached
REPLAY before that cadence, hiding the discrepancy; the deterministic fixed
event ledger exposed it because newly arriving dense views kept the unbounded
shuffle epoch open.

The backend now permits topology mutations only in the controller's FRONTIER
phase.  BALANCED retains causal birth, `sqrt(window)` multi-view frontier Adam,
and independent appearance replay, so this is not a mapping stop.  The state
transition still uses only two repeated native topology observations and
relative capacity recovery; no frame, iteration, horizon, topology-event,
Gaussian-count cutoff, or runtime freeze option was added.  Scheduler tests
were extended and **71/71 pass**.

On the same square-2 archive and allocation as v2, the third prune disappears:
topology events fall 3→2 and final GS rises **80,335→113,965**.  Held-out PSNR
rises **20.2245→20.7450 dB (+0.5205)** and is again **+0.1311 dB over B1**.
The fixed-iteration-allocation verifier is valid: Adam832/832, exact event/KF/
origin ledger, causal IMU and online density non-zero, and no auto-freeze,
drop, overlap, or tail update.  SSIM/LPIPS are still -.00559/+.04670 versus B1,
and the map remains 12,746 GS smaller, so the historical +1 dB target is not
yet accepted.

**Decision:** retain the state-connection fix and promote it to the historical
RPNG `table_01` reproduction gate, where D1 originally achieved +1.135 dB.
Do not add a birth/dense scalar sweep before that direct test.

Evidence:

- valid run and verifier:
  `results/experiments/exp78/b_strict_fair_comparison/development_fixed_iteration_v13/utmm/square-2/d1_fixed_state_rr_imu_topology_state_s0/`

## 2026-09-15 — D1 state-replay reconstruction v4: RPNG restores capacity, not quality

The direct RPNG `table_01` gate used the unchanged v3 state connection and the
same frozen official tracker archive.  The fixed-iteration-allocation verifier
passes every required check: Adam 3,305/3,305, exact event/KF/origin ledgers,
causal IMU shaping, non-zero online-density evidence, mapping/evaluation
disjointness, and zero auto-freeze, drop, preemption, overlap and tail update.

The state controller permits two native topology events, pruning
38,202→28,938 GS at frame 286 and 52,726→44,722 GS at frame 386, then closes
further topology while retaining causal birth and optimization.  Final
capacity reaches **429,801 GS**, very close to historical D1's 437,702 and
239,348 above B1's 190,453.  Capacity recovery alone nevertheless fails the
quality gate:

| Arm | PSNR | delta vs B1 | SSIM | LPIPS | Adam | View updates | Dense steps | Final GS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| B1 custom vanilla | 24.1209 | -- | .80145 | .19196 | 3,305 | 41,675 | 0 | 190,453 |
| historical wall-paced D1 | 25.3631 | +1.1354 vs old vanilla | .8355 | .1717 | 1,908 | 21,057 | 535 | 437,702 |
| fixed-work state reconstruction v4 | **23.7050** | **-0.4159** | .78417 | .22490 | 3,305 | 23,531 | 1,512 | 429,801 |

The result disproves the narrower hypothesis that final Gaussian count was
the missing one-decibel mechanism.  It also exposes a work-composition
divergence: historical D1 used 535/1,908 independent dense steps (28.0%) on
top of seven-iteration frontier packets, whereas the current BALANCED adapter
uses 1,512/3,305 dense steps (45.7%) by splitting each fixed ten-iteration
packet into roughly four frontier plus six replay iterations.  Repeated PGBA
pose revisions additionally consume 36×20 fixed structural-recovery steps.

**Decision:** keep the topology-state fix, but do not accept v4 as the Full
recipe.  A minimal-pruning control is justified because suppressing the second
8,004-point prune would predict a final count of about 437,805, almost exactly
historical D1.  It must use observation-relative state rather than a frame,
iteration, event-count, or absolute Gaussian cutoff.  In parallel, restore
historical independent dense service without taking frontier iterations away;
otherwise a pruning-only result cannot identify the old D1 mechanism.

Evidence:

- valid run and verifier:
  `results/experiments/exp78/b_strict_fair_comparison/development_fixed_iteration_v13/rpng/table_01/d1_fixed_state_rr_imu_topology_state_s0/`

## 2026-09-15 — D1 minimal-pruning control: square-2 is positive but not sufficient

The minimal-pruning control does not alter the configured opacity/size
thresholds and does not use a frame, iteration, horizon, topology-event count,
or absolute Gaussian threshold.  After the first native net-prune establishes
its own pre-prune capacity as a relative target, two distinct later capacity
observations at or above that target close further topology.  Birth, sublinear
frontier optimization and causal appearance replay continue normally.

On square-2 the transition occurred after the first topology event
(26,960→23,154 GS) when the map twice re-observed recovery above 26,960 GS.
The fixed-iteration-allocation verifier remains valid with Adam832/832, exact
event/KF/origin ledgers, causal IMU, non-zero density and zero auto-freeze,
drop, overlap and tail update.

| Arm | PSNR | delta vs B1 | SSIM | LPIPS | Adam | Views | Dense | Topology | Final GS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| B1 custom vanilla | 20.6140 | -- | .69116 | .36825 | 832 | 9,858 | 0 | 3 | 126,711 |
| v3 two-topology state | 20.7450 | +.1311 | .68557 | .41495 | 832 | 5,658 | 350 | 2 | 113,965 |
| minimal-pruning control | **20.8586** | **+.2447** | .69024 | .41023 | 832 | 5,070 | 399 | 1 | 116,268 |

Removing the second prune adds **+0.1136 dB** over v3 and improves both SSIM
and LPIPS relative to v3, so excessive repeated pruning is a real part of the
lost gain.  It still explains only a small fraction of historical D1's
+1--2 dB, and LPIPS remains worse than B1.  The earlier transition also moves
49 more fixed steps from frontier to replay, so the effect is not a pure
Gaussian-count intervention.

**Decision:** retain this as a promising diagnostic, not a frozen recipe.
Promote it directly to RPNG `table_01`; if the gain remains small, stop pruning
variants and correct the larger historical work-composition mismatch by
keeping frontier work intact and scheduling dense as separately accounted
service.

Evidence:

- valid run and verifier:
  `results/experiments/exp78/b_strict_fair_comparison/development_fixed_iteration_v14/utmm/square-2/d1_fixed_state_rr_imu_minprune_s0/`

## 2026-09-15 — D1 minimal-pruning RPNG gate: exact historical capacity, worse quality

The same no-cutoff relative-capacity rule was transferred unchanged to RPNG
`table_01`.  It closes topology after the first 38,202→28,949 net-prune and
two distinct recoveries above the relative 38,202 target.  The machine
verifier is valid with Adam3,305/3,305, exact event/KF/origin ledgers, causal
IMU and density, and zero auto-freeze, drop, overlap and tail update.

The final model contains **437,816 GS**, only 114 more than historical D1's
437,702 and 8,015 more than the two-topology v4.  Quality moves in the opposite
direction:

| Arm | PSNR | delta vs B1 | SSIM | LPIPS | Adam | Views | Dense | Topology | Final GS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| B1 custom vanilla | 24.1209 | -- | .80145 | .19196 | 3,305 | 41,675 | 0 | 20 | 190,453 |
| v4 two-topology state | 23.7050 | -.4159 | .78417 | .22490 | 3,305 | 23,531 | 1,512 | 2 | 429,801 |
| minimal-pruning control | **23.2756** | **-.8453** | .77264 | .22614 | 3,305 | 22,775 | 1,575 | 1 | 437,816 |
| historical wall-paced D1 | 25.3631 | +1.1354 vs old vanilla | .8355 | .1717 | 1,908 | 21,057 | 535 | 1 | 437,702 |

Minimal pruning therefore loses **0.4294 dB** relative to v4 despite matching
historical D1 capacity almost exactly.  Together with the square result, this
shows that repeated pruning can be mildly harmful on one short development
scene but is not the transferable key and can be beneficial cleanup on RPNG.
The old gain cannot be attributed to final Gaussian count or topology count.

**Decision:** reject minimal pruning as the recovered D1 mechanism and do not
run another pruning threshold/state variant.  Retain v4's two-observation
state connection.  The next forensic/implementation axis is the larger work
composition mismatch: historical D1 preserved seven multi-view frontier
iterations per processed keyframe packet and scheduled 535 independent dense
steps, while the current adapter replaces most ten-iteration packet credit
with one-view dense replay and performs 1,512--1,575 dense steps.  The next
arm must preserve the common B1 event Adam ledger while separately accounting
frontier and dense service instead of conflating them.

Evidence:

- valid run and verifier:
  `results/experiments/exp78/b_strict_fair_comparison/development_fixed_iteration_v14/rpng/table_01/d1_fixed_state_rr_imu_minprune_s0/`

## 2026-09-15 — exact historical D1 mapper restore: the +1 dB signal reproduces

Before adding another fixed-iteration adapter, the historical D1 source was
restored in an isolated detached worktree at
`/home/intern/VIGS-SLAM-historical-d1-9c1e2767`.  Commit `9c1e2767` contains
the exact historical `gs_backend.py`, `map_scheduler.py`,
`gaussian_model.py`, and `content_budget.py` objects.  Applying the preserved
34-line `demo.py` diff also reproduces all five SHA-256 values recorded by the
old runtime provenance.  The active integration worktree was not reverted or
overwritten.

The surviving frozen `table_01` tracker archive, final-v7 RPNG YAML and the
historical settings were then replayed unchanged: 1.5x wall pacing, 20 ms
deadline reserve, `dense_rr_imu`, appearance-only dense replay, causal online
rank birth with mean 2.5/span 2.0, no keyframes in replay, mapping after IMU
metric initialization, auto topology freeze, and zero tail.  Mapping completed
at 125.296/125.305 s with post-EOS updates 0.  The first topology event and
adaptive stop occurred at frames 286 and 408, and the final map contains
437,714 GS, only 12 more than the historical artifact.

| Arm | Fixed held-out PSNR | delta vs historical vanilla | SSIM | LPIPS | Adam | View updates | Dense completed | Final GS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| historical vanilla | 24.2278 | -- | -- | -- | 1,910 | -- | 0 | 183,765 |
| historical D1 artifact | 25.3631 | +1.1354 | .83550 | .17166 | 1,908 | 21,057 | 535 | 437,702 |
| exact-source restore | **25.4272** | **+1.1995** | .83528 | .17369 | 1,735 | 21,116 | 360 | 437,714 |

The restored run is **+0.0641 dB** over the original D1 artifact, so the old
+1 dB quality signal is reproducible and was not caused by a missing or
irrecoverable mapper checkout.  This also explains why the recent
fixed-iteration state emulations were unproductive: they were reproducing
selected state/count outcomes inside a different work-allocation path rather
than running the D1 implementation that generated the result.

One provenance limit remains.  The historical v13 replay-runner source was
not archived and its `.pyc` was overwritten; therefore this check used the
current v23 replay harness with one environment-selectable custom-root import,
while the five active mapper sources are exact.  The harness difference is
visible in work composition (1,735 vs 1,908 Adam and 360 vs 535 completed dense
steps), but not in the recovered quality or capacity.  Accordingly this is a
successful historical-reproduction diagnostic, **not yet the final fair B
claim**: the +1.1995 dB comparison still uses the old wall-paced/asymmetric
protocol.  The next B task is to preserve this exact mapper behavior while
accounting the same frontier and independent dense work under the common
fixed-iteration ledger, instead of continuing pruning/birth-controller
inventions.

Evidence:

- restored run:
  `results/experiments/exp78/b_strict_fair_comparison/historical_d1_exact_restore_v1/rpng/table_01/seed0/`
- source hashes and runner limitation: `source_manifest.txt`
- runtime contract and work counts: `mapping_replay_runtime.json`
- fixed 502-view held-out result:
  `psnr/strict_fixed_manifest/final_result.json`

## 2026-09-15 — fixed-iteration D1 port v5: full B1 frontier preserves a partial gain

The first fair-B port after the exact historical restore keeps every B1
regular RGB-D/normal gradient and all 832 event-level Adam steps.  It adds one
causal IMU-shaped, appearance-only RR dense view inside the final three
iterations of each eligible mapping event, without another optimizer step.
Unlike historical auto-freeze, topology closes only after the existing
final-v7 controller observes two net-prune events and relative capacity
recovery.  There is no absolute frame, iteration, stream-fraction, event, or
Gaussian-count cutoff.

On the predeclared UTMM `square-2` development scene, the fixed-iteration
verifier passes every event-ledger, archive, causal IMU, online-density,
no-drop/preemption/pending, mapping-disjoint and zero-tail check.  The candidate
preserves all 9,858 B1 regular view-updates, adds exactly 180 accounted dense
views, and performs the same 832 Adam steps.  It improves held-out PSNR by
**+0.3836 dB** and SSIM by +0.00703, although LPIPS is 0.00074 worse.

| Arm | Fixed held-out PSNR | SSIM | LPIPS | Adam | Regular + dense views | Topology | Final GS | Mapper wall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| B1 custom vanilla | 20.6140 | .69116 | .36825 | 832 | 9,858 + 0 | 5 | 126,711 | 41.361 s |
| D1 full-frontier RR port | **20.9976** | **.69819** | .36900 | 832 | 9,858 + 180 | 2 | 113,910 | 41.013 s |
| delta | **+0.3836** | **+.00703** | +.00074 | 0 | 0 + 180 | -3 | -12,801 | -0.348 s |

This proves that preserving the full B1 frontier fixes the negative interaction
seen in the earlier fixed-state adapters, but it does **not** yet restore the
historical +1--2 dB magnitude.  The fair rule changes optimizer semantics:
historical D1 used seven regular frontier iterations plus independent dense
Adam steps, whereas this arm combines a dense appearance gradient with an
already-counted regular step.  It also replaces the wall-cadence-dependent
auto-freeze lifecycle with final-v7 observation state.  The next decisive
check is the same unchanged arm on RPNG `table_01`, the scene on which exact
historical D1 already reproduced +1.1995 dB.

Evidence:

- run:
  `results/experiments/exp78/b_strict_fair_comparison/development_fixed_iteration_v15/utmm/square-2/d1_fixed_frontier_rr_imu_s0/`
- fair-B verifier: `fixed_iteration_verification_vs_b1.json` (`valid=true`)

## 2026-09-15 — fixed-iteration D1 port v5 RPNG: +0.7856 dB is recovered

The unchanged square-2 arm was transferred to RPNG `table_01`, where the
exact historical D1 mapper had reproduced +1.1995 dB under the old wall-paced
protocol.  The fair-B verifier is valid: both arms complete the same 3,305
event-level Adam steps and all 279 packets, the candidate preserves all 41,675
B1 regular views and adds exactly 690 dense views in those same steps, and
drop, preemption, pending work, held-out overlap, future IMU use and post-EOS
updates are zero.

| Arm | Fixed held-out PSNR | SSIM | LPIPS | Adam | Regular + dense views | Packets done/drop | Topology | Final GS | Mapper wall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| B1 custom vanilla | 24.1209 | .80145 | .19196 | 3,305 | 41,675 + 0 | 279 / 0 | 5 | 190,453 | 207.276 s |
| D1 full-frontier RR port | **24.9065** | **.83304** | **.16409** | 3,305 | 41,675 + 690 | 279 / 0 | 2 | 429,755 | 358.667 s |
| delta | **+0.7856** | **+.03159** | **-.02788** | 0 | 0 + 690 | 0 / 0 | -3 | +239,302 | +151.391 s |

Thus the fixed rule does not erase the D1 mechanism: it recovers roughly two
thirds of the historical table_01 advantage and improves all three image
metrics.  The remaining gain gap is +1.1995 - +0.7856 = **0.4139 dB**.
Absolute D1 PSNR is 25.4272 under the restored wall-paced run versus 24.9065
under fixed iteration (-0.5207), while the corresponding vanilla reference is
24.2278 versus 24.1209 (-0.1068); the net delta loss is therefore 0.4139 dB.

This is not merely a scoring change.  Historical wall pacing completed/dropped
131/145 vanilla packets and 153/124 D1 packets (the exact-source rerun was
157/120), with one D1 topology event and independent dense optimizer steps.
The fixed arm completes all 279 packets, has two topology events, combines
dense gradients into existing Adam steps, and invokes final-v7 pose-revision
rematuration throughout the sequence.  Final capacity is already close to the
historical map (429,755 versus 437,714), so Gaussian count alone cannot explain
the remaining 0.41 dB.  The next investigation must isolate independent dense
update semantics and repeated pose-revision recovery without changing the fair
event ledger or reintroducing wall/scene cutoffs.

Evidence:

- run:
  `results/experiments/exp78/b_strict_fair_comparison/development_fixed_iteration_v15/rpng/table_01/d1_fixed_frontier_rr_imu_s0/`
- fair-B verifier: `fixed_iteration_verification_vs_b1.json` (`valid=true`)

## 2026-09-15 — B primary correction: native D1 render matching restores +1.1127 dB

The fixed-Adam protocol above changed the method being tested.  It forced D1's
independent dense Adam updates into the same step as vanilla's ten KF
iterations, creating a hybrid scheduler that the historical D1 never used.
Per user correction, the primary normalization is now physical training
renders, not Adam steps.

The exact restored D1 is left untouched and defines its actually serviced
packet/KF trace and render budget.  Official vanilla then receives exactly the
same 158 mapping-event records, the same 210 tracking KF UIDs, and exactly
**21,116 native KF training renders**.  Vanilla keeps its own window/global
sampler, RGB-D/normal loss, optimizer grouping, and topology.  No dense view or
dense-update path is added to vanilla.  D1 committed 21,104 of its 21,116
renders; 12 were preempted before Adam.  All 21,116 are deliberately made
useful to vanilla, slightly favoring the baseline.

| Arm | Fixed held-out PSNR | SSIM | LPIPS | Physical renders | Adam | Final GS |
|---|---:|---:|---:|---:|---:|---:|
| official vanilla, matched to D1 | 24.3145 | .80910 | .18861 | **21,116** | 1,668 | 222,032 |
| exact native D1 restore | **25.4272** | **.83528** | **.17369** | **21,116** | 1,735 | 437,714 |
| D1 minus vanilla | **+1.1127** | **+.02618** | **-.01492** | 0 | +67 | +215,682 |

The fail-closed verifier passes archive hash, reference-runtime hash, exact
mapping service trace, exact KF UID set, exact total render count, fixed
502-view evaluator, mapping disjointness, and zero-tail/no-final-refinement.
Thus the historical D1-quality mechanism does retain a +1 dB advantage when
the baseline is matched to D1's rendering work instead of rewriting D1 into a
fixed-Adam hybrid.

This is still a provenance diagnostic, not the final paper Full: the exact
historical D1 uses the now-forbidden cadence-dependent auto-freeze.  The next
active candidate must preserve native frontier + independent dense semantics
while replacing only that lifecycle with final-v7's observation-based,
unknown-horizon state.  Its own render ledger will then define the final B0
vanilla match.

Evidence:

- D1 reference:
  `results/experiments/exp78/b_strict_fair_comparison/historical_d1_exact_restore_v1/rpng/table_01/seed0/`
- render-matched official vanilla:
  `results/experiments/exp78/b_strict_fair_comparison/development_render_matched_v1/rpng/table_01/vanilla_d1_render_matched_s0/`
- verifier:
  `results/experiments/exp78/b_strict_fair_comparison/development_render_matched_v1/rpng/table_01/d1_vs_vanilla_render_match_verification.json`

## 2026-09-15 — paper Full Stage 1: observation topology gate retains +1.2482 dB

The paper integration now proceeds on the isolated Git worktree
`/home/intern/VIGS-SLAM-paper-full`, branch `paper/d1-full-staged`.  Commit
`f3945298` freezes the exact D1/render-matched Stage 0 baseline, commit
`78892a6f` changes one behavior only, and commit `7973d126` records the accepted
result.  The changed behavior replaces historical cadence auto-freeze with a
topology-only connection to the existing unknown-horizon controller.  Native
frontier iterations, independent appearance-only dense Adam updates, causal
IMU pose shaping, online-rank birth, and historical PGBA remain unchanged;
Section 3.1 admission and Section 3.2 ERCB are both off.

The controller observed two native net-prune events at frames 286 and 501.
It stayed in FRONTIER until frame 607, when the live map recovered from 61,039
to 84,311 Gaussians against the causally observed 82,520 pre-prune capacity.
Only then did it close later topology.  This rule consumes no scene identity,
stream horizon, absolute frame/iteration, validation metric, or configured
Gaussian-count threshold.

| Arm | Fixed held-out PSNR | SSIM | LPIPS | Physical renders | Adam | Topology | Final GS |
|---|---:|---:|---:|---:|---:|---:|---:|
| official vanilla, Stage-1 render match | 24.1705 | .80225 | .19561 | **21,751** | 1,724 | native | 181,755 |
| D1 + observation topology gate | **25.4187** | **.83533** | **.17237** | **21,751** | 1,826 | 2 | 416,232 |
| candidate minus vanilla | **+1.2482** | **+.03308** | **-.02324** | 0 | +102 | -- | +234,477 |

The candidate itself differs from exact Stage 0 D1 by only **-0.0086 dB**
(25.4187 versus 25.4272).  The fail-closed verifier passes all ten checks:
same frozen archive, 159-record candidate service trace, 210 tracking KF UIDs,
exact total physical renders, committed/uncommitted accounting, locked
reference hash, fixed 502-view evaluator, mapping disjointness, and zero-tail
with no final refinement.  Stage 1 is therefore accepted; the D1 advantage is
retained without the prohibited cadence freeze.

Evidence:

- candidate:
  `results/experiments/exp78/paper_full_staged_v1/rpng/table_01/stage1_observation_topology_s0_retry1/`
- render-matched vanilla:
  `results/experiments/exp78/paper_full_staged_v1/rpng/table_01/vanilla_stage1_render_matched_s0/`
- verifier:
  `results/experiments/exp78/paper_full_staged_v1/rpng/table_01/stage1_vs_vanilla_render_match_verification.json`
- preserved preflight import failure (no mapper work):
  `results/experiments/exp78/paper_full_staged_v1/rpng/table_01/stage1_observation_topology_s0/`

## 2026-09-15 — paper Full Stage 2: C1 retains +1.0872 dB

Accepted Stage 1 was held fixed and only the paper Section 3.1 compute-paced
dense admission rule was enabled.  A single global seed is admitted first;
each later admission requires 22 already completed dense-view services.  The
candidate is chosen causally by temporal maximin plus interval water filling.
Unused credit cannot purchase a future frame.  The native D1 frontier,
independent appearance-only dense Adam updates, IMU pose shaping, online-rank
birth, PGBA, observation-based topology permission, and RR replay order are
unchanged; Section 3.2 ERCB is off.

The controller saw 1,728 causally arrived candidates and registered 13 views
(1 bootstrap + 12 paid).  It minted 284 completed-service tokens, spent 264,
left 20, and reported zero accounting error, discarded prepurchase, or future
frame use.  The strict mapper used 125.2995/125.3054 seconds and made zero
post-EOS optimizer updates.

| Arm | Fixed held-out PSNR | SSIM | LPIPS | Physical renders | Adam | Final GS |
|---|---:|---:|---:|---:|---:|---:|
| official vanilla, Stage-2 render match | 24.1978 | .80360 | .19493 | **22,210** | 1,759 | 191,870 |
| Stage 1 + C1 kappa22 | **25.2849** | **.82960** | **.17785** | **22,210** | 1,949 | 415,878 |
| candidate minus vanilla | **+1.0872** | **+.02600** | **-.01708** | 0 | +190 | +224,008 |

The fail-closed verifier passes all ten checks: comparison contract, frozen
archive, locked runtime hash, exact 162-record service trace, exact 210 KF UID
set, exact render count, committed-render accounting, fixed 502-view evaluator,
mapping disjointness, and zero-tail/no-final-refinement.  The candidate is
0.1337 dB below Stage 1 in absolute PSNR but retains the predeclared +1 dB
advantage.

This is a **development acceptance**, not final paper Full.  C1 is currently
exercised by the frozen-replay external controller, and only RPNG `table_01`
seed 0 has been tested.  The same contract must next be wired into the clean
production source path and checked for behavioral parity; cross-scene transfer
also remains mandatory before the contribution is claimed generally.

Evidence:

- candidate:
  `results/experiments/exp78/paper_full_staged_v1/rpng/table_01/stage2_c1_k22_s0_retry1/`
- render-matched vanilla:
  `results/experiments/exp78/paper_full_staged_v1/rpng/table_01/vanilla_stage2_c1_render_matched_s0/`
- verifier:
  `results/experiments/exp78/paper_full_staged_v1/rpng/table_01/stage2_c1_vs_vanilla_render_match_verification.json`
- preserved preflight validation failure (no mapper work):
  `results/experiments/exp78/paper_full_staged_v1/rpng/table_01/stage2_c1_k22_s0/`

## 2026-09-15 — paper Full Stage 2b: C1 production wiring retains +1.0826 dB

Commit `8b4f00a6` moves the validated global-seed, completed-dense-service,
interval-water-fill, no-prepurchase, and reset-aware integer ledger into the
core `vigs/map_scheduler.py`.  The production frontend now treats token
admission itself as sufficient to discover causal dense intervals when paired
with the Stage-1 observation topology gate.  It no longer needs the unrelated
full `mapping_model_scheduler`; D1's native frontier, independent appearance
dense Adam, RR draw order, IMU pose shaping, birth, PGBA, and topology
permission are unchanged.  Core scheduler tests pass 59/59 and the original
external-controller tests remain 5/5 green.

The frozen harness was switched from the external controller to the committed
core implementation and rerun under the unchanged Stage-2 recipe.  Wall-paced
packet competition produced one extra completed packet and fewer idle dense
updates than the preceding repeat (413 versus 494), so the realized pool was
11 rather than 13 views.  The token ledger still closed exactly: 226 minted,
220 spent, 6 remaining, accounting error 0, reset count 3, and no-prepurchase
violations 0.  Topology remained the same two frame-286/501 events followed by
relative capacity recovery at frame 607; mapping consumed 125.3025/125.3054
seconds with zero post-EOS updates.

| Arm | Fixed held-out PSNR | SSIM | LPIPS | Physical renders | Adam | Final GS |
|---|---:|---:|---:|---:|---:|---:|
| official vanilla, core-C1 render match | 24.1760 | .80411 | .19303 | **22,369** | 1,773 | 192,625 |
| Stage 1 + production C1 kappa22 | **25.2586** | **.82759** | **.18007** | **22,369** | 1,888 | 415,817 |
| candidate minus vanilla | **+1.0826** | **+.02348** | **-.01296** | 0 | +115 | +223,192 |

The fail-closed verifier passes all ten contract/archive/hash/trace/KF/render/
evaluator/disjointness/zero-tail checks.  Relative to the external-controller
Stage 2, absolute PSNR differs by -0.0263 dB and the retained gain by only
-0.0046 dB.  Section 3.1 is therefore accepted in production source for this
development scene.  This does not yet establish cross-scene transfer and
Section 3.2 ERCB remains disabled.

Evidence:

- candidate:
  `results/experiments/exp78/paper_full_staged_v1/rpng/table_01/stage2_c1_core_wiring_s0_retry1/`
- render-matched vanilla:
  `results/experiments/exp78/paper_full_staged_v1/rpng/table_01/vanilla_stage2_core_wiring_render_matched_s0/`
- verifier:
  `results/experiments/exp78/paper_full_staged_v1/rpng/table_01/stage2_c1_core_wiring_vs_vanilla_verification.json`
- preserved preflight import failure (no mapper work):
  `results/experiments/exp78/paper_full_staged_v1/rpng/table_01/stage2_c1_core_wiring_s0/`

## 2026-09-15 — paper Full Stage 3: ERCB production verified, +0.9809 dB HOLD

Accepted Stage 2b was left unchanged and Section 3.2 was introduced in four
separate Git checkpoints on `paper/d1-full-staged`: contract `2e17c12a`,
isolated queue `b7a3f5bf`, opt-in production wiring `7426858a`, and causal
admission-interval fix `34b85d70`.  The last fix separates immutable scheduler
interval identity from the mutable pose-interpolation endpoints that PGBA may
refresh.  This was found fail-closed when dense UID 194 changed pose brackets
after PGBA.  The Stage-3 tests pass 12/12 and the complete relevant scheduler
set passes 80/80; defaults still leave Stage 2b unchanged.

The frozen paper setting is interval-level relative service shortfall with
`K=8`, `rho=0.75`, and `gamma=log(1.5)`, selected previously on the six-scene
UTMM validation bundle.  No value was changed for `table_01`.  Both strict
runs used the same tracker archive, fixed 1.5x budget/20 ms reserve, native D1
frontier, independent dense Adam, production C1 admission, causal IMU pose,
observation topology gate, 502-view disjoint evaluator, and zero-tail.  Each
official vanilla match consumed its paired candidate's exact physical render
count in the native vanilla path.

| Pair | Custom PSNR / SSIM / LPIPS | Vanilla PSNR / SSIM / LPIPS | Exact renders | Delta PSNR |
|---|---|---|---:|---:|
| ERCB run 1 | 25.292854 / .832869 / .174297 | 24.309480 / .808570 / .190816 | 22,760 | **+0.983374** |
| ERCB repeat 1 | 25.297073 / .831986 / .176489 | 24.318719 / .807560 / .190907 | 22,824 | **+0.978354** |
| two-run mean | **25.294964** / -- / -- | **24.314100** / -- / -- | -- | **+0.980864** |

The two custom results differ by only 0.004220 dB and both ten-check verifiers
pass.  The separate RR wall sibling scored 25.256207 dB even though it received
22,994 renders, 562 dense updates, 17 admissions, and 166 completed packets;
ERCB run 1 scored +0.036647 dB higher with only 22,760/445/13/164.  This is
conservative evidence that ERCB ordering helps, but not an exact ordering-only
comparison because the wall scheduler also changed realized C1 service and
membership.

The predeclared gate was `custom - native vanilla >= +1.0 dB`.  The repeated
mean is short by 0.019136 dB, so the result is recorded honestly as **HOLD**:
production implementation and causality pass, but Stage 3 is not promoted and
the branch is not yet final paper Full.  The gate and frozen ERCB parameters
are not changed or rounded after seeing the result.  The result-only checkpoint
is branch commit `d245363e`.

Evidence:

- ERCB run 1:
  `results/experiments/exp78/paper_full_staged_v1/rpng/table_01/stage3_ercb_core_wiring_s0_retry5/`
- paired vanilla and verifier:
  `results/experiments/exp78/paper_full_staged_v1/rpng/table_01/vanilla_stage3_render_matched_s0/`,
  `.../stage3_ercb_vs_vanilla_render_match_verification.json`
- ERCB repeat 1:
  `results/experiments/exp78/paper_full_staged_v1/rpng/table_01/stage3_ercb_repeat1_s0/`
- paired vanilla and verifier:
  `results/experiments/exp78/paper_full_staged_v1/rpng/table_01/vanilla_stage3_repeat1_render_matched_s0/`,
  `.../stage3_ercb_repeat1_vs_vanilla_verification.json`
- RR wall sibling:
  `results/experiments/exp78/paper_full_staged_v1/rpng/table_01/stage3_rr_control_s0/`
- failed integration provenance is retained in the empty/partial
  `stage3_ercb_core_wiring_s0` through `retry4` directories and is excluded
  from metric claims.

## 2026-09-15 — Stage 3 completed-service correction: +0.997941 dB, HOLD 유지

기존 Stage-3 두 run의 queue 장부를 다시 감사하자 `draw_count`가 독립 dense
Adam 완료 뒤가 아니라 view 선택 순간 증가해, deadline에서 거절된 마지막
렌더 1회까지 완료 service로 기록하는 계약 위반이 있었다. 기존 결과와 commit은
삭제하지 않고 provenance로 유지했다. Branch `paper/d1-full-staged`에서
`8c4fefa5`는 draw를 pending transaction으로 바꿔 Adam 성공 뒤에만 service를
commit하고, 거절 시 동일 선택을 frozen block 앞에 복구한다. `98e4f30b`는 그
거절된 물리 렌더를 별도 telemetry로 기록해 render-matched vanilla가 그 계산량도
유효 학습으로 받도록 했다. 관련 scheduler/queue regression은 **81/81 PASS**다.

수정 후 strict 1.5x/reserve20ms run은 `dense_updates=424`, committed
`draw_count=424`, rejected pending render 1, C1 token 241 minted/220 spent/21
remaining, accounting/prepurchase violation 0, optimizer 1,922회, physical render
22,971회, final GS 416,001, zero-tail이었다. Fixed 502-view 평가는 custom
**25.282680/.831452/.176355**, 같은 170-event service trace·210 KF UID와 정확히
22,971 render를 받은 native vanilla는 **24.284738/.808383/.188710**이다.
차이는 **+0.997941 dB / +.023069 SSIM / -.012355 LPIPS**이며 fail-closed
verifier 10/10을 통과했다. Vanilla에는 custom의 committed 22,959 render뿐 아니라
미완료 physical render 12회도 모두 유효 work로 주었다.

따라서 completed-service 계약을 고친 뒤에도 약 +1 dB 이득은 유지되지만, 사전
`>= +1.000 dB` gate를 **0.002059 dB** 모자라므로 반올림하지 않고 Stage 3
HOLD를 유지한다. Stage 2b가 마지막 accepted recipe이고 final Full은 아직
확정하지 않는다. 결과 checkpoint는 `6521519d`이며, 고정 K8/rho.75/
gamma=log1.5를 table_01 결과를 본 뒤 바꾸지 않는다.

Evidence:

- corrected candidate:
  `results/experiments/exp78/paper_full_staged_v1/rpng/table_01/stage3_ercb_completed_service_s0_retry1/`
- exact native-vanilla match:
  `results/experiments/exp78/paper_full_staged_v1/rpng/table_01/vanilla_stage3_completed_service_retry1_render_matched_s0/`
- verifier:
  `.../stage3_ercb_completed_service_s0_retry1/d1_render_match_verification.json`

### Unchanged corrected repeat

동일 commit/설정의 두 번째 corrected run도 `dense_updates=draw_count=528`,
rejected pending render 1, zero-tail로 completed-service 계약을 통과했다. Fixed
custom은 **25.259935/.829845/.176052**, exact 22,732-render native vanilla는
**24.326188/.808224/.190916**, delta는 **+0.933746 dB / +.021621 SSIM /
-.014864 LPIPS**이며 verifier 10/10이다. 첫 corrected run과 합친 평균은 custom
**25.271307**, vanilla **24.305463**, delta **+0.965844 dB**다.

두 run은 같은 설정이지만 wall 경쟁에 따라 pool 11→15, dense service
424→528, completed packet 169→159로 달라졌다. 따라서 end-to-end strict
Stage-3 HOLD는 재현됐지만 §3.2 ordering 자체의 순효과는 아직 분리되지 않았다.
다음 실험은 table_01에서 K/rho/gamma를 사후 sweep하는 대신, causal C1
membership·admission 시점·dense service 기회를 하나의 reference trace로 고정한
RR↔ERCB ordering-only pair다. Repeat result checkpoint는 `e0c747e7`이다.

Evidence:

- corrected repeat:
  `results/experiments/exp78/paper_full_staged_v1/rpng/table_01/stage3_ercb_completed_service_repeat1_s0/`
- exact native-vanilla match:
  `results/experiments/exp78/paper_full_staged_v1/rpng/table_01/vanilla_stage3_completed_service_repeat1_render_matched_s0/`
- verifier:
  `.../stage3_ercb_completed_service_repeat1_s0/d1_render_match_verification.json`

## 2026-09-15 — Stage 3a fixed-event ERCB isolation: -0.008303 dB, HOLD

Wall-realized packet/service 수가 달랐던 Stage 3의 해석 혼선을 제거하기 위해,
사전 고정한 `stage3_rr_vs_ercb_fixed_event_ordering_only_v1` 계약으로 RR과
ERCB를 비교했다. 양 arm은 causal timeline 283개 전부, mapping packet 269개,
packet당 독립 appearance dense 기회 269회, C1 admission 13개와 admission
service boundary, Adam 2,761회, physical training render 38,033회, zero-tail을
정확히 공유했다. Archive/config/seed/source도 같고 fixed 502-view 평가에서
mapping-supervision overlap은 0이다.

| Arm | PSNR | SSIM | LPIPS | GS |
|---|---:|---:|---:|---:|
| Stage-2b RR | 25.624185 | .847417 | .154203 | 417,444 |
| Stage-3 ERCB | 25.615882 | .847165 | .154167 | 417,309 |
| ERCB - RR | **-.008303** | **-.000251** | **-.000036** | -135 |

Commit `c8e40530`의 verifier는 기록된 10개 parity check를 모두 통과했지만,
사전 규칙 `ERCB - RR PSNR > 0`을 통과하지 못해 §3.2를 채택하지 않는다.
K8/rho.75/gamma=log1.5나 gate를 결과 뒤에 수정하지 않았으며 Stage2b가 마지막
accepted recipe다. Result 문서는 branch commit `a01e74b1`에 저장했다.

추가 source audit에서 초기 verifier가 보지 못한 integration mismatch도 찾았다.
RR의 controller clock은 `1 + draw_count // current_pool_size`, ERCB는 자기
`epochs_started`라 동일 work에도 final clock/origin이 RR 66/25, ERCB 69/27로
달랐다. 이 run에서는 frontier ledger가 우연히 그대로여서 기존 artifact를
고쳐 쓰지는 않지만, 엄밀한 selector-only 비교는 아니다. 다음 단계는 selector와
무관한 completed-opportunity clock을 먼저 contract로 고정하고 transition trace
parity를 verifier에 추가한 뒤 pair를 재실행하는 것이다.

Evidence:

- RR:
  `results/experiments/exp78/paper_full_staged_v1/rpng/table_01/stage3a_fixed_event_rr_s0/`
- ERCB:
  `results/experiments/exp78/paper_full_staged_v1/rpng/table_01/stage3a_fixed_event_ercb_s0/`
- verifier:
  `results/experiments/exp78/paper_full_staged_v1/rpng/table_01/stage3a_ordering_isolation_verification.json`
- branch result:
  `/home/intern/VIGS-SLAM-paper-full/paper_full_stages/stage3a_ordering_isolation_result.md`

## 2026-09-15 — Stage 3b selector-independent lifecycle repair: -0.003189 dB, HOLD

Stage3a의 post-run clock 설명부터 정정한다. Active RR 경로는
`1 + draw_count // current_pool_size` 같은 bounded 공식이 아니라 실제
`CausalShuffleQueue`가 shuffle block을 refill한 native epoch였다. ERCB의 raw
`epochs_started`는 `ceil(draws / current_pool_size)` 계열 fractional pool-pass라
동일 269 service에서도 RR 66/origin25, ERCB 69/origin27로 달랐다. 따라서
Stage3a는 work-count isolation이었지만 엄밀한 selector-only lifecycle
isolation은 아니었다.

Stage3b에서는 accepted RR의 실제 shuffle-refill 의미를 reference로 보존했다.
ERCB queue가 candidate membership을 동기화하는 private RR shadow를 소유하고,
성공적으로 완료된 dense Adam에서만 shadow draw를 commit한다. Cancelled/rejected
draw는 clock을 진전시키지 않는다. Shared model controller는 selector의 raw
epoch 대신 이 lifecycle API만 읽고, raw ERCB 69는 진단 telemetry로만 남는다.
Static/growing/shrinking/reset/cancel schedule unit test와 기존 scheduler/C1
regression이 통과했고, 변경은 contract→queue/API→backend wiring→telemetry→
verifier의 분리 commit으로 저장했다.

새 `stage3_rr_vs_ercb_fixed_event_ordering_only_v2` pair는 283 causal event,
269 packet-paid dense opportunity, 동일 C1 admission 13개, Adam 2,761회,
physical render 38,033회, zero-tail을 공유한다. 269/269 opportunity에서 lifecycle
candidate set, completed-service index, lifecycle clock이 정확히 같고 controller
trace도 같다. 양 arm 모두 final shared clock/origin은 66/25이며, 새 RR의 selected
UID trace와 final clock은 보존된 Stage3a RR reference와도 exact다. Fail-closed
verifier는 **12/12 PASS**다.

| Arm | PSNR | SSIM | LPIPS | GS |
|---|---:|---:|---:|---:|
| Stage-2b RR | 25.617258 | .846843 | .154703 | 417,294 |
| Stage-3 ERCB | 25.614069 | .847204 | .154142 | 417,339 |
| ERCB - RR | **-.003189** | **+.000361** | **-.000560** | +45 |

Lifecycle integration bug는 고쳤고 SSIM/LPIPS 방향은 좋지만, 사전 primary
규칙은 `ERCB - RR PSNR > 0`이다. PSNR delta가 non-positive라 §3.2는 승격하지
않고 Stage2b를 마지막 accepted recipe로 유지한다. K8/rho.75/gamma=log1.5와
acceptance gate는 바꾸지 않는다. 결과 checkpoint는 branch commit
`f907cfed`이다. 다음 행동은 table_01 파라미터 sweep이 아니라 paper §3.2의
수식·algorithm 설명과 production queue가 실제로 같은 확률법칙을 구현하는지
감사하고, 차이가 있을 때만 새 stage 계약을 먼저 고정하는 것이다.

Evidence:

- RR:
  `results/experiments/exp78/paper_full_staged_v1/rpng/table_01/stage3b_fixed_event_rr_clockfix_s0/`
- ERCB:
  `results/experiments/exp78/paper_full_staged_v1/rpng/table_01/stage3b_fixed_event_ercb_clockfix_s0/`
- verifier:
  `results/experiments/exp78/paper_full_staged_v1/rpng/table_01/stage3b_selector_independent_clock_verification.json`
- branch result:
  `/home/intern/VIGS-SLAM-paper-full/paper_full_stages/stage3b_selector_independent_clock_result.md`

## 2026-09-15 — Stage 3c C2 orthogonal isolation: -0.004557 dB, HOLD

Stage3b의 음수 결과가 C1의 작은 admitted pool과 C2의 상호작용 때문인지
분리하기 위해, 사전 고정한 `stage3c_c2_orthogonal_fixed_event_ordering_only_v1`
계약으로 C1을 끄고 accepted Stage1 D1 mapper 위에서 C2만 비교했다. 양 arm은
causally arrived dense pool 전체를 각 opportunity 전에 등록하며, 차이는 RR 대
고정 `K=8`, `rho=.75`, `gamma=log(1.5)` service-shortfall ERCB 선택뿐이다.

양 arm은 causal event 283개, completed mapping packet 279개, fixed dense
opportunity 269개, Adam 2,761회, physical training render 38,033회, tracking
origin 210개, frontier work와 zero-tail을 정확히 공유한다. Dense 1,728장이
도착했고 그중 1,690장은 mapping opportunity 전에 등록됐다. 마지막 38장은
마지막 opportunity 뒤 도착했으므로 두 arm에서 동일하게 pending이며 optimizer가
만지지 않았다. Actual stability-filtered lifecycle candidate membership도
269/269 exact이고 fail-closed verifier는 **12/12 PASS**다.

| Arm | PSNR | SSIM | LPIPS | GS |
|---|---:|---:|---:|---:|
| Stage1 + full-pool RR | 25.572639 | .847869 | .153598 | 417,665 |
| Stage1 + full-pool ERCB | 25.568082 | .847436 | .154360 | 417,650 |
| ERCB - RR | **-.004557** | **-.000433** | **+.000762** | -15 |

실제 candidate interval은 모든 269 opportunity에서 K보다 많았고 범위는
36--541이다. ERCB block start 36회도 전부 K 초과 상태였다. 따라서 Stage3b의
`interval_count <= K` 구간에서 C2가 membership을 바꾸지 못했다는 현상은
실패의 유일한 원인이 아니다. C1을 제거해도 primary PSNR gate가 음수이므로
§3.2를 승격하지 않고 **Stage2b(+1.082609dB)**를 마지막 accepted로 유지한다.
파라미터 sweep은 하지 않는다. 다음은 growing stream에서 lifetime interval
service count와 bounded 1.5x bonus가 late-arriving interval을 실제로 충분히
서비스하는지 수식·구현 의미를 감사한다.

Evidence:

- RR:
  `results/experiments/exp78/paper_full_staged_v1/rpng/table_01/stage3c_c2_orthogonal_rr_s0/`
- ERCB:
  `results/experiments/exp78/paper_full_staged_v1/rpng/table_01/stage3c_c2_orthogonal_ercb_s0/`
- verifier:
  `results/experiments/exp78/paper_full_staged_v1/rpng/table_01/stage3c_c2_orthogonal_verification.json`
- mapping/verifier/harness commits:
  `1deb2075` / `af9c5dff` / `ea134475`
- branch result commit:
  `fd9913c4`

## 2026-09-15 — Stage 3d global-residue C2 isolation: +0.012620 dB, ACCEPT in isolation

Stage3c 사후 trace audit에서 interval-local ERCB가 final generation의 267회
service를 263개 view에 써서, 아직 856--1,382개의 eligible view가 미서비스인데도
4개 UID를 반복한 사실을 찾았다. 논문에서 의도한 “random reshuffling 위의
bounded correction”과 맞추기 위해 파라미터를 바꾸지 않고, 기존
service-shortfall 확률법칙의 base measure만 아직 서비스되지 않은 global epoch
residue에 조건부로 제한했다. C1은 계속 꺼서 C2 의미 하나만 검증했다.

Contract `7697e93a` → queue core `5adffabe` → production opt-in wiring
`f51dc26d` → fail-closed verifier `9c0679d6` → lab harness `c3548b6` 순으로
분리 저장했다. 관련 scheduler/verifier regression은 97/97 PASS다. 실행 pair는
283 event/279 packet/269 dense opportunity/Adam2,761/render38,033/210 tracking
origin/zero-tail을 정확히 공유하며, 269/269 actual candidate·lifecycle trace와
controller trace도 동일하다. 1,728 arrivals 중 1,690장이 opportunity 전에
등록됐고 마지막 38장은 양쪽에서 동일 pending이다.

Global-residue verifier는 final generation에서 양 arm 모두 267 service/267 unique
view임을 재구성했다. Repaired C2는 repeat-before-exhaustion 0, 기존 block 안으로
새 arrival이 침투한 횟수 0, queue telemetry mismatch 0이며 전체 **13/13 PASS**다.
모든 269 opportunity와 36 C2 block start는 K8 초과 interval 상태다.

| Arm | PSNR | SSIM | LPIPS | GS |
|---|---:|---:|---:|---:|
| Stage1 + full-pool RR | 25.554556 | .847585 | .153467 | 417,671 |
| Stage1 + global-residue C2 | 25.567176 | .848015 | .153832 | 417,603 |
| C2 - RR | **+.012620** | **+.000431** | **+.000365** | -68 |

사전 primary gate `C2 - RR PSNR > 0`를 처음 통과했으므로 global residue를
§3.2의 선택 semantics로 채택한다. 다만 이득이 작고 LPIPS는 악화했으며 C1을
끈 isolation이므로 최종 Full 확정은 아니다. 마지막 integrated accepted recipe는
여전히 Stage2b(+1.082609dB)다. 다음은 C1 admission과 repaired C2를 별도 계약과
커밋으로 결합하고, C1 membership/work/lifecycle을 RR control과 exact하게 맞춘 뒤
양수 gate를 다시 통과해야 한다.

Evidence:

- RR:
  `results/experiments/exp78/paper_full_staged_v1/rpng/table_01/stage3d_global_residue_rr_s0/`
- repaired C2:
  `results/experiments/exp78/paper_full_staged_v1/rpng/table_01/stage3d_global_residue_ercb_s0/`
- verifier:
  `results/experiments/exp78/paper_full_staged_v1/rpng/table_01/stage3d_global_residue_verification.json`
- paper-branch result:
  `/home/intern/VIGS-SLAM-paper-full/paper_full_stages/stage3d_global_residue_result.md`
- result commit:
  `b2acecd1`

## 2026-09-15 — Stage 4 C1+C2 integration: -0.003491 dB, HOLD

Stage2b의 accepted C1(global seed1, completed dense service 22회당 paid
admission 1장)과 Stage3d의 repaired global-residue C2를 별도 Stage4 계약으로
처음 결합했다. Contract `e908b528` → lab harness `6b3c7c3` → verifier
`8b56bcd4` → pending-field semantic audit fix `321fa0bb` 순으로 분리 저장했다.
관련 scheduler/verifier 94/94와 C1 controller 5/5가 통과했다.

실행 pair는 1,728 causal arrival에서 동일한 13장(bootstrap1+paid12)을
등록했고 derived C1 pending은 1,715장이다. Token mint/spend/remain/discard는
양쪽 모두 269/264/3/2, accounting error와 no-prepurchase violation은 0이다.
283 event/279 packet/269 dense opportunity/Adam2,761/render38,033/210 tracking
origin/actual lifecycle·controller trace/zero-tail이 모두 exact하며 전용
verifier **17/17 PASS**다.

| Arm | PSNR | SSIM | LPIPS | GS |
|---|---:|---:|---:|---:|
| Stage1 + C1 + RR | 25.621600 | .847244 | .154738 | 417,262 |
| Stage1 + C1 + global-residue C2 | 25.618109 | .847057 | .153905 | 417,336 |
| C2 - RR | **-.003491** | **-.000187** | **-.000833** | +74 |

Primary PSNR gate는 음수여서 C2를 Full에 통합하지 않는다. Final generation은
양 arm 모두 동일한 13개 view에 267 service를 사용해 66개의 완전한
without-replacement epoch를 끝내고 residue 2장을 남겼다. 즉 C1이 pool을 매우
작게 제한한 뒤에는 RR과 C2가 누적 coverage를 똑같이 만들고 C2는 epoch 내부
순서만 바꾼다. 이는 Stage3d full-pool의 작은 양수 효과가 C1 결합에서 사라진
구조적 이유이며, K/rho/gamma나 gate를 사후 조정할 근거가 아니다. 마지막
integrated accepted recipe는 계속 Stage2b(render-matched **+1.082609dB**)다.

Evidence:

- C1+RR:
  `results/experiments/exp78/paper_full_staged_v1/rpng/table_01/stage4_c1_c2_global_residue_rr_s0/`
- C1+global-residue C2:
  `results/experiments/exp78/paper_full_staged_v1/rpng/table_01/stage4_c1_c2_global_residue_ercb_s0/`
- verifier:
  `results/experiments/exp78/paper_full_staged_v1/rpng/table_01/stage4_c1_c2_global_residue_verification.json`
- paper result:
  `/home/intern/VIGS-SLAM-paper-full/paper_full_stages/stage4_c1_c2_global_residue_integration_result.md`
- result commit:
  `38042c2f`

## 2026-09-15 — Stage 5 seed1/2/3 Full retention replication: +1.333130 dB, original gate HOLD

Stage4 seed0을 판정에서 제외하고, 사전 고정한 mapper seed 1/2/3에 대해
`C1+RR / C1+global-residue C2 / native vanilla render-match` 3-arm을 모두
완료했다. Tracker는 동일한 immutable seed0 archive이며, RR/C2는 seed 안에서
동일 stochastic seed를 쓴다. 각 seed의 RR/C2 arm은 C1 admission 13장,
arrival 1,728장, terminal C1 pending 1,715장, event 283개, completed packet
279개, fixed dense opportunity 269개, Adam 2,761회, physical render 38,033회,
zero-tail을 정확히 공유한다. Native vanilla도 paired C2와 동일한 mapping event,
tracking KF UID 210개, physical render 38,033회를 사용한다.

모든 seed에서 Stage4 fairness verifier **17/17**, native render-match verifier
**10/10**이 통과했고 multi-seed aggregate도 immutable input/evaluator와 정확한
seed set을 확인했다.

| Mapper seed | C1+RR | C1+C2 | C2-RR | worst-Q1 Δ | RR-hard-Q1 Δ | Vanilla | Full-Vanilla |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 25.542154 | 25.546805 | +.004651 | +.004641 | +.004806 | 24.259483 | **+1.287321** |
| 2 | 25.593264 | 25.596146 | +.002882 | +.003608 | +.004378 | 24.186688 | **+1.409458** |
| 3 | 25.582025 | 25.568103 | -.013922 | -.018360 | -.016485 | 24.265491 | **+1.302612** |
| **Mean paired Δ** | — | — | **-.002130** | **-.003370** | **-.002434** | — | **+1.333130** |

따라서 기존 Stage5 사전 규칙 중 `Full-vanilla mean >= +1dB`와
RR-hard-Q1 2/3 양수는 통과했지만, mean overall/worst-Q1/RR-hard-Q1의
비음수·양수 조건은 실패했다. 기준을 사후 변경하지 않으므로 Stage5 자체는
**HOLD**다. 반면 complete C1+C2 구조의 vanilla 대비 이득은 세 seed 모두
`+1.28dB` 이상이고 평균 **+1.333130dB**여서 D1 계열의 주 이득은 안정적으로
유지됐다.

이 조건은 C1이 1,728 arrivals를 13-view pool로 줄인 뒤 final generation에서
267 service로 동일 pool을 66 complete epoch 순회한다. 즉 admitted pool 기준으로
service가 풍족하여 RR/C2는 cumulative coverage가 같고 within-epoch order만 다르다.
ERCB가 이겨야 하는 범위를 실제 service-shortfall로 한정한다는 사용자 설명은
타당하지만, 실행 중 도착한 해석이므로 이번 결과를 사후 PASS로 바꾸지는 않는다.
다음 실험 전에 workload/service trace만으로 rich/shortfall stratum을 정하는 별도
cross-scene 계약을 고정한다.

실행 전에 발생한 backend import, legacy dense-render ledger double count, vanilla
metric-init gate 누락의 pre-GPU 실패 3건은 삭제하지 않고
`failed_pre_gpu_import/`에 보존했다. 수정 뒤 성공한 artifact만 판정에 사용했다.

Evidence:

- artifact root:
  `results/experiments/exp78/paper_full_staged_v1/rpng/table_01/stage5_full_retention_replication/`
- aggregate:
  `verification/stage5_cohort.json`
- paper result:
  `/home/intern/VIGS-SLAM-paper-full/paper_full_stages/stage5_full_retention_replication_result.md`
- paper result commit:
  `bb5707ca`
