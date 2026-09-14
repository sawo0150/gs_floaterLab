# exp78 D — dataset-general optimization

This lane begins only after the official reproduction gate, shared evaluation
contract, mapping-only isolation, and active-path Aria audit are sufficiently
stable.  Changes are tested one causal axis at a time with repeated paired A/B,
first on the frozen development subset and then without retuning on validation.

Hard carve or floater pruning is not used to mask a rendering-quality deficit
below the strict 27 dB milestone.

## Current result

The first fixed-recipe mapping-only transfer now covers RPNG `table_01`,
`table_06`, and untouched validation `table_02`. gsSLAM wins all three metrics
on 3/3 sequences; sequence-mean PSNR gain is **+1.598 dB**, below the +2 dB
acceptance gate. See [D1](rpng_mapping_only_ablation.md).
