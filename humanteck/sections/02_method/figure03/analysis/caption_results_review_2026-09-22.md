# Fig.2에 따른 캡션·Results 문장별 검토 — 2026-09-22

대상: `humanteck/HumanTeck_Song_s_intern/paper.tex` 전체 활성 본문을 읽고,
Fig.2와 Results and Conclusion을 원본 실험 기록에 대조했다.
**이번 산출물은 검토안이다. 원고·현행 캡션·그림은 수정하지 않았다.**
영문 수정안: `caption_results_proposal_2026-09-22.tex`.

## 먼저 해결할 불일치

원고 127–132행은 예전 두 이미지 caption이다. current/caption.md 및 제작
스크립트에는 이미 (a)/(b) caption이 있어 서로 다르다. 원고가 현재 파일에
기록된 버전과 언제/어떻게 달라졌는지는 확인하지 않았으며, 원고가 자동으로
현행 캡션과 일치한다고 가정하면 안 된다. 수정안 채택 시 원고·current·스크립트
CAPTION을 함께 갱신해야 한다.

## 캡션 문장별

1. `Photometric convergence on RPNG ... table_06.`
   - 장면과 목적 설명은 유지한다. 이 그림의 convergence는 growing-map의
     품질 진행이며 순수 optimizer의 수렴률 정리나 wall-clock 속도가 아니다.
   - RPNG 인용키 `chen2023monocular` 유지.
2. `Insets show intermediate renderings ... (left) and ours (right).`
   - 수정 필요. 실제는 (a) 곡선, (b) VIGS-SLAM/ours/GT 세 열이며 ours는 가운데다.
   - (a)의 평균 held-out PSNR과 19 dB 아래 축척 압축을 짧게 설명한다.
   - (b)는 두 방법의 1.4k iteration 결과와 GT·확대 영역을 설명한다.
     그림에 방법명이 있으므로 좌우 위치를 캡션에서 반복할 필요는 없다.
   - VIGS-SLAM의 `zhu2026vigs` 인용 유지. GT는 학습 checkpoint 결과가 아님.
3. `Our method first reaches ... with 1,000 fewer mapping iterations.`
   - 1000 차이는 정확하다. 다만 evaluated/observed가 빠져 연속 구간까지
     확인한 최초 도달이나 실제 최대값처럼 읽힐 수 있다.
   - 별표의 뜻은 `First evaluated attainment of the baseline's highest observed PSNR.`로
     짧게 남기고 구체적인1400/2400/23.28 수치는 Results로 옮긴다.
   - 축은19 dB 아래도 표시하므로 omitted/truncated가 아닌 compressed가 정확하다.

## Results 문장별

| 원고 문장 | 판단 | 수정 방향 |
|---|---|---|
| 139–140: We evaluate on ... wearable glasses ARIA. | 데이터셋 순서 유지. 표현 정리 | mapping quality를 명시하고 our Aria sequences로 줄인다. 이 평가의 Carve OFF를 여기에 쓴다. |
| 141: Under matched optimization step budgets ... +1.60/+0.52/+2.45. | 수치는 정확, budget 명칭은 틀림 | shared tracker outputs / matched total training-render budgets. 평균은 scene-averaged held-out PSNR로 명시한다. |
| 142: Our method requires fewer mapping iterations ... | 대표 장면의 관측을 전체 일반 결론처럼 쓰지 않기 | Fig.2(a)의555개 고정 평가뷰를 먼저 정의하고, baseline 최고 관측값23.28dB에 대한 first evaluated attainment 1400 vs2400을 쓴다. |
| 143: After the same number ... clearer text and finer details ... | 관찰과 (b)를 직접 연결 | At1400 iterations, the selected view in Fig.2(b) shows clearer lettering ...로 한정한다. 모든 frame에서의 개선이나 같은 wall-time이라는 의미로 확장하지 않는다. |
| 145: We present ... achieving faster ... appearance and geometry ... | 앞 결과와 반복되며 geometry의 실증 범위가 불명확 | 다음 방법 요약문과 합쳐 framework의 세 구성요소를 요약한다. 이 photometric figure로 geometric convergence 향상을 주장하지 않는다. |
| 146: Our system introduces view management ... Carve ... | 방법 설명 자체는 유지 가능 | view-set growth, entropy-regularized sampling, opacity-directed Carve를 한 문장으로 요약한다. |
| 147–148: This approach provides a foundation ... | 응용 동기로 타당하나 길음 | limited computation에서 incremental map refinement의 기반이라는 문장으로 압축한다. 실제 Aria 기기 실시간 통합을 완료했다고 읽히지 않도록 한다. |

## 사실 대조

- 공식 결과: `context/experiments/benchmark_custom/metric_benchmark_v2_fixed_eval_20260917/summary.md`.
  RPNG8개+1.598585, UTMM7개+0.517175, Aria2개+2.452740 dB.
  각 장면의 평가뷰 평균 PSNR 차이를 장면별 동일 가중치로 평균했다.
  17개 ours runtime 모두 causal_carve_enabled=False임을 직접 확인했다.
- table_06 재계측 runtime: 총 training renders는 양쪽34437로 같고,
  optimizer steps는 ours2714 / baseline2719다. 따라서 동일 optimizer step budget은 부정확하다.
- 같은1400 checkpoint에서도 ours17807 / baseline17680 training renders다.
  이 checkpoint의 input prefix는 양쪽1546으로 같다. 따라서 동일 iteration 비교는
  가능하지만 동일 rendering work/time으로 바꾸어 표현하지 않는다.
- 원본 curve: baseline best23.2813446526@2400,
  ours23.3186030551@1400. 다음1600/1800에서는23.22523/22.98178로 재하락한다.
  1000 fewer iter.는 최초 저장 checkpoint 도달 차이다. 지속 수렴이나 속도 배수는 아니다.
- curve의555뷰 평균@1400: baseline22.65482 / ours23.31860.
  사진 frame1420의 전체 이미지 PSNR@1400: baseline26.93750 / ours27.68292.
  서로 다른 집계이므로 사진의 PSNR과 curve 값이 같다고 설명하지 않는다.
- 평가 스크립트는 전체 궤적의 고정 held-out 집합을 checkpoint마다 공통 평가 pose로
  렌더링한다. 따라서 coverage·pose 변화도 반영하는 지도 품질의 진행이다.
  평가용 post-EOS pose 사용과 학습 시 미래 pose를 쓰는 것은 별개이며,
  이 도판으로 순수 optimizer/ERVS 단독 인과 효과를 주장하지 않는다.

## 본문과 캡션의 역할

캡션: 장면·패널 구분·1.4k 사진·축척 변경·별표 정의.
Results: 평가 설정·정량 개선·555뷰 정의·1400/2400의 구체적 근거·선택 사진 관찰.
고정 평가 pose, snapshot 간격, scene 탐색 등의 상세 provenance는 위 기록과 긴 논문의
평가 절에 남긴다. 두 쪽 초고 캡션에 나열하지 않는다.

## 전체 TeX 연결상 남는 범위

Abstract/Introduction/제목은 photometric+geometric convergence를 함께 내세운다.
현재 Fig.2와 +PSNR 수치의 Carve OFF 결과는 photometric 부분의 근거다.
Carve의 geometry 개선을 결과로 주장하려면 별도 geometry/region-GT 검증을 연결해야 한다.
이는 이번 Fig.2 caption에서 geometry 표현을 늘려 해결할 수 있는 문제가 아니다.
기존 Abstract/Method의 일반 영문 문법까지 일괄 수정하지 않았고, 이번 요청인
figure와 Results의 의미·근거 일치에 집중했다.

수정안은 아직 조판하지 않았다. PDF 크기나 도형 배치를 건드릴 필요는 없으며,
원고 반영 시 caption·본문 길이로 인한 줄바꿈/페이지 배치만 확인하면 된다.
