# exp62 — OKVIS2‖3dgs-custom 진짜 라이브(tracking‖mapping 병렬) 파이프라인, Codex 자율 마일스톤 실행

- 상태: **M1~M5 전부 통과 (2026-08-10 야간, 00:14~01:28, 약 74분).** exp61에서 확인한
  "OKVIS2는 라이브 콜백 인프라가 이미 있지만 incremental 브릿지·매퍼 폴링 루프는 전혀
  없음" 격차를 실제로 메웠다 — **트래킹과 매핑이 진짜 동시에(타임스탬프로 확인) 도는
  파이프라인이 1253/305/12F 세 장면 모두에서 real-time budget(1.5×) 안에 zero-tail로
  완주.** Codex CLI(`codex exec --dangerously-bypass-approvals-and-sandbox`)에게 마일스톤
  단위로 위임, 각 마일스톤은 exp61 오프라인 reference와 객관적으로 비교하는 자체 검증
  리포트(`verify/M{n}_report.json`)를 산출해야 다음 단계로 진행하는 방식으로 무인 실행.
  ⚠ **품질(PSNR)은 아직 게이트에 없음** — M4/M5는 타이밍(예산 준수·tail 0)만 검증했고,
  예산 제약 하에서 Gaussian 수가 예산 없는 M3 대비 크게 줄었다(1253: 63만→5,382개) —
  다음 단계는 held-out PSNR 평가 추가.
- 선행: [exp61](exp61_okvis2_3dgs_custom_benchmark_repro.md) §6(OKVIS2 vs VIGS 비교), §7(병렬
  실행에 뭐가 없는지 코드 레벨 감사).

## 왜 OKVIS2 기반인가 (exp61 §6 요약)

VIGS-SLAM의 핵심 문제는 트래킹(DROID, GPU)과 매핑(3DGS, GPU)이 **같은 GPU를 나눠 써야** 해서
narrow window로 속도를 벌면 정확도가 3~5배 희생되는 제로섬 구조라는 것(exp59/61 §6). OKVIS2는
CPU 트래킹이라 이 경쟁이 구조적으로 없고, 스테레오라 단안 IMU 스케일 드리프트(305 실패
원인) 문제도 없다. 대신 "진짜 라이브로 트래킹↔매핑이 동시에 도는 코드"가 전혀 없다
(exp61 §7 — `PIPELINE_comparison.md`의 "overlap" 수치는 `max(tracking, mapping)` 산수였고,
팀원 스스로 `rtf_accounting.py`에서 "그 파이프라인은 만들거나 돌린 적 없다"고 정정함).

## 설계 원칙 (강건성 우선, 단일 지표 최적화 금지)

1. **C++↔Python IPC는 파일 큐로.** 소켓/공유메모리 대신 원자적 파일 쓰기(tmp+rename) +
   폴링. 한쪽이 죽어도 다른 쪽은 안 죽고, 재시작하면 자동으로 따라잡는다.
2. **예산 스케줄러는 단순한 wall-clock 체크.** 정교한 예측 모델 대신 "마감시각까지 돌다가
   끊는다."
3. **절대 프레임 번호 하드코딩 금지.** 항상 상대 시간/비율로 — exp59에서 이미 이 실수로
   305/12F 재현이 실패했다.
4. **기존에 검증된 로직 재사용, 트리거만 교체.** `build_okvis_chunks.py`의 causal anchoring,
   `ppm_from_omnidata.py`/`refilter_init.py`의 알고리즘은 이미 exp61에서 우리 GPU로 검증
   완료 — 다시 짜지 말고 배치 루프를 이벤트-단위 트리거로만 바꾼다.
5. **매 마일스톤마다 최소 2개 장면(1253+305)으로 검증.** 하나만 보고 통과시키지 않는다.

## 마일스톤

| # | 목표 | 완료 기준(자동 검증) |
|---|---|---|
| M1 | Aria VRS를 실시간 페이싱으로 재생하며 OKVIS2 콜백(`setImagesCallback`/`setImuCallback`/`setOptimisedGraphCallback`)에 흘려넣는 소스 클래스 | 두 장면 다 오프라인 배치 결과(`okvis_data/{1253,305}_online/mav0/okvis2-slam_trajectory.csv`)와 ATE-Sim3 오차 5% 이내 |
| M2 | 콜백 훅에서 keyframe event를 파일 큐(`live_events/event_NNNN.json`, atomic write)로 쓰기 | 큐 내용이 기존 완성 chunk tree(`data/chunks_okvis_{1253,305}/manifest.json`)의 pose/landmark와 일치 |
| M3 | Python 쪽 폴링 루프로 큐 소비 + 기존 `train_incremental.py` 학습 로직 연결(예산 없이) | 최종 PLY의 N/PSNR이 exp61 배치 결과(1253: N=915,084 / 305: N=813,645, `share/exp61_.../` PLY)와 근사 일치 |
| M4 | wall-clock 예산 스케줄러 추가 | 1253+305 둘 다 실제 예산(각 장면 스트림 길이 × 1.5) 안에서 완주, tail update 0 |
| M5 | 12F로 확장, 필요시 이벤트 batching(exp61 §7r 참고) 적용 | 세 장면 모두 M4 기준 통과 |

## 실행 환경

- 작업 디렉토리: `/home/wosas/Desktop/26-1_RPM/gsProjects/okvis2_bench_5070ti/live_bridge/`
  (신규 git repo, 새 코드 전용 — `okvis2`/`mapper_3dgs`는 exp61에서 빌드·검증된 그대로 두고
  건드리지 않음, `VIGS-SLAM`/`3dgs-custom` dirty worktree도 미접촉)
- 참조 자료: `live_bridge/reference/`에 팀원 벤치마크의 검증된 배치 스크립트 사본
  (`build_okvis_chunks.py`, `ppm_from_omnidata.py`, `refilter_init.py`, `run_okvis_pipeline.py`,
  `HANDOFF.md`, `PIPELINE_comparison.md`, `STAGE_okvis2_tracking.md`) — 세션 스크래치패드가
  아니라 영구 경로라 밤새 사라지지 않음.
- 실행기: `codex exec`(OpenAI Codex CLI, `codex-cli 0.146.0`, ChatGPT 인증 이미 설정됨).
  **이 머신에서 codex 자체 bwrap 샌드박스가 중첩 샌드박스와 충돌해 파일쓰기가 실패**하는 걸
  확인해서(`Failed RTM_NEWADDR: Operation not permitted`),
  `--dangerously-bypass-approvals-and-sandbox`로 우회 — 사용자 확인 후 승인받음(2026-08-10).
  개인 데스크톱이고 작업 디렉토리를 `live_bridge/`로 프롬프트에서 강하게 제한하며, 마일스톤마다
  git commit으로 되돌림 가능한 체크포인트를 남긴다.
- 오케스트레이터: `scripts/incremental/codex_milestone_loop.sh`(gs_floaterLab, 이 리포).
  마일스톤 순서대로 `codex exec` 호출 → 완료 후 마일스톤이 산출한 `verify/M{n}_report.json`의
  `status` 필드 확인 → `pass`면 git commit 후 다음 마일스톤, `fail`이면 **자동 재시도 없이
  즉시 중단**하고 로그에 실패 지점을 명확히 남김(강건성 원칙 4번 위반 여지를 만들지 않기
  위해 — 실패를 덮고 넘어가지 않는다).
- 로그: `live_bridge/logs/orchestrator.log`(전체), `live_bridge/logs/M{n}.jsonl`(마일스톤별
  codex 이벤트 스트림), `live_bridge/verify/M{n}_report.json`(마일스톤별 자체검증 리포트).

## 사용자 직접 재검증 (2026-08-10, Codex 리포트 신뢰하지 않고 독립 확인)

Codex의 자체 검증 리포트를 그대로 믿지 않고 raw 로그/PLY를 직접 파싱해서 재확인했다.

**확인된 것(핵심 주장은 사실)**: 1253을 새로 재실행(`RUN_TAG=VERIFY1`)해서 `timeline.tsv`를
직접 계산 — 트래커/매퍼가 **0.0003초 차이로 동시 시작**(진짜 동시 실행, `max()` 산수가
아님), 총 wall 67.37s(예산 98.25s 이내), `training_audit.jsonl`을 직접 파싱해
`last_chunk_processed` 이후 `optimizer_step` **0건**(tail 0) 확인.

**Codex가 놓친 진짜 문제 — Gaussian 이상치**: M5 세 장면 PLY를 직접 열어 좌표 분포를 보니,
포인트의 5.3~7.4%가 원점에서 수십만~수백만 단위 떨어진 극단 이상치다(1253: 5.3%/최대
360만, 305: 7.4%/최대 193만, 12F: 7.3%/최대 293만 — 세 장면 모두 재현, 일회성 아님).
M1~M5 어떤 마일스톤도 포인트클라우드 자체의 기하학적 정합성을 검증 기준에 넣지
않아서 못 잡았다. real-time 제약 하 일부 keyframe이 불충분한 관측으로 causal anchoring이
degenerate하게 튀는 것으로 추정(미확정, 다음 진단 대상).

**Held-out PSNR 실측** (`verify/eval_live_psnr.py` 신규 작성, `run_okvis_pipeline.py`의
`build_okvis_colmap`/`score()`를 그대로 재사용해 exp61과 동일한 held-out 프로토콜
idx%5==0∪{N-1}, unmasked, VGG LPIPS로 각 라이브 run 자신의 causal trajectory 기준
채점):

| 장면 | 라이브 real-time(지금) | exp61 배치(예산 없음) | VIGS strict streaming(증명된 실시간) |
|---|---:|---:|---:|
| 1253 | **15.52dB** (SSIM 0.705, N=5,355, opacity>0.5 0.41%) | 24.83dB (N=915,084) | **27.86dB** |
| 305 | **15.78dB** (SSIM 0.791, N=7,742, opacity>0.5 1.14%) | 27.56dB (N=813,645) | 18.74dB |
| 12F | **15.44dB** (SSIM 0.796, N=43,492, opacity>0.5 0.00%) | 25.56dB (N=135,296) | 25.90dB |

**결론**: M1~M5가 검증한 "트래킹‖매핑이 진짜 실시간으로 동시에, zero-tail로 돈다"는
아키텍처 주장은 독립 재확인 결과 사실이다. 하지만 **현재 예산 스케줄러가 매퍼를 너무
심하게 굶겨서(opacity>0.5 비율이 0~1.1%) 지도 품질이 VIGS strict streaming(증명된
실시간) 대비 한참 못 미친다.** "구조는 됐고, 품질 튜닝은 완전히 남은 과제"라는 SUMMARY.md의
자체 진단이 정확했다.

## 사용자 직접 버그 수정 3건 (2026-08-10, 재검증 이후)

독립 재검증에서 나온 "PSNR이 너무 낮다"는 문제를 직접 진단·수정했다. 세 가지 원인이
겹쳐 있었고, 전부 `live_train.py`(M3~M4에서 Codex가 작성한 신규 파일)에 있었다.

**버그 1 — `deadline_margin`이 전체 1.5배 예산을 스케일하지 않음.** 원래 수식은
`deadline = 시작 + (이벤트_센서시각 + 평균간격×margin)`이라 margin을 아무리 키워도
"평균 keyframe 간격 하나 분량"만 늘어났다(1253 기준 1.42초). 전체 스트림
길이(65.5초) 대비 1.5배 예산(98.25초)과 연결이 안 돼 있었다. **수정**: 이벤트의
마감시각이 "지금까지 지난 센서 시각 × budget_multiplier"에 비례하도록
`EventDeadlineScheduler`를 재작성(`--deadline-margin` → `--budget-multiplier`,
기본값 1.5로 변경, 옛 플래그는 이제 명시적으로 에러). 실측: wall 67.4s(예산의 68%만
사용)→98.1s(99.9%).

**버그 2 — `producer_done`이 남은 큐 전체를 즉시 잘라버림.** `LiveBudgetHooks.stop_reason()`이
"트래커가 끝났는가"를 "지금 이 이벤트를 더 학습해도 되는가"보다 먼저 체크해서,
OKVIS2가 끝나자마자 아직 안 처리된 backlog 이벤트들이 각자의 마감시각과 무관하게
평균 2.16 iteration에서 잘렸다(트래킹 중 처리된 이벤트는 평균 23.9였음). **수정**:
`producer_done` 체크를 제거하고 deadline만으로 판단하도록 변경 — "더 이상 새
이벤트가 안 온다"는 큐 반복자(`LiveChunkSource.__iter__`)만 알면 되는 정보였지,
학습 루프가 알 필요는 없었다.

**버그 3(가장 큰 레버) — 라이브 파이프라인이 1024² 원본 해상도로 학습.** exp61의
89초/8,673-iteration 배치 기준은 `HANDOFF.md`가 "캠페인 최대 단일 개선"이라 기록한
`g1ify`(256² 사전 리사이즈, 16배 적은 픽셀)를 썼는데, 라이브 파이프라인은 이 최적화가
아예 없이 원본 1024²로 학습하고 있었다 — iteration당 실측 65~90ms로 배치 기준(~10ms)
대비 6~9배 느림. **수정**: `live_train.py`에 `--train-resolution 256` 추가 —
`colour_landmarks()`는 원본 1024² 이미지·intrinsics로 정확히 색을 샘플링하고,
`write_colmap()` 호출 직전에만 `build_okvis_chunks` 모듈의 `W/H/F/C` 전역을
256/256/125.0/128.0으로 잠깐 바꿔치기(bracket)한 뒤 즉시 원복 — 이미지도 저장 시
256²로 리사이즈.

**1253 누적 효과** (`RUN_TAG=VERIFY1`→`FIXED2`→`FIXED3_256`로 재현):

| | 원본(버그 3건) | 버그1+2 수정 | +버그3(256px) 수정 |
|---|---:|---:|---:|
| wall / 예산(98.25s) | 67.4s(68%) | 98.1s(99.9%) | 90.8s(92%) |
| 목표 177 iter 달성 이벤트 | 0/46 | 0/46 | **42/46** |
| 총 optimizer step | 489 | 1,057 | **7,574**(배치 기준 8,673에 근접) |
| Gaussian 수 | 5,331 | 5,909 | **662,972** |
| **PSNR (held-out)** | 15.52dB | 15.96dB | **19.55dB (+4.03dB)** |

exp61 배치 기준(24.83dB)·VIGS strict streaming(27.86dB)에는 아직 못 미치지만, 세
버그 수정만으로 실시간 예산 안에서 **+4dB** 회복했다. 남은 격차는 §"결론"에서 이미
지적한 background_polish류 유휴시간 활용 부재, 그리고 아직 미해결인 이상치
Gaussian(5~7%) — 이제 이 두 가지가 다음 우선순위다. 305/12F는 아직 이 3개 수정을
적용해 재측정하지 않음(다음 단계).

## 결과 요약 (마일스톤별)

| # | 결과 | 핵심 수치 |
|---|---|---|
| M1 | **pass** | ATE-Sim3 vs 오프라인: 1253 3.4cm / 305 4.8cm(둘 다 5% 기준 대비 여유). 실시간 페이싱 비율 ~1.00 |
| M2 | **pass** | 이벤트 큐 개수 일치율 93.9%(1253)/94.4%(305), pose 오차 1.4cm/0.07cm |
| M3 | **pass** | **트래킹↔매핑 동시 실행을 타임스탬프로 확정**(`concurrent_confirmed: true`). N 비율 0.69/0.68(예산 없음) |
| M4 | **pass** | 1253 67.3s/98.25s, 305 136.3s/201.5s 예산 통과, tail update 0. N이 5,382/7,707로 급감(예산 제약 효과) |
| M5 | **pass** | 12F 112.2s/165.0s까지 배칭 없이 통과(467 keyframe을 1:1 이벤트로 처리해도 예산 안에 들어옴 — `batching_G_used: null`), 세 장면 tail update 전부 0 |

전체 커밋: `live_bridge` repo에 마일스톤별 7개 커밋(`00cd6cc`~`90478dd`). Codex 자체 요약은
`live_bridge/SUMMARY.md` 참고 — 다음으로 추천한 작업: held-out PSNR을 라이브 러너에도
추가해서 "예산 때문에 놓친 품질"을 곡선으로 보이게 하기, 그다음 configurable batching(G=6
부터) 실측.

## 알려진 한계 (Codex 자체 보고, `SUMMARY.md`)

- 이 워크스테이션의 절대 경로(데이터/calib/conda env/자매 repo)가 하드코딩돼 있음 — 다른
  머신으로 옮기려면 경로를 설정 가능하게 바꿔야 함
- OKVIS2 keyframe 선택이 미세하게 비결정적이라, 검증은 "완전하고 연속적인 소비"를 확인하는
  식이지 정확한 이벤트 개수를 고정하지 않음
- **예산 준수는 "필요하면 iteration을 줄이거나 건너뛰는" 방식으로 달성** — 12F는 다수
  이벤트가 매퍼에 늦게 도착했음. real-time 계약(예산+tail0)은 지켰지만 held-out PSNR과
  매핑 완성도는 M4/M5 게이트 대상이 아니었음
- 이미지 디코드/COLMAP 파일 생성/씬 로딩 등 이벤트당 고정 오버헤드가 있음 — 지금 RTX
  5070 Ti에서는 12F도 여유 있게 통과했지만 더 느린 GPU/스토리지에서는 여유가 줄어들 수 있음

## 다음 단계 (미착수, 2번째 재검증 후 우선순위 재정정)

1. **305/12F에도 3개 버그 수정 적용해 재측정** — 지금까지 수치는 1253만 검증됨
2. **Gaussian 좌표 이상치(5~7%) 원인 진단·수정** — 여전히 미해결. 256px 수정 이후 PSNR
   채점 자체가 느려진 것도(이전 ~2분→~6분) 이 이상치가 원인일 가능성
3. **background_polish류 유휴시간 활용 메커니즘 도입** — 3개 버그 수정 후에도 exp61 배치
   기준(24.83dB)·VIGS(27.86dB) 대비 아직 5~8dB 부족. `iters_per_event=177` 자체를 더
   올리거나, VIGS처럼 "새 이벤트 없는 유휴 시간에 과거 뷰 재방문"을 추가해야 그 격차를
   메울 수 있을 것으로 보임(아직 검증 안 됨, 다음 실험 대상)
4. **12F용 configurable batching 실측** — G=1/3/6/9 비교, 총 연산량 고정한 채 품질/지연 곡선 확인
5. 워크스테이션 절대 경로를 scene manifest로 교체, 데이터 무결성 자동 체크 추가
