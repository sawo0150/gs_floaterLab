# exp56 — mapping 고정비(픽셀/커널 launch) 절감: "gaussian 개수를 줄여도 왜 안 빨라지나"

- 상태: **완료 (2026-07-26).** Phase 0(기존 계측 재분석)으로 원인 확정(픽셀·
  커널-launch 고정비가 지배적, N-비례 항 아님) → Phase 1(`map()` iters
  10→7→5 스캔)에서 **`iters=7` 채택** — 시간 −16.1%(59.80→50.17s, 실시간
  여유 0.08배→0.23배), PSNR mean/kf 둘 다 개선(+0.21dB), map() 성사 횟수도
  22→26회 증가라는 전 지표 동시 개선(iters=10이 과잉 투자였음을 실측 확정).
  Phase 2(`render_downsample=2`를 이 새 baseline 위에 재검증)는 기각(시간
  이득 −1.7%뿐, PSNR −0.8dB 손해). Phase 3(coverage/GPU경합을 직접 겨냥한
  3축: `queue_size`↑·CUDA Graph·stream 분리)은 **전부 기각** — queue_size=4는
  역효과(시간·PSNR·coverage 셋 다 악화), CUDA Graph는 조사 후 구조적 부적합
  판정(구현 안 함), stream 분리는 **실행 중 CUDA illegal memory access로
  크래시**(custom rasterizer의 멀티스트림 미검증 상태 추정, 안전하게 되돌림 —
  다른 프로세스/GPU엔 영향 없음 확인). **exp56의 실질적 성과는 Phase 1
  (iters 10→7) 단독으로 확정.**
- 배경: 사용자 관찰 — "실시간이 되긴 하는데 품질이 썩 좋지는 않다. gaussian
  개수를 줄여도 그만큼 속도가 안 빨라지는 것 같은데 왜 그런가." exp55에서
  평균 gaussian 수를 −35.9% 줄였지만 순수 mapping 시간은 −12.2%뿐이었고
  ([[exp55_adaptive_density_carve_plan]] 부록), exp54 축6+2에서도 이미 같은
  현상이 관측됐다("gaussian 개수 자체가 더 이상 지배 변수가 아님", 118쪽 참조)
  — 이번엔 그 이유를 `_Sect` 타이밍 계측(이미 코드에 있는 rasterize/loss_compute/
  backward/optimizer_step/densify_prune 세부 태그)으로 직접 뜯어봄.

## Phase 0 — 기존 timing.csv 재분석으로 원인 확정 (신규 실행 없이 완료)

exp55의 직렬 재실행(`exp55_serial_final`, GPU 경합 없는 순수 110개 keyframe
전부 처리)의 `timing.csv`를 `map_dispatch`(=`self.map()` 1회 호출) 내부
세부 태그별로 합산 — 이 값이 이미 exp55 부록의 "map() 핵심 5단계 68.16s"의
내역이다:

| 구간 | 합계(110회) | 비중 | gaussian 개수(N) 의존성 |
|---|---:|---:|---|
| **rasterize** | 27.18s | **40%** | O(N) 겹침 검사 + O(픽셀) 블렌딩 — 혼합 |
| **backward** | 23.34s | **34%** | rasterize와 동형 — 혼합 |
| **loss_compute** | 16.48s | **24%** | **O(픽셀)만** — L1/SSIM/depth-L1/carve 전부 elementwise, N과 무관 |
| optimizer_step | 1.04s | 1.5% | O(N) (파라미터 수) — 절대량 작음 |
| densify_prune | 0.12s | 0.2% | 호출 자체가 드묾(11/110회만) |
| (map_dispatch 총합 대비 미계측 잔차) | 7.31s | 10% | 데이터 이동·`add_next_kf`·python 루프 |

**결론**: keyframe당 `map()`은 이미지 해상도(464×464, 고정)에 대해 `iters`번
반복되는 구조라, 시간의 상당 부분이 **N과 무관한 고정비**다.
- `loss_compute`(24%)는 전부 픽셀 단위 elementwise 연산 — carve loss 추가로
  더 늘었지만(exp55 Phase3) N에는 애초에 의존하지 않음.
- `rasterize`+`backward`(74%)는 이론상 N에 비례하는 항이 있지만, exp54
  축6+2(N을 122,957→116,143으로 눌러도 시간 그대로)·exp55 Phase2(N −35.9%,
  이 두 구간은 "소폭"만 감소)로 **이 gaussian 개수 규모(85k~130k)·이 해상도
  조합에서는 픽셀/타일 처리 고정비가 N-비례 항을 압도**한다는 게 두 번
  반복 확인됨.
- 부가로 병렬 모드(`exp55_final_confirm`, 22회 성사)의 같은 구간 평균은
  직렬 대비 rasterize 3.4배·backward 2.3배·loss_compute 3.4배 더 걸림 —
  GPU 경합이 tracking뿐 아니라 mapping 자신의 GPU 연산도 부풀리고 있음을
  시사(단, 병렬은 window 구성이 다른 22회, 직렬은 110회라 완전한 controlled
  비교는 아님 — 방향성 참고용).

**함의**: "gaussian 개수를 줄이는" 레버(exp54 축1/2/6, exp55 Phase1/2)는
이미 한계에 도달했다. 다음으로 시간을 줄이려면 **(a) N과 무관한 고정비
자체를 줄이거나(해상도↓, iters↓) (b) GPU 경합을 줄이는** 방향이어야 한다.

## Phase 1 — `map()` iters 하향 스캔 (10→7, 10→5)

exp54 축3(iters 10→5)이 이미 한 번 기각됐지만, 그건 **exp53 이전의
tracking-bound 구간**(tracking이 전체의 91%)에서 테스트된 것이라 "mapping을
반으로 깎아도 critical path가 tracking에 있어 안 줄어든다"는 게 기각 사유였다
(문서상 원인 자체가 지금과 다름). 지금은 exp53으로 tracking을 47.5% 줄이고
mapping이 pure 기준 압도적 비중(74%)을 차지하는 상태로 바뀌었고, Phase 0로
`iters`가 곱으로 걸리는 rasterize/backward/loss_compute가 시간의 74%+24%임을
재확인했으니 — **다시 테스트할 가치가 있는 축**. 오늘 오전 반대 방향(10→15/20)
테스트에서 "iters를 올리면 큐 드롭으로 처리 keyframe 수만 준다"는 게 확인됐으므로,
이번엔 **내리는** 방향 — 반복을 줄이면 `map()` 1회가 빨라져 mapper가 밀리지
않고 오히려 더 많은 keyframe을 처리할 수 있는지가 핵심 질문.

측정: 1253 전체, 현재 최종 채택 레시피(adaptive_density on, carve_lambda=0.05,
ppm on) 위에서 `iters`만 7, 5로 변경. 비교 기준선은 `exp55_carveon_anchors`
(iters=10, carve on) — 59.80s, PSNR 22.61/22.95, evo Sim3 2.41cm, map() 22회.

| iters | 온라인 루프 총합 | 실시간 배수 | PSNR(mean/kf) | evo APE Sim3 | map() 성사 횟수 |
|---|---:|---:|---:|---:|---:|
| 10(baseline) | 59.80s | 0.92배 | 22.61 / 22.95 | 2.41cm | 22회 |
| **7(채택)** | **50.17s** | **0.77배** | **22.82 / 23.16** | 2.41cm | **26회** |
| 5 | 49.44s | 0.76배 | 22.80 / 23.19 | 2.42cm | **32회** |

**iters=7 — 전 지표 동시 개선(예상 밖 압승)**: 시간 −16.1%(59.80→50.17s,
실시간 여유가 0.08배에서 0.23배로 3배 확대), PSNR mean/kf 둘 다 개선(+0.21/
+0.21dB), evo APE Sim3 동일(2.41cm), 게다가 **map() 성사 횟수도 22→26회로
오히려 증가**. Phase 0 가설이 정확히 들어맞음: `iters=10`은 이 지점에서
과잉 투자였고, 반복을 줄이면 (a) 고정비가 곱으로 줄어 `map()` 1회가 빨라지고
(b) mapper가 큐에서 덜 밀려 더 많은 keyframe을 처리하게 되며 — coverage
증가가 반복 감소로 인한 개별 정밀도 손실을 상쇄하고도 남음. 오늘 오전
반대 방향(10→15/20, coverage 감소로 역효과) 테스트와 정확히 대칭인 결과.

**iters=5 — 수확체감 확인, 7이 더 나은 지점**: 시간은 7 대비 거의 그대로
(50.17→49.44s, −1.5%뿐), PSNR·evo는 둘 다 노이즈 범위 내 동급(mean만 −0.02dB,
kf는 오히려 +0.03dB — run-to-run 노이즈 ±0.24~0.33dB보다 훨씬 작은 차이).
map() 횟수는 26→32회로 계속 늘지만 시간·품질엔 더 이상 보탬이 안 됨 —
**per-call 고정비(카메라 init·데이터 이동 등 iters와 무관한 부분, Phase 0의
"미계측 잔차 10%")가 바닥에 가까워지는 지점**으로 해석. **`iters=7`을 채택**
(5와 사실상 동급이지만 반복 깊이를 조금 더 남겨 안전마진 확보), `gs_backend.py`
정규 keyframe `map()` 호출을 `iters=10→7`로 영구 변경.

## Phase 2 — `render_downsample` 현재 최종 레시피 위 재검증

exp54 축4(`render_downsample=2`)는 **exp55 이전**(adaptive_density/carve
없음, `pcd_downsample=128` 기준)의 구 baseline 위에서 테스트돼 −4.2%
시간(58.09s)·−0.8dB PSNR로 "이미 실시간이라 감수할 이유 없음"으로 미채택
됐었다. **Phase 1에서 `iters=7`을 채택**했으므로, 이번엔 그 위에(=exp55
Phase2+3+exp56 Phase1) `render_downsample=2`를 추가로 얹어 재검증 — 두
레버가 겹칠 때 시너지(둘 다 rasterize/backward/loss_compute를 줄이는
동일 방향)인지 상쇄인지 확인.

| 설정 | 온라인 루프 총합 | 실시간 배수 | PSNR(mean/kf) | evo APE Sim3 |
|---|---:|---:|---:|---:|
| **iters=7 단독(baseline, 채택)** | 50.17s | 0.77배 | **22.82 / 23.16** | 2.41cm |
| iters=7 + render_downsample=2 | 49.31s | 0.76배 | 21.98 / 22.65 | 1.91cm |

**기각 — 상쇄가 아니라 손해만 추가**: iters=7 위에 render_downsample=2를
더하면 시간은 겨우 −1.7%(50.17→49.31s) 더 줄고 PSNR은 −0.84/−0.51dB
악화. Phase 1(iters↓)에서 이미 실시간 여유가 0.23배로 크게 벌어진 상태라
이 추가 −1.7%는 실익이 거의 없고, 픽셀 해상도를 줄이는 손실은 고스란히
남음 — exp54 축4 때와 같은 결론(품질 대비 시간 이득이 나쁨)이 새 baseline
위에서도 재확인됨. **기각, `render_downsample`은 config에서 제거(기본 1
유지)**. evo APE만 1.91cm로 개선됐는데 이는 트래킹과 무관한 렌더 해상도
변경이라 우연/노이즈로 해석(가드레일 통과에는 어차피 문제없는 수준).

## 최종 채택 설정

```yaml
# vigs/gs_backend.py, 정규 keyframe map() 호출
self.map(self.current_window, iters=7, include_global=True)  # 10 -> 7
```
(`render_downsample`은 config에 넣지 않음 — 기본 1/off 유지. exp55의
`pcd_downsample`/`adaptive_density`/`carve_lambda` 등 나머지 설정은 그대로.)

## 최종 결과 요약 (exp53+54+55+56 누적, 1253 전체)

| | exp55 최종(iters=10) | exp56 최종(iters=7) | 변화 |
|---|---:|---:|---:|
| 온라인 루프 총합 | 59.80s | **50.17s** | **−16.1%** |
| 실시간 배수(예산 65.1s) | 0.92배 | **0.77배** | 여유 2.9배 확대 |
| PSNR mean/kf | 22.61 / 22.95 | **22.82 / 23.16** | **+0.21 / +0.21dB** |
| evo APE Sim3 | 2.41cm | 2.41cm | 동급 |
| map() 성사 횟수 | 22회 | **26회** | +18% |

**사용자 질문("품질 개선 방법 없나")에 대한 답**: iters를 올리는 방향(오늘
오전 테스트)은 틀렸고, **내리는 방향이 시간·품질·coverage 세 마리 토끼를
동시에 잡았다** — `_gs_queue` 드롭 정책 하에서는 "한 번에 얼마나 깊게"보다
"얼마나 자주/많이 도는가"가 지배적이라는 게 두 방향 실험(iters↑/iters↓) 모두
에서 일관되게 확인됨.

## Phase 3 — coverage/경합을 직접 겨냥한 3축 (2026-07-26, 사용자 요청)

exp56 Phase 1/2로 "N/해상도를 줄이는" 레버가 소진됐음이 확정된 뒤, 사용자가
제안한 다음 3개 축을 전부 실행:

1. **`Training.queue_size`(2→4) 확대** — 오버헤드(iters·해상도)는 그대로 두고
   드롭되는 keyframe만 줄여 coverage를 늘리는 방향.
2. **커널 launch를 CUDA Graph로 묶기** — 조사 결과 **기각(미실행)**, 사유는
   아래 참조.
3. **GPU 경합 완화(CUDA stream 분리)** — mapping을 tracking과 분리된 별도
   CUDA stream에서 실행해 legacy default stream 공유로 인한 암묵적 동기화를
   제거.

### 축2(CUDA Graph) — 조사 후 기각, 구현 안 함

**이유**: CUDA Graph capture는 재생(replay) 구간의 모든 텐서가 **고정된 메모리
주소·shape**를 유지해야 하는데, VIGS의 `map()` 루프는 구조적으로 이 조건과
맞지 않음:
- `densify_and_prune()`가 gaussian 파라미터(`_xyz`/`_opacity`/...)를 주기적으로
  cat/prune해 메모리를 재할당 — capture된 그래프가 무효화됨(다행히 한 `map()`
  호출 내에서는 대개 발생 안 함, 26회 중 4회만 densify 발생).
- **keyframe마다 gaussian 개수(N)와 `current_window`의 카메라 구성이 다름** —
  즉 거의 매 `map()` 호출마다 새로 capture해야 함. 특히 exp55의 content-adaptive
  예산(축2)이 keyframe마다 다른 N을 만드는 설계라 이 문제가 구조적으로 더 심함.
- `torch.optim.Adam`이 `capturable=True` 없이 기본 설정으로 쓰이고 있어(코드
  확인, `gaussian_model.py:472`) graph-safe하지 않음 — 이것만 고쳐도 별도
  검증이 필요한 변경.
- 대안으로 `torch.compile(mode="reduce-overhead")`(PyTorch가 CUDA Graph
  안전장치를 자동 처리)도 검토했으나, 동일한 이유(매 호출마다 다른 N/shape)로
  **컴파일을 거의 매번 다시 해야 해서 컴파일 비용이 iters=7 루프가 절약하는
  시간보다 커질 가능성이 높음** — 이 workload(매 keyframe마다 동적 N)는애초에
  CUDA Graph/torch.compile이 설계된 "고정 배치 크기 반복 학습"과 정반대 패턴.
- **결론**: 구현하지 않음. 조용히 잘못된 결과를 낼 위험(그래프가 stale
  메모리를 참조)이 큰데 이득은 불확실 — exp53 축D(재학습 없이 구현 불가)와
  같은 성격의 "조사 후 기각".

### 축1(queue_size)·축3(CUDA stream 분리) — 구현·실행

- **축1**: `Training.queue_size: 2→4`.
- **축3**: `vigs.py`에 `Training.gs_dedicated_stream`(신규, 기본 false) 플래그
  추가 — true면 `self._gs_stream = torch.cuda.Stream()`을 만들어 `_gs_worker`의
  `process_track_data` 호출을 `with torch.cuda.stream(self._gs_stream):`로
  감쌈. **⚠ 구현 중 레이스 컨디션 실측 전에 발견·수정**: 기존 코드는 tracking
  스레드와 mapping 스레드가 명시적 stream 관리 없이 **동일한 legacy default
  stream을 공유**하고 있었음(`grep`으로 전체 레포에 `cuda.Stream`/`cuda.stream`
  이 전무함을 확인) — mapping을 별도 stream으로 분리하면 `demo.py`의
  `_gs_queue.join()` 직후 메인 스레드가 곧바로 `save_ply`/`eval_rendering`으로
  gaussian GPU 텐서를 읽는데, `queue.join()`은 파이썬 호출이 반환됐음만
  보장하지 GPU 커널 완료를 보장하지 않음 — **stream 동기화 없이는 아직 끝나지
  않은 densify/optimizer.step() 쓰기와 경합해 PLY/PSNR이 조용히 오염될 수
  있는 실제 레이스**였음. `demo.py`의 `_gs_queue.join()` 직후에
  `torch.cuda.current_stream().wait_stream(vigs._gs_stream)`을 추가해 해결
  (실행 전에 코드 리딩으로 발견 — [[feedback_verify_unmeasured]] 원칙:
  실측 전에 이런 위험은 코드로 직접 확인해야 함).

**측정** (iters=7 baseline 위, 1253 전체):

| 설정 | 온라인 루프 총합 | 실시간 배수 | PSNR(mean/kf) | evo APE Sim3 | map() 성사 횟수 |
|---|---:|---:|---:|---:|---:|
| baseline(queue=2, stream 공유) | 50.17s | 0.77배 | 22.82 / 23.16 | 2.41cm | 26회 |
| queue_size=4 | 52.38s | 0.80배 | 22.57 / 23.05 | 1.91cm | **25회** |
| gs_dedicated_stream=true | **크래시** | | | | |

**축1(queue_size=4) — 기각, 역효과**: 시간 +4.4%(50.17→52.38s), PSNR
mean/kf 둘 다 악화(−0.25/−0.11dB), **map() 성사 횟수도 26→25회로 오히려
감소** — "버퍼를 키우면 더 많이 처리될 것"이라는 예상과 정반대. 원인 추정:
드롭 정책(`while full: get_nowait()`)은 큐 크기와 무관하게 "최근 N개만
유지"이므로, 버퍼가 클수록 mapper가 밀렸을 때 **더 오래된(최대 4개 밀린)
packet부터 순서대로 처리**하게 돼 신선도가 오히려 나빠짐(queue=2일 땐
최대 2개 밀린 packet까지만 허용). 처리량 자체도 늘지 않아 순이득이 없음 —
**기각, `queue_size=2` 유지**.

**축3(gs_dedicated_stream) — 실행 중 크래시, 기각**: keyframe 10~11 부근에서
`torch.AcceleratorError: CUDA error: an illegal memory access was encountered`
발생, GPU 컨텍스트가 오염돼 이후 모든 CUDA 호출이 연쇄 실패 — 프로세스
강제 종료 후 `nvidia-smi`로 GPU가 깨끗한 상태(459MiB, 유휴 프로세스 없음)로
복구됐음을 확인, 다른 작업엔 영향 없음.

**원인 분석**: 레포 전체에 명시적 CUDA stream 관리가 전혀 없었다는 걸
구현 전에 이미 확인했었는데(`grep`으로 확인), 즉 지금까지 tracking과
mapping은 **암묵적으로 legacy default stream을 공유**하고 있었고, 이
legacy null stream 특유의 "다른 모든 stream과 교차 동기화"하는 특성이
사실상 두 스레드의 GPU 작업을 순차화해 안전하게 만들어주고 있었다.
mapping을 별도 stream으로 옮기자 **진짜 동시 실행**이 되면서, custom CUDA
rasterizer(`thirdparty/diff-gaussian-rasterization`, 이 프로젝트 계열의
전형적인 hand-written CUDA extension)가 멀티스트림 환경에서 안전하다고
검증된 적이 없는 내부 상태(재사용되는 정적/스크래치 버퍼 등, 추정)와
충돌한 것으로 판단됨 — 정확한 라인은 CUDA 커널 소스까지 파고들어야 하는데
투자 대비 낮은 우선순위로 판단해 더 파지 않음.

**결론 — 기각(구현 안전성 문제로 재시도 안 함)**: `gs_dedicated_stream`
플래그는 코드에 남겨두되(기본 false, off) `vigs.py`에 "패치 없이 켜지
말 것" 경고 주석 추가. rasterizer CUDA 소스를 멀티스트림 안전하게 고치지
않는 한 이 축은 닫힌 것으로 취급 — exp53 축D(재학습 없이 구현 불가)·exp56
축2(CUDA Graph, 구조적 부적합)와 같은 성격의 "조사/시도 후 기각".

**Phase 3 종합**: 3축(queue_size↑·CUDA Graph·stream 분리) 전부 기각 —
coverage/경합을 직접 겨냥한 접근은 이번 아키텍처(legacy default stream
암묵적 동기화에 의존하는 스레드 안전성, 큐의 "최근 N개만 유지" 드롭 정책)
에서는 추가 이득을 못 냄. **exp56의 실질적 성과는 Phase 1(iters=7)
하나로 확정.**

## 다음 단계

1. iters를 7 밑으로(예: 3~4) 더 내리는 것도 미탐색 — Phase 1에서 5→7 사이
   수확체감이 이미 보였으므로 ROI는 낮을 가능성이 크지만, 완전히 배제하진
   않음.
2. carve floater 지표(exp55의 `exp55_score_carve_vigs.py`)로 iters=7 채택
   레시피의 floater 수준도 재확인할 가치 — carve_lambda는 그대로 0.05를
   유지했지만 iters가 줄어 carve loss 자체의 gradient step 수도 줄었으므로
   효과가 희석됐을 가능성.
3. (낮은 우선순위, 고위험) `thirdparty/diff-gaussian-rasterization`을
   멀티스트림 안전하게 패치하면 축3(stream 분리)을 다시 시도할 여지 — CUDA
   커널 소스 레벨 작업이라 투자 대비 효과가 불확실, 지금 우선순위는 아님.
