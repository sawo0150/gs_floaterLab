# T1/T2 공통 sequence 목록

2026-10-01. 본문 dataset 평균과 부록 sequence별 표가 공유할 예정 목록이다. 아래는 전체 대상 후보이며 모두 최신 코드로 실행 완료되었다는 뜻이 아니다.

| Dataset | Sequence |
|---|---|
| RPNG | table_01, table_02, table_03, table_04, table_05, table_06, table_07, table_08 |
| UTMM | ego-centric-1, ego-centric-2, ego-drive, fast-straight, slow-straight-1, slow-straight-2, square-1, square-2 |
| Aria | aria1253, aria1253rot, aria301_12F, aria301_305 |

- 과거 benchmark-B와 dense-supervision replay manifest에는 UTMM slow-straight-1을 제외한 19 scenes가 있다. missing export/실행 실패 기록을 보존하며 표에서 조용히 삭제하지 않는다.
- 현재 actual tracking FIFO에는 aria1253, table_06, square-1, aria1253rot 네 sequence만 있다. RPNG/UTMM 전 dataset 검증이 아니다.
- Aria1253와 rot는 독립적인 모든 환경을 대표하는 두 scene으로 가정하지 않는다. 같은 장소의 trajectory variant 여부를 metadata에 기록한다.
- 추후 파일의 실제 scene alias와 이 표의 이름을 manifest로 매핑한다. raw path와 논문 표시명을 구분한다.
- 각 scene의 frame count, duration, resolution, train/eval UID, metric pose 출처, 실패/미실행 사유를 수집한다.
- 최종 포함 목록을 먼저 고정한 뒤 같은 paired cohort로 mean을 계산한다. 일부 scene 제외 시 n/N 및 이유를 main/supp에 모두 표시한다.

출처: [VIGS-SLAM의 sequence별 rendering 표](https://arxiv.org/html/2512.02293v2), 로컬 `context/experiments/ERCB_ablation/benchmark-B/evidence/manifest.json`, `context/experiments/campaigns/06_gain_attribution/fifo_live/README.md`.
