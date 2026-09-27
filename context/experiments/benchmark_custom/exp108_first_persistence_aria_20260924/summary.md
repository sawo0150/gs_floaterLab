# Exp108 — first-persistence local topology

| Scene | Candidate | Fresh vanilla | delta vanilla | delta Exp94 R4 | Clone | Render cand/vanilla | Adam cand/vanilla | GS cand/vanilla | Verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| aria/aria1253 | **25.755865** | 23.979334 | **+1.776532** | -0.019837 | 70 | 13,620/13,620 | 1,055/1,071 | 177,207/175,878 | PASS |

SSIM is 0.824987/0.779900 (`+0.045087`) and LPIPS is
0.319630/0.408106 (`-0.088476`). The ticket added no render or Adam step.
Double evaluation, exact render matching, frozen archive/config,
dense/keyframe opportunity parity, held-out disjointness, and zero-tail all
pass.
