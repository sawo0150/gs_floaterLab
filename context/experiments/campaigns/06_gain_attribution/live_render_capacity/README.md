# RTX 5090: actual tracking + mapping render capacity

2026-09-25 사용자 요청: 실제 tracker를 같이 실행할 때 KF당 완료할 수 있는 렌더링 수 기록.

> **최종 비교 기준:** `comparison15_imu_v2`의 IMU pose prediction20/20/15 및 frontend4/2 결과를 사용한다. 이전100000 설정의 기록은 진단용으로 보존한다. [최종 요약](SUMMARY.md).

## 프로토콜

- Native timestamp 1× RGB+IMU, 현재 paired mapper, local native 최대 1 step/packet.
- 실제 DROID 기반 tracker/IMU/PGBA 실행. Frozen archive는 RGB 경로·timestamp·고정 calibration·heldout 목록만 사용. 저장된 pose/depth/packet 사용 금지.
- 초기 모델 로딩은 입력 시작 전 별도 기록. 입력 시작 후 mapping 초기화·dense pose·전송·tracking 모두 측정.
- 먼저 15 renders/KF 공통 credit의 실행 가능성을 확인. 이후 시간 여유의 실제 추가 학습량을 확인하는 uncapped idle probe를 사용.
- 전체 scene timestamp deadline에서 mapper 종료. Tracking 지연·미처리 KF·취소·EOS overrun까지 공개. 평균 처리량만으로 실시간 통과 판정 금지.
- camera render / backward / 실제 commit을 구분. KF denominator는 map generation별 admission과 고유 KF 둘 다 기록.
- 처리량 진단이며 품질 개선 주장 아님. Production 소스는 변경하지 않음.

Runner: `benchmarks/online_gs/campaigns/gain_attribution/measure_live_render_capacity.py`

## 결과

요약: [실측 결과와 해석](SUMMARY.md). 원본 결과와 검증 CSV는 `results/campaigns/gain_attribution/live_render_capacity/` 아래에 보존했다.

### 계측 준비와 첫 실행

- v1/aria/paired15: 필수 Omnidata/TRT 상대경로가 worker worktree에 없어 시작 실패. 기존 official dynamic RTX5090 engine 디렉터리를 실행 cwd로 지정.
- v2/aria/paired15: 계측 runner가 같은 intrinsics tensor를 반복 전달했으나 frontend가 /8 in-place로 수정하여 tracking 초기화 실패. 프레임마다 clone하도록 runner 수정. 모델 알고리즘 수정 아님.
- v3/aria/paired15: 현재 frontend1/0 설정에서 1303frame 완주, 65.124s/65.100s 입력, 1545 committed renders/103 KF admissions=15.00. zero-tail PASS. 입력시작 지연 p95 723ms/최대2405ms, 따라서 hard realtime 판정 불가. 품질평가 미실시.
- v3/aria/vanilla15: official tracking CUDA 모듈 경로 누락으로 시작 실패; 기존 built backend 경로 추가.
- v4/aria/vanilla15: official asynchronous IMU reset이 진행 중 map model을 교체하는 race 확인. 원본소스 변경 없이 reset을 existing Gaussian lock으로 보호. 양쪽 metric IMU 초기화 이후 mapping 시작으로 통일.
- v5/aria/paired_capacity: 다른 계측 run의 GPU 사용을 idle 검사에서 감지하여 시작하지 않음. 기존 run을 종료하지 않고 순차 실행.

이후 비교는 공식 frontend4/2 반복 횟수를 양쪽에 사용한다. 15renders/KF 이전 frozen-tracker 실험은 mapper만의 품질근거로 유지하고, 본 실험의 live tracking 결과와 혼합하지 않는다.

### Aria uncapped capacity probe (v6, official frontend4/2)

原速65.100s 내 mapper 완료1669 camera renders /100 KF admissions = **16.69renders/KF**. Native1045 + extra624. Tracking 전체종료67.901s, 시작지연p95=3.719s/최대4.510s. Mapper optimizer zero-tail. **16.69를 안정적인 real-time capacity로 채택하지 않는다.** 초기모델로드1.030s는 별도.
Map 및 자기 tracker의 eval-only trajectory export 완료. 별도15/KF 실시간 비교패널 진행.

**2026-09-25 (5090 live / aria / vanilla):** renders/KF=15.0, complete=True, PSNR=19.12804331306283; timing/quality 별도 판정.

```json
{
  "dataset": "aria",
  "scene": "aria1253",
  "arm": "vanilla",
  "returncode": 0,
  "output": "results/campaigns/gain_attribution/live_render_capacity/comparison15_v1/aria/vanilla",
  "valid_execution": true,
  "runtime": {
    "dataset": "aria",
    "scene": "aria1253",
    "arm": "official_vanilla_budgeted",
    "gpu": "NVIDIA GeForce RTX 5090",
    "image_size_hw": [
      464,
      464
    ],
    "duration_seconds": 65.09999891300004,
    "tracking_elapsed_seconds": 65.11999104206916,
    "model_load_seconds": 0.9562514660647139,
    "input_frames": 1303,
    "tracked_frames": 1303,
    "training_renders": 1575,
    "backward_renders": 1575,
    "committed_renders": 1575,
    "kf_admissions": 105,
    "unique_mapper_kfs": 91,
    "renders_per_kf_admission": 15.0,
    "tracking_kfs_final": 115,
    "renders_per_kf_cap": 15,
    "start_lag_ms": {
      "50": 0.1660400303080678,
      "95": 1104.2392377508795,
      "99": 1951.211601062678,
      "100": 2095.836127176881
    },
    "end_lag_ms": {
      "50": 33.42064318712801,
      "95": 1154.234473698306,
      "99": 2001.2048580101693,
      "100": 2145.833747112192
    },
    "track_call_ms": {
      "50": 14.026142889633775,
      "95": 119.23862752737465,
      "99": 277.2119999746794,
      "100": 1211.507206899114
    },
    "mapper_queue_max": 2,
    "zero_tail_observed": true,
    "error": null,
    "worker_errors": [],
    "quality_evaluated": false,
    "source_unchanged": true,
    "official_commit": "22ffe24c6df81d0bf63bd20057565c00c51d2996"
  },
  "evaluation": {
    "protocol": "saved_map_independent_double_evaluation_v1",
    "cooldown_seconds": 15,
    "input_sha256": {
      "ply": "6fca0657690273432d1735ac5635a92519b88f8c9f7ce83c0d34ebd8385e64e2",
      "full_trajectory": "7fb33cc845afe523987fec9161151abf520d8e9dc614d092bf0280c3b699ff75",
      "kf_trajectory": "b3bf5664ca5c36e0a9bf81d36de6cb16e1a5079d2e79ef709b288d171707b929",
      "mapped_uids": "58f8083b15046c8de4bd69478a13555d270b0fb74a3dcf2453705418dab9c846",
      "fixed_manifest": "40df31333e5bddd13ba178c7246d7d8fb364a32886a1345ac0d5e9748572713f"
    },
    "checks": {
      "unchanged_inputs": true,
      "same_views": true,
      "same_gaussian_count": true,
      "same_fixed_view_count": true,
      "psnr_agrees": true,
      "ssim_agrees": true,
      "lpips_agrees": true
    },
    "max_abs_per_view_difference": {
      "psnr": 0.0,
      "ssim": 0.0,
      "lpips": 0.0
    },
    "fixed_psnr_first": 19.12804331306283,
    "fixed_psnr_second": 19.12804331306283,
    "pass": true
  },
  "psnr": 19.12804331306283
}
```

**2026-09-25 (5090 live / aria / paired):** renders/KF=14.87, complete=True, PSNR=19.957373200482085; timing/quality 별도 판정.

```json
{
  "dataset": "aria",
  "scene": "aria1253",
  "arm": "paired",
  "returncode": 0,
  "output": "results/campaigns/gain_attribution/live_render_capacity/comparison15_v1/aria/paired",
  "valid_execution": true,
  "runtime": {
    "dataset": "aria",
    "scene": "aria1253",
    "gpu": "NVIDIA GeForce RTX 5090",
    "image_size_hw": [
      464,
      464
    ],
    "input_frames": 1303,
    "tracked_frames": 1303,
    "duration_seconds": 65.09999891300004,
    "tracking_elapsed_seconds": 67.70445135398768,
    "model_load_seconds": 0.9989035780308768,
    "renders_per_kf_cap": 15,
    "frontend_iterations": [
      4,
      2
    ],
    "training_renders": 1487,
    "backward_renders": 1487,
    "committed_renders": 1487,
    "native_committed_renders": 949,
    "additional_committed_renders": 538,
    "kf_admissions": 100,
    "unique_mapper_kfs": 86,
    "renders_per_kf_admission": 14.87,
    "tracking_kfs_final": 115,
    "start_lag_ms": {
      "50": 43.04291703738272,
      "95": 3599.2716584238196,
      "99": 4425.872091103811,
      "100": 4521.190007100813
    },
    "end_lag_ms": {
      "50": 93.24520302470773,
      "95": 3649.268577375912,
      "99": 4475.868415308651,
      "100": 4571.190911112353
    },
    "track_call_ms": {
      "50": 6.585555034689605,
      "95": 167.4138161470182,
      "99": 361.57062832964584,
      "100": 2363.979151006788
    },
    "mapper_queue_max": 1,
    "peak_cuda_allocated_bytes": 6023322624,
    "worker": {
      "accepted": 98,
      "completed": 98,
      "cancelled": 0,
      "failed": 0,
      "unfinished_tasks": 0,
      "closed": true,
      "stopped_at": 973529.307683906,
      "productive_idle_calls": 538,
      "input_wait_seconds": 47.06507476710249,
      "error": null
    },
    "zero_tail_observed": true,
    "overruns": [],
    "error": null,
    "source_unchanged": true,
    "quality_evaluated": false
  },
  "evaluation": {
    "protocol": "saved_map_independent_double_evaluation_v1",
    "cooldown_seconds": 15,
    "input_sha256": {
      "ply": "4ffa99c44a9504de1df0b9324f739633eae61571201703cf0391cbfaedb671c8",
      "full_trajectory": "ca10c2f44bf7363bbb85fe5dd17fd3e89872f9e7c7c9ea9501b8364835c0a739",
      "kf_trajectory": "f807c72575aea3b8e9886febda67a6fb3030aa97aab452a977765607b6c6f493",
      "mapped_uids": "5e7184cd0a4288e117d003ecb2348dc7f6c86c78bd287cf94c29466b7bb94776",
      "fixed_manifest": "40df31333e5bddd13ba178c7246d7d8fb364a32886a1345ac0d5e9748572713f"
    },
    "checks": {
      "unchanged_inputs": true,
      "same_views": true,
      "same_gaussian_count": true,
      "same_fixed_view_count": true,
      "psnr_agrees": true,
      "ssim_agrees": true,
      "lpips_agrees": true
    },
    "max_abs_per_view_difference": {
      "psnr": 0.0,
      "ssim": 0.0,
      "lpips": 0.0
    },
    "fixed_psnr_first": 19.957373200482085,
    "fixed_psnr_second": 19.957373200482085,
    "pass": true
  },
  "psnr": 19.957373200482085
}
```

**2026-09-25 (5090 live / rpng / vanilla):** renders/KF=14.9765625, complete=True, PSNR=19.750227318153726; timing/quality 별도 판정.

```json
{
  "dataset": "rpng",
  "scene": "table_06",
  "arm": "vanilla",
  "returncode": 0,
  "output": "results/campaigns/gain_attribution/live_render_capacity/comparison15_v1/rpng/vanilla",
  "valid_execution": true,
  "runtime": {
    "dataset": "rpng",
    "scene": "table_06",
    "arm": "official_vanilla_budgeted",
    "gpu": "NVIDIA GeForce RTX 5090",
    "image_size_hw": [
      344,
      616
    ],
    "duration_seconds": 92.24467062950134,
    "tracking_elapsed_seconds": 144.6606153290486,
    "model_load_seconds": 0.9692721349420026,
    "input_frames": 2767,
    "tracked_frames": 2767,
    "training_renders": 1920,
    "backward_renders": 1920,
    "committed_renders": 1917,
    "kf_admissions": 128,
    "unique_mapper_kfs": 100,
    "renders_per_kf_admission": 14.9765625,
    "tracking_kfs_final": 232,
    "renders_per_kf_cap": 15,
    "start_lag_ms": {
      "50": 42233.83921175264,
      "95": 55187.75255820947,
      "99": 55654.49667709647,
      "100": 55905.6513478281
    },
    "end_lag_ms": {
      "50": 42275.48345585819,
      "95": 55221.09476327896,
      "99": 55687.839362625964,
      "100": 55938.99412616156
    },
    "track_call_ms": {
      "50": 11.065330007113516,
      "95": 194.1053914371874,
      "99": 757.4418073520093,
      "100": 1765.8294889843091
    },
    "mapper_queue_max": 2,
    "zero_tail_observed": true,
    "error": null,
    "worker_errors": [],
    "quality_evaluated": false,
    "source_unchanged": true,
    "official_commit": "22ffe24c6df81d0bf63bd20057565c00c51d2996"
  },
  "evaluation": {
    "protocol": "saved_map_independent_double_evaluation_v1",
    "cooldown_seconds": 15,
    "input_sha256": {
      "ply": "551702f6c1800d1b768757db0a15fe2bf18eaa266eb3092ba7d0677ffbf85114",
      "full_trajectory": "78185407b726180ab647b136b2080eb829105bb4b5812464d16c39ca13fc935c",
      "kf_trajectory": "ed96b8810360920f2c7c67c1101a784cfc22d23c3e2be83d0c8ded86ac2e8c63",
      "mapped_uids": "e9ea2d892434b9c3765318950d9564e39e71639e2ea266683b304b436c010fbd",
      "fixed_manifest": "dc75e1ce0c7a40611c0cf208091d1fc9c47b19127e2efcddd1c0ac8a952e406a"
    },
    "checks": {
      "unchanged_inputs": true,
      "same_views": true,
      "same_gaussian_count": true,
      "same_fixed_view_count": true,
      "psnr_agrees": true,
      "ssim_agrees": true,
      "lpips_agrees": true
    },
    "max_abs_per_view_difference": {
      "psnr": 0.0,
      "ssim": 0.0,
      "lpips": 0.0
    },
    "fixed_psnr_first": 19.750227318153726,
    "fixed_psnr_second": 19.750227318153726,
    "pass": true
  },
  "psnr": 19.750227318153726
}
```

**2026-09-25 (5090 live / rpng / paired):** renders/KF=12.356164383561644, complete=True, PSNR=17.74931611928854; timing/quality 별도 판정.

```json
{
  "dataset": "rpng",
  "scene": "table_06",
  "arm": "paired",
  "returncode": 0,
  "output": "results/campaigns/gain_attribution/live_render_capacity/comparison15_v1/rpng/paired",
  "valid_execution": true,
  "runtime": {
    "dataset": "rpng",
    "scene": "table_06",
    "gpu": "NVIDIA GeForce RTX 5090",
    "image_size_hw": [
      344,
      616
    ],
    "input_frames": 2767,
    "tracked_frames": 2767,
    "duration_seconds": 92.24467062950134,
    "tracking_elapsed_seconds": 114.77325514797121,
    "model_load_seconds": 0.9883626750670373,
    "renders_per_kf_cap": 15,
    "frontend_iterations": [
      4,
      2
    ],
    "training_renders": 1804,
    "backward_renders": 1804,
    "committed_renders": 1804,
    "native_committed_renders": 1804,
    "additional_committed_renders": 0,
    "kf_admissions": 146,
    "unique_mapper_kfs": 134,
    "renders_per_kf_admission": 12.356164383561644,
    "tracking_kfs_final": 212,
    "start_lag_ms": {
      "50": 16754.55019378569,
      "95": 24958.66595535772,
      "99": 25402.64868058963,
      "100": 25602.334270020947
    },
    "end_lag_ms": {
      "50": 16789.22815877013,
      "95": 24992.00916077243,
      "99": 25435.994302493058,
      "100": 25635.67457778845
    },
    "track_call_ms": {
      "50": 10.912080993875861,
      "95": 152.09480065386737,
      "99": 519.3312291451954,
      "100": 2372.3965460667387
    },
    "mapper_queue_max": 1,
    "peak_cuda_allocated_bytes": 5897691136,
    "worker": {
      "accepted": 167,
      "completed": 167,
      "cancelled": 0,
      "failed": 0,
      "unfinished_tasks": 0,
      "closed": true,
      "stopped_at": 973865.557795089,
      "productive_idle_calls": 0,
      "input_wait_seconds": 81.40250038809609,
      "error": null
    },
    "zero_tail_observed": true,
    "overruns": [],
    "error": null,
    "source_unchanged": true,
    "quality_evaluated": false
  },
  "evaluation": {
    "protocol": "saved_map_independent_double_evaluation_v1",
    "cooldown_seconds": 15,
    "input_sha256": {
      "ply": "e0a4cc45eef73ebda2ada206b12d6c0d6f2fe204c3e84fc82519a306a94b6f29",
      "full_trajectory": "44018e84c6131f86cc011175acfa52662f1ccd2e559a4c11961438035f52f2d2",
      "kf_trajectory": "aa3d16f6f72be2d950798d149445730e705d8be79b46a4734a6cbed1494733eb",
      "mapped_uids": "3d37bb4986dfaf2c869184a4c72fa4a59a6104fe843bf9d46dfd6c3c19da3b30",
      "fixed_manifest": "dc75e1ce0c7a40611c0cf208091d1fc9c47b19127e2efcddd1c0ac8a952e406a"
    },
    "checks": {
      "unchanged_inputs": true,
      "same_views": true,
      "same_gaussian_count": true,
      "same_fixed_view_count": true,
      "psnr_agrees": true,
      "ssim_agrees": true,
      "lpips_agrees": true
    },
    "max_abs_per_view_difference": {
      "psnr": 0.0,
      "ssim": 0.0,
      "lpips": 0.0
    },
    "fixed_psnr_first": 17.74931611928854,
    "fixed_psnr_second": 17.74931611928854,
    "pass": true
  },
  "psnr": 17.74931611928854
}
```

**2026-09-25 (5090 live / utmm / vanilla):** renders/KF=15.0, complete=True, PSNR=15.932410775879283; timing/quality 별도 판정.

```json
{
  "dataset": "utmm",
  "scene": "square-1",
  "arm": "vanilla",
  "returncode": 0,
  "output": "results/campaigns/gain_attribution/live_render_capacity/comparison15_v1/utmm/vanilla",
  "valid_execution": true,
  "runtime": {
    "dataset": "utmm",
    "scene": "square-1",
    "arm": "official_vanilla_budgeted",
    "gpu": "NVIDIA GeForce RTX 5090",
    "image_size_hw": [
      328,
      648
    ],
    "duration_seconds": 53.80941700935364,
    "tracking_elapsed_seconds": 54.21531682100613,
    "model_load_seconds": 0.9776018559932709,
    "input_frames": 1614,
    "tracked_frames": 1614,
    "training_renders": 1140,
    "backward_renders": 1140,
    "committed_renders": 1140,
    "kf_admissions": 76,
    "unique_mapper_kfs": 66,
    "renders_per_kf_admission": 15.0,
    "tracking_kfs_final": 83,
    "renders_per_kf_cap": 15,
    "start_lag_ms": {
      "50": 481.2916947994381,
      "95": 2005.3403889411125,
      "99": 2143.2882076175883,
      "100": 2211.6433371556923
    },
    "end_lag_ms": {
      "50": 514.7399742854759,
      "95": 2038.785323570482,
      "99": 2176.585762973409,
      "100": 2244.906442472711
    },
    "track_call_ms": {
      "50": 15.821823035366833,
      "95": 109.74582834169267,
      "99": 148.76152368960894,
      "100": 1126.2725749984384
    },
    "mapper_queue_max": 1,
    "zero_tail_observed": true,
    "error": null,
    "worker_errors": [],
    "quality_evaluated": false,
    "source_unchanged": true,
    "official_commit": "22ffe24c6df81d0bf63bd20057565c00c51d2996"
  },
  "evaluation": {
    "protocol": "saved_map_independent_double_evaluation_v1",
    "cooldown_seconds": 15,
    "input_sha256": {
      "ply": "6311ebab4c08fe2d6fa21d6f3e27eb7a1a0230432d2c80b0a7fadd6b7cf2e63d",
      "full_trajectory": "88ee576c5cc94d08db77428b05e53fe399f552306948e28e1680f4401b5ec07f",
      "kf_trajectory": "2cb11e2a13554c6e219c5022c467835505096d220c73bd408515c83a81e4b04d",
      "mapped_uids": "db3e0565a93afbedce6a408faa1d569c0c802d660cd738915a369aed68cacfd2",
      "fixed_manifest": "6a54fdd3ccf272b762c4c4ebca13803f09e28efe4f43cbddf940cbb80dba8e26"
    },
    "checks": {
      "unchanged_inputs": true,
      "same_views": true,
      "same_gaussian_count": true,
      "same_fixed_view_count": true,
      "psnr_agrees": true,
      "ssim_agrees": true,
      "lpips_agrees": true
    },
    "max_abs_per_view_difference": {
      "psnr": 0.0,
      "ssim": 0.0,
      "lpips": 0.0
    },
    "fixed_psnr_first": 15.932410775879283,
    "fixed_psnr_second": 15.932410775879283,
    "pass": true
  },
  "psnr": 15.932410775879283
}
```

**2026-09-25 (5090 live / utmm / paired):** renders/KF=9.338709677419354, complete=True, PSNR=10.661520877002198; timing/quality 별도 판정.

```json
{
  "dataset": "utmm",
  "scene": "square-1",
  "arm": "paired",
  "returncode": 0,
  "output": "results/campaigns/gain_attribution/live_render_capacity/comparison15_v1/utmm/paired",
  "valid_execution": true,
  "runtime": {
    "dataset": "utmm",
    "scene": "square-1",
    "gpu": "NVIDIA GeForce RTX 5090",
    "image_size_hw": [
      328,
      648
    ],
    "input_frames": 1614,
    "tracked_frames": 1614,
    "duration_seconds": 53.80941700935364,
    "tracking_elapsed_seconds": 54.257197850965895,
    "model_load_seconds": 1.0228394890436903,
    "renders_per_kf_cap": 15,
    "frontend_iterations": [
      4,
      2
    ],
    "training_renders": 579,
    "backward_renders": 579,
    "committed_renders": 579,
    "native_committed_renders": 569,
    "additional_committed_renders": 10,
    "kf_admissions": 62,
    "unique_mapper_kfs": 51,
    "renders_per_kf_admission": 9.338709677419354,
    "tracking_kfs_final": 67,
    "start_lag_ms": {
      "50": 37.54812723491341,
      "95": 815.2980811544692,
      "99": 1110.0741498172265,
      "100": 1238.3972937241197
    },
    "end_lag_ms": {
      "50": 71.00432808510959,
      "95": 848.6888194805941,
      "99": 1143.3376137784198,
      "100": 1271.6472297906876
    },
    "track_call_ms": {
      "50": 16.326683515217155,
      "95": 115.76564809656699,
      "99": 169.42909147939613,
      "100": 1083.914713934064
    },
    "mapper_queue_max": 1,
    "peak_cuda_allocated_bytes": 4727297536,
    "worker": {
      "accepted": 55,
      "completed": 55,
      "cancelled": 0,
      "failed": 0,
      "unfinished_tasks": 0,
      "closed": true,
      "stopped_at": 974103.137808721,
      "productive_idle_calls": 10,
      "input_wait_seconds": 50.23719126393553,
      "error": null
    },
    "zero_tail_observed": true,
    "overruns": [],
    "error": null,
    "source_unchanged": true,
    "quality_evaluated": false
  },
  "evaluation": {
    "protocol": "saved_map_independent_double_evaluation_v1",
    "cooldown_seconds": 15,
    "input_sha256": {
      "ply": "c42fc296ad79c095501cc19f8afd476d9b2f7013d28ba4f7763fd8f45df2d0c6",
      "full_trajectory": "6394e4663d616a6b66f88ad14d3e6f03b15858d9d34352f504be9bad1004c226",
      "kf_trajectory": "ddad2dbda248a5389ffc764f9c30d3a8477858c9f5c2c5ffab23cb9b5583efdb",
      "mapped_uids": "1cc31c87bc6b333f8920597f3b973a8f61235262c3343bad330486551f03adf1",
      "fixed_manifest": "6a54fdd3ccf272b762c4c4ebca13803f09e28efe4f43cbddf940cbb80dba8e26"
    },
    "checks": {
      "unchanged_inputs": true,
      "same_views": true,
      "same_gaussian_count": true,
      "same_fixed_view_count": true,
      "psnr_agrees": true,
      "ssim_agrees": true,
      "lpips_agrees": true
    },
    "max_abs_per_view_difference": {
      "psnr": 0.0,
      "ssim": 0.0,
      "lpips": 0.0
    },
    "fixed_psnr_first": 10.661520877002198,
    "fixed_psnr_second": 10.661520877002198,
    "pass": true
  },
  "psnr": 10.661520877002198
}
```

**2026-09-25 (5090 RPNG tracking-only):** official frontend4/2 설정·mapping0에서도 tracking114.451s/입력92.245s, p95lag24.644s. 같은 tracker+paired15의114.773s와 유사; 이 설정의 1×불가를 렌더 예산만으로 해결할 수 없음. 현재frontend1/0 별도 확인.

결과: `results/campaigns/gain_attribution/live_render_capacity/tracking_controls/rpng_official/result.json`

**2026-09-25 설정 정정:** comparison15_v1, current_frontend, v3–v6 및 tracking_controls는 IMU_poseinit_after=100000을 상속했다. IMU preintegration/BA는 실행됐지만 IMU pose prediction은 사실상 비활성이다. 일반 벤치마크 설정으로 해석하지 않는다. 공식 RPNG=20/UTMM=15 및 Aria live=20을 복원한 comparison15_imu_v2를 별도로 실행한다. 기존 측정은 삭제하지 않는다.

### 보존: frontend1/0, IMU prediction 비활성 진단

| Scene | renders/KF | extra KF/dense | PSNR | tracking/input s |
|---|---:|---:|---:|---:|
|aria|15.000|298/297|20.819492|65.121/65.100|
|rpng|13.617|20/20|17.627378|92.257/92.245|
|utmm|9.379|4/4|15.381491|53.971/53.809|

3run 각각 저장된 map을 2회 평가하여 동일 PSNR 확인. 반복 training은 아님. 결과 위치: results/campaigns/gain_attribution/live_render_capacity/current_frontend.

**2026-09-25 (5090 live / aria / vanilla / IMU pose init 20):** renders/KF=15.0, complete=True, PSNR=19.15189616370747; timing/quality 별도 판정.

```json
{
  "dataset": "aria",
  "scene": "aria1253",
  "arm": "vanilla",
  "returncode": 0,
  "output": "/home/intern/gs_floaterLab/results/campaigns/gain_attribution/live_render_capacity/comparison15_imu_v2/aria/vanilla",
  "valid_execution": true,
  "runtime": {
    "dataset": "aria",
    "scene": "aria1253",
    "arm": "official_vanilla_budgeted",
    "gpu": "NVIDIA GeForce RTX 5090",
    "image_size_hw": [
      464,
      464
    ],
    "duration_seconds": 65.09999891300004,
    "tracking_elapsed_seconds": 65.11964329902548,
    "model_load_seconds": 1.0793560920283198,
    "input_frames": 1303,
    "tracked_frames": 1303,
    "training_renders": 1575,
    "backward_renders": 1575,
    "committed_renders": 1575,
    "kf_admissions": 105,
    "unique_mapper_kfs": 91,
    "renders_per_kf_admission": 15.0,
    "frontend_iterations": [
      4,
      2
    ],
    "IMU_poseinit_after": 20,
    "tracking_kfs_final": 115,
    "renders_per_kf_cap": 15,
    "start_lag_ms": {
      "50": 0.17287407536059618,
      "95": 1151.9027482601803,
      "99": 1692.1743120765314,
      "100": 1854.12937507499
    },
    "end_lag_ms": {
      "50": 39.014609064906836,
      "95": 1201.895476831122,
      "99": 1742.1689365408383,
      "100": 1904.1219950886443
    },
    "track_call_ms": {
      "50": 12.477935990318656,
      "95": 125.9241090272553,
      "99": 247.71152553614237,
      "100": 1419.3473730701953
    },
    "mapper_queue_max": 2,
    "zero_tail_observed": true,
    "error": null,
    "worker_errors": [],
    "quality_evaluated": false,
    "source_unchanged": true,
    "official_commit": "22ffe24c6df81d0bf63bd20057565c00c51d2996"
  },
  "evaluation": {
    "protocol": "saved_map_independent_double_evaluation_v1",
    "cooldown_seconds": 15,
    "input_sha256": {
      "ply": "1bbbe101631eb2a4c191a27be2fd49b7f59e024ffed09148ab7a51fdbe5e81ca",
      "full_trajectory": "35e5a1ff795097b563db44283d4fc992d22c21a803cb964ac825584dd49f7467",
      "kf_trajectory": "b8ba4ba308f93f89815010b4b03100c756c9049c299184e0ad321ca257b8980e",
      "mapped_uids": "58f8083b15046c8de4bd69478a13555d270b0fb74a3dcf2453705418dab9c846",
      "fixed_manifest": "40df31333e5bddd13ba178c7246d7d8fb364a32886a1345ac0d5e9748572713f"
    },
    "checks": {
      "unchanged_inputs": true,
      "same_views": true,
      "same_gaussian_count": true,
      "same_fixed_view_count": true,
      "psnr_agrees": true,
      "ssim_agrees": true,
      "lpips_agrees": true
    },
    "max_abs_per_view_difference": {
      "psnr": 0.0,
      "ssim": 0.0,
      "lpips": 0.0
    },
    "fixed_psnr_first": 19.15189616370747,
    "fixed_psnr_second": 19.15189616370747,
    "pass": true
  },
  "psnr": 19.15189616370747
}
```

**2026-09-25 (5090 live / aria / paired / IMU pose init 20):** renders/KF=14.794117647058824, complete=True, PSNR=19.369261101002003; timing/quality 별도 판정.

```json
{
  "dataset": "aria",
  "scene": "aria1253",
  "arm": "paired",
  "returncode": 0,
  "output": "/home/intern/gs_floaterLab/results/campaigns/gain_attribution/live_render_capacity/comparison15_imu_v2/aria/paired",
  "valid_execution": true,
  "runtime": {
    "dataset": "aria",
    "scene": "aria1253",
    "gpu": "NVIDIA GeForce RTX 5090",
    "image_size_hw": [
      464,
      464
    ],
    "input_frames": 1303,
    "tracked_frames": 1303,
    "duration_seconds": 65.09999891300004,
    "tracking_elapsed_seconds": 67.12773757707328,
    "model_load_seconds": 1.017427757033147,
    "renders_per_kf_cap": 15,
    "frontend_iterations": [
      4,
      2
    ],
    "IMU_poseinit_after": 20,
    "training_renders": 1509,
    "backward_renders": 1509,
    "committed_renders": 1509,
    "native_committed_renders": 976,
    "additional_committed_renders": 533,
    "kf_admissions": 102,
    "unique_mapper_kfs": 88,
    "renders_per_kf_admission": 14.794117647058824,
    "tracking_kfs_final": 115,
    "start_lag_ms": {
      "50": 40.82125809509307,
      "95": 2916.704759059937,
      "99": 3759.3185235443525,
      "100": 3882.944155135192
    },
    "end_lag_ms": {
      "50": 90.86674905847758,
      "95": 2966.699071833861,
      "99": 3809.3196334620006,
      "100": 3932.940435130149
    },
    "track_call_ms": {
      "50": 6.718310993164778,
      "95": 163.32092520315197,
      "99": 338.8731386000293,
      "100": 2279.241285054013
    },
    "mapper_queue_max": 1,
    "peak_cuda_allocated_bytes": 5742557696,
    "worker": {
      "accepted": 100,
      "completed": 100,
      "cancelled": 0,
      "failed": 0,
      "unfinished_tasks": 0,
      "closed": true,
      "stopped_at": 975217.73765023,
      "productive_idle_calls": 533,
      "input_wait_seconds": 46.84259536815807,
      "error": null
    },
    "zero_tail_observed": true,
    "overruns": [],
    "error": null,
    "source_unchanged": true,
    "quality_evaluated": false
  },
  "evaluation": {
    "protocol": "saved_map_independent_double_evaluation_v1",
    "cooldown_seconds": 15,
    "input_sha256": {
      "ply": "39577240a536bfc4cb4f97021767fa613067971f590c4a6b84cac32d296638a4",
      "full_trajectory": "f98435288e0a671fc9b7ee09ba895c0f795145014fe9e7700a47c797c23d736d",
      "kf_trajectory": "ec4f76f82d467f6d9cab1fc80c65bec2759f372838f9ed6c3d6e48d8a2fd0f39",
      "mapped_uids": "abfb5e86e1523284b8152c17eaebf80919c004153e5623d607d851f79417e9f5",
      "fixed_manifest": "40df31333e5bddd13ba178c7246d7d8fb364a32886a1345ac0d5e9748572713f"
    },
    "checks": {
      "unchanged_inputs": true,
      "same_views": true,
      "same_gaussian_count": true,
      "same_fixed_view_count": true,
      "psnr_agrees": true,
      "ssim_agrees": true,
      "lpips_agrees": true
    },
    "max_abs_per_view_difference": {
      "psnr": 0.0,
      "ssim": 0.0,
      "lpips": 0.0
    },
    "fixed_psnr_first": 19.369261101002003,
    "fixed_psnr_second": 19.369261101002003,
    "pass": true
  },
  "psnr": 19.369261101002003
}
```

### 설정 복원 근거와 측정 범위

- IMU_poseinit_after는 IMU BA 전체 on/off가 아니라 DepthVideo.init_next_pose를 시작하는 KF index다. 이전 mapper setup은 demo.py의 CLI 기본값100000을 상속했다. 실제 공식 eval_rpng_mono.py는20, eval_utmm_mono.py는15, 기존 Aria live script는20을 지정한다.
- comparison15_imu_v2는 양쪽에20/20/15를 동일 적용하고, frontend 반복도4/2로 맞춘 비교다. frontend1/0 진단과 섞지 않는다.
- VIGS 공식 mapper는 window+global2, 우리 paired runtime은 native window only 및 추가 full-pool KF/dense 교대 ERVS다. 우리 원본 YAML에 global6이 남아 있지만 OnlineMapperRuntime의 paired 설정이 실행 시0으로 덮어쓴다.
- 15회는 gradient 학습용 카메라 렌더 상한이며 no-grad 보조 렌더는 별도 집계한다. 보조 렌더의 실행시간은 전체시간에 포함한다. CUDA 배치 한 호출이 여러 카메라면 카메라 수만큼 센다.
- 1× 입력률로 검사하는 이번 측정은 과거 strict27의1.5× 시간 계약과 다르다. 이 테스트로 strict27 목표 달성을 주장하지 않는다.
- 모델/engine 로딩과 저장 후 held-out 평가만 입력 clock 밖에 있다. 중간 initialization·reset·pose refinement·host-device transfer 비용은 숨기지 않는다.

재실행(새 output 경로 필요):
```bash
python3 benchmarks/online_gs/campaigns/gain_attribution/run_live_capacity_comparison.py --output results/campaigns/gain_attribution/live_render_capacity/comparison15_imu_v2
python3 benchmarks/online_gs/campaigns/gain_attribution/analyze_live_capacity_comparison.py --panel results/campaigns/gain_attribution/live_render_capacity/comparison15_imu_v2
```

**2026-09-25 (5090 live / rpng / vanilla / IMU pose init 20):** renders/KF=15.0, complete=True, PSNR=19.393897207792815; timing/quality 별도 판정.

```json
{
  "dataset": "rpng",
  "scene": "table_06",
  "arm": "vanilla",
  "returncode": 0,
  "output": "/home/intern/gs_floaterLab/results/campaigns/gain_attribution/live_render_capacity/comparison15_imu_v2/rpng/vanilla",
  "valid_execution": true,
  "runtime": {
    "dataset": "rpng",
    "scene": "table_06",
    "arm": "official_vanilla_budgeted",
    "gpu": "NVIDIA GeForce RTX 5090",
    "image_size_hw": [
      344,
      616
    ],
    "duration_seconds": 92.24467062950134,
    "tracking_elapsed_seconds": 143.90024235099554,
    "model_load_seconds": 0.9903057309566066,
    "input_frames": 2767,
    "tracked_frames": 2767,
    "training_renders": 1965,
    "backward_renders": 1965,
    "committed_renders": 1965,
    "kf_admissions": 131,
    "unique_mapper_kfs": 103,
    "renders_per_kf_admission": 15.0,
    "frontend_iterations": [
      4,
      2
    ],
    "IMU_poseinit_after": 20,
    "tracking_kfs_final": 232,
    "renders_per_kf_cap": 15,
    "start_lag_ms": {
      "50": 40873.092114692554,
      "95": 54613.43911582371,
      "99": 55030.74322041357,
      "100": 55343.61072536558
    },
    "end_lag_ms": {
      "50": 40913.04843639955,
      "95": 54646.77380514331,
      "99": 55064.081701692194,
      "100": 55376.95312767755
    },
    "track_call_ms": {
      "50": 11.23138703405857,
      "95": 198.81669057067447,
      "99": 732.9151607630777,
      "100": 1766.401274013333
    },
    "mapper_queue_max": 2,
    "zero_tail_observed": true,
    "error": null,
    "worker_errors": [],
    "quality_evaluated": false,
    "source_unchanged": true,
    "official_commit": "22ffe24c6df81d0bf63bd20057565c00c51d2996"
  },
  "evaluation": {
    "protocol": "saved_map_independent_double_evaluation_v1",
    "cooldown_seconds": 15,
    "input_sha256": {
      "ply": "958bd3623defde4335d0c168cb93c5be54a0b9073e90b14ea1eb1e38bda6f359",
      "full_trajectory": "5c808efcba58b9cbddeb348529b8253c150cb772e198032c1e481a9370352a56",
      "kf_trajectory": "c068a952dbb812529ab2d2680e8e210f6c0b7e58d819775731bddb1f910a5d19",
      "mapped_uids": "2b32f5faafdff81c04275d8f32333dc6327c0957cf2658f606d4557d8c1c7d84",
      "fixed_manifest": "dc75e1ce0c7a40611c0cf208091d1fc9c47b19127e2efcddd1c0ac8a952e406a"
    },
    "checks": {
      "unchanged_inputs": true,
      "same_views": true,
      "same_gaussian_count": true,
      "same_fixed_view_count": true,
      "psnr_agrees": true,
      "ssim_agrees": true,
      "lpips_agrees": true
    },
    "max_abs_per_view_difference": {
      "psnr": 0.0,
      "ssim": 0.0,
      "lpips": 0.0
    },
    "fixed_psnr_first": 19.393897207792815,
    "fixed_psnr_second": 19.393897207792815,
    "pass": true
  },
  "psnr": 19.393897207792815
}
```

**2026-09-25 (5090 live / rpng / paired / IMU pose init 20):** renders/KF=12.431506849315069, complete=True, PSNR=17.91506887384363; timing/quality 별도 판정.

```json
{
  "dataset": "rpng",
  "scene": "table_06",
  "arm": "paired",
  "returncode": 0,
  "output": "/home/intern/gs_floaterLab/results/campaigns/gain_attribution/live_render_capacity/comparison15_imu_v2/rpng/paired",
  "valid_execution": true,
  "runtime": {
    "dataset": "rpng",
    "scene": "table_06",
    "gpu": "NVIDIA GeForce RTX 5090",
    "image_size_hw": [
      344,
      616
    ],
    "input_frames": 2767,
    "tracked_frames": 2767,
    "duration_seconds": 92.24467062950134,
    "tracking_elapsed_seconds": 115.05593004706316,
    "model_load_seconds": 0.9790114569477737,
    "renders_per_kf_cap": 15,
    "frontend_iterations": [
      4,
      2
    ],
    "IMU_poseinit_after": 20,
    "training_renders": 1815,
    "backward_renders": 1815,
    "committed_renders": 1815,
    "native_committed_renders": 1815,
    "additional_committed_renders": 0,
    "kf_admissions": 146,
    "unique_mapper_kfs": 134,
    "renders_per_kf_admission": 12.431506849315069,
    "tracking_kfs_final": 211,
    "start_lag_ms": {
      "50": 16218.141476390883,
      "95": 24732.21334721893,
      "99": 25261.129038538784,
      "100": 25386.162296985276
    },
    "end_lag_ms": {
      "50": 16253.81841394119,
      "95": 24765.55816041073,
      "99": 25294.474418002646,
      "100": 25419.50389998965
    },
    "track_call_ms": {
      "50": 11.036241077817976,
      "95": 148.47610847791654,
      "99": 524.4779063202649,
      "100": 2364.336129045114
    },
    "mapper_queue_max": 1,
    "peak_cuda_allocated_bytes": 6296079360,
    "worker": {
      "accepted": 168,
      "completed": 168,
      "cancelled": 0,
      "failed": 0,
      "unfinished_tasks": 0,
      "closed": true,
      "stopped_at": 975553.96269679,
      "productive_idle_calls": 0,
      "input_wait_seconds": 81.27212666894775,
      "error": null
    },
    "zero_tail_observed": true,
    "overruns": [],
    "error": null,
    "source_unchanged": true,
    "quality_evaluated": false
  },
  "evaluation": {
    "protocol": "saved_map_independent_double_evaluation_v1",
    "cooldown_seconds": 15,
    "input_sha256": {
      "ply": "0ceaad36c4fe022c4ada63e0883abe317e7568d7f018c80e366f6ccbe8db0c6b",
      "full_trajectory": "19839972fc706d51d97feac803262e1b0821f4797c84d5f57625682b52559cd4",
      "kf_trajectory": "0db42477b3b6b0ebea0252176e666ce803c2ada1e1cfab86bd58550c26699755",
      "mapped_uids": "1678e63929e7eaa25b31e1ca3ba8d79d29eb96e354bc6a23ec6fd68afdbd4a8b",
      "fixed_manifest": "dc75e1ce0c7a40611c0cf208091d1fc9c47b19127e2efcddd1c0ac8a952e406a"
    },
    "checks": {
      "unchanged_inputs": true,
      "same_views": true,
      "same_gaussian_count": true,
      "same_fixed_view_count": true,
      "psnr_agrees": true,
      "ssim_agrees": true,
      "lpips_agrees": true
    },
    "max_abs_per_view_difference": {
      "psnr": 0.0,
      "ssim": 0.0,
      "lpips": 0.0
    },
    "fixed_psnr_first": 17.91506887384363,
    "fixed_psnr_second": 17.91506887384363,
    "pass": true
  },
  "psnr": 17.91506887384363
}
```

**2026-09-25 (5090 live / utmm / vanilla / IMU pose init 15):** renders/KF=14.8125, complete=True, PSNR=15.772941839547805; timing/quality 별도 판정.

```json
{
  "dataset": "utmm",
  "scene": "square-1",
  "arm": "vanilla",
  "returncode": 0,
  "output": "/home/intern/gs_floaterLab/results/campaigns/gain_attribution/live_render_capacity/comparison15_imu_v2/utmm/vanilla",
  "valid_execution": true,
  "runtime": {
    "dataset": "utmm",
    "scene": "square-1",
    "arm": "official_vanilla_budgeted",
    "gpu": "NVIDIA GeForce RTX 5090",
    "image_size_hw": [
      328,
      648
    ],
    "duration_seconds": 53.80941700935364,
    "tracking_elapsed_seconds": 54.224206325015984,
    "model_load_seconds": 0.9401339939795434,
    "input_frames": 1614,
    "tracked_frames": 1614,
    "training_renders": 1198,
    "backward_renders": 1198,
    "committed_renders": 1185,
    "kf_admissions": 80,
    "unique_mapper_kfs": 70,
    "renders_per_kf_admission": 14.8125,
    "frontend_iterations": [
      4,
      2
    ],
    "IMU_poseinit_after": 15,
    "tracking_kfs_final": 84,
    "renders_per_kf_cap": 15,
    "start_lag_ms": {
      "50": 451.8559720017947,
      "95": 2271.3793244969565,
      "99": 2440.24302139529,
      "100": 2513.9707014895976
    },
    "end_lag_ms": {
      "50": 485.2536098915152,
      "95": 2304.675796418451,
      "99": 2473.506338190054,
      "100": 2547.2330898046494
    },
    "track_call_ms": {
      "50": 16.05649699922651,
      "95": 108.4596041997429,
      "99": 145.15403433935694,
      "100": 1157.2024939814582
    },
    "mapper_queue_max": 1,
    "zero_tail_observed": true,
    "error": null,
    "worker_errors": [],
    "quality_evaluated": false,
    "source_unchanged": true,
    "official_commit": "22ffe24c6df81d0bf63bd20057565c00c51d2996"
  },
  "evaluation": {
    "protocol": "saved_map_independent_double_evaluation_v1",
    "cooldown_seconds": 15,
    "input_sha256": {
      "ply": "234c61f5a91fa3fb8b00adeb48f1569eac1a19cde434a5d198b0ac20c97bebe8",
      "full_trajectory": "bc47155b7f43277dbbc905739e06f61c259062f82c9728cbe86ff2c2818c0925",
      "kf_trajectory": "af1aeab1e2ed339be74c76b5b7336e2da03f0c250a2716323cc1325b540c6541",
      "mapped_uids": "8a873627a23e86f3550be5057a62a1acce7078ea215b645fa5c422cb44591b87",
      "fixed_manifest": "6a54fdd3ccf272b762c4c4ebca13803f09e28efe4f43cbddf940cbb80dba8e26"
    },
    "checks": {
      "unchanged_inputs": true,
      "same_views": true,
      "same_gaussian_count": true,
      "same_fixed_view_count": true,
      "psnr_agrees": true,
      "ssim_agrees": true,
      "lpips_agrees": true
    },
    "max_abs_per_view_difference": {
      "psnr": 0.0,
      "ssim": 0.0,
      "lpips": 0.0
    },
    "fixed_psnr_first": 15.772941839547805,
    "fixed_psnr_second": 15.772941839547805,
    "pass": true
  },
  "psnr": 15.772941839547805
}
```

**2026-09-25 (5090 live / utmm / paired / IMU pose init 15):** renders/KF=9.725806451612904, complete=True, PSNR=11.333392038757419; timing/quality 별도 판정.

```json
{
  "dataset": "utmm",
  "scene": "square-1",
  "arm": "paired",
  "returncode": 0,
  "output": "/home/intern/gs_floaterLab/results/campaigns/gain_attribution/live_render_capacity/comparison15_imu_v2/utmm/paired",
  "valid_execution": true,
  "runtime": {
    "dataset": "utmm",
    "scene": "square-1",
    "gpu": "NVIDIA GeForce RTX 5090",
    "image_size_hw": [
      328,
      648
    ],
    "input_frames": 1614,
    "tracked_frames": 1614,
    "duration_seconds": 53.80941700935364,
    "tracking_elapsed_seconds": 54.23131016595289,
    "model_load_seconds": 0.9880402199923992,
    "renders_per_kf_cap": 15,
    "frontend_iterations": [
      4,
      2
    ],
    "IMU_poseinit_after": 15,
    "training_renders": 603,
    "backward_renders": 603,
    "committed_renders": 603,
    "native_committed_renders": 591,
    "additional_committed_renders": 12,
    "kf_admissions": 62,
    "unique_mapper_kfs": 51,
    "renders_per_kf_admission": 9.725806451612904,
    "tracking_kfs_final": 69,
    "start_lag_ms": {
      "50": 48.31820778781548,
      "95": 897.8222062753047,
      "99": 1258.9267505763553,
      "100": 1391.202298225835
    },
    "end_lag_ms": {
      "50": 81.89430506899953,
      "95": 931.1807567253708,
      "99": 1292.183768195099,
      "100": 1424.4517893530428
    },
    "track_call_ms": {
      "50": 16.602297022473067,
      "95": 119.88800545223053,
      "99": 173.4459390654222,
      "100": 1109.1877430444583
    },
    "mapper_queue_max": 1,
    "peak_cuda_allocated_bytes": 4413300736,
    "worker": {
      "accepted": 57,
      "completed": 57,
      "cancelled": 0,
      "failed": 0,
      "unfinished_tasks": 0,
      "closed": true,
      "stopped_at": 975792.043849241,
      "productive_idle_calls": 12,
      "input_wait_seconds": 50.111344545381144,
      "error": null
    },
    "zero_tail_observed": true,
    "overruns": [],
    "error": null,
    "source_unchanged": true,
    "quality_evaluated": false
  },
  "evaluation": {
    "protocol": "saved_map_independent_double_evaluation_v1",
    "cooldown_seconds": 15,
    "input_sha256": {
      "ply": "6fd9ef86f5f46290aab32607fac3560c5caa53730ca2d88658301c7e18ca8b18",
      "full_trajectory": "7fbf81578c3d6ce84904723d4e3b8c87b8263fe172f0b90edebe000a2f97c353",
      "kf_trajectory": "98b5308566c6b1b0af02de6f97bedc35bba216121ff2042654311880ed1616bf",
      "mapped_uids": "c50d3f77afb2f088efd094095ace9690bafc3d7ac30ddf09697c3905813e88a0",
      "fixed_manifest": "6a54fdd3ccf272b762c4c4ebca13803f09e28efe4f43cbddf940cbb80dba8e26"
    },
    "checks": {
      "unchanged_inputs": true,
      "same_views": true,
      "same_gaussian_count": true,
      "same_fixed_view_count": true,
      "psnr_agrees": true,
      "ssim_agrees": true,
      "lpips_agrees": true
    },
    "max_abs_per_view_difference": {
      "psnr": 0.0,
      "ssim": 0.0,
      "lpips": 0.0
    },
    "fixed_psnr_first": 11.333392038757419,
    "fixed_psnr_second": 11.333392038757419,
    "pass": true
  },
  "psnr": 11.333392038757419
}
```

**2026-09-25 최종 5090 동시 tracking 비교:** 공식 벤치마크 IMU pose prediction20/20/15 및 frontend4/2 복원, 15 training renders/KF 상한. 바닐라→우리 실제 학습량 Aria15.00→14.79/RPNG15.00→12.43/UTMM14.81→9.73, PSNR차 +0.22/−1.48/−4.44dB. 우리 extra KF/dense267/266,0/0,6/6. 6run 실행 audit·저장map 평가2회 일치 PASS이나 실시간/품질개선 주장은 불성립. RPNG mapping-off도111.477s>92.245s 입력(p95lag21.848s). 기존100000 설정 결과는 진단용 보존; 자세한 최종표는 SUMMARY.md.

## Tracking만 실행한 대조

같은 integration frontend4/2·IMU pose prediction20으로 RPNG mapping을 끈 결과, 학습 렌더0회에서도 입력92.245초를 처리하는 데 **111.477초**가 걸렸다. 입력 시작 지연p95는21.848초였다. Mapping 포함 우리 실행115.056초와 비교하면, 이 설정에서1× 입력을 따라가지 못하는 문제는 mapping을 제거해도 남는다. 단일 실행의 시간 차이를 정확한 mapping 비용으로 해석하지 않는다.

이 대조는 우리 integration tracker를 사용했다. 공식 VIGS source만의 tracker-only 결과는 아니다. 결과: `results/campaigns/gain_attribution/live_render_capacity/tracking_controls/rpng_imu20/`.


```json
{
  "control": {
    "dataset": "rpng",
    "scene": "table_06",
    "gpu": "NVIDIA GeForce RTX 5090",
    "image_size_hw": [
      344,
      616
    ],
    "input_frames": 2767,
    "tracked_frames": 2767,
    "duration_seconds": 92.24467062950134,
    "tracking_elapsed_seconds": 111.47741140401922,
    "model_load_seconds": 0.9764816609676927,
    "renders_per_kf_cap": 0,
    "frontend_iterations": [
      4,
      2
    ],
    "IMU_poseinit_after": 20,
    "training_renders": 0,
    "backward_renders": 0,
    "committed_renders": 0,
    "native_committed_renders": 0,
    "additional_committed_renders": 0,
    "kf_admissions": 0,
    "unique_mapper_kfs": 0,
    "renders_per_kf_admission": null,
    "tracking_kfs_final": 211,
    "start_lag_ms": {
      "50": 15621.982467127964,
      "95": 21848.16193124279,
      "99": 22197.513717282567,
      "100": 22414.957850705832
    },
    "end_lag_ms": {
      "50": 15655.966247315519,
      "95": 21881.504934863184,
      "99": 22230.858656391505,
      "100": 22448.29764973838
    },
    "track_call_ms": {
      "50": 11.128294980153441,
      "95": 150.54237145232034,
      "99": 505.92566715321186,
      "100": 2336.5740890149027
    },
    "mapper_queue_max": 0,
    "peak_cuda_allocated_bytes": 5663801856,
    "worker": {
      "accepted": 0,
      "completed": 0,
      "cancelled": 0,
      "failed": 0,
      "unfinished_tasks": 0,
      "closed": true,
      "stopped_at": 975949.517564393,
      "productive_idle_calls": 0,
      "input_wait_seconds": 91.94403816002887,
      "error": null
    },
    "zero_tail_observed": true,
    "overruns": [],
    "error": null,
    "source_unchanged": true,
    "quality_evaluated": false,
    "protocol": "tracking_only_capacity_control"
  },
  "audit": {
    "complete": true,
    "zero_training": true,
    "no_renderer_calls": true,
    "causal_arrivals": true,
    "no_error": true,
    "source_unchanged": true
  }
}
```
