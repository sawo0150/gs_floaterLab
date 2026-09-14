# exp78 — VIGS benchmark reproduction and fair transfer

## Goal

Reproduce the official VIGS-SLAM RPNG/UTMM result before using that baseline in
a matched strict-streaming comparison with gsSLAM.  A weak or protocol-mismatched
vanilla run is not accepted as evidence that gsSLAM wins.

## Lanes

| Folder | Question | Status |
|---|---|---|
| `a_paper_reproduction/` | Does clean official VIGS reproduce the paper-native RPNG/UTMM result? | **Qualified public-artifact reproduction complete:** RPNG mean PSNR passes; UTMM exact paper state is unrecoverable and local gap is disclosed; README TensorRT probes complete |
| `b_strict_fair_comparison/` | Which method wins with identical input, held-out UIDs, runtime and TensorRT state? | Frozen schema/common scheduler/pinned runner complete; 1.5× RPNG 3-sequence mapping-only comparison valid |
| `c_aria_overfit_audit/` | Which gsSLAM choices are active Aria-specific assumptions? | Active-path audit complete; absolute Aria curve replaced by causal online rank in benchmark arm |
| `d_dataset_general_optimization/` | Which causal, dataset-independent changes transfer across RPNG, UTMM and Aria? | RPNG 3/3 all-metric wins, mean +1.598 dB; full validation/1×/Aria regression still pending |

## Non-negotiable separation

- Lane A has no 1×/1.5× deadline.  It records native FPS and peak memory and
  stops before final global BA and color refinement.
- Lane B reports 1× and canonical 1.5× separately, requires mapping-disjoint
  predeclared UIDs, zero optimizer steps after sensor EOS/deadline, and matches
  TensorRT on/off between methods.
- Post-final BA/color-refinement values are never mixed with online pre-final
  values.
- Mapping-only comparisons reuse identical tracking packets before any
  end-to-end comparison is interpreted.

## Acceptance target

The final claim requires at least +2.0 dB mean PSNR over matched vanilla VIGS
on both RPNG and UTMM, SSIM/LPIPS improvements in the same direction, wins on a
majority of each dataset's sequences, strict runtime/causality compliance, and
less than 0.3 dB regression on the retained Aria 1253/305 checks.
