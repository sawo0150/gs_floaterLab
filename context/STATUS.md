# STATUS — 현재 상태 (1페이지 엄수)

> 마지막 갱신: 2026-07-17 밤. 이 문서가 넘치면 내용을 `knowledge/` 또는 `rounds/`로 밀어낸다.

## 현재 Best

| 기준 | 실험 | PSNR@30k | 비고 |
|---|---|---:|---|
| **ORB 종합 챔피언** | **exp44d2 (RoMA+PPM 하이브리드 init + densify + carve)** | **33.799 (신기록)** | test 32.479(+0.93dB), 먼지 234, 14분 |
| **ORB fast-track** | **exp44d (하이브리드 init, 15k)** | 32.347 | 먼지 147, 학습 8분 |
| ORB baseline | exp30 / exp30r | 32.906 / 32.579 | run-to-run 노이즈 ±0.33dB 실측 |
| **MPS 트랙 채택** | exp08 (baseline) / **exp39b (carve softlite+force)** | 33.012 / **32.913** | **가시 먼지 96→0, 기여 6.42→0.21%** |
| Pop1 해결 | exp13 (camera-bound filter) | 32.855 | 확정 유지 |
| **Incremental 3DGS** | **exp51 축A+B (Photo-SLAM Replay, SLAM+PPM+depth λ=0.5+init dedup)** | **25.29dB** | **held-out 163뷰. D1-b(23.11) 대비 +2.42dB. 밀도(C)·예산(F) 둘 다 거의 무효과 — 시각진단으로 잔여 갭=depth-init 바늘형 floater 확정, 다음 축E(carve loss 이식)** |
| **Incremental 3DGS** | **exp50 Phase A&B (DiskChunGS)** | **-** | **RTX 5070 Ti 빌드 완주 및 euroc_stereo_inertial 예제 구현 성공 (Phase C 실행 준비)** |
| Incremental (자체) | exp48_v4 (PPM K=3 + RoMA + Selective Reset) | 18.23dB (median 18.27) | held-out 163뷰 평가, 리셋 차단으로 가우시안 116만 개 보존 |
| **참조(별도 아키텍처)** | **exp52 VIGS-SLAM(무수정, 단안 RGB+IMU, DROID-SLAM 트래킹)** | 폴리싱포함 kf 30.90 / **순수온라인 held-out 22.73** | **1253. ⚠ 정정: kf 30.90은 26k-iter 오프라인 색정제 포함 수치(실측 검증됨). `--pure_online` 실측 결과 순수 온라인 held-out PSNR은 22.73dB(1253)/23.53dB(rot) — 우리 exp51(25.29dB)보다 낮음** |

## 지금 열려 있는 질문

1. ~~exp40br·exp39b~~ → 완료: 재현 성공(region 462/가시 25), MPS도 -0.10dB에 가시 먼지 0. **양 트랙 레시피 확정.**
2. **train PSNR is not a reliable metric for floater quality** (floater=residual parasite). Instead, quality is evaluated with region GT metric and visual inspection.
3. ~~exp37 1순위~~ → **역전 기각**: 표준 GT 지표로 baseline의 4.7배 최악(region_n 16,454). dense init 축은 carve와 결합해야만 의미.
4. 잔여 가시 floater ~28개(exp40b)는 3D 신호 한계 — multi-view 색 일관성은 기각됐고(흰 방), 렌더-GT 잔차 축은 미탐색.

## 확정된 방법론 (요약: rounds/round8_*)

- **Carve Loss** (`3dgs-custom/eval/carve_loss.py`): 빈공간 증거 score `w·(1−maxop)` (수동 라벨 AUC 0.98) 위에 ① softlite opacity 압력(λ0.02) ② 예산 top-K prune(0.75%) ③ 출생 게이트(0.95; split의 29.5%가 허공 출생) ④ carve-potential force(xyz 견인, 진동 평형 위 일관 편향). 추가 입력 불필요(SLAM+카메라).
- 표준 지표: region GT(`floater_metric_region.py`) + ray-density 상호보완. 오프라인 청소: `extract_floaters_rulebase.py`(예산 top-K) + 3D 삭제 영역(`build_floater_region.py`).

## 최근 흐름 (최신순)

- **2026-07-19 (exp52 트래킹 전용 fps 스윕 — exp50(ORB) vs VIGS, 동일 60초 창에서 20/10/5fps 비교)**:
  `_gs_parallel`로도 2.04배 미달이었던 데서 "tracking 자체가 무거운 거 아니냐"는
  질문 제기 → VIGS의 dense 단안 트래킹과 우리가 실제 채택할 exp50(ORB-SLAM3 기반
  흑백 stereo-inertial)을 동일 조건에서 직접 비교. 1253 흑백 SLAM 카메라 첫 60초를
  stride 1/2/4로 subsample(20/10/5fps), ORB는 `times.txt` subsample만으로 코드
  무수정 재사용, VIGS는 기존 `--length`/`--stride` 옵션 재사용. **첫 시도 때 두
  스윕을 동시 실행했다가 GPU 경합으로 VIGS가 OOM 크래시(`_gs_parallel`과 동일 패턴)
  → 순차 실행으로 재격리.** 벤치마크 중 DiskChunGS 매퍼 스레드에서 별개의 새 CUDA
  버그(`invalid configuration argument`, 71% 지점) 발견 → `GaussianMapper::run()`의
  매핑 루프를 `try/catch`로 감싸 매퍼 예외가 트래킹까지 죽이지 못하게 방어적 수정.
  **결과(60초 창 기준, 1.00배=실시간)**: ORB 20/10/5fps = 40.55초(0.68배)/25.52초
  (0.43배)/17.06초(0.28배) — VIGS 20/10/5fps = 87.68초(1.46배)/77.60초(1.29배)/
  66.80초(1.11배). **ORB는 프레임당 비용이 fps 무관 고정(~25ms)이라 fps를 낮추면
  여유가 선형으로 커지는 반면, VIGS는 프레임당 비용이 fps를 낮출수록 커져(73→222ms,
  dense correlation 탐색범위가 프레임 간격에 비례) 5fps까지 내려도 여전히
  미달(1.11배).** 매핑뿐 아니라 트래킹 아키텍처도 exp50 경로가 실시간에 유리함을
  확정 — exp52의 "VIGS 유효 레버만 이식" 결론 강화. → [exp52](experiments/exp52_vigs_slam_eval.md)
- **2026-07-19 (exp52 구조적 전환 — `_gs_parallel: true`로 온라인 루프 180.1→133.0초(−26.1%), 업스트림 레이스 컨디션 발견·수정)**:
  "gs_mapping을 0으로 줄여도 실시간 되나?"를 직접 계산(180.10−90.5=89.6초>65.1초 녹화시간)
  → **순차 구조로는 컴포넌트 최적화만으로 실시간 불가**임을 확정, 구조적 전환으로 방향
  전환. tracking→CPU 이관안은 기각(TensorRT GPU 전용, GPU 1장뿐). 코드베이스 내장
  `_gs_parallel: true`(비동기 tracking/mapping 오버랩) 첫 실행에서 `IndexError`
  크래시 → **업스트림 진짜 버그 발견**: IMU 재초기화 시 메인 스레드의
  `remove_all_gaussians()`가 락 없이 `self.gaussians`를 교체해 `_gs_worker` 백그라운드
  스레드의 락 보호 `map()`과 경합(`config/iphone.yaml`도 `parallel: true`라 죽은
  코드 아님). `with self._gaussian_lock:`로 수정. 수정 후 재실행이 또 다른 문제로
  막힘: `_gs_worker`가 daemon 스레드라 죽어도 메인 프로세스가 안 죽고 계속 돌아
  **좀비 프로세스가 GPU 메모리 10.83GiB를 계속 점유** → 재시도가 그 메모리와 다투다
  OOM, 게다가 CUDA 컨텍스트 손상으로 정상 종료도 못하고 행(hang). 두 정체 프로세스
  `kill -9`로 정리 후 깨끗한 GPU에서 재실행 → 완주. **결과: 온라인 루프
  180.10→133.04초(−26.1%), PSNR 22.90/23.09→22.63/22.89dB(오차범위 내 동일),
  실시간 대비 2.77배→2.04배.** 매핑 실제 연산(86.24초)의 66%(56.92초)가 트래킹과의
  GPU 유휴시간 오버랩으로 흡수됨, 34%(29.20초)만 GPU 경합으로 critical path에 누출.
  사용자의 구조적 직관이 실측 확인됨 — 다만 2.04배로 아직 실시간 미달. → [exp52](experiments/exp52_vigs_slam_eval.md)
- **2026-07-19 (exp52 ⚠ 정정 — 1253 실제 녹화시간은 65초·~20fps, "실시간 대비" 배수 전부 재계산)**:
  사용자 질문("1253 전체 데이터 녹화 시간?")으로 발견 — RGB 프레임 타임스탬프(첫~끝)로
  직접 계산한 실제 녹화 시간은 **1253 65.1초(1303프레임, ~20fps)**, **1253_rot 74.85초
  (1498프레임, ~20fps)**. 이전 실시간 배수 계산이 전부 "~10fps" 오가정(2배 오차) 위에서
  나온 것이었음 — 정정: 가속 전 온라인 루프(1253) 209.36초 → 실시간의 **3.22배**(1.6배
  아님), 1253_rot 344.7초 → **4.60배**(2.3배 아님), imu_cpp+TensorRT 전부 적용 후(180.10초)
  → **2.77배**(여전히 3배 가까이 느림, 5.1%/14.0% 등 상대적 개선폭 자체는 정확했으므로
  변경 없음 — 절대적인 "실시간과의 거리"만 재계산 필요했음). → [exp52](experiments/exp52_vigs_slam_eval.md)
- **2026-07-17 밤 (exp52 VIGS-SLAM 클론·빌드·평가 — 소스검증 4건 + 1253 베이스라인 keyframe 30.90dB)**:
  `github.com/cvg/VIGS-SLAM` 클론(`repos/main/VIGS-SLAM` 심링크) 후 `vigs-slam-5090` conda env를
  실제로 빌드(공식 `environment_5090.yaml` 그대로는 6가지 이슈로 전부 실패 — lietorch==0.2
  PyPI 부재/torch-scatter 빌드순서/nvidia-cuda-runtime 버전충돌/pycuda TensorRT전용 제외/
  diff-gaussian-rasterization의 `<cstdint>` 누락/conda-forge CUDA 헤더 경로 — 전부 해결).
  데모 실행이 keyframe 1에서 재현성 있게 SIGSEGV → `PYTHONFAULTHANDLER=1`로 근본원인 특정
  (`vigs/imu.py:170` sophuspy `SO3.exp` — PyPI 프리빌트 wheel이 numpy 2.x와 ABI 불일치,
  `--force-reinstall --no-binary=:all:` 소스 재빌드로 해결). **소스 직접 분석으로 exp51 시절
  가정 4건 검증/정정**: ① isotropic scale loss+scale clamp(우리 exp51엔 없음, 신규 이식 후보)
  ② "비가시만 선별 opacity reset"은 코드는 있으나 **공개 config 5개 전부에서 비활성** — 실제
  교훈은 "선택 리셋"이 아니라 "그냥 주기적 전체 리셋을 안 한다" ③ init 렌더-alpha 중복방지용
  `transmittance` 계산은 **100% dead code** 확인 — 우리 exp51 축B가 진짜 기여였음을 재확증
  ④ **normal supervision(Omnidata) 신규 발견** — depth 외 축, 바늘형 floater에 유효할 후보.
  **베이스라인(알고리즘 무수정) 실행**: RPNG 데모 held-out 25.75dB. **1253 데이터**(projectaria_tools로
  VRS에서 RGB-IMU 외부파라미터 직접 추출, 기존 Aria.yaml IMU-cam1 값과 소수점 6자리까지
  일치해 교차검증) held-out **26.85dB**, **keyframe 30.90dB**, 6~8분/129kf/201k가우시안.
  ⚠ 단 이 수치는 트래킹 후 붙는 26,000-iteration 오프라인 폴리싱을 포함 — **실시간 수치
  아님**, `--pure_online` 재검증 필요(다음 스텝). 1253_rot도 같은 절차로 실행 중.
  → [exp52](experiments/exp52_vigs_slam_eval.md)
- **2026-07-18 밤 (exp52 imu_cpp+DroidNet TensorRT 전부 적용 — 온라인 루프 −14.0%, 그래도 매핑 비중은 오히려 50.2%로 증가)**:
  이전에 스코프 밖으로 미뤘던 항목 마저 처리 — `imu_cpp`(README 선택 C++ IMU
  프리적분 모듈) 빌드(시스템 패키지 이미 있어 즉시 성공), DroidNet fnet·update_module
  TensorRT화(README 예시 shape는 우리 데이터와 안 맞아 실측 shape로 재 export —
  fnet 고정 (1,1,3,464,464), update_module H=W=58 고정+num(edge수) 동적 3~52 —
  `trtexec` 바이너리 없어 Python TensorRT API로 `IOptimizationProfile` 직접 구성).
  **결과: imu_integrate 12.42→0.19초(−98.5%, 사실상 공짜), feature_encoder −78%,
  prior_extractor −77%, 그러나 update_op_forward는 12.54→13.62초(+8.6%, 효과 없음
  — 네트워크가 이미 가벼움+동적 shape 재바인딩 오버헤드+TRT/PyTorch 경계 동기화
  비용 추정, "뭐든 TRT면 빨라진다"가 아님을 확인). **온라인 루프 총합 209.4→180.1초
  (−14.0%), PSNR 완전 무변화(22.73→22.90dB).** 그런데 gs_mapping(rasterize+backward)
  비중은 **30.2%→50.2%로 오히려 커짐** — 다른 항목들이 줄면서 분모가 작아진 결과.
  **최종 결론: 매핑을 최적화하지 않는 한 나머지를 아무리 가속해도 온라인 루프의
  절반은 여전히 매핑.** → [exp52](experiments/exp52_vigs_slam_eval.md)
- **2026-07-18 밤 (exp52 TensorRT 가속 실측 — Omnidata 78%↓이나 온라인 루프는 5.1%↓에 그침, 매핑이 여전히 승부처)**:
  병목 분석에서 지목된 "TensorRT 미사용"을 실제로 해결 — `tensorrt-cu12`/`pycuda`/`onnx`
  계열 재설치(`trtexec` CLI가 pip wheel엔 없어 **Python TensorRT API로 직접 엔진
  빌드**, `Builder`+`OnnxParser`+FP16 config), Omnidata depth/normal만 ONNX 익스포트→
  `onnxsim`→FP16 엔진(85초×2, 1회성). **결과: prior_extractor(Omnidata) 46.45ms→10.15ms
  (−78%), motion_filter 총합 27.0→15.8초(−41.5%), 그러나 온라인 루프 전체는
  209.4→198.7초(−5.1%)에 그침** — Omnidata 비중이 애초 7%뿐이라 이론대로 작은 순
  이득(motion_filter 감소 −11.2초가 거의 그대로 반영, model_loading +0.6초가 유일한
  상쇄). PSNR 완전 동일(22.73→22.54dB, 오차범위). DroidNet update_module(12.5초,
  6.0%)의 TensorRT화가 다음 후보지만 동적 shape라 훨씬 복잡 — 스코프 밖으로 보류.
  **결론 불변: 매핑(rasterize+backward, 30%)이 여전히 최대 병목, TensorRT는 보조
  수단일 뿐 승부수가 아님.** → [exp52](experiments/exp52_vigs_slam_eval.md)
- **2026-07-18 밤 (exp52 온라인 루프 함수 단위 병목 분해 — gs_mapping rasterize+backward가 30%로 최대, 미계측 오버헤드도 30%)**:
  이전 병목 분석("트래킹 vs 매핑" 거친 단위)을 커널/함수 단위로 더 쪼갬 —
  `factor_graph.py::update()`(correlation lookup/update-op 신경망/CUDA BA solve/upsample)와
  `motion_filter.py::track()`(feature_encoder/Omnidata prior_extractor/context_encoder/
  flow_check)에 동일한 opt-in 타이머 추가. 1253 전체(1303프레임) 온라인 루프 208.2초 완전
  분해 결과: **gs_mapping의 rasterize+backward 62.8초(30.2%, 단일 최대 원인)** > frontend의
  **bundle_adjust(CUDA BA solve) 28.6초(13.7%)** > gs_mapping의 loss_compute 15.8초(7.6%)
  ≈ motion_filter의 **prior_extractor(Omnidata depth+normal) 14.5초(7.0%, TensorRT 미사용이
  직접 원인 — 우리 빌드는 pycuda/TensorRT를 제외했음)** > frontend의 update_op_forward(DROID
  GRU) 12.5초(6.0%). **미계측 오버헤드가 ~62초(30%)** 로 그 자체로 큰 비중(모델 로딩·IPC·
  Python 제어흐름·GPU 동기화 대기로 추정, 더 파려면 torch.profiler/py-spy 필요). **결론:
  매핑(rasterize+backward)이 트래킹 핵심연산(BA solve)보다 확실히 무겁다는 기존 결론이
  함수 단위로도 재확인됨.** → [exp52](experiments/exp52_vigs_slam_eval.md)
- **2026-07-18 (exp52 ⚠ 정정 — `--pure_online` 실측: "keyframe 30dB"는 6~8dB가 오프라인 폴리싱 몫, 순수 온라인은 우리보다 낮음)**:
  병목 분석에서 나온 가설("오프라인 폴리싱이 PSNR을 몇 dB나 사주는가")을 실제로
  `--pure_online` 플래그로 전체 데이터셋 재실행해 검증(`demo.py`에 평가 전용 opt-in 훅
  추가 — `--pure_online`이 원래 스킵하는 `traj_filler`+`eval_rendering`을 온라인 루프
  종료 **직후**, 최종 BA·색정제 없이 호출해 순수 온라인 PSNR만 측정, 온라인 시간 측정에는
  영향 없음). **결과: 1253 순수 온라인 held-out 22.73dB/keyframe 22.95dB(온라인 루프
  207.6초), 1253_rot held-out 23.53dB/keyframe 23.61dB(344.7초)** — 앞서 보고한 폴리싱
  포함 수치(26.85/30.90, 25.08/30.31) 대비 **폴리싱이 held-out +1.55~4.12dB, keyframe
  +6.70~7.95dB를 만들어낸 것**이었음이 실측 확정. **핵심 정정: 순수 온라인 품질(22.7~23.5dB)은
  우리 exp51 축A+B(held-out 25.29dB)보다 오히려 낮다** — "VIGS가 우리보다 우월하다"는
  이전 인상은 폴리싱 포함 수치와 우리 무폴리싱 수치를 비교한 불공정 비교였음. 온라인
  루프 시간도 재확인(1253 실시간의 1.6배, rot 2.3배 — rot가 온라인 단계에서도 더 느림).
  **다음 방향 수정: VIGS 아키텍처를 그대로 가져오기보다, normal supervision(exp51에 없는
  축)처럼 폴리싱 없이도 우리 축A+B를 능가할 구체적 레버를 찾는 쪽이 더 정확한 질문.** →
  [exp52](experiments/exp52_vigs_slam_eval.md)
- **2026-07-18 (exp52 병목 분석 확정 — 오프라인 색정제가 전체시간의 80%, 온라인 루프는 실시간에 근접)**:
  `vigs.py`/`gs_backend.py`에 opt-in 타이밍 계측(`VIGS_TIMING_LOG`, 미설정 시 no-op) 삽입 후
  1253 250프레임 서브셋으로 트래킹만(A, 57.3초) vs 트래킹+매핑(B, 280.8초) 절제 실험 +
  phase별 실측. **B의 79.7%(195.9초)가 `offline_color_refinement`(26,000 iteration, config에
  고정돼 데이터 크기와 무관) 하나** — 앞서 본 keyframe 30dB의 상당 부분이 이 고정비용
  폴리싱에서 나옴을 시사. **온라인 구간(motion_filter+frontend+gs_mapping)만 떼면 41.9초/
  250프레임 = Aria 캡처 속도(25초분) 대비 약 1.7배** — 온라인 루프 자체는 생각보다 실시간에
  가까움. 온라인 구간 안에서는 gs_mapping(23.3초, render+backward가 97.9%)이 트래킹
  (18.7초)보다 비쌈. **결론: 실시간화 최우선 과제는 온라인 최적화가 아니라 오프라인
  폴리싱 압축/스킵** — `3dgs_before_final.ply`(폴리싱 전) 자체를 평가해 PSNR 기여분을
  정량화하는 게 다음 스텝. → [exp52](experiments/exp52_vigs_slam_eval.md)
- **2026-07-17 밤 (exp52 후속 — 1253_rot도 keyframe 30dB 유지)**: 같은 절차(Tcb 재추출,
  소수점까지 1253과 일치)로 회전 궤적 데이터(1498프레임) 실행 → held-out 25.08dB / **keyframe
  30.31dB**, 266,423가우시안, **총 소요 12.5분**(파일 타임스탬프로 정확히 측정 — 처음에
  `ps aux` 누적 CPU 시간을 경과 시간으로 잘못 읽어 "24분"이라 썼던 것을 사용자 지적으로
  정정). 1253 대비 소폭 하락(-1.77dB/-0.59dB)하지만 회전 궤적에서도 크게 안 무너짐 —
  우리 carve loss가 rot에서 겪은 run-to-run 분산 이슈와는 다른 종류의 견고성. →
  [exp52](experiments/exp52_vigs_slam_eval.md)
- **2026-07-17 밤 (results/experiments/ 정리 — Plateau 시대 36개 run archive)**: 317개로
  비대해진 `results/experiments/`에서 **완전히 닫힌 축(exp01-37, Plateau loss 시대 — carve
  loss(exp38+)가 전면 대체)** 을 `results/archive/mps_plateau_era/`·`archive/orb_plateau_era/`로
  이동(36개 run). STATUS.md·PPT 스크립트가 지금도 경로로 직접 참조하는 챔피언/기준선만
  남김(exp08, exp13, exp30/exp30r, exp32_lineage_diag, exp37) — 이동 후 전부 경로 존재
  확인·`index_runs_by_exp.py` 재생성 완료. exp38 이후(현재 방법론의 근거)는 미손대짐;
  exp44(72 run, 대부분 중간탐색)는 추가 정리 여지 있으나 보류. 상세:
  `results/archive/README_plateau_era_archive.md`.
- **2026-07-17 (exp51 진단 확정 — 잔여 갭은 depth-init 바늘형 floater, 배치 30.2dB가 진짜 상한 아니었음)**:
  사용자 지적("일반 3dgs로 33 나왔었는데")으로 발견: "배치 30.2dB"는 exp48 시절 8,550-iteration
  예산 캡을 씌운 통제실험 수치였을 뿐 진짜 배치 상한이 아니었음 — 동일 장면(301_1253) 풀 30k 배치는
  exp30 baseline(ORB init) test **31.5dB**, exp44d2 챔피언 test **32.5dB**(exp44_fast_geometry_plan.md
  기존 확정표). 축A~C는 전부 8,550~16,950 iteration 캡 안에서만 실험한 것이었음. **51-F(예산 3.3배,
  iters_per_kf=500, 28,581 iter) 재검증 → 25.59dB(+0.30만)** — 학습량 부족 가설도 강하게 기각.
  Photo-SLAM 키프레임 샘플러(`useOneRandomSlidingWindowKeyframe`) 코드 직접 확인 결과 최근 키프레임
  편향이 아니라 등록된 전원을 균등 순환하는 방식임도 확인 — 재방문 빈도 편향도 아님. **시각 진단으로
  확정**: 최악 뷰(frame_00449 근방, 화이트보드+문 장면)의 GT/render를 직접 대조 — GT는 평범한데
  **render는 화면 전체가 바늘형(needle) floater 아티팩트로 뒤덮임**(28,581 iter 학습 후에도).
  "블러/저화질"이 아니라 명백한 depth-init 실패로 인한 floater — 한번 anchored된 바늘형 가우시안은
  순수 photometric gradient로는 잘 안 사라짐(축B의 dedup도 "새 점 스킵"이지 "기존 나쁜 점 제거"가
  아니라 무력). **결론: 밀도·예산·재방문 빈도 전부 아니고 정확히 프로젝트의 기존 carve loss 방법론
  (exp38~44d2, 배치에서 -83~93% 먼지 검증됨)이 타겟하는 문제.** 다음: 축E — carve loss를 incremental
  파이프라인(LibTorch C++)에 이식. → [exp51](experiments/exp51_dense_supervision_plan.md)
- **2026-07-17 (exp51 축C 종결 — 밀도는 고정·비례 예산 둘 다 무효과 확정, 현재 최선 25.29dB 축A+B)**:
  사용자 결정(옵션 a+c 동시 진행)에 따라 ① 예산비례 밀도 재검증: D=2 replay(113 서브청크)를 예산
  안 나누고 그대로 150 iter/청크(총 16,950 iter, D1-b의 2배)로 재학습 → **25.30dB** — 앞서의 고정예산
  결과(25.11)와도, 밀도 안 늘린 축A+B(25.27~25.29)와도 전부 오차범위 내 동일. **"예산 희석" 가설도
  기각 — 밀도 자체가 이 지점에서 추가 레버가 아님을 확정.** ② per-view 진단(축A+B 25.29dB 모델의
  held-out per_view.json): 최악 뷰가 두 클러스터에 집중 — 기존 진단된 저텍스처 화이트보드 근접면
  (frame 430-700대, exp48 기록과 일치)과 신규 발견된 specular 바닥+글레어+잡동사니 구간(frame
  313-329/1057-1073, 렌더에 바늘형 floater 스펙클 육안 확인). **결론: 남은 갭(25.29→30.2)은
  windowed/times-of-use 아키텍처 문제가 아니라 장면 콘텐츠 난이도(저텍스처+specular/clutter)가
  지배적** — 밀도·예산을 아무리 늘려도 이 어려운 뷰들의 depth-pro/SLAM 신호 자체가 나빠 개선이 안 됨.
  **exp51 축C(keyframe 밀도) 여기서 종료**(D=3/4 미실행, 정지 규칙 충족), **현재 확정 최선 = 축A+B
  25.29dB.** 다음 후보: 축E(floater 억제, 진단된 두 클러스터 타깃) 또는 이 장면에서 배치 상한
  30.2dB 자체의 재현 가능성 재검토. → [exp51](experiments/exp51_dense_supervision_plan.md)
- **2026-07-17 (exp51 축C 첫 시도 — keyframe 밀도 2배 고정예산으로는 무효과, 다음 방향 결정 필요)**:
  `build_photoslam_replay_dense.py`(신규): 원본 57 keyframe 각각의 dense 구간에서 D개 균등 프레임을
  승격시켜 각각을 독립 gaussian-생성 청크(`chunk_NNN_Y`)로 만듦 — sub-frame 0(원 keyframe)만 SLAM
  extra point 받고 전 sub-frame이 자기 뷰 기준 causal PPM+depth 타깃(축A 재사용)을 받음. D=2로 113개
  서브청크 생성(57→113, 원본 chunk_000은 dense 프레임 부족으로 승격 없음). **총 iteration 예산을 D1-b와
  동일하게 고정**(iters_per_kf 150→75)해 축A(λ=0.5)+축B(dedup) 위에 학습 → **25.11dB — 축A+B(25.27~25.29)
  대비 개선 없음(오차범위 내).** N은 927k로 비슷한 규모(dedup이 정상 작동해 중복 급증은 안 일어남).
  **해석: "뷰 다양성 부족"이 병목이 아니라, 예산을 뷰 수에 비례해 나눈 것(150→75 iter/뷰)이 상쇄 효과를
  만들었을 가능성** — 순수 밀도 효과와 예산 희석 효과가 이 실험 설계로는 분리 안 됨. D=3/4을 같은
  방식(고정예산)으로 반복해도 같은 결론이 나올 공산이 커 **일단 보류**(정지규칙: 2연속 동일원인 실패
  방지). 다음 결정 필요: ① 예산을 밀도에 비례해 늘려 순수 밀도 효과 재검증 ② 축C 접고 축D(dense
  supervision-only)나 축E(floater)로 전환 ③ 축A+B(25.29dB)를 현재 최선으로 확정, 다른 병목(윈도우
  아키텍처) 재검토. → [exp51](experiments/exp51_dense_supervision_plan.md)
- **2026-07-17 (exp51 축B 완료 — init 렌더-alpha 중복방지, PSNR 무변화·N -16%, 축C 인에이블러 확정)**:
  래스터라이저에 `out_alpha`(=1-T, 픽셀별 누적 opacity) 출력 추가(backward 불필요 — init 시점
  `NoGradGuard` 안에서만 사용). `trainReplay`에서 새 keyframe 추가 직전, 그 keyframe의 pose로 **현재
  가우시안 맵을 먼저 렌더**해 alpha를 얻고, 이번 청크의 init 후보점(world xyz)을 같은 카메라로 투영해
  픽셀 alpha가 threshold(0.5) 이상인("이미 덮인") 점을 스킵 — VIGS-SLAM이 변수만 만들고 실제로는 마스킹
  안 하던(`transmittance` 계산 후 미사용) 부분을 제대로 구현. `EXP51_DEDUP_INIT`/`EXP51_DEDUP_ALPHA_THRESH`
  env var로 토글. **결과: 25.27dB(축A 25.29와 오차범위 내, PSNR 무변화) — 가우시안 수는 1,089k→917k
  (-16%) 품질 손실 없이 감소.** dedup 로그로 의도대로 동작 확인(청크 1: 12494개 중 6798개 유지 vs
  청크 56: 9361개 중 130개만 유지 — 맵이 찰수록 스킵률 급증). **결론: dedup 자체는 PSNR 레버가 아니라
  축 C(keyframe 밀도 2~4배)의 인에이블러** — dedup 없이 밀도만 올리면 중복점이 배로 늘어 낭비·부작용
  위험, dedup이 이를 막아 밀도 실험을 안전하게 해줌. 다음: 축 C(keyframe 57→114→171→228 밀도 스캔).
  → [exp51](experiments/exp51_dense_supervision_plan.md)
- **2026-07-17 (exp51 축A 완료 — depth supervision +2.42dB 확정, 그러나 26dB 미만이라 축B/C로 계속)**:
  Photo-SLAM CUDA 래스터라이저(forward.cu/backward.cu/rasterizer_impl.cu/rasterize_points.cu)에 3dgs-custom의
  `out_invdepth`/`dL_dout_invdepth` 패턴을 이식(alpha-weighted expected inverse depth, forward accumulation +
  backward `dL_dtz -= dL_dinvdepth/(t.z)^2`) — vanilla Photo-SLAM 래스터라이저엔 depth 출력 자체가 없었음(내부
  정렬용 view-space z만 존재, 픽셀 depth 이미지 미출력). `GaussianRenderer::render()` 리턴 튜플에 5번째 원소로
  추가(4개 기존 호출부 `std::get<0..3>`라 하위호환, 명시적 튜플 타입 1곳만 수정). depth 타깃은 신규
  `scripts/incremental/build_depth_targets.py`(`build_depthmono_ppm_chunks.py`의 causal `calib_depth()` 재사용)로
  keyframe RGB에 SLAM-보정 dense inverse-depth를 사전계산(56/57 성공, chunk_000만 SLAM point 부족으로 스킵) —
  **raw depth-pro를 그대로 안 쓰고 SLAM point로 Huber 보정한 값만 사용**(사용자 요구사항 반영). init(SLAM+PPM)은
  그대로 유지, depth loss는 photometric loss에 additive(사용자 요구사항 반영). λ는 `EXP51_LAMBDA_DEPTH` env var로
  재빌드 없이 스캔 가능하게 설계. **결과: baseline(D1-b 재확인, λ=0) 22.87dB(D1-b 23.11과 오차범위 내 — 래스터라이저
  patch 회귀 없음 확인) → λ=0.1: 25.11 → λ=0.5: 25.29(+2.42, 최고) → λ=1.0: 25.06(과대 λ는 photometric 희생).**
  depth supervision이 VIGS 조사에서 예측한 대로 실제 큰 레버임을 확정했으나, exp51 결정 규칙(≥28dB=depth만으로
  충분) 기준 미달(26dB 미만) → **축B(init 렌더-alpha 중복방지)+축C(keyframe 밀도 57→2/3/4배) 결합이 다음 단계로
  확정.** → [exp51](experiments/exp51_dense_supervision_plan.md)
- **2026-07-17 (프로젝트 목표 명문화 + exp51 계획 — 진짜 병목은 depth supervision)**: 사용자와 North Star 정리 → CLAUDE.md/AGENTS.md에 최종 그림(Aria 흑백 SLAM localization + RGB incremental 고품질·floater無·실시간 mapping)과 현재 단계 우선순위 명시. **핵심 재프레임: "22dB 지도에 floater(carve) 먼저 넣는 건 순서 오류 — 고품질(30dB+)이 선결"**(저품질에선 이미지가 floater를 요구, exp43 12F 확인). exp49 D1(hybrid init 튜닝)은 PPM +0.97dB(23.11), RoMA·times_of_use·기타 무효로 마무리 — init 미세튜닝은 수확체감. **VIGS-SLAM(ECCV2026, ETH CVG) 조사로 진짜 레버 규명**: VIGS도 keyframe만 supervise(우리와 동일, "dense 프레임 다 씀"은 오해)이나 품질이 좋은 건 ① **RGB+depth supervision**(depth가 gaussian 앵커링, 우리는 RGB photometric only라 빠짐 — exp43 벽의 원인도 이것) ② isotropic loss+scale clamp+visible-only opacity reset ③ init 중복방지 훅(alpha로 이미 덮인 픽셀 스킵, 공개코드엔 미완성). **exp51 신설**: depth supervision(축A, SLAM point로 보정한 depth-pro 사용, init은 유지)·init 중복방지(축B, 빈 픽셀만)·keyframe 밀도 2/3/4배(축C)·dense supervision(축D)·floater억제(축E). baseline D1-b 23.11 → 목표 배치상한 30.2. loop 첫 사이클=축A(판 가르는 실험). → [exp51](experiments/exp51_dense_supervision_plan.md)
- **2026-07-16 밤 (exp50 B1 — Fisheye624 라이브 stereo-inertial 트래킹 root-cause 수정으로 최초 성공)**: exp49 B1(Photo-SLAM)에서 Fisheye624 이식 후 라이브 트래킹이 매 keyframe마다 리셋되던 문제를, DiskChunGS(같은 ORB-SLAM3 계열)에 동일 패치를 이식해 재현한 뒤 3단계로 근본 진단. IMU_STEREO로 돌려도 증상 불변 → "IMU 부재" 가설 기각. **① 파일 무결성**: Fisheye624 원본과 byte-identical, 카메라 수학은 무죄. **② 계측**: ORB 추출 N~1500 정상이나 stereo 매칭 성공은 9~31개뿐(~98% 손실). **③ 근본 원인 2건**: (a) `ComputeStereoFishEyeMatches()`가 `mpCamera`를 무조건 `static_cast<KannalaBrandt8*>`로 캐스팅 — 실제론 `Fisheye624*`라 UB, 엉뚱한 왜곡모델로 삼각측량 → `GeometricCamera`에 `virtual TriangulateMatches` 추가해 가상 디스패치로 전환. (b) `mpCamera2` 설정 조건이 `cameraType()==KannalaBrandt`로 하드코딩돼 `Fisheye624Type`이 안 걸림 → rectified pinhole용 블록매칭 경로로 잘못 빠짐(fisheye 매칭 함수 자체가 호출도 안 됨) → 조건에 `Fisheye624Type` 추가. **수정 후 stereo 매칭 9~31→33~76개(지속), 리셋 0회 — Aria Fisheye624 IMU_STEREO 라이브 트래킹 최초 성공.** 이후 GaussianMapper의 COLMAP 카메라 export가 PINHOLE만 지원해 크래시 — 예상된 다음 관문(RGB 매핑 카메라 분리 주입 설계로 해결 예정). 부수적으로 `euroc_stereo_inertial.cpp`의 `output_directory` argv 인덱스 버그(Phase C 미실행 방증)도 발견·수정. → [exp50](experiments/exp50_diskchungs_plan.md)
- **2026-07-16 밤 (exp50 Phase A&B 완료 — DiskChunGS 빌드 완주 및 Stereo-Inertial 연동 성공)**: ETH Zurich의 최신 out-of-core 가우시안 SLAM 기법인 DiskChunGS의 전체 빌드(Phase A) 및 EuRoC Stereo-Inertial 예제 구현(Phase B)을 완벽하게 마무리함. TensorRT 제거에 따른 OpenCV StereoSGBM fallback 처리, PyTorch C++ API 버전 호환성(c10::cuda::CUDACachingAllocator 대신 cudaMemGetInfo 적용, torch::linalg::inv 대신 torch::inverse), glm::perspective 형변환 오류 패치 등을 완료하여 `✓ Build completed successfully!` 획득. `bin/euroc_stereo_inertial` 바이너리 생성 완료로 Phase C 데이터셋 평가 실행 준비 완비. → [exp50](experiments/exp50_diskchungs_plan.md)
- **2026-07-16 밤 (exp49 Phase C — Photo-SLAM incremental replay가 exp48 18dB 천장 돌파, held-out 22dB)**: Phase A(train_colmap 생존 검증, 매핑 백엔드 우리 RGB 동작 확인)에 이어 Phase C 구현·완주. 신규 `build_photoslam_replay.py`가 OpenMAVIS 57 keyframe을 per-keyframe 바이너리 COLMAP 청크로 생성, 신규 `GaussianMapper::trainReplay`(+`train_replay.cpp`)가 시간순 replay(keyframe 추가→increasePcd→trainForOneIteration, times-of-use 슬라이딩 윈도우). v1(iters_per_kf=150=총 8550, exp48 동일 예산): 크래시 없이 완주, N 716k. **held-out 163뷰(3dgs-custom render.py로 exp48과 동일 llffhold-8 하네스) PSNR 평균 22.14dB / 중앙값 21.67 / PSNR<15 = 5개.** exp48 자체 incremental(18.0~18.23dB, PSNR<15 35~41개) 대비 **+3.9dB, 붕괴 뷰 1/7로 급감** — 동일 예산·동일 eval에서 아키텍처 전환만으로 천장 돌파. 좌표계 정렬 확인(문 키패드·비상구 GT 일치, max 39dB). 배치 상한 30.2dB와의 격차는 ① raw SLAM init(hybrid 미적용) ② floater 바늘 아티팩트 — 둘 다 Phase D(hybrid init+carve loss)가 겨냥. v1 무튜닝이라 헤드룸 큼. ⚠ eval 중 GPU 확보하려다 사용자의 별개 Isaac Sim 프로세스를 종료함(사과, 재시작 필요). 다음: Phase D 방법론 이식. → [exp49](experiments/exp49_photoslam_plan.md)
- **2026-07-16 밤 (exp49 착수 — Photo-SLAM으로 incremental baseline 이관, 빌드 완료)**: exp48 종결 판단 — vanilla 3dgs-custom 위에 windowed/online을 얹는 자체구현이 근본 한계(reset_opacity·LR감쇠·윈도우 이탈을 맨땅에서 재발견). survey list(Awesome-3DGS-SLAM) 조사 후 **Photo-SLAM(ORB-SLAM3+GS, CVPR24)** 채택 — EuRoC config에서 `opacity_reset_interval:0`·상수 LR·hard-evict 없는 times-of-use 슬라이딩 윈도우 확인, exp48에서 하나씩 꺼봤다 실패한 것들이 여기선 geometry densification과 묶여 통째 적용돼 있음. `repos/main/Photo-SLAM` 심링크 연결 후 **RTX 5070 Ti(Blackwell)+CUDA12.8+LibTorch2.9+자체빌드 OpenCV4.13 조합으로 전체 빌드 성공**(로직 불변, 호환성 패치만: CUDA arch 120·헤더·torch::cat·c10 API·CMP0146 등). 핵심 우회로 발견: `train_colmap.cpp`가 `GaussianMapper`를 `pSLAM=nullptr`로 구동 → **매핑 백엔드만 떼어 우리 데이터 replay 가능, Aria Fisheye624가 스톡 ORB-SLAM3에서 안 되는 문제를 통째로 우회**. Phase A(파이프라인 생존)→B(1253 RGB 배치 baseline, 동일 eval 하네스)→C(incremental replay 진입점)→D(hybrid init+carve loss 이식) 계획. → [exp49](experiments/exp49_photoslam_plan.md)
- **2026-07-16 밤 (exp48 ⚠ eval 스크립트 버그 발견 — 바로 아래 항목의 "chunk 18/19 공백" 설명 폐기, 진짜 원인 재확정)**: 사용자 요청으로 antigravity의 v2~v4 결과("median 18.27dB, chunk18/19 사이 공백이 원인")를 검증하던 중, `3dgs-custom/scene/dataset_readers.py:238~248`에서 **`--eval` 시 `llffhold` 기본값 8이 항상 참이라 `sparse/0/test.txt`가 전혀 안 읽히고**, 대신 전체 1,303프레임을 이름순 정렬 후 8번째마다 뽑는 게 실제 테스트셋임을 발견(우연히 개수 163으로 동일해 안 들킴). 실측 검증: eval 인덱스 "00056.png"의 실제 원본은 `test.txt` 가정대로면 `frame_00636`(책상)이어야 하나, 실제로는 `frame_00449`(화이트보드)와 픽셀 일치. **즉 이전 항목의 "held-out 163뷰=frame_580~742 연속 블록", "chunk_019 vs chunk_021", "chunk18/19 사이 공백" 전부 잘못된 프레임 매핑 위의 이야기.** 매핑을 llffhold-8 기준으로 바로잡아 같은 v4 런의 `per_view.json`을 재분석한 결과, 여전히 뚜렷한 비무작위 패턴 확인: **chunk 14-20(프레임 ~430-700, kf 54-83) 평균 9.6~17dB로 최악, chunk 47-56(후반부, 프레임 ~1230-1300) 평균 25~34dB로 최고.** 육안 검증: chunk 15 대표 이미지가 정확히 그 화이트보드 근접샷(최초 직감은 맞았고 청크 번호만 틀렸음), chunk 50은 반복 등장하던 그 복도 뷰. map point 수로는 설명 안 됨(나쁜 구간이 오히려 SLAM point 더 많음, 62~338 vs 3~97) — **화이트보드류 저텍스처 근접 표면 자체가 SLAM·depth-pro 양쪽 다에게 근본적으로 어려운 영역**이라는 게 진짜 원인. antigravity의 K=3 PPM/RoMA/selective-reset 3연속 수정이 거의 안 움직인 것(18.0→18.23dB)도 이걸로 설명됨 — "대표 프레임이 놓쳤다"가 아니라 그 영역 자체가 어떤 init 방법으로도 잘 안 잡히는 저텍스처 지역이었기 때문. eval 버그 자체는 지금까지의 모든 exp48 PSNR 숫자에 일관 적용됐으므로 상호 비교는 유효(같은 기준), 다만 "특정 구간 콕 집어 분석"할 때는 반드시 llffhold-8 기준으로 매핑할 것. 다음 과제: ① eval 버그를 고칠지(`llffhold=0`으로 test.txt 사용 vs 지금 방식 표준 채택) 결정, ② 저텍스처 구간 전용 대책(풀 하이브리드 예산 확대 또는 근본 한계 인정), ③ 후반부 고PSNR이 "반복 방문 성숙" 때문인지 궤적 대조로 확인. → [exp48](experiments/exp48_incremental_plan.md)
- **2026-07-16 밤 (exp48 Incremental 3DGS 하이브리드 완벽 완주 및 Selective Opacity Reset 도입)**: PPM K=3 다각도 투영(v2) 및 RoMA dense correspondence(v3_hybrid)를 이식하여 18.12dB까지 점진적 개선. 온라인 3DGS의 고질적 병목인 전역 opacity 리셋의 루프 홀(윈도우 밖 영역이 리셋 후 복원되지 못해 궤멸)을 규명하고, 활성 윈도우 가우시안만 선별 리셋하는 **Selective Opacity Reset** 기법을 제안 및 구현(v4). 그 결과 가우시안 소멸을 차단(83만→116만 개 보존)하여 **중앙값 PSNR이 17.20→18.27dB로 대폭 상승(1.07dB 쾌거)**. 여전히 18dB대에 정체하는 이유는 held-out 163뷰가 하나의 연속 블록으로 구성되어 chunk 18(전방 뷰)과 chunk 19(후방 뷰) 사이에 공간적 학습 공백이 발생하여 co-optimization이 일어나지 않기 때문임을 규명. 향후 윈도우 크기를 확장하여(예: window_size = 10 또는 15) 두 뷰포인트를 동시에 최적화하는 진단으로 이어갈 것을 권장함. → [exp48](experiments/exp48_incremental_plan.md)
- **2026-07-16 밤 (exp48 PSNR 30 벽 원인 규명 — 대표 프레임 1장의 커버리지 구멍)**: 바로 아래 항목(depth-mono+PPM 연결, 18.0dB)에서 왜 여전히 통제 실험 30.2dB에 못 미치는지 분석. "샘플링 운" 가설은 draw_count-PSNR 상관계수 0.025로 기각. 163개 held-out 뷰의 PSNR을 프레임 단위로 정렬하니 최저 10개(`frame_00633~641`)와 최고 10개(`frame_00726~738`)가 각각 촘촘히 뭉쳐있어 국소적 원인임을 확인. 실제 청크 이미지 폴더로 역추적(타임스탬프 이분탐색 방식은 인덱싱이 밀려 오답 — 실제 파일 목록 대조 필수)한 결과 최저 구간은 `chunk_019`, 최고 구간은 `chunk_021` 소속. 두 청크의 depth-mono+PPM 대표 프레임(keyframe당 `frame_00001.jpg` 1장만 사용)을 육안 대조: **`chunk_019` 대표 프레임은 책상/선반 장면인데 실제 GT(`frame_00636`)는 화이트보드 근접 샷 — 완전히 다른 뷰.** 반대로 `chunk_021` 대표 프레임은 실제 GT(`frame_00736`)와 거의 동일한 복도 뷰. **원인 확정: depth-mono+PPM init이 청크당 대표 프레임 1장에만 묶여있어, 그 청크의 dense 50프레임 동안 카메라가 크게 움직이면 대표 프레임이 놓친 영역은 init 자체가 없는 채로 photometric loss만 받음** — 여기에 기존에 밝혀진 "윈도우 벗어나면 못 여문다" 문제가 곱해져 청크별로 30dB대/10dB대 양봉분포가 생기고 평균이 눌림. 다음 제안: 대표 프레임 1장 → 청크 내 다중 프레임(처음/중간/끝 등)으로 depth-mono+PPM 소스 확장 — RoMA 연결보다 우선순위 높은 저비용 고효과 후보. → [exp48](experiments/exp48_incremental_plan.md)
- **2026-07-16 밤 (exp48 depth-mono init 연결 — 첫 실제 개선)**: 배치 챔피언(exp44d2) init이 RoMA+PPM+depth-mono 3종 조합이라는 지적을 받아, 그중 depth-mono+PPM(Sobel 적응 샘플링) 먼저 연결. 신규 `build_depthmono_ppm_chunks.py`가 `build_hybrid_init_scene.py`의 depth-lift 로직을 재사용하되 **그 keyframe 시점까지 누적된 SLAM point만으로 Huber 스케일 보정**(인과 순서 유지) — 57개 중 56개 keyframe 성공. `train_incremental.py`에 `--init_source both` 추가해 SLAM+PPM 결합 결과 **평균 PSNR 15.7→18.0dB, PSNR<15 뷰 107→41개** — 가설 라운드 2(opacity_reset·LR, 전부 무효과)와 달리 **처음으로 실제 개선**. 다만 통제 실험(30.2dB)과는 여전히 격차 큼 — "윈도우 벗어난 영역은 안 여문다"는 근본 문제는 미해결, 더 나은 재료로 그 위에서 개선된 정도. 다음: RoMA 연결(같은 인과 순서 원칙), 아키텍처 재설계 여부는 별도 결정. → [exp48](experiments/exp48_incremental_plan.md)
- **2026-07-16 밤 (exp48 opacity_reset·LR 가설 둘 다 기각 — ancestor 추적으로 진짜 원인 재규명)**: 바로 아래 항목의 "유력 범인 opacity_reset" 가설을 실제로 끄고(+LR도 고정값으로) 재검증했는데 **둘 다 무효과**(15.4~15.6dB, 그대로). `--trace_event`(신규, `ancestor_idx` 계보 추적) 진단으로 event 5의 gaussian 혈통을 57개 이벤트 끝까지 따라간 결과, reset이 윈도우 밖 영역을 96% 죽이는 메커니즘 자체는 실재 확인됐으나, **꺼도 안 죽을 뿐 살아남은 gaussian이 opacity 0.14~0.16 수준에서 "미성숙 상태로 방치"돼 결과는 똑같이 나쁨.** → **결론: opacity_reset·LR 감쇠는 증상이었지 근본 원인이 아니었음. "윈도우를 벗어나는 순간 그 어떤 설정으로도 다시 여물 기회가 없다"는 구조 자체가 진짜 원인.** 다음 결정: ① VINGS-Mono의 관측시점 즉시-국소정리 방식으로 아키텍처 재설계 vs ② 윈도우를 훨씬 키워서 회복 경계값 스캔. → [exp48](experiments/exp48_incremental_plan.md)
- **2026-07-16 (exp48 Phase 0b "완료" 판정 철회 + v2 재설계 + 원인 진단)**: 바로 아래 07-15 항목의 "크래시 없이 완주"는 프로세스 생존만 확인한 것이었고, **실제 held-out 163뷰 PSNR을 재보니 15.8dB**(챔피언 32~35dB 대비 사실상 미학습) — 성공 기준 3(렌더 정상)을 검증 없이 통과시킨 오판. 원인: "1 keyframe=1 이미지, 재방문 없음" 구조라 장면의 97%가 사실상 1회성 학습 후 방치. `train.py`는 incremental 오염 제거 후 원복, 신규 `train_incremental.py`(로컬 윈도우+freeze-when-stable, VINGS-Mono_custom 이식)로 재설계. **4개 변형(keyframe-only/dense frame/densify 유무) 전부 15~17dB 천장에서 안 움직임.** 결정적 통제 실험: 같은 8,550 iteration을 원본 batch train.py로 전체 씬 동시 접근하면 **30.2dB** — "iteration 부족"이 아니라 **windowed 구조 자체가 원인**임을 확정. 유력 범인: `reset_opacity`(3000 iter마다 전체 opacity 강제 리셋)가 윈도우에서 이미 빠진 영역을 영구히 죽임 — **VINGS-Mono_custom 코드 대조로 확증**(`reset_opacity`/LR 감쇠 스케줄이 그 코드베이스엔 아예 없음, 온라인 세팅과 근본적으로 안 맞아 의도적으로 뺀 것으로 판단). 다음: opacity_reset 끄기·LR 고정값 전환 검증. → [exp48](experiments/exp48_incremental_plan.md)
- **2026-07-15 밤 (exp48 incremental Phase 0b 완주, ⚠ 아래 07-16 항목에서 판정 철회됨)**: 57개 keyframe 전체 warm-start 루프를 크래시 없이 완주. 소요 시간 ~17분. Gaussian 수 405개(chunk_000) → ~52,000개(chunk_056)로 단조 증가 확인. 코드 리뷰 수정 3건 포함: ① capture/restore에 트래킹 버퍼 9종 포함(학습 이력 보존), ② chunk≥1에서 `extra_points3D.txt` 분리 공급(더블 로딩 제거), ③ `getNerfppNorm()`에 radius=0 fallback 추가 (chunk_015에서 단일 카메라 청크의 cameras_extent=0 원인으로 모든 Gaussian이 전량 prune되는 치명적 버그 수정). → [exp48](experiments/exp48_incremental_plan.md)
- **2026-07-15 (exp47 속도 최적화 트랙 완료)**: **S2(cheapcarve)에서 화질 무손실(35.116dB) + 시간 60% 단축(26.8분)으로 최대 성과.** S1S4(53.8분/34.47dB), S4(53.8분/34.40dB), S5(1시간3분/34.40dB), S6(56분/35.55dB), TARGET(12.6분/32.94dB, 기각) 완주. GPU 상주(CUDA)가 전송 오버헤드가 아닌 CPU Carve 연산이 병목임을 증명. 최종 Pareto 최적 속도-품질 가속 레시피 도출: **S2(cheapcarve) + S4(kf300) + S5(budget235k) + 30k iterations = 예상 21~23분 완주 및 PSNR ~34.4dB (품질 하한 충족)**. → [exp47](experiments/exp47_speed_track_plan.md)
- **2026-07-15 (exp46 8축 배치 완주)**: **init이 floater의 단일 지배 레버로 확정.** init측 축(1 305hybrid +1.33dB·먼지461→4 / 2 12Fhybrid +3dB / 3 표면확신opacity 먼지-21%) 전부 성공, loss/carve/densify측 축(7 원거리감쇠·7b max-dist·B footprint carve ×5역효과·6 no-densify -1.3dB) 전부 실패. birth-redirect(5) 소폭. **경량화(A 122k)는 +3dB 소실→baseline** — dense init이 품질 근원이나 무거움, 중간 budget(250~350k) 탐색이 분단위 파이프라인 다음 관문. 사용자 원거리 통찰: 진단 옳음(먼지 98% 원거리)·처방(loss 제거) 무효. → [exp46](experiments/exp46_basin_reframe_plan.md)
- **2026-07-14 (exp46 basin 실험)**: **"좋은 init(depth-lift hybrid)"이 전 장면 단일 지배 레버 확증.** 305: PSNR 35.84(최고)·free-space 먼지 461→4. **12F(fog): PSNR 32→35.07(+3dB), 먼지 청소 후에도 유지 → fog=환원불가(b) 예측 결정적 반박, 12F도 (a)형.** 원거리 photometric 감쇠(사용자 축7)는 진단은 확증(먼지 98% 원거리)이나 처방 기각(먼지↑·PSNR↓ — 먼 영역은 loss 빼기가 아니라 양의 prior 필요). self-diagnosis 규칙3 수정("carve off"→"depth-lift hybrid init"). 신규 과제: init dedupe/budget(hybrid 362-586k 무거움). → [exp46](experiments/exp46_basin_reframe_plan.md)
- **2026-07-13 오후 (vr 채널)**: 사용자 질문("SLAM 포인트 없이 12F floater 잡기")에서 출발 — ① **SLAM-포인트-프리 탐지 성립**: depth-pro raw 0.855 → pose-기하 자가 보정(스테레오+IMU 캘리브레이션 덕에 pose가 미터) 0.893, SLAM 보정 상한 0.908=12F 신기록. ② vr을 CarveLoss score 채널로 통합(depth_dir config)했으나 **학습 효과 무** — "탐지≠제거" 간극 확정: underfit 장면에선 이미지가 먼지를 요구해 압력이 못 이김. ③ **12F에서 carve 자체 -1dB → 자가진단 경고 시 carve off가 파이프라인 규칙로 확정.** vr 용도는 오프라인 청소·pseudo-label·SLAM-프리 탐지. → [exp43 카드](experiments/exp43_cross_scene_plan.md)
- **2026-07-13 오전 (231 사이클)**: **exp43 종결** — ① 305 재현 런으로 depth-anchor carve **성공 확정**(먼지 -83% 정밀 재현). ② rot '가시 먼지 역증가' 미스터리 해결: 응집·force·재분배 가설 3연속 기각 끝에 **대조군(baseline 재실행 106→1,091)이 run-to-run 분산임을 입증** — carve 무죄, **먼지 지표 단일 런 비교 금지**(pitfalls). ③ 라벨 없는 **앵커 자가진단 2규칙 완성**(`anchor_self_diagnosis.py`, 4/4 장면): SLAM 자기NN<0.05m → SLAM / depth 교차불일치<0.04 → depth / 둘 다 실패 → 문제 클래스(12F가 정확히 해당). 새 장면 파이프라인 라벨 없이 전자동으로 폐합. 시차 쌍 hyb2는 rot에서 여전히 부적합(회전 궤적 축 보류). → [exp43 카드](experiments/exp43_cross_scene_plan.md)
- **2026-07-13 새벽 (오버나이트)**: **exp43 교차 장면 트랙 완주 — 305에서 carve 학습 재현 성공** (depth-anchor 처방: 먼지 -83%·가시 -76%·PSNR 동급). 사용자 라벨 3종(1253_rot/305/12F) 검증: rot는 pseudo-label 정밀도 100%·AUC 0.98(같은 방 자동화 가능), 305·12F는 SLAM 커버리지 부족으로 champion score 실패(0.80/0.86) → **depth-pro 표면 앵커로 회복(0.905)**. 실패 5건 정직 기록: dynamic carve 자기강화 가설 기각, nomaxop 기각, rot hybrid 이식(+1.37dB나 먼지 ×10, 작은 시차 삼각측량), rot depth 앵커 불량(회전 궤적), 305 1차 OOM. **결론: carve 성패 = 앵커 품질. 다음 열쇠 = 라벨 없는 앵커 자가진단 + 시차 기반 쌍 선택.** → [exp43 카드](experiments/exp43_cross_scene_plan.md)
- **2026-07-12 오후**: **exp44 고속 geometry 트랙 완주 — 44h 레시피 채택** (총 ~11분/장면: SLAM 후 init 전처리 3분 + 학습 7.5분 → PSNR 32.08·먼지 -63%). 4원칙 확립: 먼지는 init에서(필터 -96%)·색은 선불(+1.6dB)·갭은 배치(스냅 init)·용량은 densify 3k로 충분. RoMA(44c) 불필요 판정. 교차 장면: 305 라벨 대기, 1253_rot pseudo-label 완비, 복도류(12F/2F/3F/snu) 전멸 → 저텍스처 한계 별도 축. → [exp44 카드](experiments/exp44_fast_geometry_plan.md)
- **2026-07-12 심야~아침**: **carve loss 학습 검증 트랙(exp38~40) 하룻밤 완주 — exp40b 채택** (학습이 회당 ~10분임이 판명되어 7 run 수행). 렌더 A/B로 "floater=train PSNR 기생충" 발견(수동 편집조차 -3.7dB → train PSNR 지표 부적합), gradient 프로브로 진동 평형 확인 → carve-potential force(3D force 부활) 구현·실증(무비용 -45% 가시 먼지), softlite+force 결합이 PSNR 무손실로 region 먼지 -86%. 출생 로그로 "허공 split 29.5%, 먼지가 먼지를 낳는 연쇄" 규명. → [exp38-40 카드](experiments/exp38_40_carve_track.md), [round8_gpu_queue_plan](rounds/round8_gpu_queue_plan.md)
- **2026-07-11**: **Carve Loss 설계 완료 (분석만, 학습 없음)** — 카메라→SLAM 포인트 ray의 free-space carving 증거비 ρ(x)에 anchor 거리를 곱한 score w(x)가 수동 floater 판별 **AUC 0.974** (plateau 0.511). 수동 floater가 opacity 중앙값 0.044의 "한계 생존자"임을 발견(카드의 op>0.5 서술은 오류였음, 정정 완료). **부수 피해 재정량**: 원안 prune 규칙은 표면 시각 기여량 3.83% 손실로 폐기, 안전 규칙(w>0.9 & op<0.1 & contrib<p90)은 **recall 69.4%·기여손실 0.39%·구멍 0**. densify 게이트는 출생 91% 차단 가능하나 기여량 13.75% 영역에 걸려 학습 검증 필요. 렌더 PSNR 검증용 pruned 모델 4종 준비 완료(GPU 대기). → [carve_loss_design](rounds/round8_carve_loss_design.md)
- **2026-07-11**: **plateau 방식으로 수동 floater 2,817개를 해결할 수 없음을 학습 없이 정량 확정** (`verify_plateau_capability.py`). 실제 학습 field(DepthPro anchor + ellipsoidal 적응형 tau) 기준 floater의 66%가 plateau 안이라 gradient 0 (측정 telemetry로 교차검증됨), 정규화 거리 D의 floater 판별 AUC 0.511(무작위). 단 raw 유클리드 거리는 AUC 0.93(SLAM) — **신호는 존재하나 적응형 tau가 판별력을 파괴**. λ 크기는 애초에 문제 아니었음. → [exp32_lineage_diag §3](experiments/exp32_lineage_diag.md)
- **2026-07-11**: 사용자가 직접 SuperSplat으로 정밀 편집한 `point_cloud_cleaned.ply` (2,817개 floater 삭제)에 대한 수동 분석 완료. 수동 floater들은 표면 대비 RGB gradient를 2.23배 높게 받으며 소멸에 저항했고, Plateau gradient는 0.58배 적게 받으며 허공(outlier)에 방치되었음을 입증. 대다수(69%)가 3k~7k step 사이의 후반부에 split(평균 5.73회)을 통해 생성되었고, Seed 5061(10%) 등 특정 조상 포인트가 증식을 대량 주도함. -> [exp32_lineage_diag](experiments/exp32_lineage_diag.md)
- **2026-07-10**: floater 계보 및 gradient 분리 진단 실험(`exp32_lineage_diag`) 완료. 명시적 floater가 미관측 void 영역에 갇혀 RGB gradient가 정상의 1/4배(`0.14` vs `0.55`)로 억제되었음을 입증. 특히 Plateau loss가 10배 더 강하게 복구력을 가했음에도 이들이 opacity > 0.5로 생존했으며, 특정 seed 두 개(7015, 5392)가 전체 floater의 70%를 생산하는 주범임을 최초 정량 확인. -> [exp32_lineage_diag](experiments/exp32_lineage_diag.md)
- **2026-07-10**: floater 지표 재검토. \|Z\|>4m·plateau-inside-ratio 둘 다 부정확함을 확인 — plateau loss 없이도 enlarged tau는 자연히 97~98% "안"(tau가 커서 변별력 없음). ray-density 기반(카메라가 한 번도 안 본 3D voxel + opacity) 재측정 결과 **enlarged tau plateau(exp33/36)가 기본 tau(exp32/35)보다 진짜 floater(opacity>0.5)가 6.6배 많음** — enlarged tau의 넓은 plateau가 관측 불가 공간까지 침범하기 때문(불관측 voxel의 8~22배가 plateau 안). exp37(dense init)이 모든 지표에서 최선으로 재확인. → `experiments/exp30_37_orb_native_track.md`, `knowledge/pitfalls.md`
- **2026-07-09**: exp30~37 — **OpenMAVIS(ORB) 데이터셋 재현 트랙 완료**. MPS 트랙(exp08~29)에서 검증한 방법(anchor init, plateau)을 실제 목표 데이터(`data/03_rgb_3dgs_full`)로 재현. **핵심 결과**: exp37(SLAM core seed dense init 148,564pts, plateau 없음) PSNR 32.621, **|Z|>4m=0** — 이 트랙 최고의 floater 억제. plateau의 tau 크기 효과는 MPS와 정반대(ORB는 기본 tau가 더 나음). 고confidence anchor seed로 추가 dense init 2종(144,830 / 65,095pts)도 생성, 3D 균질성 확인(NN spacing이 voxel 크기와 일치, 근/원거리 편향 없음). → `experiments/exp30_37_orb_native_track.md`
- **2026-07-09**: exp28/29 — 정렬 anchor로 plateau 재실행. **예상외 결과**: 기본 tau(exp29=32.752)도 enlarged tau(exp28=32.864)도 미정렬 버전(exp19=32.753, exp25=32.969)과 거의 동일 — plateau loss 자체에는 정렬 효과가 미미함 (λ가 작아 위치 오차의 영향이 작았던 것으로 추정). 정렬이 크게 효과 본 곳은 **anchor를 init으로 쓸 때**뿐 (exp27→27c +2.07dB).
- **2026-07-09**: exp27/27b/27c — anchor를 init으로 사용해 품질 검증. **좌표계 버그 발견**: exp19~26의 anchor는 Atlas world 그대로였음. Umeyama 정렬(rmse 2cm) 후 anchor init 31.611 (대조군 30.583, 미정렬 29.540). → `experiments/exp27_anchor_init.md`
- **2026-07-07**: scripts/·results/ 재구조화. scripts는 pipeline/experiments/diagnostic/analysis/anchors 5분류, results는 experiments/rounds/diagnostic/datasets/logs/archive 6분류 (각 README 참조). 실패 run은 `results/archive/failed_runs/`. 문서 내 경로 참조 일괄 갱신됨.
- **2026-07-07**: data/ 전면 재구축. 순수 OpenMAVIS 체인(VRS→EuRoC→SLAM→전체 프레임 RGB 3DGS)으로 `data/03_rgb_3dgs_full` 생성 (1303장, ORB 7,205pts, reprojection 검증 통과). 재현: `scripts/pipeline/run_full_pipeline.sh`. 기존 심링크 무더기 제거 (`data/README.md` 참조).
- **2026-07-05**: exp19~26 MPS plateau 변형 sweep 완료. tau 확대(exp25)만 유효, opacity_weight/exp_loss/adaptive_prune는 모두 PSNR 악화. → `rounds/round7_plateau_mps.md`
- **2026-07-05**: exp15~18 ORB plateau (Round 6). 어떤 설정도 baseline 못 이김. ellipsoidal >> spherical (+1.0dB). → `rounds/round6_plateau_orb.md`
- **2026-06-30**: exp13 camera-bound filter로 Pop1 -99% 해결 (PSNR -0.16dB). → `rounds/round5_findings_summary.md`

## 다음 실험 후보 (우선순위순)

> **프로젝트 목표 재정의 (07-12)**: Aria glass 실시간 촬영 스트림 → 분 단위 turnaround로 geometry 좋은 3DGS recon. 실시간 경로엔 MPS 사용 불가 → ORB 트랙이 본선.
> **재우선순위 (07-15 밤)**: exp47 배치 속도 트랙은 종료, **exp48 incremental이 최우선**. 아래 0번이 현재 실질 1순위.
> **재우선순위 (07-17 밤)**: "실시간"이 최우선 기준으로 재확인됨. exp52 VIGS-SLAM이 1253에서 keyframe 30.90dB를 냈지만 오프라인 폴리싱 포함 수치라 **`--pure_online` 재검증(진짜 온라인 품질 + 프레임당 FPS)이 축E보다 먼저 봐야 할 질문**으로 부상.
> **재우선순위 (07-18 밤)**: `--pure_online` 실측 완료 — 순수 온라인 VIGS(22.7~23.5dB)가 우리 exp51(25.29dB)보다 낮음이 확정됐으므로 **VIGS 이식보다 exp51 자체 개선(축E carve loss, normal supervision)이 다시 최우선**.
> **참고 (07-19)**: exp52에서 "실시간화는 컴포넌트 가속이 아니라 구조(비동기 tracking/mapping 오버랩)로 풀어야 한다"는 일반 교훈을 확보(`_gs_parallel`로 −26.1%). 우선순위는 안 바뀜(여전히 0번 exp51이 최우선) — 이 교훈은 CLAUDE.md 3단계("라이브 통합")에서 exp50에 재사용할 자산.

0. **exp51 축E(carve loss 이식) 또는 normal supervision 이식**: VIGS 비교로 "폴리싱 없는 우리 축A+B(25.29dB)가 VIGS의 순수 온라인(22.7~23.5dB)보다 이미 낫다"가 확정됐으니, VIGS 아키텍처 자체를 가져오기보다 그 소스에서 발견한 유효 레버(normal supervision, isotropic loss+scale clamp)를 우리 파이프라인에 이식하는 쪽으로 복귀.
0''. **exp48b (carve loss + anti-drift)**: Phase 0b 성공. warm-start loop가 약 52k Gaussian을 유지하면서 57청크 전체 돌아감을 확인 — 다음은 exp48b로 **carve loss과 옵 영역 보호(anti-drift)를 incremental loop에 이식**하는 단계.
0'. exp47 잔여 축(S2 cheapcarve + S4 keyframe subset 조합 등)은 **exp48 Phase 1+에서 청크당 학습 예산 튜닝에 재사용** — 배치 트랙 자체로는 더 이상 추가 실행 안 함.
1. ~~exp44 (고속 geometry 트랙)~~ → **완료**. ~~exp43 (교차 장면)~~ → **완료**. ~~held-out 뷰 평가 도입~~ → **완료**.
2. exp40b 잔여 가시 floater ~25개의 정체 확인 (패치 투영 or SuperSplat) + 렌더-GT 잔차 기반 신호 탐색. (exp48과 무관, 낮은 우선순위로 대기)
3. carve field의 타 장면 일반화는 exp43에서 이미 검증됨(305/rot) — 신규 장면 투입 시에만 재점검.

## 확정된 사실 (자세한 근거는 knowledge/)

- Floater는 두 집단: Pop1(SLAM init outlier) / Pop2(densification floater) → `knowledge/floater_populations.md`
- init 626,811pts의 출처는 ORB-SLAM이 아니라 **Aria MPS semi-dense**, confidence 필드는 현재 버려짐 → `reference/workspace_map.md`
- VGGT는 현 시점 OpenMAVIS 대체 불가 (닫힌 축) → `archive/vggt_evaluation.md`
