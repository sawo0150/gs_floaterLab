# v08: overview 안의 supervision 재설계

내장 imagegen 편집. Imagegen 스킬을 사용해 기존 v07을 보존하고 새 버전으로 저장한다. 설계 reference는 **overview만** 사용한다: DN-Splatter Fig. 1, PGSR Fig. 4. 별도 loss 도식·ablation은 이번 생성의 reference에서 제외했다.

입력 1: `overall_pipeline_v07.png` (편집 대상).
입력 2: `reference_figures/loss_figures/dn_splatter_fig01_overview.png` (구성 참고).
입력 3: `reference_figures/loss_figures/pgsr_fig04_overview.png` (supervision 연결 참고).

Carve의 free-space opacity 억제를 설명하는 개념 시안이며, 후보 loss 선택이나 실제 실험 결과를 확정하지 않는다. Depth/normal의 활성화 여부와 최종 objective는 제출 configuration에 맞춰 확인해야 한다.

```text
Use case: precise-object-edit / scientific overview figure.
Asset: wide academic overall pipeline figure, new version of Image 1.
Inputs: Image 1 is the EDIT TARGET (our current overview). Image 2 (DN-Splatter Fig.1) and Image 3 (PGSR Fig.4) are OVERVIEW DESIGN REFERENCES ONLY: borrow their integration of geometry illustration and supervision inputs, never their exact figures, scenes, labels or methods.

Preserve the three main functional territories, their proportions and headings: "Online observations", "Training-view management", "Gaussian map optimization". Preserve the left observations/frontend and the middle (a) View Growth and (b) View Sampling, including K/I badges, growing retained pool 3->4->5, selection count vs inverse-preference probability bars and sampled view queue. Counts high means sampling probability low; counts low means probability high. One view per update. Preserve the completed-updates return to View Growth. Do not replace this with a generic chain of boxes.

MAIN EDIT: redesign ONLY the right optimization territory into a coherent mini-overview of shared map + two supervision routes. Crisp clean white/light lavender background, existing navy typography, muted gray base supervision and purple new geometry. Rich compact scientific illustration, not a dashboard.
1. Keep the shared Gaussian room map at top. Beneath it use a small gray arrow labelled "Render" into a compact strip of three rendered thumbnails: RGB, Depth, Normal. All show exactly the same room viewpoint and geometry, with RGB color, depth falsecolor, normal falsecolor. No mismatched observed/rendered camera viewpoints.
2. Consolidate the base losses into ONE low-emphasis compact rounded band labelled "Base supervision" and below "RGB (K + I) · Depth / Normal (K)". Connect the rendered quantities and selected observations to this band. This means eligible keyframe depth/normal priors only; intermediate images supply RGB, not depth/normal. Remove the large old observed-versus-rendered RGB pair and orange zoom boxes. No independent huge boxes for every base loss.
3. Replace the OLD bottom geometry panel AND its termination-weight chart with a compact geometric illustration titled "(c) Ray-space geometry supervision". Absolutely NO histogram, no mean-depth toy comparison and no experimental before/after images. A thin dashed CALLOUT from a small highlighted point in the shared map connects to this illustration; callout is not a data arrow.
4. In that illustration show one camera icon on left, a straight viewing ray pointing RIGHT, an observed surface plane on right with a narrow uncertainty band and a depth tick "D". Space between camera and the band is labelled "Observed free space". Only a very few translucent Gaussian ellipsoids: a red erroneous Gaussian well in front of the surface, and a purple near-surface Gaussian. Label the red one "Suppress premature opacity" with a small leader and a downward alpha indicator. Do NOT draw a position-movement arrow toward the surface, do NOT erase all Gaussians, do NOT show geometry behind the surface as known empty. This is a schematic constraint, not a promised optimized result.
5. The existing bottom keyframe-depth evidence line must reach this geometric illustration at the D/surface evidence, labelled "Verified keyframe depth". Branch this evidence path into the base supervision as well for depth/normal priors. No sensor ground truth or future frames.
6. Base supervision and the purple geometry supervision must have TWO SEPARATE arrows into ONE small circle labelled "Map objective" at the far right; only this circle returns via ONE upward "Update" arrow to the SAME shared Gaussian map. There must be no base-loss->geometry-loss arrow. Both are parallel contributors to optimization, not serial stages.

Minor connective cleanup if needed, without changing other panels: geometry initialization arrow must originate at the Online frontend pose/depth outputs and end at Shared Gaussian map; arrived image filmstrip goes to View Growth independently. The selection-history loop goes from sampled queue to Selection counts with just one arrowhead at counts. Use consistent same-ID thumbnail images wherever repeated. Do not change the existing growth or sampling policy.

Keep the figure clean, full, legible and publication-like, not text-heavy. Retain footer "Schematic examples — not experimental results". No paper captions from reference images, no copied source labels, no extra contributions, no logos. This is an overview, NOT a standalone loss explainer. Output one complete wide figure.
```
