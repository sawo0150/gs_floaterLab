> 번호 통합(2026-09-11): 이 문서는 **exp77 단계 D**의 기록이다. 본문의 exp80는 이전 ID다. [통합 카드](../README.md)

# exp80 — Why Aria quality does not transfer: code/log diagnosis

Analysis date: 2026-09-10. Full benchmark completion/results are recorded in
`exp80_vigs_1x_zero_tail_16seq.md`. Evidence is `evidence/diagnostics.json`.

## Strongest confirmed execution mismatch: 40 ms reserve on a 33 ms stream

The RTX5090 profile sets `EXP69_REPLAY_TRACKING_RESERVE_MS=40` in
`exp69_axes/hardware_profiles.sh`. In `vigs/vigs.py`, `_polish_gate()` only admits
replay concurrent with active tracking if:

```
replay_step_budget + tracking_reserve <= next_arrival_deadline - now
```

Aria is approximately 20 fps (50 ms spacing), whereas these ETH-preprocessed
RPNG/UTMM inputs are approximately 30 fps (33.3 ms spacing). At 30 fps the 40 ms
reserve alone exceeds a normal frame slot, even before paying for a replay step.
The overlap flag can be true while no overlap work is actually admitted.

This is observed, not just inferred from flags: exp79 Aria repeats record
`gate_allowed_tracking=710/675` and maximum deadline slack 54.599 ms. All completed
exp80 benchmark telemetry records zero `gate_allowed_tracking`; normal maximum
slack is approximately 36–39 ms. Counter names refer to successful gate decisions,
not a direct count of completed overlapping Adam updates. Timestamp jitter or a
gap could permit an exception in another run; the claim is about this evidence.

The profile was tuned for Aria's cadence and fails to provide the intended
tracking/replay overlap at this benchmark cadence. This is the clearest concrete
configuration problem. It is **not yet an isolated estimate of the PSNR lost**:
only a matched reserve-policy ablation can establish that effect.

## Measured consequence: less effective replay, despite longer sequences

| Quantity | Aria exp79 repeat1 | RPNG table_06 exp80 |
|---|---:|---:|
| Frames | 1303 | 2767 |
| Producer 1× budget | 65.10 s | 92.24 s |
| Main tracking-call accumulated wall time | 34.49 s | 71.91 s |
| Mapper dispatch accumulated wall time | 11.53 s | 29.16 s |
| Idle-replay accumulated wall time | 20.60 s | 9.09 s |
| Replay scheduler updates | 6613 | 2101 |
| Final admitted replay pool | 404 | 420 |
| Mean lifetime selections per admitted view | 16.37 | 5.00 |
| Final replay step wall EMA | 3.09 ms | 6.92 ms |
| Held-out PSNR | 27.499 dB | 21.442 dB |

Wall timers for different threads overlap and must not be added into a GPU-time
pie chart. Main tracking-call time includes waits as well as work. Per-frame
tracking wall cost is similar (about 26 ms); at 30 rather than 20 fps, that leaves
far less slack per frame. More map dispatches and larger maps consume additional
capacity. The scene has over twice as many images but receives less than one third
as many replay updates as the Aria repeat. Final map counts are in the benchmark
summary; RPNG maps are several times larger than Aria's roughly 100k Gaussians.
A larger count is evidence of workload scaling, not proof that those Gaussians
are floaters or should be pruned.

RPNG table_01/02 each average only about 3.3 selections per admitted view. In
longer table_04, the last admission cohort has only ~5% of the first cohort's
mean selection count. The existing replay/admission law does not preserve
learning opportunities automatically as input cadence, map size and sequence
length change. Pool coverage fractions are provided as diagnostics, not a claim
that every non-heldout image must be admitted.

## Confirmed short-sequence failure: initialization gates consume the stream

`vigs/vigs.py` defers mapping until `video.IMU_initialized`. The run uses UTMM
IMU initialization at 15 keyframes, RPNG at 20, without per-sequence retuning.
Progress immediately before the log's IMU-initialization start:

| Sequence | Frame progress | Fraction of sequence | Consequence |
|---|---:|---:|---|
| Aria exp79 | 185/1303 | 14.2% | substantial mapping/replay window remains |
| UTMM fast-straight | 241/332 | 72.6% | 11.04 s total budget, 65 completed Adam calls, zero dense replay |
| UTMM slow-straight-2 | 456/597 | 76.4% | zero dense replay |
| UTMM slow-straight-1 | never reaches threshold | 13 KF < 15 | empty map, terminal diagnostic crashes |

These are initialization **start** progress markers; initialization completion
and useful mapping occur later. Thus the remaining useful learning window is
no larger than these fractions suggest. `fast-straight` achieves only 4.896 dB
with 2524 final Gaussians despite good aligned ATE. The strict cutoff also stops
an initialization burst from silently finishing after its budget. Simply lowering
the keyframe threshold is not established safe: insufficient inertial excitation
may worsen metric scale and pose estimation.

## Tracking failures and geometry limitations must remain separate

- UTMM square-2: 92.76 cm Sim(3) ATE, 2.74% recall@10cm; tracking failure is an
  independent explanation for this sequence's poor rendering.
- Low Sim(3) positional ATE does not certify rotation/depth/pixel alignment.
  Slow-straight-2 and ego-centric-1 retain roughly 24–25% scale error.
- RPNG table_02 has 16.64 dB despite ~4.13 cm ATE and 97.88% recall. Its temporal
  thirds are 16.45/16.48/17.00 dB; poor quality is not restricted to the last frames.
- Table_07 failed with a CUDA gather/index-out-of-bounds assertion during PGBA,
  around frame 1697, before EOS. This is a reliability issue, not a low-PSNR
  measurement. The asynchronous traceback cannot localize the precise bad index
  without a dedicated reproduction.

These observations leave initial depth/geometry quality, pose-to-map consistency
following PGBA and inherent image complexity as plausible additional limits.
No GT-pose/GT-depth intervention or converged fixed-pose rendering experiment was
performed here, so those causes are not confirmed. Do not attribute the entire
cross-scene dB gap to a single scheduler or tracking parameter.

## Long-sequence memory/stability limits

Table_08 fails around frame 7719 in frontend correlation-pyramid concatenation,
requesting ~1004 MiB with ~599.5 MiB GPU free. GPU caching is enabled by the 5090
profile; `_images_gpu[t]` retains arriving tracking images, while maps and graph
state also grow. The allocation site and total memory pressure are confirmed;
this run does not isolate how much is due to caches versus graph buffers, map
state or allocator fragmentation. Disabling all caches is therefore not yet a
validated fix and would also change runtime. A bounded cache/memory experiment
belongs after the small mapping diagnostic set, not a fresh full sweep.

## Counterevidence against simplistic explanations

Exp77 already scored only ~19 dB with 1.5× and queue drain. Correctly applying
the 5090 profile at 1× did not magically recover 27 dB, and its overlap remained
blocked by the 40 ms cadence mismatch. Table_01 lost many replay updates relative
to exp77 but only ~0.17 dB; table_05 improved ~0.21 dB. More total updates therefore
cannot be assumed sufficient to recover 27 dB. Cross-scene absolute PSNR also
varies with scene content; Aria 27 dB is not evidence of universal 27 dB quality.

The exp78-versus-exp79 comparison changes terminal rematuration, pruning,
cutoff behavior and synchronization instrumentation simultaneously. It is not
an isolated measurement of the value of post-stream learning. Likewise exp77
versus exp80 changes pacing, profile, carve, terminal behavior and instrumentation.
Matched sequence deltas describe outcomes; they do not identify a single cause.

## Next iterations: small fixed diagnostic set, no repeated 16-sequence sweeps

User preference: complete the current full run, then focus on a few selected
sequences. Primary set:

1. **Aria1253**: regression control, including its existing same-seed variance.
2. **RPNG table_06**: relatively good tracking, early enough initialization,
   reasonable runtime; main mapping/overlap diagnostic.
3. **UTMM fast-straight**: short-stream initialization and cutoff stress case.

Keep table_02 as a later transfer check instead of tuning all RPNG scenes.
Table_07 PGBA reliability should have a separate short-prefix reproduction,
not be mixed into PSNR scheduler selection.

First planned intervention: on table_06, compare the unchanged 40 ms reserve
with a declared smaller reserve (e.g. 20 ms) while holding input timestamps,
seed, map logic, heldout IDs, EOS guard, instrumentation, and all other profile
flags fixed. Log actual overlapping gate admissions, completed Adam counts,
tracking latency/ATE, held-out PSNR and zero-tail audit. The profile wrapper
currently overwrites the reserve, so an explicit override **after** profile
application is required; merely exporting a variable beforehand is not a valid
ablation. A smaller reserve is a diagnostic setting, not a recommended universal
production default. Repeat matched baseline/candidate runs before accepting a
small PSNR gain, because Aria's existing zero-tail repeats vary by 1.32 dB.

Second, if needed, allow more optimization on saved table_06 pose/init only as
an explicitly **offline diagnostic**, holding topology fixed first to isolate
appearance/geometry optimization from growth. If it cannot fit despite ample
updates, inspect initialization and pose/depth consistency; if it recovers,
focus on online work allocation. Such a diagnostic must never be reported as
an online benchmark improvement. No follow-up ablation was launched in exp80.
