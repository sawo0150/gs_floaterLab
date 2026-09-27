# Exp120 — frozen exact-render unified dense transfer

Exp119's one-slot rule, LPM mass prior, and gamma are transferred
without retuning. RPNG must pass before Aria starts.

| Dataset / scene | Arm | PSNR | Delta | Dense renders/share | Total renders | Adam | GS |
|---|---|---:|---:|---:|---:|---:|---:|
| rpng / table_01 | mass_normalized_control | 25.579600 | +0.000000 | 538 / 1.40% | 38302 | 3030 | 417830 |
| rpng / table_01 | unified_mass_normalized | 25.393478 | -0.186122 | 2148 / 5.61% | 38302 | 3030 | 419055 |
| rpng / table_01 | unified_mass_rr | 25.425005 | -0.154595 | 2148 / 5.61% | 38302 | 3030 | 418769 |
| aria / aria1253 | mass_normalized_control | 25.726313 | +0.000000 | 202 / 1.48% | 13620 | 1055 | 177100 |
| aria / aria1253 | unified_mass_normalized | 25.780710 | +0.054396 | 867 / 6.37% | 13620 | 1055 | 177883 |
| aria / aria1253 | unified_mass_rr | 25.772388 | +0.046075 | 867 / 6.37% | 13620 | 1055 | 177897 |

Completed scenes: **2/2**.
Gate: **PASS**.

## Three-family interpretation (including Exp119 UTMM)

| Quantity | Result |
|---|---:|
| Control mean PSNR | 24.175445 dB |
| Unified normalized mean PSNR | 24.127515 dB |
| Unified normalized - control | -0.047930 dB |
| Unified normalized - unified RR | +0.000805 dB |
| Mean dense share, control -> unified | 1.47% -> 6.22% |
| Committed global replacements | 2,758 |
| Normalized/RR differing selection rows | 293 |

All archive/config/event/render/Adam/admission, held-out, double-evaluation,
zero-tail, corrected-cardinality, recent-window, cap, transactional-evidence,
and lifecycle checks pass. Dense work is active and quality-safe, but the
normalized-vs-RR difference is noise-scale and does not establish an ERCB
quality gain. RPNG loses 0.186 dB versus its fresh control, so this rule is not
promoted to a 17-scene quality result.
