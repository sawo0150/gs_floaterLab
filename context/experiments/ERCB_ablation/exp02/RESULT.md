# Exp02 — RGB capture-time service latency scheduler candidates

> Date: 2026-09-12
> Verdict: **Latency improves, final held-out quality does not. All proposed methods were implemented and screened; no candidate dominates RR.**

## Question

The count-based ERCB result is small. Is the actual growing-pool bottleneck the
capture-to-first-applied-update latency, and can a latency-first scheduler reduce
that delay while also beating causal random reshuffling (RR) in held-out PSNR?

The latency clock starts at the **physical RGB capture timestamp**, as requested.
A service completes only when that frame's gradient is included in an optimizer
update that is actually applied. A draw or backward whose update is discarded is
not counted. Frames without a remaining optimizer slot at sensor EOS are
right-censored and retained as unserved; zero-tail is unchanged.

## Implemented methods

Every distinct method in the two `research/` documents was implemented as an
independent arm over one shared ticket/archive interface. All arrived training
frames remain in the archive and llffhold-8 views never enter the scheduler.

| Arm | Research method | Implemented signal/action |
|---|---|---|
| `dense_moment` | Dense proposal 1 | Mandatory ticket service plus pose/RGB feature-moment and prefix compensation |
| `dense_service_field` | Dense proposal 2 | Sparse local cross-view kernel and effective-service credit; indirect credit never retires a ticket |
| `pair_mean_dense3` | Dense proposal 3 | Fresh/old gradients at the same parameters; reference-sketch descent chooses the mixture |
| `debt_utility_A` | Candidate A | Direct-service debt plus loss and signed-gradient-sketch utility |
| `prefix_balance_B` | Candidate B | Deadline/ticket-constrained short-block signed-sketch prefix balancing |
| `approx_mir_C` | Candidate C | Cached signed-sketch interference replay with 25% global RR exploration |
| `pair_safe_D` | Candidate D | Same-parameter fresh/old gradients and the two-loss safe alpha interval |

The pair arms use two paid backward slots and one optimizer application. Their
backward and optimizer counts are recorded separately. Pair densification receives
both views' visibility/screen-space gradient statistics. The gradient sketch uses
a stable spatial hash of Gaussian coordinates rather than mutable compacted row
indices. Cheap observation features use causal pose, RGB mean/std, and quadrant
means and are exposed to a policy only upon frame arrival.

## Physical schedule and representative scenes

For each UTMM scene, RGB timestamps are aligned to the VIGS producer start. A
training frame becomes eligible at the first measured exp80 optimizer-slot start
at or after capture. The measured slot completion time converts its first applied
service iteration back to seconds.

The initial screen deliberately uses two capacity regimes rather than all six:

- `slow-straight-2`: `mu/lambda=0.312`, an infeasible capacity stress control.
  No `k=1` scheduler can serve every arrival before EOS.
- `ego-drive`: `mu/lambda=1.608`, a feasible but nontrivial growing pool used for
  candidate and parameter selection.

The remaining six-scene run is used only after selecting and freezing two methods.

## Common first screen

Fixed first-screen settings were ticket fraction `.75`, deadline `32` optimizer
slots, block `8`, shortlist `24`, temperature `.25`, seed 0, resolution 4.
`capture_rr` disables ticket priority and keeps the same measurement hooks.

| Scene | Arm | Held-out PSNR | Served fraction | p95 latency | Optimizer updates |
|---|---|---:|---:|---:|---:|
| slow-straight-2 | capture RR | **14.958** | .312 | 17.703 s | 163 |
|  | ticket archive RR | 14.714 | .312 | 16.506 s | 163 |
|  | dense moment | 14.362 | .312 | 16.506 s | 163 |
|  | service field | 14.410 | .312 | 16.506 s | 163 |
|  | debt–utility A | 14.657 | .312 | 16.506 s | 163 |
|  | prefix balance B | 14.728 | .312 | 16.520 s | 163 |
|  | approximate MIR C | 14.728 | .312 | 16.506 s | 163 |
|  | pair mean | 13.754 | .308 | 16.703 s | 81 |
|  | pair safe D | 13.767 | .308 | 16.703 s | 81 |
| ego-drive | capture RR | **20.504** | .995 | 14.858 s | 1,968 |
|  | ticket archive RR | 19.631 | .998 | 8.017 s | 1,968 |
|  | dense moment | 19.615 | .998 | 8.017 s | 1,968 |
|  | service field | 19.641 | .998 | 8.017 s | 1,968 |
|  | debt–utility A | 19.702 | .998 | 8.017 s | 1,968 |
|  | prefix balance B | 19.314 | .998 | 8.011 s | 1,968 |
|  | approximate MIR C | 19.415 | .998 | 8.017 s | 1,968 |
|  | pair mean | 18.791 | .998 | 11.358 s | 984 |
|  | pair safe D | 18.939 | .998 | 11.358 s | 984 |

The stress scene confirms the capacity bound: policies can change which frame is
served but cannot raise the served fraction beyond the available `163/522` slots.
On the feasible scene, hard service cuts p95 latency almost in half but costs about
0.8 dB. Pair policies additionally lose optimizer cadence and are rejected.

## Parameter tuning and implementation correction

The first screen was not treated as tuned. On `ego-drive`, the ticket executor was
separated from policy logic. Fractions `.25/.50/.65/.75` and deadline 128/256/free
variants were tested. The best ticket-only quality point was `.75` with the hard
deadline disabled: **19.645 dB, p95 9.955 s**. Weaker service was not monotonically
better, so the loss cannot be explained only by an over-aggressive `.75/32` choice.

Two implementation issues found during tuning were corrected and regression-tested.
Because the token fix changed 639/1,222 `ego-drive` first-service iterations, the
complete two-scene screen was rerun as v4; the table above contains only v4 values.

1. A token bucket capped before subtraction aliased fractions above `.5`; the
   corrected bucket realizes the requested long-run fraction.
2. Prefix B initially respected only deadline urgency, not the ticket fraction.
   Its apparent 20.519 dB result had p95 15.148 s, worse than RR, and is invalid as
   a latency-policy win. It is excluded. Corrected blocks include at least the
   configured ticket quota.

After correction, the frozen shortlist is the two highest-quality valid methods:

- Debt–Utility A: fraction `.75`, deadline disabled, temperature `.50`, shortlist
  32 — tuning PSNR 19.805 dB, p95 9.241 s.
- Service Field: fraction `.75`, deadline disabled, temperature `.25`, shortlist
  24 — tuning PSNR 19.739 dB, p95 9.352 s.

Corrected Prefix B (`temperature=.10`, block 4, shortlist 16) reaches 19.583 dB
and is not in the valid top two. Its already completed six-scene transfer is kept
only as supplementary negative evidence.

No parameter is changed after this point.

## Frozen 6-scene transfer

| Scene | RR PSNR | Debt A | Delta | Service Field | Delta |
|---|---:|---:|---:|---:|---:|
| ego-centric-1 | **22.901** | 21.890 | -1.010 | 22.031 | -0.869 |
| ego-centric-2 | **20.225** | 19.668 | -0.558 | 19.608 | -0.617 |
| ego-drive | **20.529** | 19.786 | -0.743 | 19.710 | -0.819 |
| fast-straight | 13.351 | 13.450 | +0.099 | **13.489** | +0.138 |
| slow-straight-2 | 14.958 | 14.945 | -0.013 | **14.980** | +0.021 |
| square-1 | **22.188** | 21.549 | -0.639 | 21.006 | -1.183 |
| **6-scene mean** | **19.025** | 18.548 | **-0.477** | 18.471 | **-0.555** |

Debt wins only the capacity-infeasible `fast-straight` scene (1/6). Service Field
wins the two infeasible controls (2/6) and loses all four feasible scenes. Mean
worst-Q1 falls from RR 16.053 to Debt 15.538 and Service Field 15.478 dB.
The corrected Prefix supplementary transfer averages 18.650 dB (`-0.375 dB`,
1/6 wins); it is less negative after transfer but was not one of the two methods
selected by the frozen `ego-drive` screen/tuning rule.

For the four capacity-feasible scenes, mean p95 latency changes from RR **25.988 s**
to Debt **18.526 s (-7.462 s, -28.7%)** and Service Field **18.540 s
(-7.448 s, -28.7%)**. Six-scene mean served fraction rises from `.7208` to
`.7368/.7375`. Training wall time is comparable (mean 35.94/35.82/36.87 s;
Service Field is +2.6%), but this end-to-end
number also includes policy-induced topology differences and is not an isolated
microbenchmark of scheduler arithmetic.

## Verdict and theoretical implication

**No method from the research folder dominates RR.** The latency mechanism works,
but quality does not follow direct-service latency. This rejects the strong causal
hypothesis that late frames' direct first-service delay is the main final-quality
bottleneck in this harness.

The observed trade-off is consistent with dense cross-view supervision: frames that
have not been selected directly may already receive useful indirect service from
neighbours. Hard direct tickets then replace archive updates that maintain global
coverage and topology development. The service-field, moment, signed-utility, MIR,
and pair corrections tested here were insufficient to recover that displaced value.

This does not show that online latency is unimportant. If the paper needs an anytime
mapping claim, Service Field/Debt are valid latency–quality Pareto points, but they cannot be
presented as a final-PSNR improvement or as the ERCB binary ablation win. For a module
whose paper table is only `ERCB on/off`, the earlier interval ERCB result remains the
only positive held-out-quality evidence; exp02 supplies a negative mechanistic study.

## Limitations

- Single seed is adequate for candidate elimination, not a statistical superiority
  claim. The valid shortlisted candidates are already negative by 0.477–0.555 dB on average.
- Final VIGS pose and cumulative geometry initialization are fixed offline across
  arms. This isolates scheduling but is not strict online localization evidence.
- Physical capture and measured VIGS optimizer timing determine eligibility and
  latency, while optimization is replayed in 3dgs-custom. This is not a live
  end-to-end latency run.
- Final PSNR was measured; a dense held-out quality-vs-wall-clock curve was not.
- The low-dimensional feature/sketch approximations are intentionally cheap and can
  be stale. Their failure does not rule out an exact, more expensive gradient method.

## Evidence and reproduction

- Machine summaries: `evidence/screen_v4_summary.json`, `evidence/final_v3_summary.json`
- Physical schedules and audit: `evidence/capture_schedules/`
- Full artifacts: `data/benchmarks/ercb_exp02_latency_final_v3_runs/`
- Corrected initial all-method screen: `data/benchmarks/ercb_exp02_latency_screen_v4_runs/`
- Superseded pre-token-fix screen: `data/benchmarks/ercb_exp02_latency_v1_runs/`
- Tuning runs: `data/benchmarks/ercb_exp02_latency_tuning_v2/`
- Code: `runtime/latency_scheduler.py`, `train.py`, and
  `scripts/incremental/{build_ercb_latency_schedules.py,compute_service_latency.py,run_ercb_latency_candidates.sh,run_ercb_latency_tuning.sh,summarize_ercb_latency.py}`
- Verification: `pytest -q tests/test_view_scheduler.py` → **37 passed**.
