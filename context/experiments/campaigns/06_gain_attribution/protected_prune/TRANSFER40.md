# Opacity0.1 pruning의 Aria / UTMM 적용 (2026-09-27)

사용자 요청에 따라 같은 규칙을 Aria1253·UTMM square-1에 적용했다. **추가 학습은 두 번만** 실행했고 OFF는 앞선 동일 설정 실행, RPNG는 직전 pruning 검증 결과를 재사용했다. 초기화 수와 기본 preset은 변경하지 않았다.

세 장면 모두 Gaussian은 감소했지만 PSNR은 소폭 하락했다. 따라서 0.1 pruning은 개수 절감 후보이며 무손실 개선으로 주장하지 않는다.

| 장면 | Gaussian OFF→0.1 | 감소 | PSNR OFF→0.1 | ΔPSNR | mapper 초 OFF→0.1 | 시간 감소 |
|---|---:|---:|---:|---:|---:|---:|
| aria | 192,623→151,604 | 21.3% | 25.9107→25.8162 | -0.0945 | 33.25→33.08 | 0.5% |
| rpng | 357,071→159,616 | 55.3% | 25.2237→25.0709 | -0.1527 | 108.12→99.62 | 7.9% |
| utmm | 141,545→96,733 | 31.7% | 22.2231→22.1207 | -0.1024 | 37.45→36.65 | 2.2% |

## 고정 조건과 검증

40 renders/KF. Opacity < 0.1인 오래된 점만 삭제하며 최근10번의 비어 있지 않은 KF birth batch는 보호한다. Completed training render150 단위로 packet 경계에서 검사하며 마지막 입력 이후 cleanup은 없다. Densify/size-prune/KF-cap/Carve OFF. PPM init64/regular256·online-rank2.5/span2, ERVS κ16/τ₀4,3:3:6,영상별Adam,denseRGB,blurOFF,scale projection 유지.

추가 두 실행에서 보호점 삭제0,parameter/Adam moment 정렬,동일 birth CSV와view선택·admission·loss/LR순서·render/Adam총수와prefix·입력pose·평가cohort,zero-tail 감사가 통과했다. Aria4760회,UTMM3600회 render/Adam이며 RPNG9080회는 직전 결과다. 마지막 지도세대 birth−prune=최종개수도 확인했다. CPU41테스트와 저장지도별 독립평가2회가 통과했다. 단일seed·frozen causal tracker이며 실제 concurrent tracking/geometry 일반화 검증은 아니다.

Aria/UTMM의 baseline은 이전 완료 실행을 재사용했으므로 시간은 개략적인 단일-run 비교다. Aria0.5%,UTMM2.2%의 차이를 확실한 속도 향상으로 해석하지 않는다. RPNG도 반복 timing benchmark는 아니다.

## Init 증가에 대한 해석

점 개수 절감 여지는 생겼지만 init을 늘려도 같은 시간·품질이 유지된다는 근거는 아직 없다. 추가점은 생성·학습·보호기간 동안 메모리와렌더링 비용을 쓰고,낮은opacity삭제가 곧 불필요한점의 정확한 식별을 뜻하지도 않는다. 세장면 모두PSNR이약0.09–0.15dB 낮아졌다.

별도 비교를 한다면 현재0.1pruning을 고정하고 모든 장면에서 birth생성량1.25배 하나만 시험하는 가설은 가능하다. 이는 downsample공통배율0.8(init51.2/regular204.8)에 해당한다. **이번에는 실행하거나 채택하지 않았다.** 장면별파라미터를 정하지 않는다.

## 산출물

- 추가 실행과 종합 JSON: `results/campaigns/gain_attribution/protected_prune/transfer40_v1/`
- 종합: `comparison.json`; scene별 `summary.json`, `opacity01/independent_audit.json`, `source_lock.json`
- Runner: `run_protected_prune_comparison.py --dataset aria|utmm --cases opacity01 --baseline-dir .../b40_d1/{dataset}`
- 기존 RPNG 결과: [SUMMARY.md](SUMMARY.md)
