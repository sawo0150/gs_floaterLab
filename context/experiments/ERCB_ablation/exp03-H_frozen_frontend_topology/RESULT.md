# exp03-H — frozen frontend packet + shared topology isolation

날짜: 2026-09-15  
상태: **2-scene seed0 완료; trace 통제 성공, ERCB 이득 미복구·NO-GO**

## 질문

exp03-G보다 한 단계 더 통제해 RR와 ERCB가 정확히 같은 causal frontend packet과 같은
Gaussian topology 결정을 받을 때, 과거 3dgs-custom fixed replay의 큰 저예산 ERCB
이득이 VIGS에서도 복구되는가?

## 구현 및 계약

- mapper가 실제 받은 KF RGB/depth/normal/GT pose와 dense record를 CPU tensor packet으로
  한 번 기록하고 두 arm에서 exact replay했다.
- keyframe birth는 해당 causal packet에서 즉시 수행했다.
- native RR reference의 densify/prune 생존 stable point ID와 신규 Gaussian 초기값을
  기록하고, 비교 arm은 같은 packet 경계에서 같은 topology 사건을 적용했다.
- unified B1, KF RGBD+normal full update, dense RGB appearance+opacity update, q physical
  packet credit, fixed 1.5× sensor budget, zero-tail을 유지했다.
- GT pose와 reference topology를 쓰는 **diagnostic**이며 strict 결과가 아니다.

초기 v1은 trace 저장 I/O가 packet↔optimizer interleaving을 바꿔 두 번째 topology 직전
stable ID가 `95,435 vs 115,361`로 실패했다. packet capture와 topology capture를 나눈
v2도 세 번째 사건에서 `140,149 vs 143,470`으로 실패했다. 두 실패 output은 보존했다.
v3는 topology 사건을 iteration/frame fraction이 아닌 관측된 causal packet count에
결박했다. VIGS 구현 커밋은 `2eaa5386`, `03baae1e`, `cd27decf`다.

## 결과

Primary는 mapping-excluded fixed held-out이다.

| Scene / budget | RR PSNR | ERCB PSNR | ERCB−RR | Adam RR/ERCB | KF–dense RR / ERCB | Packet | Topology | Final GS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| UTMM square-1 / q15 | 17.8230 | 17.8844 | **+0.0614** | 1012/1011 | 392–620 / 392–619 | 70/70 | 3/3 | 162,792/162,792 |
| RPNG table_07 / q3 | 19.7574 | 19.6960 | **−0.0614** | 612/612 | 187–425 / 186–426 | 204/204 | 1/1 | 579,323/579,323 |

- 두 pair 모두 frontend packet 수와 내용, topology event packet/before/after trace,
  final Gaussian 수, pending birth 0, sensor-EOS zero-tail을 검증했다.
- UTMM은 wall budget 경계에서 ERCB가 dense step 1회 적었고, RPNG는 총 step은 같지만
  causal pool population clock 때문에 KF 1회를 dense 1회로 바꿨다. 따라서 완전한
  optimizer-service sequence 고정은 아니지만 차이는 각 1회다.
- 두 장면 fixed PSNR delta 평균은 `−0.00002 dB`, 사실상 0이다.

## 왜 과거 이득이 복구되지 않았나

이번 결과로 **online pose 오차, frontend packet 차이, final topology 개수 차이만이 원인**이라는
가설은 기각된다. 남은 핵심 차이는 scheduler가 보는 문제 자체다.

1. 과거 fixed replay는 static homogeneous RGB pool과 fixed initialization/topology에서
   한 arrival event가 평균 UTMM 17.65장, RPNG 8.98장을 한꺼번에 열었다. ERCB가
   interval 간 부족한 service를 재배분할 여지가 컸다.
2. 현재 VIGS는 keyframe마다 dense를 최대 1장 admit하므로 대부분의 dense KF bracket이
   singleton이다. 실제 H의 dense candidate/interval은 UTMM `112/110`, RPNG
   `388/388`이다. interval score가 사실상 view score로 퇴화한다.
3. VIGS update는 homogeneous하지 않다. KF는 RGBD+normal 및 geometry, dense는
   appearance+opacity만 담당한다. ERCB는 dense 내부 interval exposure만 조절하며
   현재 loss 감소량이나 geometry 기여도를 측정하지 않는다.
4. q3 RPNG에서 dense 388장에 dense update가 425/426회뿐이고, relative-floor ERCB도
   최소 service 0·under-4 286장(RR 247장)이었다. 이 구현은 새 view별 최소 update를
   보장하는 coverage scheduler가 아니다.

따라서 과거 결과는 틀렸다기보다 **fixed static replay에서의 저예산 interval allocation
효과**이고, 현재 one-loop VIGS의 동적 singleton admission과 heterogeneous loss에는 그대로
전이되지 않는다.

## 판정 및 다음 단계

ERCB를 production RR 대신 채택하지 않는다. K/gamma/scene별 budget sweep도 하지 않는다.
다음으로 볼 가치가 있는 단일 구조 축은 selector 파라미터가 아니라, causal admission에서
한 KF bracket의 dense view를 1장보다 더 모아 **실제 interval unit을 복원**하고 각 admitted
view의 최소 service debt를 명시하는 것이다. 그 뒤에만 residual/learning-progress utility를
추가한다. optimizer-to-packet service sequence까지 완전히 고정한 검증은 필요할 때 별도
diagnostic으로 남긴다.

Machine-readable 결과는 [evidence/summary.json](evidence/summary.json)에 있다.
