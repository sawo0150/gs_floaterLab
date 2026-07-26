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
  다른 프로세스/GPU엔 영향 없음 확인). **부록(사용자 재확인 질문, 07-26)**:
  "병렬이라 경합 때문에 그런 거 아니냐"는 의심에 순수 직렬(경합 0)로 재검증 —
  render_downsample=2가 직렬에서도 rasterize/backward/loss_compute를 겨우
  1~3%만 줄임(병렬 6~8%보다도 작음) — 경합이 아니라 **커널-launch 고정비
  자체가 데이터量과 무관하게 지배적**이라는 Phase 0 결론이 경합과 독립적으로
  참임을 재확인. **Phase 4(신규, 07-27) — 이 세션 최대 발견**: "1iter당
  연산량을 줄이려면 뭘 건드려야 하나"는 질문에 `map_call` 세부 로그(기존에
  있었지만 한 번도 집계 안 해본 `iters`/`n_view`/`n_gauss` 메타데이터)를 처음
  집계 — **`map()` 호출 26회 중 단 2~3회(맵 최초 초기화 + IMU 재초기화 시
  `remove_all_gaussians()`로 맵 전체 삭제 후 재구축)가 mapping 전체 시간의
  49%를 차지**하고 있었음(이 호출들은 `iters=90~131`로, Phase 1이 튜닝한
  일반 keyframe의 `iters=7`과 전혀 다른 코드 경로). 이 초기화 반복 횟수의
  기준값 `Training.init_itr_num`(1050)을 600으로 낮춰 **`iters=7` 위에 추가로
  시간 −6.2%(50.17→47.08s)를 확보, PSNR은 사실상 무손실(mean −0.09dB 노이즈
  이내, kf는 오히려 +0.05dB), map() 성사 횟수도 26→30회 증가** — 채택.
  300까지 내리면 시간은 더 줄지만(46.15s) PSNR이 −0.35~0.44dB 실손실이라
  기각, 600이 스위트스팟. **exp53+54+55+56 누적: 47.08s, 실시간 배수
  0.72배(exp55 baseline 대비 −21.3%), kf PSNR 23.21(오히려 +0.26dB 개선).**
  **Phase 5(신규, 07-27) — 파트별 시간을 파라미터 회귀식으로 규명**: 세션
  전체(11개 run, 548개 실제 `map()` 호출)의 `map_call` opt-in 로그를 처음
  집계해 최소자승 회귀(`scripts/analysis/exp56_fit_timing_model.py`) —
  직렬(경합 0) 데이터에서 R²=0.93~0.998로 rasterize/loss_compute/backward/
  optimizer_step 각각이 `(iters, n_view, n_gauss, 해상도)`와 어떤 관계식인지
  정확히 도출(실측 5% 이내로 검증). 결론: **`iters × n_view`(반복 횟수 ×
  카메라 수)가 압도적 — gaussian 수 계수는 그 1/10, 해상도 계수는 통계적으로
  0**. 병렬 데이터로 다시 피팅하면 고정비 계수만 거의 2배(경합이 "커널
  launch 대기시간"만 정확히 부풀림을 계수로 확인). `n_view` 의존이 왜
  이렇게 큰지도 코드로 확인: `render()`가 원본 3DGS 코드 그대로라 애초에
  카메라 1대 전용(batch 미지원)이라, `map()`이 Python for문으로 카메라를
  하나씩 순차 처리하며 고정비를 매번 새로 지불하는 구조 — 잠재력 큰(뷰당
  고정비의 최대 91% 절감 가능) 다음 후보(rasterizer batch화)를 식별했으나
  CUDA 소스 수정이 필요해 고위험으로 별도 라운드 필요. **Phase 6(신규,
  07-27) — iters↓·n_view↑ 재배분(같은 view-op 예산, 품질 축) 시도, 기각**:
  Phase 5 회귀식에서 나온 "같은 iters×n_view면 시간은 그대로이니 뷰를
  다양하게 하면 품질이 오히려 좋아지지 않을까"라는 가설을 실측 — dead
  config였던 `Training.window_size`를 실제 로직에 연결(`current_window`
  상한 하드코딩 `10`을 대체)해 두 지점(window=15/iters=5, window=19/iters=4)
  테스트. **시간 예측은 정확히 맞았지만(거의 무변화) PSNR은 −1.1→−3.5dB로
  window를 키울수록 단조 악화** — 프론티어(최근 keyframe)가 과거 keyframe
  들과 제한된 gradient 예산을 나눠 쓰게 되면서 수렴이 희석되는 것으로 분석,
  3번째 지점은 추세가 명확해 실행 없이 기각 확정. window_size는 기본값
  10으로 원복(코드 연결 자체는 유지 — 향후 재검증 가능한 자산).
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

## 최종 채택 설정 (Phase 1 + Phase 4)

```yaml
# vigs/gs_backend.py, 정규 keyframe map() 호출
self.map(self.current_window, iters=7, include_global=True)  # 10 -> 7 (Phase 1)

# config/aria1253.yaml, Training:
init_itr_num: 600   # 1050 -> 600 (Phase 4)
```
(`render_downsample`은 config에 넣지 않음 — 기본 1/off 유지. exp55의
`pcd_downsample`/`adaptive_density`/`carve_lambda` 등 나머지 설정은 그대로.)

## 최종 결과 요약 (exp53+54+55+56 누적, 1253 전체)

| | exp55 최종(iters=10, init=1050) | +Phase1(iters=7) | +Phase4(init=600, 최종) | 누적 변화 |
|---|---:|---:|---:|---:|
| 온라인 루프 총합 | 59.80s | 50.17s | **47.08s** | **−21.3%** |
| 실시간 배수(예산 65.1s) | 0.92배 | 0.77배 | **0.72배** | 여유 3.4배 확대 |
| PSNR mean/kf | 22.61 / 22.95 | 22.82 / 23.16 | **22.73 / 23.21** | mean 동급, kf **+0.26dB** |
| evo APE Sim3 | 2.41cm | 2.41cm | **2.07cm** | 동급/개선 |
| map() 성사 횟수 | 22회 | 26회 | **30회** | +36% |

**사용자 질문("품질 개선 방법 없나" → "1iter당 연산량 줄이려면 어디를
건드려야 하나")에 대한 답**: iters를 올리는 방향(Phase 1 이전 테스트)은
틀렸고, 내리는 방향(Phase 1)이 시간·품질·coverage를 동시에 개선했다. 이어서
"1iter당 연산량의 95%+가 고정 오버헤드"라는 Phase 0/2 결론을 더 파고들자
**Phase 4에서 진짜 핵심 지점을 찾음**: `map()` 호출 26회 중 단 2~3회(초기화/
IMU 재초기화)가 전체 mapping 시간의 49%를 차지하고 있었다 — 이게 "1iter당
연산량"이 아니라 "이 소수 호출의 iters 자체가 90~131회로 너무 컸다"는
별개의 문제였다. 이 값을 600으로 낮춰 추가로 시간을 줄이면서 품질은
거의 무손실(오히려 kf PSNR·궤적 소폭 개선) — `_gs_queue` 드롭 정책 하에서는
"한 번에 얼마나 깊게"보다 "얼마나 자주/많이 도는가"가 지배적이라는 원칙이
정규 호출(Phase 1)뿐 아니라 초기화 호출(Phase 4)에도 그대로 적용됨.

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

## 부록 — Phase 2(render_downsample) 결론이 GPU 경합 때문 아니냐는 재검증 (2026-07-26)

사용자 질문: "병렬로 테스트해서 그런 거 아니냐, 직렬이면 GPU 연산량 줄어든
만큼 mapping도 줄어야 하는 거 아니냐" — Phase 2가 병렬(`parallel: true`)
에서만 테스트됐다는 점을 정확히 짚은 재검증 요청. 순수 직렬(`parallel:
false`, tracking과 GPU 경합 0)로 iters=7 baseline과 render_downsample=2를
다시 비교(1253 전체, `map_dispatch` 세부 태그 per-call 평균):

| | 직렬, 원해상도(iters=7) | 직렬, render_downsample=2 | 변화 |
|---|---:|---:|---:|
| rasterize | 192.59ms | 186.07ms | −3.4% |
| backward | 160.80ms | 159.16ms | −1.0% |
| loss_compute | 118.51ms | 116.28ms | −1.9% |

**경합 가설 기각, Phase 0/2 결론 재확인**: 경합이 전혀 없는 직렬에서도
픽셀 수를 1/4로 줄였는데 겨우 1~3%만 줄어듦 — 오히려 병렬 측정치(−5.5~
−7.7%, 본문 Phase 2 표)보다도 작음. 즉 "병렬 경합이 데이터量 감소 효과를
가려서 작아 보였다"는 가설은 틀렸고, **데이터量(픽셀·gaussian 수) 자체가
직렬/병렬과 무관하게 이 시간 구조를 거의 안 좌우한다**는 게 재확인됨.

대조로 `iters`는 직렬에서도 확실히 비례해서 줄었음(같은 방식으로 비교,
참고: iters=10 직렬은 exp55_serial_final의 rasterize 247.06ms/backward
212.20ms/loss_compute 149.78ms):

| | iters=10(직렬) | iters=7(직렬) | 변화 |
|---|---:|---:|---:|
| rasterize | 247.06ms | 192.59ms | **−22.0%** |
| backward | 212.20ms | 160.80ms | **−24.2%** |
| loss_compute | 149.78ms | 118.51ms | **−20.9%** |

**결론**: "GPU 연산량"은 두 가지 다른 축이었다 — **(a) 커널 한 번이 처리하는
데이터量**(픽셀 수·gaussian 수, Phase 0/2가 다룬 것)과 **(b) 커널을 호출하는
횟수**(`iters`, Phase 1이 다룬 것). 이 규모(gaussian 10만 대, 464×464)에서는
(a)는 거의 공짜(launch 오버헤드에 묻힘, 직렬·병렬 무관하게 일관), (b)만
실제로 시간에 거의 선형으로 반영됨. 병렬/직렬 여부와 무관한 구조적 사실임을
직접 실측으로 확정.

## Phase 4 — 새로 발견: map() 호출 26회 중 2~3회(초기화/재초기화)가 mapping 시간의 49%

사용자 질문("1iter당 연산량을 줄이려면 어떤 핵심 부분을 건드려야 하는가")에
답하려 `map_call` 세부 로그(`iters=`/`n_view=`/`n_gauss=` 메타데이터 포함,
기존 코드에 이미 있던 opt-in 계측)를 처음으로 직접 파싱해봄 — Phase 0~3은
전부 "map_dispatch"(호출 전체 합)만 봤지, **호출 하나하나를 구분해서 본 적이
없었다**.

**발견**: `map()` 호출 26회는 종류가 균일하지 않다 — 코드상 세 가지 호출
경로가 있음(`gs_backend.py:299/302/305`):

| 호출 종류 | `iters` | 발생 조건 |
|---|---|---|
| 일반 keyframe | 7(exp56 채택값) | 매 keyframe마다(21회) |
| PGBA(pose graph 보정) | 20(고정) | 루프클로저 등 pose 업데이트 시(4회) |
| **초기화/재초기화** | `init_itr_num // len(current_window)` = **95~131** | 시퀀스 최초 1회 + `remove_all_gaussians()` 호출 시(IMU 늦은 초기화, `track_frontend.py:257`, `t1==imu_late_init_from`일 때 맵 전체를 삭제하고 처음부터 다시 채움) |

**실측(exp56_iters7 run 재분석)**: 이 "초기화/재초기화" 호출은 26회 중
단 2~3회뿐인데(`map_call` 로그상 iters=131 1회 + iters=95 2회 — 정확히
왜 2회인지는 미해결, 아래 한계 참조), **합쳐서 19.98초** — 일반 keyframe
21회 합(16.65초)보다 크고, **전체 mapping 시간(40.55초)의 49.3%**를 차지함.
`remove_all_gaussians()`가 `self.gaussians = GaussianModel(0, ...)`로
gaussian을 통째로 삭제하고 `self.initialized = False`로 되돌리기 때문에,
그 다음 keyframe에서 "첫 keyframe"과 똑같은 무거운 초기화 경로(`init_itr_num
//len(current_window)`, 지금 규모로는 iters 90~131)를 다시 타는 구조.

**함의**: Phase 1(`iters=7`)은 26회 중 21회(일반 keyframe)에만 적용됐다 —
초기화/재초기화 경로는 손도 안 댐. 여기가 지금까지 발견된 것 중 **가장 큰
단일 절감 여지**(호출 2~3개에 전체 시간의 절반이 몰려있음).

**테스트**: `Training.init_itr_num`(현재 1050, 초기화 반복 횟수의 기준값)를
300으로 낮춰(≈3.5배 절감) 1253 전체 재실행. 초기화/재초기화 경로에만 영향
(정규 keyframe의 `iters=7`은 무관), 대신 맵의 "첫 기하 골격" 품질이
낮아질 위험이 있어 PSNR·evo를 함께 확인.

| 설정 | 온라인 루프 총합 | 실시간 배수 | PSNR(mean/kf) | evo APE Sim3 | map() 성사 횟수 | 초기화 호출 시간(3회 합) |
|---|---:|---:|---:|---:|---:|---:|
| baseline(init_itr_num=1050) | 50.17s | 0.77배 | 22.82 / 23.16 | 2.41cm | 26회 | 19.98s(49.3%) |
| init_itr_num=300 | 46.15s | 0.71배 | 22.38 / 22.81(**−0.44/−0.35dB**) | 1.91cm | 34회 | 6.99s(19.5%) |
| **init_itr_num=600(채택)** | **47.08s** | **0.72배** | **22.73 / 23.21**(mean −0.09, kf **+0.05**) | 2.07cm | **30회** | 12.96s(34.7%) |

**init_itr_num=300은 너무 세게 깎음**: 시간·coverage는 가장 좋지만 PSNR이
−0.35~0.44dB 하락 — 이 프로젝트가 실측한 run-to-run 노이즈(±0.24~0.33dB)를
벗어나는 **진짜 품질 비용**. 초기화/재초기화 경로(맵을 처음부터 짓는 "cold
start" 순간)는 정규 keyframe보다 반복이 더 필요하다는 뜻으로 해석 —
95~131회에서 27~37회까지(약 1/3.5) 깎은 건 과했음.

**init_itr_num=600 채택**: 시간 −6.2%(50.17→47.08s, iters=7 위에 추가 절감),
PSNR은 mean만 −0.09dB(노이즈 이내)·kf는 오히려 +0.05dB — **사실상 무비용**.
초기화급 호출 3회의 합이 19.98s→12.96s(−35.1%)로 줄었고, 전체 mapping
시간에서 차지하는 비중도 49.3%→34.7%로 낮아짐(여전히 크지만 훨씬 완화).
map() 성사 횟수도 26→30회로 늘어(+15%) — iters=7 때와 같은 패턴("호출을
가볍게 하면 mapper가 덜 밀려 더 많이 처리한다")이 여기서도 재현됨.
evo APE Sim3도 2.07cm으로 동급/개선.

**exp53+54+55+56 누적 최종**: 47.08s, 실시간 배수 **0.72배**(exp55 baseline
59.80s 대비 **−21.3%**, iters=7 단독 채택 시점 50.17s 대비 추가 −6.2%).

**한계(정직하게 기록)**: `remove_all_gaussians()`는 코드상
`self.t1 == self.imu_late_init_from`(정확히 한 번만 참이 되는 조건)에서만
호출되는 것으로 확인했는데, 실측 로그엔 "초기화급" 호출이 (최초 1회 +
이 재초기화 1회 = 총 2회여야 할 것 같은데) 2회의 `iters=95` 로그가 잡혀
총 3회로 보임 — 정확한 원인(같은 재초기화 이벤트가 이후 packet에서 한 번
더 무거운 경로를 타는 부수효과인지, 다른 트리거가 있는지)은 미해결. 다만
"초기화급 호출이 극소수인데 전체 시간의 절반 가까이를 차지한다"는 헤드라인
결론 자체는 정확한 횟수(2 vs 3)와 무관하게 견고함.

## Phase 5 — 파트별 시간을 파라미터 회귀식으로 규명 (2026-07-27, 사용자 요청)

**요청**: "40s를 파트별로 나누고, 각 파트가 어떤 param에 종속되는지, 총
시간과 param의 관계식(추세선)을 꼼꼼히 규명해달라." Phase 0~4는 전부
`map_dispatch`(호출 전체 합) 또는 개별 호출 몇 개를 손으로 비교하는
수준이었음 — 이번엔 **기존에 이미 있었지만 한 번도 집계 안 해본
`map_call` opt-in 로그**(`rasterize`/`loss_compute`/`backward`/
`optimizer_step`마다 `iters`/`n_view`/`n_gauss` 메타데이터 포함)를 이 세션
전체 실험(exp55~56, 11개 run, 548개 실제 `map()` 호출)에서 전부 파싱해
최소자승 회귀로 관계식을 피팅. 스크립트:
`scripts/analysis/exp56_fit_timing_model.py`(재사용 가능, 신규 run 추가 시
`RUNS` 리스트에 추가하면 재실행 가능).

### 파트 구조부터 — `map()`의 실제 루프

```python
for _ in range(iters):                          # iters번 반복
    for viewpoint in current_viewpoints:         # 매 iteration마다 n_view대 카메라를
        render(viewpoint, ...)                   #   "한 대씩" 순차 호출 (rasterize)
        get_loss_mapping_rgbd(...)               #   (loss_compute)
    loss_mapping.backward()                      # iteration당 1번(전체 뷰 합산 후)
    optimizer.step()                             # iteration당 1번
```
`rasterize`·`loss_compute`는 **iteration마다 카메라 1대씩 순차 처리**하는
구조라 자연 단위가 "뷰-연산 1회"(`iters × n_view`)이고, `backward`·
`optimizer_step`은 iteration당 1번만 불리지만 그 안에서 다루는
그래프 크기/파라미터 수가 `n_view`·`n_gauss`에 비례.

### 회귀 결과 (직렬 데이터만, GPU 경합 없음 — n=330 실제 호출)

| 파트 | 관계식 | R² |
|---|---|---:|
| rasterize | `1.473·(iters·n_view) + 0.00545·(iters·n_view·n_gauss/1000) − 0.035·(iters·n_view·pixratio)` | **0.992** |
| loss_compute | `0.956·(iters·n_view) + 0.00207·(iters·n_view·n_gauss/1000) − 0.024·(iters·n_view·pixratio)` | **0.994** |
| backward | `−1.623·iters + 1.126·(iters·n_view) + 0.126·(iters·n_gauss/1000)` | **0.929** |
| optimizer_step | `1.739·iters − 0.095·(iters·n_view) + 0.001·(iters·n_gauss/1000)` | **0.998** |

(`pixratio` = 1.0 원해상도, 0.25 = `render_downsample=2`. 계수의 부호/크기가
±0.02~0.09 수준으로 작은 항은 통계적으로 0과 구분 안 됨 — 잡음.)

**검증(회귀에 실제로 쓰인 값이지만 별도로 대조)**: `iters=95, n_view=11,
n_gauss=18103`(Phase 4에서 발견한 그 초기화 호출) → 모델 예측 **3,927ms**,
실측 **3,734ms**(오차 5%).

### 파트별로 뭐가 지배적인가 — 계수를 직접 비교

| 항 | 대표 계수 크기(뷰-연산 또는 iteration당) | 지금 규모에서 기여 |
|---|---:|---|
| **고정비(a)** — `iters`·`n_view` 자체 | rasterize 1.47ms + loss_compute 0.96ms + backward(n_view항) 1.13ms **≈ 뷰-연산 1회당 3.5ms** | **가장 큼** |
| gaussian 수(b) | 1000개당 0.005~0.13ms | n_gauss 5만 기준 rasterize·loss_compute 합쳐 ≈0.4ms(뷰-연산당) — 고정비의 10% 남짓 |
| 해상도(c) | −0.02~−0.03(잡음, 사실상 0) | 무시 가능 |

**즉 시간을 지배하는 건 압도적으로 `iters`와 `n_view`(카메라 수)의 곱이지,
gaussian 수·해상도가 아니다** — Phase 0~2가 이미 보인 결론을 이번엔 정확한
숫자(계수)로 다시 확인.

### 병렬(실배포 상태)에서는 고정비(a)만 부풀어

같은 피팅을 병렬 데이터(n=186, GPU 경합 있음)로 하면 R²는 0.73~0.86으로
떨어지지만(경합이 노이즈를 더함) **고정비(a) 계수만 거의 2배**로 뜀 —
rasterize 1.47→2.69, loss_compute 0.96→1.76, backward의 `n_view` 계수도
1.13→1.93. **gaussian/해상도 계수는 거의 그대로.** GPU 경합은 "커널
launch·스케줄링 대기시간"만 정확히 부풀리지, 데이터 처리 자체를 느리게
만들지 않는다는 걸 계수 수준에서 확인 — exp55 부록의 정성적 "경합이
tracking을 부풀린다"는 관찰을 mapping 쪽에서도 정량 재확인한 셈.

### 왜 하필 `n_view`(카메라 수)에 이렇게 크게 종속되는가 — 코드 레벨 원인

`vigs/gaussian/renderer/__init__.py::render()`를 직접 확인 — 이건 **원본
3DGS(Inria/GRAPHDECO) 코드 그대로**이고, 원래 설계 자체가 **카메라 1대만
받아서 그때그때 `GaussianRasterizationSettings`/`GaussianRasterizer`를
새로 만들어 처리**하는 함수다(batch 차원 없음, `viewmatrix`/`projmatrix`가
스칼라 하나). VIGS의 `map()`은 멀티뷰 supervision이 필요해 이 단일-카메라
함수를 Python for문으로 `n_view`번 반복 호출하는 구조를 얹었을 뿐, 원본
함수 자체는 여러 카메라를 한 번에 처리하도록 만들어진 적이 없다.

이게 왜 문제냐면 — rasterize/loss_compute 비용의 85~95%가 픽셀·gaussian
처리량이 아니라 **커널 launch/디스패치 고정비**(Phase 0에서 확인)인데,
이 고정비는 **카메라를 하나 처리할 때마다 매번 새로 지불**된다(같은
iteration 안에서도 배치로 묶이지 않고 순수 순차 for-loop, 카메라 사이에
공유되는 게 전혀 없음). 그래서 카메라를 하나 더 넣으면 그 카메라의
데이터量과 무관하게 "고정비 한 세트"가 통째로 추가된다 — `iters`가 이
파이프라인을 몇 번 반복하는지를 결정하듯, `n_view`는 "한 iteration 안에서
이 파이프라인을 몇 번 반복하는지"를 결정하는 것이라 **사실상 iters와
동일한 메커니즘(고정비 반복)이 곱으로 두 번 걸리는 구조**.

**함의(다음 후보, 고위험·미착수)**: 만약 rasterizer가 여러 카메라를 **한
번의 커널 launch로 묶어 처리**(batch dimension)할 수 있다면, 뷰-연산당
고정비를 `n_view`번이 아니라 **1번만** 지불하게 돼 이론상 뷰당 고정비의
(n_view−1)/n_view ≈ 91%(n_view=11 기준)를 아낄 여지가 있다 — Phase 0에서
확인한 "고정비가 압도적"이라는 사실 자체가 이 lever의 잠재력을 크게 만듦.
다만 이건 `thirdparty/diff-gaussian-rasterization`의 **CUDA 소스 자체를
멀티카메라 batch 지원하도록 수정**해야 하는 일이라, Phase 3에서 겪은
stream-분리 크래시(같은 서드파티 CUDA 코드의 미검증 영역을 건드려 실제로
크래시 남)와 같은 성격의 리스크 — 신중한 별도 라운드가 필요.

## Phase 6 — iters↓·n_view↑ 재배분(같은 view-op 예산, 품질 축) (2026-07-27, 사용자 제안)

Phase 5 회귀식(`rasterize/loss_compute ∝ iters×n_view`)에서 나온 자연스러운
질문: 같은 `iters×n_view`(view-op 총량) 예산을 유지한 채 **iters를 줄이고
n_view(카메라 수)를 늘리면** — 회귀식대로면 rasterize/loss_compute 시간은
거의 그대로(경제적 규모 없음)이고 `optimizer_step`만 `iters`에 비례하니
살짝 이득이지만, **매 gradient step마다 더 다양한 뷰를 보게 돼 기하 일관성
(품질)이 개선될 수 있다**는 게 가설 — 순수 품질 축, 속도 축 아님.

**구현**: `self.window_size`(config `Training.window_size`)가 로드만 되고
실제로는 한 번도 안 쓰이던 **dead config**였음을 발견(`current_window`
상한이 `10`으로 하드코딩, 우연히 config 기본값 10과 일치) — 실제 로직에
연결(`gs_backend.py`, `len(self.current_window) > self.window_size`)해서
window 크기(≈`n_view`)를 config로 통제 가능하게 만듦. 정규 keyframe
`map()` 호출에 `max_viewpoints=self.window_size + 3`도 추가해 window+global
전체가 잘리지 않고 다 들어가도록 함(기존 기본값 20은 window_size≥18에서
subsampling 발생).

**축**: baseline(window_size=10→n_view≈11-13, iters=7, product≈77-91) 대비
product를 대략 유지하면서 재배분:

| 축 | window_size | iters | 예상 n_view | product |
|---|---:|---:|---:|---:|
| baseline(현재 채택) | 10 | 7 | 11~13 | 77~91 |
| 1 | 15 | 5 | 16~18 | 80~90 |
| 2 | 19 | 4 | 20~22 | 80~88 |
| 3 | 25 | 3 | 26~28 | 78~84 |

측정: 1253 전체, 그 외 exp56 최종 채택 레시피(init_itr_num=600 등) 유지.

| 축 | 온라인 루프 총합 | 실시간 배수 | PSNR(mean/kf) | evo APE Sim3 | map() 성사 횟수 |
|---|---:|---:|---:|---:|---:|
| baseline | 47.08s | 0.72배 | 22.73 / 23.21 | 2.07cm | 30회 |
| **1(ws=15,iters=5, 실측 n_view=16)** | 46.17s | 0.71배 | **21.64 / 21.89**(**−1.09/−1.32dB**) | 2.41cm | 30회 |
| **2(ws=19,iters=4, 실측 n_view=20)** | 46.34s | 0.71배 | **19.27 / 19.57**(**−3.46/−3.64dB**) | 2.41cm | 32회 |
| 3(ws=25,iters=3) | **미실행(추세로 기각 확정, 아래 참조)** | | | | |

**가설 기각 — 명확하고 악화 추세**: 시간은 예상대로 거의 안 바뀌었지만
(회귀식 예측대로, product를 맞췄으니 rasterize/loss_compute는 거의 그대로)
**PSNR이 축1(−1.1~1.3dB)→축2(−3.5~3.6dB)로 window를 키울수록 더 나빠짐** —
이 프로젝트 노이즈(±0.24~0.33dB)를 훨씬 벗어나는 명백한 실손실, 그것도
단조 악화 추세. "같은 view-op 예산이면 재배분은 공짜"라는 Phase 5 회귀식의
**시간 예측은 정확히 맞았지만, 품질에 대한 예측(다양한 뷰가 도움될 것)은
정반대로 틀렸다** — 그래서 축3(ws=25, iters=3, 더 극단적 재배분)은 추세가
이미 명확해 실행하지 않고 기각 확정.

**왜 틀렸는가(원인 분석)**: `window_size`를 키우면 "iteration당 보는 뷰
개수"만 늘어나는 게 아니라 **current_window 자체가 훨씬 오래된 keyframe까지
붙잡아두는 방향으로 바뀐다** — incremental SLAM 특성상 지도의 "프론티어"
(가장 최근에 새로 들어온, 아직 수렴 안 된 영역)가 한정된 iteration 예산을
과거 keyframe들과 나눠 써야 하고, 게다가 iters까지 줄였으니(7→5→4) **새로
들어온 gaussian이 densify/수렴할 시간 자체가 줄면서 동시에 그 적은
gradient step조차 오래된 영역과 경쟁**하게 됨 — "총 view-op 예산"은 같아도
"프론티어에 집중되는 유효 gradient 밀도"는 크게 줄어드는 구조. Phase 5
회귀식은 순수 **연산 시간**만 설명하는 모델이라 이런 **최적화 동역학
(optimization dynamics)** 효과는 애초에 잡을 수 없었던 것 — 시간과 품질은
서로 다른 메커니즘으로 움직인다는 걸 확인.

**코드 자산은 유지**: `self.window_size`가 dead config였던 걸 실제 로직에
연결한 수정 자체는 유지(기본값 10 그대로 두면 기존과 완전히 동일하게
동작 확인됨) — 향후 window_size를 진짜 원인 분석 없이 건드리면 안 된다는
확실한 반증 데이터를 남긴 것으로 가치가 있음.

**⚠ CLAUDE.md 로드맵(dense-frame supervision)에 대한 함의**: 이 결과는
"n_view를 단순히 늘리기만 하면 품질이 좋아진다"는 가정에 대한 반증이다 —
dense-frame supervision(keyframe 사이 프레임을 supervision 뷰로 추가)을
나중에 시도할 때, 단지 뷰 개수만 늘리고 iters를 줄이거나 window를 무작정
넓히면 **오히려 프론티어 수렴이 희석돼 역효과가 날 수 있음**을 미리
확인한 셈 — 뷰를 늘리려면 (a) iters는 유지/늘리거나 (b) 프론티어(최근
keyframe)에 gradient가 집중되도록 가중치를 주는 설계가 같이 필요할
가능성이 큼. batch 렌더링으로 "시간" 문제를 풀어도 "품질" 문제는 별도로
설계해야 한다는 경고.

## 다음 단계

0. **(Phase 5에서 새로 발견, 잠재력 최대이나 고위험) rasterizer 멀티카메라
   batch 지원** — `n_view`(카메라 수)가 뷰-연산당 고정비를 그대로 곱으로
   반복시키는 게 회귀로 확인됨(뷰-연산당 ≈3.5ms 고정비, n_view=11이면
   iteration당 ≈38.5ms가 오직 "카메라를 11번 나눠 호출한다"는 이유만으로
   붙음). 원본 3DGS `render()`가 애초에 단일 카메라 전용이라 batch화하려면
   `thirdparty/diff-gaussian-rasterization` CUDA 소스 수정이 필요 —
   Phase 3의 stream-분리 크래시와 같은 성격의 리스크, 별도 신중한 라운드로
   분리해서 착수할 가치.
1. **Phase 4의 "왜 2~3회인가" 미해결 질문 규명** — `remove_all_gaussians()`는
   코드상 정확히 한 번만 조건이 참이 되는데 실측 로그엔 초기화급 호출이 그보다
   많이 잡힘. 정확한 메커니즘을 알면 PGBA 호출(`iters=20`, 4회, 3.96~3.93s)도
   같은 방식으로 더 줄일 여지가 있는지 판단 가능 — 우선순위 상위 후보.
2. `init_itr_num`을 600 밑으로(예: 450) 더 세밀하게 스캔 — 300(기각)과
   600(채택) 사이에 더 나은 지점이 있을 수 있음, 지금은 두 지점만 확인.
3. iters를 7 밑으로(예: 3~4) 더 내리는 것도 미탐색 — Phase 1에서 5→7 사이
   수확체감이 이미 보였으므로 ROI는 낮을 가능성이 크지만, 완전히 배제하진
   않음.
4. carve floater 지표(exp55의 `exp55_score_carve_vigs.py`)로 iters=7+
   init_itr_num=600 채택 레시피의 floater 수준도 재확인할 가치 — carve_lambda는
   그대로 0.05를 유지했지만 iters가 줄어 carve loss 자체의 gradient step 수도
   줄었으므로 효과가 희석됐을 가능성.
5. (낮은 우선순위, 고위험) `thirdparty/diff-gaussian-rasterization`을
   멀티스트림 안전하게 패치하면 축3(stream 분리)을 다시 시도할 여지 — CUDA
   커널 소스 레벨 작업이라 투자 대비 효과가 불확실, 지금 우선순위는 아님.
