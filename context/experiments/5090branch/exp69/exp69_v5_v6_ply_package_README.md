# exp69 v5 vs final v6 PLY comparison

이 폴더는 네 장면을 동일한 strict 1.5× causal-streaming 조건에서 비교하기 위한 PLY 묶음이다.

- `v5_before_carve`: pose-active/archive scheduler와 exact PGBA moment transport를 쓰되 causal carve는 끈 버전
- `v6_final`: v5 + visible-lazy causal carve(`lambda_soft=0.01`, opacity-prox budget `0.005`) + terminal simple dust pruning
- 모든 장면에 동일 설정을 썼으며 장면별 튜닝이나 post-stream 추가 학습은 하지 않았다.

| scene | v5 PSNR | v6 PSNR | Δ v6−v5 | opacity≤0.1 v5→v6 | opacity>0.3 v5→v6 |
|---|---:|---:|---:|---:|---:|
| aria1253 | 27.745 | 27.427 | −0.318 | 17,144→14,293 | 66,640→65,846 |
| aria301_305 | 27.660 | 28.090 | +0.431 | 20,663→15,260 | 52,297→49,400 |
| aria301_12F | 26.186 | 23.905 | −2.281 | 37,146→21,597 | 99,667→105,042 |
| aria1253_rot | 24.213 | 23.484 | −0.729 | 42,924→31,423 | 86,904→87,143 |

해석은 제한적으로 해야 한다. v6는 네 장면 모두에서 low-opacity dust를 줄였지만, 12F와
1253_rot에서는 high-opacity Gaussian 수가 줄지 않았고 PSNR도 하락했다. strict 시간 예산에서
carve maintenance가 replay와 같은 GPU 시간을 사용하면서 v6 replay step이 v5의
4,542→2,404(12F), 3,743→2,613(1253_rot)으로 줄어든 것이 주요한 동반 현상이다. 따라서 현 상태의
v6를 보편적 개선으로 판정하지 않는다.

각 장면 폴더에는 아래 파일이 있다.

- `v5_before_carve.ply`
- `v6_final.ply`

루트의 `comparison_manifest.json`에는 원본 run 경로, 정량 지표, vertex 수와 SHA-256이 들어 있다.
`exp69_result.html`에는 실험 맥락과 해석이 정리되어 있다.
