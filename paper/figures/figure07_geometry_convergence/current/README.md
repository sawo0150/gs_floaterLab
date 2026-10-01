# 실제 중간 지도 진단

실제 immutable checkpoint 14개에서 독립 수작업 region metric을 계산했다. 처음부터 두 방법이 공유한 camera frusta의 고정 region(전체 annotation의71.8%)을 사용한다. 관측·지도 확장 때문에 지표가 단조롭게 감소하지 않음을 보존한다. Surface completeness/accuracy 또는 시간축 결과는 아직 아니다.

`figure.pdf`, `figure.svg`, `figure.png`는 `analysis/measured_region_curve.csv`에서 생성한다. 수작업 reference는 평가 전용이며 mapper에 제공하지 않았다.
