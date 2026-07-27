# Online SLAM 매핑 PLY 비교 — baseline / 최종(online) / 후처리(색정제)

| | baseline | 최종(online만) | + 후처리(색정제) |
|---|---|---|---|
| 파일 | `baseline_exp52_0720_online_first_psnr22.60.ply` | `final_exp56_0727_camcache_psnr23.49.ply` | `postprocessed_exp56_0727_finalize_psnr26.53_kf30.33.ply` |
| 원본 | `results/experiments/exp52_timingfix_parallel/3dgs_before_final.ply` | `results/experiments/exp56_ax8_camcache/3dgs_before_final.ply` | `results/experiments/exp56_finalize_polish/3dgs_final.ply` |
| 시점 | 07/20 (타이밍 버그 수정 직후, exp53~56 최적화 이전) | 07/27 (exp56 Phase1+4+7+8 전부 적용, 최종 채택) | 07/27 (exp56 최종 레시피 + `--pure_online` 없이 전체 파이프라인 재실행) |
| PSNR mean/kf | 22.60 / 22.92 dB | 23.49 / 23.88 dB | **26.53 / 30.33 dB** |
| 온라인 루프 총합 | 98.94s (실시간 배수 1.52배) | 45.79s (실시간 배수 0.70배) | 45.79s(온라인) + **오프라인 색정제 ~196s 고정비용** |
| 파일 크기(gaussian 수 비례) | 14.08MB (207,103개) | 6.17MB (90,770개) | 4.93MB (72,541개) |

같은 1253 시퀀스, 같은 online incremental mapping 파이프라인.

## 후처리(색정제) 결과 — 2026-07-27 신규 실측

`demo.py --gsmapping --final_ba_inertial`(= `--pure_online` **없이** 전체 파이프라인,
exp56 최종 레시피 위에서 실행)로 확인: 온라인 루프가 끝난 뒤 `vigs.terminate()`가
① 오프라인 backend BA(7+12 iter) ② 전체 프레임 재매핑 1회 ③ **`color_refinement`
(`Training.position_lr_max_steps` = 26,000 iteration 고정, 시퀀스 길이·프레임수와
무관)**을 순서대로 돌린다. 이 26,000-iteration 색정제 하나가 전체 후처리 시간의
~80%(07/18 250프레임 서브셋 기준 실측: 195.9초)를 차지하는 고정비용.

**핵심 발견(exp52_vigs_slam_eval.md에서 구버전 설정으로 처음 발견, 이번에 exp56
최종 레시피로 재검증)**: "keyframe 30dB" 같은 VIGS 논문 헤드라인 수치의 대부분은
온라인 재구성 자체가 아니라 이 오프라인 폴리싱이 만든 것.

| | 구버전(07/18, exp52 이전 설정) | exp56 최종 레시피(07/27, 이번 재검증) |
|---|---:|---:|
| 온라인만(held-out/kf) | 22.73 / 22.95 dB | 23.49 / 23.88 dB |
| + 후처리(held-out/kf) | 26.85 / 30.90 dB | **26.53 / 30.33 dB** |
| 후처리가 사주는 dB | +4.12 / +7.95 | **+3.04 / +6.45** |

exp56이 온라인 품질 자체를 이미 많이 끌어올려놔서(+0.76dB) 후처리로 얻는 "추가" 이득폭은
소폭 줄었지만, 절대적인 후처리 이득(+3~6dB)은 여전히 압도적으로 큼 — 현재 구조로는
26,000 iteration이 시퀀스 종료 후 한 번에 블로킹으로 도는 고정 배치 작업이라 "실시간"이
아니라 "끝나고 한 번에 몰아서" 하는 구조. 실시간 호환으로 바꾸려면 이 refinement를
세션 내내 GPU 유휴 시간에 나눠 돌리는 상시 백그라운드 프로세스로 재설계해야 함
(자세한 내용은 `ppt_outline_20260727.md` §4 및 `vigs_realtime_journey_0727.pptx`
슬라이드 19-20 참조).
