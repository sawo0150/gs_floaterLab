# exp84 — GT-pose RGB frame-density convergence diagnostic

> 상태: 완료. 이는 dense supervision의 잠재력을 pose/streaming 오차에서 분리한
> **offline 원인 진단**이며 strict-streaming 성과로 세지 않는다.

## 질문

같은 정확한 pose, 초기 Gaussian, RGB loss, Adam step 예산에서 학습 RGB pool만
조밀하게 만들면 sparse frame 반복보다 held-out PSNR이 더 빨리 오르는가?

## 계약

- scene: UTMM `ego-drive`의 앞 1,000 RGB
- pose: `groundtruth.txt`를 각 RGB timestamp에 보간한 GT pose
- split: stock 3DGS `--eval` llffhold-8, train 875 / held-out 125
- supervision: RGB L1 + DSSIM만 사용; depth/normal/carve/plateau 없음
- 공통: resolution 4, seed 0, 8,000 iteration, 동일 optimizer/densification/SH 설정
- 공통 initialization: stride16/phase1 RGB에서 만든 deterministic 360,612-point
  multi-depth scaffold. 모든 arm이 같은 `points3D.ply`를 읽으므로 dense arm에만
  추가 초기 색을 주지 않는다.
- nested train pools:
  - stride16/8/4/2: `frame_index mod stride = 1`
  - stride1: held-out을 제외한 전체 train pool
  - 선택 수는 63/125/250/500/875이며 held-out overlap은 모두 0
- 각 pool은 무작위 without-replacement epoch로 sampling한다. 총 optimizer step은
  같고, frame 수에 따라 view당 평균 재방문 횟수가 달라지는 것이 의도한 변수다.

## held-out 수렴 결과

학습 중 float render 125-view 평균 PSNR:

| stride | train RGB | @500 | @1k | @2k | @4k | @8k |
|---:|---:|---:|---:|---:|---:|---:|
| 16 | 63 | **16.542** | **18.373** | 19.545 | 20.900 | 21.599 |
| 8 | 125 | 16.478 | **18.485** | **20.032** | **22.102** | 23.475 |
| 4 | 250 | 16.425 | 18.340 | 19.807 | 21.906 | **23.529** |
| 2 | 500 | 16.421 | 18.119 | 19.552 | 21.909 | 23.507 |
| 1 | 875 | 16.398 | 18.210 | 19.526 | 21.575 | 23.267 |

최종 저장 PLY를 다시 렌더해 8-bit PNG로 계산한 독립 확인:

| stride | final PSNR | Δ vs stride16 | worst-Q1 | stride16 대비 이긴 view | final GS |
|---:|---:|---:|---:|---:|---:|
| 16 | 21.585 | — | 17.239 | — | 1,175,373 |
| 8 | 23.455 | +1.870 | **20.642** | 92/125 | 1,310,938 |
| **4** | **23.509** | **+1.924** | 20.622 | 94/125 | 1,372,336 |
| 2 | 23.486 | +1.901 | 20.627 | **96/125** | 1,384,156 |
| 1 | 23.247 | +1.661 | 20.388 | 86/125 | 1,420,175 |

stride4−stride16의 paired view-bootstrap 95% CI는 **[+1.524,+2.325]dB**다.
seed 간 CI가 아니라 동일 held-out view에 대한 paired CI이므로 run-to-run 재현성을
대체하지는 않는다.

## 해석

1. **정확한 pose에서는 더 조밀한 RGB supervision의 이득이 실재한다.** 8k에서
   stride1도 stride16보다 +1.668dB이고, 최적 stride4는 +1.930dB다.
2. **모든 frame이 유한 예산의 최적은 아니다.** 875장 전체는 view당 약 9.1회만
   서비스되는 반면 stride4는 약 32회다. stride4/8이 stride1보다 높으므로 새 정보와
   재방문 사이에 내부 optimum이 있다.
3. 효과는 초반부터 단조롭게 나오지 않는다. 500 step에는 sparse가 근소 우세하고,
   stride8−stride16은 2k +0.487, 4k +1.202, 8k +1.876dB로 커졌다. 새로운 view가
   topology/appearance에 흡수될 충분한 반복 서비스가 필요하다는 증거다.
4. 이 결과는 exp83의 strict VIGS dense 실패와 모순되지 않는다. exp83 post-init
   dense는 139 후보에 266 replay, 즉 약 1.9회/view뿐이었고 pose도 GT가 아니다.
   다음 strict 설계는 모든 dense frame을 pool에 넣기보다 **causal stride4~8 수준의
   compact admission + 반복 service**를 먼저 검증해야 한다.

## 구현·산출물

- 3dgs-custom base: `da1dbda7fe55981421e2184216efedc7c6540469`
- `train.py`: opt-in `--train_frame_stride/--train_frame_phase`
- dataset builder: `scripts/incremental/build_benchmark_causal_dataset.py`
- runner: `scripts/incremental/run_exp84_gt_pose_density.sh`
- parser: `scripts/incremental/summarize_exp84_gt_pose_density.py`
- machine-readable result: `evidence/ego-drive-1000/summary.json`
- 최초 `--quiet` 실행은 milestone print까지 숨겨 무효 처리했으며 삭제하지 않고
  `evidence/ego-drive-1000/invalid_quiet/`에 보존했다.

## 다음 단일 축

exp83 strict B1/KF 서비스 보존 조건에서 dense admission을 모든 중간 frame이 아니라
causal stride8(우선)로 제한하고, admission된 view에 기존 1회성 quota보다 반복 service를
주어 `dense replay / admitted dense`를 올린 paired arm을 만든다. GT 결과에서 stride8은
4k에 이미 stride16보다 +1.20dB였으므로 strict 예산에서 가장 먼저 시험할 절충점이다.
