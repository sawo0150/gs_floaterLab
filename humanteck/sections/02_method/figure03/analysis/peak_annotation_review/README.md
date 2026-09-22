# Fig.3 수평선 문헌 조사와 결정안

2026-09-21. 사용자가 논문 figure를 직접 보고 비단조 PSNR 곡선의 iteration 차이
표시 방식을 판단해 달라고 요청했다. 본 기록은 원문 figure의 관찰과 우리 데이터에
대한 제안을 구분한다. 신규 학습·GPU 평가 없음. 기존 선택본은 수정하지 않았다.

## 권고

**Baseline의 best observed PSNR을 목표로 삼되, 긴 수평선 대신 선택한 실제
checkpoint 두 점에서 위로 올린 짧은 가로 괄호를 사용한다.** Figure에 넣을 주 비교는
Ours2000과 baseline2400의 **400 fewer iter.**를 권고한다. Ours는2000부터 이후
저장 checkpoint에서도 기준 이상이다. 최초 sampled 도달1400을 쓰는1000-iteration
비교는 수치상 가능하지만,1600·1800의 재하락 때문에 주 시각 강조로는 덜 적합하다.

[추천 검토안: 400 iter](frame1420_remaining_checkpoints.png) ·
[첫 도달 검토안: 1000 iter](frame1420_first_sampled.png) · [수치](metrics.json)

두 검토안 모두 원래 curve와 frame1420 inset, 낮춘 높이, 하단 가운데 범례를 보존한다.
점은 실제 저장 checkpoint다. 가로 괄호의 y위치는 annotation용이며 동일 PSNR선이
아니다. 두 점의 y값이 달라도 왜곡되지 않도록 실제 점에서 수직 guide를 올린다.
`Same PSNR`, `converged`, `speedup` 대신 target 품질 이상의 지도에 필요한
mapping iteration 차이라고 해석한다. 모든 미래 시점의 유지나 wall time 단축을
입증하는 것은 아니다.

## 실제 figure 확인

원문 PDF를 다운로드해 Poppler로 페이지 렌더링한 뒤 시각적으로 확인했다.
웹 PDF screenshot 도구가 이미지 대신 텍스트 참조만 반환해 로컬 렌더로 보완했다.
3DGS² Fig.4는 arXiv 원본 figure PNG를 직접 열어 확인했다.
원본과 페이지 PNG는 `references/convergence_review_20260921/`에 보관한다.

| 논문/figure | 실제 축·배치 | 수평선/가속 표현 | 우리에게 적용할 부분 |
|---|---|---|---|
| [HAMMER v2 Fig.5, p.7](https://arxiv.org/pdf/2501.14147v2#page=7) | Home/Basement 두 패널. x Map Optimization Step, y Evaluation PSNR. 하단 공유 범례 | 곡선 자체로 map quality evolution을 비교. 기준 PSNR 수평선이나 교점 간 가속 화살표 없음 | 현재 incremental 평가 범위와 가장 가까움. coverage 포함 map-quality curve의 근거이며 가속률 공식의 근거는 아님 |
| [3DGS-LM Fig.1, p.1](https://lukashoel.github.io/3DGS-LM/static/3DGS-LM_paper.pdf#page=1) | x Time(s), y PSNR(dB), 여러 baseline/LM 곡선. 오른쪽 동일 시간의 이미지·확대 crop | 곡선 일부에53s/87s/109s의 짧은 점선 가로 괄호. baseline의 작은 하락을 그대로 표시 | **시각적 표현은 가장 직접적인 참고.** 긴 전체 수평선 대신 작은 구간·분명한 endpoints. Caption/본문에서 first crossing 또는 유지 조건의 공통 판정 규칙은 확인되지 않음 |
| [Turbo-GS v1 Fig.1/2, p.1–2](https://arxiv.org/pdf/2412.13547v1#page=1) | Fig.1 x training seconds, y LPIPS; Fig.2 x iterations, y LPIPS. Fig.1에 실제 이미지와 소요 시간 병기 | 명시적인 동품질 수평선 없이 곡선과 시간·품질 수치로 비교. Fig.2에서는 적은 iteration으로 더 낮은 LPIPS를 달성하는 패턴 | 실제 시간과 iteration은 각각 보고할 수 있음. PSNR·LPIPS·loss를 서로 혼동하지 말 것. 이 기록은v1 figure 번호 기준 |
| [3DGS² v2 Fig.4](https://arxiv.org/html/2501.13975v2#S5) | 여섯 학습 이미지와 local optimization loss 감소 곡선. x 약1–60 step, 작은 loss 값의 y축 | 한 번의 교점 화살표보다 loss 감소 속도와 잔여 오차 곡선을 보여줌 | 고정 목적함수의 local optimizer convergence 예시. online held-out PSNR의 fluctuation을 없애는 근거로 사용할 수 없음 |
| [Taming 3DGS Fig.1, p.1](https://humansensinglab.github.io/taming-3dgs/docs/paper_lite.pdf#page=1) | 왼쪽47min/8min 실제 이미지 비교. 오른쪽 x Gaussian 수(M), y PSNR | 오른쪽 선은 학습 trajectory가 아닌 model-budget/quality 비교 | 예산별 결과를 연결한 선과 한 run의 수렴 곡선 구분. 우리의15/30/60 endpoint 표를 수렴 curve로 바꾸는 근거가 아님 |

3DGS-LM의 실제 figure에는 작은 시간 괄호가 있다는 것을 이번 시각 검토로 확인했다.
따라서 앞선 ‘수평선은 빼자’는 제안은 **전체 plot을 가로지르는 threshold 선을
빼자는 것으로 한정**하고, 명시적인 checkpoint 비교 괄호는 사용할 수 있다고 판단한다.
관측된 문헌 범위를 넘어 ‘모든 논문이 이 방식을 쓴다’고 주장하지 않는다.

HAMMER의 held-out evaluation은 장치당10개 frame이며 전체 장면을 포괄한다.
동일 페이지 Table I는 별도 Replica 학습 view 평가임을 구분해야 한다.
이는 우리555-view 평가를 training PSNR로 바꿀 이유가 되지 않는다.

## 우리 수치에 적용

원시 데이터: `results/figure03_scene_search_20260921/rpng/table_06/evaluation/curves.json`.
기준은 저장된 baseline checkpoint의 최고값이다. 200-step 사이의 진짜 최대값은
관측하지 않았으므로 `best observed`라고 설명한다.

| 항목 | iteration | PSNR (dB) | baseline 최고 대비 |
|---|---:|---:|---:|
| Baseline best observed | 2400 | 23.281345 | 0 |
| Ours first sampled attainment | 1400 | 23.318603 | +0.037258 |
| Ours 다음 checkpoint | 1600 | 23.225231 | −0.056114 |
| Ours 그다음 checkpoint | 1800 | 22.981779 | −0.299566 |
| Ours 이후 모든 저장점에서 기준 유지 시작 | 2000 | 23.980361 | +0.699016 |

Ours의 선형 보간 교점은 약1387.04(up),1479.81(down),1860.00(up)으로 여전히
세 개다. Baseline 최고값으로 바꾸면 baseline의 peak는 하나지만 Ours의 fluctuation이
사라지는 것은 아니다. 따라서 최고값 선택만으로 교점의 모호성이 해결되지는 않는다.

첫 도달1400은 정확히 관측한 checkpoint지만 기준 초과가0.037 dB이고 이후 하락이
명백하다. 통계적 유의성이나 이 차이가 노이즈라는 판단은 하지 않는다. 첫 도달의
일시적 성격을 고려해 주 annotation에는2000을 권고한다.

2000 선택 규칙은 `min{k_i : Q_ours(k_j) >= q_best for every stored j >= i}`이다.
이는 문헌의 표준을 인용한 것이 아니라 **이번 유한 관측열에서 정한 사후 진단**이다.
checkpoint 사이의 하락을 배제하지 못하며, 미래에도 유지된다는 보장은 아니다.
이를 보편적 수렴 속도 지표로 사용할 경우 전체 scene·복수 run과 사전 evaluation
protocol이 필요하다. 현재는 대표 그림의 설명용 비교다.

## 축과 주장 범위

사용자 의도대로 x축은 mapping iterations를 유지한다. 400/2400=16.7%라는
iteration 절감률은 계산할 수 있지만 이 대표 장면의 수치를 wall-clock speedup으로
바꾸지 않는다. 원본 로그에서 Ours2000은25379 renders/input prefix1997,
baseline2400은30381 renders/input prefix2341이다. 서로 다른 입력 진행 상태이며
전체 run rendering budget 일치가 checkpoint별 동일 상태를 뜻하지 않는다.
우리 주장은 growing-map의 전체 품질 진행이고 ERCB만의 인과적 optimizer 가속은 아니다.

## 추천 캡션 추가 문장

> *The bracket compares the baseline checkpoint with the highest observed
> PSNR (2,400 iterations) against the earliest stored checkpoint from which
> ours remains above that PSNR at every subsequent stored checkpoint
> (2,000 iterations). This is a comparison of mapping iterations, not wall-clock time.

원래 캡션의555 held-out views, frame1420,800/1400/2600 inset,상하 arm 설명은 유지한다.
해당 유지 조건을 캡션에 담을 지면이 없으면 **400 fewer iter. 숫자까지 빼고**
HAMMER처럼 원시 곡선·세 시점 이미지만 두는 것이 설명 없는 숫자를 넣는 것보다 낫다.

## 제외한 대안

- Baseline final: 마지막 한 점이 peak보다 낮아 비교 의미가 endpoint 하락에 의존함.
- Baseline peak의 첫 교점을 수평선 전체로 연결: Ours의 세 교점이 남음.
- 누적 최고값 envelope를 raw PSNR로 대체: online 현재 map 품질 하락이 가려짐.
- Moving average로 교점을 유일하게 만듦: window 선택이 도달 시간을 바꾸므로 회피.
- 각 방법의 자기 최종/최고 PSNR의98%: 서로 다른 목표 품질이며 dB의 비율은
  선형 이미지 정확도 비율도 아님. 이번 조사에서 검증한 기준으로 채택하지 않음.

## 파일·검증

두 SVG는 선택본에 annotation만 추가한 review 파일이다. main SVG/PDF는 보존했다.
코드: `scripts/review_peak_annotations.py`. [자동 검증](validation.json).
Fig.3의 입력 source hash, 원시28점, 내장 image6개 동일성을 검사하고 PNG를 확인했다.
