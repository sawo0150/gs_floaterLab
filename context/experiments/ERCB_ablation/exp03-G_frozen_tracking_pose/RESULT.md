# exp03-G — frozen tracking-pose ERCB isolation

날짜: 2026-09-15  
상태: **3-seed × 2-scene 완료; 양수 진단이지만 strict 근거 아님**

## 결과

GT absolute pose로 mapping/evaluation pose를 고정하고 native online
birth/densify/prune를 남긴 채 dense-role RR과 interval relative-floor ERCB를 비교했다.

| Scene / budget | Seeds | ERCB−RR fixed held-out PSNR | 승수 |
|---|---:|---:|---:|
| RPNG table_07 / q3 | 3 | **+0.2546 ± 0.1852 dB** | 3/3 |
| UTMM square-1 / q15 | 3 | **+0.0588 ± 0.0196 dB** | 3/3 |

표의 ±는 seed 간 sample standard deviation이다. 모든 run은 sensor-EOS zero-tail을
통과했다. RPNG/UTMM seed0의 Adam 및 KF/dense service는 각각
`612/306-306`, `1009/433-576`으로 pair-match됐다.

## 판정

Pose feedback을 제거하면 ERCB delta가 일관되게 양수로 돌아왔다. 다만 frontend packet과
native topology는 arm별 실행에 따라 여전히 달랐고, RPNG final Gaussian 수도
`467,330 vs 478,909`로 갈렸다. 따라서 이는 **pose/topology 폐루프가 실패 원인의 일부**라는
진단이지 strict VIGS에서 ERCB 우위가 확립됐다는 결과가 아니다. 이를 더 분리하기 위해
exp03-H에서 frontend packet과 topology 결정까지 공유했다.

Machine-readable 결과는 [evidence/summary.json](evidence/summary.json)에 있다.
