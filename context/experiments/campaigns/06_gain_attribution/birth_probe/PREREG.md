# Birth probe — immediate effect of a keyframe birth on trained views (measurement) — PREREG (2026-10-09)

At every KF birth after the first of a generation, up to 6 older keyframes (older than the newest 6) that see the
largest share of the new points ("covered", share > 5%) and up to 6 that see none ("control") are rendered without
gradient right before and right after the birth (no optimizer step in between); Δ = PSNR after − before against each
keyframe's own RGB. Training is unchanged (online uniform with replacement); no-grad renders do not count as training.
aria1253, seed 0, 1 run. Read-out: mean Δ and share of negative Δ, covered vs control; a clearly negative covered Δ
(and ≈0 control) is direct evidence that births degrade trained regions.
