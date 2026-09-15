# Academic carve method — research decision

Date: 2026-09-01  
Status: method proposal, not an experiment result  
Code target: `/home/intern/gs_floaterLab/repos/main/VIGS-SLAM`

## 1. Decision

Do not present the current transit/terminal ratio plus opacity penalty as the
paper method. Keep it as the engineering baseline.

The paper method should instead be framed as:

> **Causal floater removal as uncertainty-aware premature ray-termination
> risk minimization, with a budgeted viewset selected to maximally reduce the
> posterior uncertainty of Gaussian validity.**

Working names:

- Overall method: **CLEAR-GS** — Causal Likelihood-based Empty-space Assessment
  and Regularization for Gaussian Splatting.
- Loss: **CPTR** — Causal Premature-Termination Risk.
- View selector: **EIG-VS** — Evidence Information-Gain Viewset Selection.

Names are provisional. The definitions below matter more than the acronym.

## 2. Why the current method is not yet an academic contribution

The present implementation is a strong engineering prototype, but its main
choices are not derived from one statistical objective:

1. A sparse voxel field records transit and terminal counts.
2. A Gaussian receives `transit / (transit + 3 * terminal)` evidence, with
   direction/Fisher and optional anchor or neighborhood modifiers.
3. Its support is approximated using the center plus six `±2σ` samples, with a
   separate large-ellipsoid path.
4. The soft objective adds the derivative of
   `lambda * score * sigmoid(opacity_logit)`.
5. Prune/proximal actions use thresholds, persistence and a heuristic
   `opacity * scale_area * observations` harm budget.

These are individually reasonable, but reviewers can ask why the terminal
weight is 3, why a score threshold is 0.5, why direction conditioning should
multiply the score, and why only opacity receives the continuous gradient.
The current answer is empirical tuning, not a unified likelihood.

The important code locations are:

- `causal_carve.py:351-387`: fixed carve parameters.
- `causal_carve.py:554-643`: local transit/terminal ratio.
- `causal_carve.py:1111-1184`: seven-sample and ellipsoid support scoring.
- `causal_carve.py:1890-1945`: opacity-only soft gradient.
- `causal_carve.py:1965-2129`: contribution-bounded prune/proximal actions.

## 3. Research gap after the 2025–2026 literature

Several nearby ideas already exist:

- **StableGS** identifies opacity/color gradient deadlock, uses cross-view depth
  consistency and dual opacity.
- **TIDI-GS** combines multi-view consistency, spatial relations and learned
  importance for floater pruning.
- Recent depth-guided 3DGS work includes explicit empty-space penalties in
  front of estimated surfaces.
- **PUP 3D-GS**, TrimGS and related methods prune by uncertainty or rendering
  importance, primarily for compactness and fidelity preservation.
- **FisherRF**, **POp-GS**, ActiveGAMER, GAVIS and 2026 coverage optimization
  select views for radiance uncertainty, active exploration or geometric
  coverage.

Therefore none of the following alone is a safe novelty claim:

- “We use depth to remove floaters.”
- “We penalize opacity in free space.”
- “We use multi-view consistency.”
- “We select views with Fisher information.”
- “We protect important Gaussians during pruning.”

The narrower open gap is the combination of:

1. a ray-level probability of **premature termination caused by the full
   anisotropic footprint** of a Gaussian;
2. explicit propagation of online depth and pose uncertainty into that risk;
3. passive, causal selection of already-arrived views for **floater hypothesis
   discrimination**, rather than next-best-view radiance acquisition;
4. sequential, risk-controlled action based on posterior confidence.

## 4. CPTR: Causal Premature-Termination Risk

### 4.1 Depth evidence as a distribution

For an arrived ray `r=(o,d)` let the estimated surface depth be a random
variable

```text
Z_r ~ Normal(z_hat_r, sigma_r^2).
```

`sigma_r^2` combines:

```text
depth uncertainty
+ J_pose * Sigma_pose * J_pose^T
+ a representation/calibration floor.
```

The evidence is causal: only poses, BA depths and uncertainty available by the
current sensor timestamp may be used.

### 4.2 Analytic anisotropic ray–Gaussian footprint

For Gaussian `i` with center `mu_i`, covariance `Sigma_i`, opacity/density
amplitude `alpha_i`, define `A_i = Sigma_i^-1` and `x = mu_i - o`:

```text
a = d^T A_i d
b = d^T A_i x
c = x^T A_i x
t_bar = b / a
s_parallel^2 = 1 / a.
```

The line integral of the unnormalized 3D Gaussian over `[l,u]` is

```text
M_ir(l,u) = alpha_i * exp[-0.5 * (c - b^2/a)] * sqrt(2*pi/a)
             * [Phi(sqrt(a)*(u-t_bar)) - Phi(sqrt(a)*(l-t_bar))].
```

This quantity is the Gaussian occupancy mass intersecting the ray segment. It
changes differentiably with center, covariance and opacity. It replaces both a
center-only label and the fixed seven-query approximation.

### 4.3 Expected free-space mass

The verified free interval ends before the uncertain surface. With a small
calibration margin `m0`, define

```text
E_free(ir) = E_{Z_r}[ M_ir(t_min, Z_r - m0) ].
```

The expectation can be evaluated with a closed-form Gaussian-CDF convolution
or a fixed two-/three-point quadrature. Pose/depth uncertainty softens the
boundary rather than changing a scene-specific hard margin.

### 4.4 Termination-aware loss

Let `T_ir` be the transmittance reaching Gaussian `i` along ray `r`. The risk
that this Gaussian terminates a ray inside verified empty space is

```text
R_ir = T_ir * (1 - exp[-E_free(ir)]).
```

The proposed loss is

```text
L_CPTR = (1 / |R|) * sum_r confidence_r * sum_i R_ir.
```

Interpretation: minimize the expected probability that an arrived,
depth-verified ray terminates before its plausible first surface.

This is preferable to `score * opacity` because:

- it optimizes the actual free-space footprint, not only the center;
- an opacity/scale compensation cannot preserve the loss;
- occluded Gaussians receive little pressure through `T_ir`;
- center, scale, rotation and opacity obtain gradients from one geometric
  objective;
- uncertainty controls false positives continuously.

The existing voxel field can remain as a broad-phase index and evidence cache.
It should no longer define the final loss value.

## 5. Sequential validity posterior

Each Gaussian has a latent label

```text
Y_i = 1  (floater / invalid occupancy)
Y_i = 0  (supported surface or legitimate appearance primitive).
```

Each selected ray produces soft contradictory evidence derived from `R_ir` and
near-surface support. Maintain either:

- a calibrated log-likelihood ratio and an SPRT decision; or
- a generalized Beta posterior with fractional free/surface evidence.

The preferred paper formulation is an SPRT because type-I surface deletion
risk can be stated explicitly:

```text
LLR_i <- LLR_i + w_ir * log p(e_ir | Y_i=1) / p(e_ir | Y_i=0).
```

The likelihoods are calibrated on synthetic injected floaters and a held-out
development scene. A Gaussian is not irreversibly removed until the upper SPRT
boundary is crossed. The lower boundary clears a false alarm. Values between
the boundaries remain undecided.

This converts “persistence=3” into a controlled sequential test with declared
false-positive and false-negative targets.

## 6. EIG-VS: academic viewset selection

### 6.1 The selection target

Candidate views are already-arrived, causal RGB/depth keyframes. We are not
planning the future camera trajectory.

For view `v` and Gaussian `i`, estimate

```text
u_iv = P(visible_i | v)
       * depth_confidence_v
       * expected floater/surface likelihood separation
       * current visual contribution_i.
```

The value of a view is the expected reduction in entropy of the Gaussian
validity variables, not the Fisher information of color/SH parameters:

```text
Gain(v | S) = sum_i C_i * [H(Y_i | E_S)
                           - E H(Y_i | E_S, observation from v)].
```

### 6.2 Diverse budgeted set

Under conditional independence, information gain is submodular. Select up to
`B` views with lazy greedy maximization:

```text
S* = argmax_{S subset V_arrived, cost(S)<=B}
       I(Y_candidates ; O_S | E_past).
```

The practical surrogate is a saturating weighted coverage objective:

```text
F(S) = sum_i C_i * [1 - exp(-sum_{v in S} u_iv)]
       + eta * logdet(I + sum_{v in S} H_v).
```

The first term targets floater discrimination and naturally discounts
redundant views. The optional log-det term provides directional conditioning.
Fisher is therefore a diversity/conditioning term, not the primary novelty or
the primary ordering signal.

### 6.3 Difference from adjacent active-view work

- FisherRF/POp-GS: parameter uncertainty for acquiring views that improve NVS.
- ActiveGAMER/GAVIS/coverage methods: physical exploration, visibility or map
  completeness.
- EIG-VS: choose a bounded subset of **already observed** views that most
  discriminates “valid surface vs floater” for currently risky Gaussians.

That distinction must be explicit in the paper and experiments.

## 7. Safe optimization and appearance preservation

CPTR should first run as a soft, reversible objective. Hard deletion is a
posterior decision, not the loss itself.

Recommended ladder:

```text
telemetry-only
-> CPTR soft gradient
-> geometry-opacity quarantine
-> SPRT-confirmed prune.
```

Two implementation variants should be evaluated:

1. **Standard 3DGS:** apply CPTR to center/covariance/opacity with a small trust
   region and render-contribution budget.
2. **Dual geometry/appearance opacity:** use the StableGS idea as a substrate,
   not as our novelty; CPTR acts on geometry opacity while appearance opacity
   preserves translucency and fine detail.

Do not claim that dual opacity is new.

## 8. Evaluation that can support an academic claim

### 8.1 Ground truth

Use two complementary label sources:

1. **Controlled injection:** move/clone real Gaussians into verified free space
   while retaining realistic opacity, scale and color distributions. Include
   hard cases that overlap surfaces in some views.
2. **Direct VIGS SuperSplat labels:** real floaters and real hard negatives on
   the exact evaluated PLY, without Sim3 label transfer.

Injection alone is not ecological validity; manual labels alone are too small
for calibration. Both are necessary.

### 8.2 Metrics

- Average precision and calibrated precision/recall; ROC-AUC is secondary due
  to severe class imbalance.
- Recall at fixed surface false-positive rate.
- Precision at fixed visual-contribution removal budget.
- Expected calibration error / Brier score for the validity posterior.
- Strict held-out PSNR/SSIM/LPIPS before and after soft action.
- Region geometry metric and visible high-opacity floater count.
- Runtime, selected rays/views and score age in strict streaming.

### 8.3 Required baselines

```text
current transit/terminal score
current score + perfect full refresh
opacity/scale/connected-component heuristics
render-contribution pruning (TrimGS-like)
depth consistency (StableGS-like)
center-only premature termination
CPTR footprint without uncertainty
full CPTR
```

Viewset baselines:

```text
all available
recent K
uniform/random
novelty/covisibility
Fisher/POp-style
EIG-VS
```

### 8.4 Generalization protocol

- Tune likelihood calibration and thresholds only on development scenes.
- Freeze them before testing multiple held-out scenes and trajectories.
- Report paired scene-level differences with bootstrap confidence intervals.
- Include batch 3DGS and strict incremental 3DGS if claiming representation-
  level rather than VIGS-only generality.
- Keep strict streaming 27 dB as the entry gate; do not optimize hard carve on
  sub-quality maps.

## 9. Minimal implementation sequence

### A0 — Mathematical and numerical validation

- Implement analytic ray–ellipsoid interval mass in an isolated module.
- Compare value and gradients against dense numerical integration.
- Test extreme scales, grazing rays and near-singular covariance.

### A1 — Frozen-map detector

- No optimization or pruning.
- Compute CPTR and posterior on saved maps.
- Evaluate injected and direct SuperSplat labels.

### A2 — Soft CPTR

- Enable differentiable loss only on selected rays/Gaussians.
- Establish PSNR/geometry Pareto curve and test opacity-scale compensation.

### A3 — EIG-VS

- Hold loss and compute budget fixed.
- Compare view selectors on posterior calibration and action-time AP.

### A4 — Sequential action

- Add SPRT quarantine/prune only after soft CPTR is safe.
- Predeclare type-I surface deletion target and contribution budget.

### A5 — Strict streaming integration

- Reserve a geometry compute lane so CPTR does not steal RGB replay.
- Report action-time freshness and zero-tail compliance.

## 10. Paper claim, if the evidence succeeds

A defensible main claim would be:

> We formulate floater suppression in incremental Gaussian splatting as
> uncertainty-aware premature ray-termination risk. An analytic anisotropic
> footprint loss penalizes only Gaussian mass supported inside causally
> verified free space, while an information-gain viewset selects arrived views
> that maximally reduce Gaussian-validity uncertainty under a fixed budget.

Avoid stronger claims such as “first floater-free 3DGS,” “first free-space
loss,” or “first information-based view selection.” Those are not defensible
against the current literature.

## 11. Primary literature anchors

- [StableGS](https://arxiv.org/abs/2503.18458) — floater gradient deadlock,
  cross-view depth consistency, dual opacity.
- [TIDI-GS](https://arxiv.org/abs/2601.09291) — multi-view/spatial/importance
  floater pruning.
- [Geometry Field Splatting](https://openaccess.thecvf.com/content/CVPR2025/papers/Jiang_Geometry_Field_Splatting_with_Gaussian_Surfels_CVPR_2025_paper.pdf)
  — footprint-aware geometry-field rendering.
- [Gaussian Opacity Fields](https://arxiv.org/abs/2404.10772) — opacity-field
  geometry and ray-based surface extraction.
- [DS-NeRF](https://arxiv.org/abs/2107.02791) — uncertain depth supervision of
  ray termination.
- [SLAIM](https://openaccess.thecvf.com/content/CVPR2024W/NRI/html/Cartillier_SLAIM_Robust_Dense_Neural_SLAM_for_Online_Tracking_and_Mapping_CVPRW_2024_paper.html)
  — ray-termination distribution and empty-space constraints.
- [POp-GS](https://openaccess.thecvf.com/content/CVPR2025/html/Wilson_POp-GS_Next_Best_View_in_3D-Gaussian_Splatting_with_P-Optimality_CVPR_2025_paper.html)
  — optimal experimental design for 3DGS view selection.
- [PUP 3D-GS](https://openaccess.thecvf.com/content/CVPR2025/html/Hanson_PUP_3D-GS_Principled_Uncertainty_Pruning_for_3D_Gaussian_Splatting_CVPR_2025_paper.html)
  — uncertainty-aware pruning for compactness.
- [ActiveGAMER](https://openaccess.thecvf.com/content/CVPR2025/html/Chen_ActiveGAMER_Active_GAussian_Mapping_through_Efficient_Rendering_CVPR_2025_paper.html)
  — rendering-based information gain for active mapping.
- [GAVIS](https://openaccess.thecvf.com/content/CVPR2026/html/Xue_Uncertainty-driven_3D_Gaussian_Splatting_Active_Mapping_via_Anisotropic_Visibility_Field_CVPR_2026_paper.html)
  — anisotropic visibility uncertainty and active mapping.
- [Coverage Optimization for Camera View Selection](https://openaccess.thecvf.com/content/CVPR2026/papers/Chen_Coverage_Optimization_for_Camera_View_Selection_CVPR_2026_paper.pdf)
  — transmittance-pattern information gain and coverage surrogate.

