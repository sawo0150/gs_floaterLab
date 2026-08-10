# exp61 — OKVIS2→3dgs-custom incremental 매핑 결과 (RTX 5070 Ti 재현)

팀원(martian35) 벤치마크 `aria-online-3dgs-bench`의 OKVIS2 stereo+IMU 트래킹 →
`3dgs-custom` incremental 매퍼(`train_incremental.py`, exp48과 동일 계보) 파이프라인을
우리 RTX 5070 Ti에서 재현한 결과 PLY다. 자세한 배경/수치는
`context/experiments/exp61_okvis2_3dgs_custom_benchmark_repro.md` 참고.

| 파일 | 장면 | 학습 wall time | Gaussian 수 | OKVIS2 트래킹(online/mapdump) |
|---|---|---:|---:|---:|
| `1253__okvis2_incremental_hybrid_init_89s_915084gs.ply` | aria1253 | **89초**(49 events, 8,673 iter) | 915,084 | 49.3s / 53.1s |
| `305__okvis2_incremental_hybrid_init_216s_813645gs.ply` | aria301_305 | **216초**(124 events, 18,352 iter) | 813,645 | 81.8s / 88.1s |

**중요한 제약**: 이 PLY는 real-time 예산 스케줄러 없이 GPU가 낼 수 있는 최고 속도로
학습한 결과다(팀원의 정식 `--mapper_budget_ms` 스케줄러 커밋이 아직 우리 쪽에 없어서
보류 중). 즉 "89초에 실시간 예산을 지키며 이 정도가 나온다"가 아니라 "예산 제약 없이
돌리면 89초 걸리고 이 정도 지도가 나온다"는 뜻이다. PSNR 등 정량 평가는 아직 안 돌렸다
(eval 스크립트 자체도 팀원 recipe 의존). VIGS-SLAM strict streaming 결과(1253 27.86dB,
`gs_floaterLab/strict_streaming_online/`)와는 서로 다른 조건이라 직접 비교하면 안 된다.
