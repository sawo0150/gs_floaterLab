# exp70.5 — VIGS-SLAM vanilla depth/normal loss ablation (aria1253)

이 디렉터리의 로컬 원본(카드/서사)은 `gs_floaterLab/context/experiments/exp70/exp70.5_vigs_vanilla_depth_normal_loss_ablation.md`에 있다.

- 코드: `VIGS-SLAM-vanilla-check`(`cvg/VIGS-SLAM` origin/main `22ffe24c`, 알고리즘 무수정)
- 데이터: aria1253 (RGB 1303장·IMU 65,425샘플)
- 실행: `--gsmapping --pure_online`(오프라인 26k-iter 색 정제 생략) + `VIGS_EVAL_PURE_ONLINE=1`
- 토글: `Training.alpha`(depth loss 계수), `Training.lambda_dnormal`(normal loss 계수) — config만 변경, 코드 무수정

## 결과 (held-out, pure-online)

| condition | held PSNR | held SSIM | held LPIPS | kf PSNR | wall time |
|---|---:|---:|---:|---:|---:|
| both_off (depth OFF / normal OFF) | 23.14 | 0.7550 | 0.4107 | 23.35 | 234s |
| depth_only (depth ON / normal OFF) | 22.43 | 0.7425 | 0.4240 | 22.62 | 231s |
| normal_only (depth OFF / normal ON) | 21.96 | 0.7360 | 0.4570 | 21.95 | 232s |
| both_on (vanilla 기본값) | 22.14 | 0.7407 | 0.4487 | 22.34 | 233s |

두 감독 항 모두 이 순수-온라인 조건에서는 개별로도 손해였다(both_off가 최고). n=1이라
hard 채택/기각 판단은 보류 — 반복 검증 전까지 잠정 결과.

## 파일

- `aria1253__<condition>_<PSNR>dB_exp70.ply` — 해당 조건의 최종 온라인 Gaussian 지도(오프라인 정제 미적용)
- `aria1253__<condition>_<PSNR>dB_exp70_held.json` / `_kf.json` — held-out / keyframe PSNR·SSIM·LPIPS
- `aria1253__<condition>_<PSNR>dB_exp70_config.yaml` — 해당 run의 정확한 resolved config

렌더 이미지·전체 로그 등 부가 산출물은 로컬(`VIGS-SLAM-vanilla-check/exp_depth_normal_ablation/outputs/`)에만 있고 이 폴더에는 올리지 않았다(기존 exp68/69 convention과 동일하게 ply+json+config만 공유).
