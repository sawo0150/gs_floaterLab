# T2-main — 동일 시간 Dataset 평균 비교

작성: 2026-10-01. 상태: **계획 작성 완료 / 최종 산출물 미제작**. ID는 논의용이며 최종 LaTeX 번호가 아니다.

## 목적

tracking을 같이 켠 1×/1.5× 시간 조건에서 품질·지도 크기·지연을 dataset 평균으로 비교한다.

## 만들 구성

- 열: Dataset | Time allowance | Method | PSNR ↑ | SSIM ↑ | LPIPS ↓ | #Gaussians(k) | Input lag p95(s).
- 1×와 1.5×를 분리한다. 방법 후보는 T1과 같고 현재 실제 자료는 VIGS-SLAM/Ours다.
- 평균에 포함된 sequence 수 n/N를 dataset label 또는 각주에 표시한다.
- 시간이 부족하면 렌더 수/실제 종료시간은 T2-supp로 보내되 지연 조건은 본문에서 감추지 않는다.
- 현재 RPNG/UTMM은 대표 1개씩이므로 이를 전체 dataset 평균이라고 부르지 않는다.

## 비교 조건과 해석

같은 입력 시간 허용, 하드웨어, warmup 범위, zero-tail을 공유한다. 1.5×는 입력 재생을 느리게 한 조건이며 센서 속도 1.5배가 아니다. 현재 mapper는 deadline에 중단하지만 tracking은 늦게 끝나는 run이 있어 전조건 real-time 달성이라고 쓰지 않는다. 최신 live는 D3를 포함하며 T1과 Ours 정의 일치 여부를 확인한다.

[공통 프로토콜](../../../plan/visual_assets/protocol.md) · [원본 확인 기록](../../../plan/visual_assets/source_audit.md) · [방법 후보](../../../plan/visual_assets/baseline_registry.md)

## 확인한 원본과 관련 자료

- [README.md](../../../../context/experiments/campaigns/06_gain_attribution/fifo_live/README.md)
- [LIVE_FIFO_COMPARISON.md](../../../../../VIGS-SLAM-custom/docs/LIVE_FIFO_COMPARISON.md)

## 다음 제작 작업

현재 16 live run의 verified metrics를 초안 자료로 연결한다. 전체 sequence 확대 전에는 representative-scene comparison으로 표기한다. T2-supp와 한 데이터 원본을 사용한다.

## 산출물 및 완료 기준

- 데이터 출처: run ID, code/config hash, scene/evaluation IDs, checkpoint, budget unit을 provenance에 보존한다.
- Figure: scripts → output 검토본 → PDF 재렌더 확인 → current의 PDF/SVG/PNG/caption/provenance.
- Table: raw metric 참조 → 경량 집계 데이터 → output의 TeX/preview → 수치·단위·평균 확인 → current.
- 값이 없는 칸은 —(미측정), 실패 F, 적용 불가 NA, 목표 미도달 NR로 구별한다.
- 이번 단계는 MD 계획만 작성한다. GPU 실험·논문 TeX 삽입·휴먼테크 원본 교체는 수행하지 않았다.

## 표 틀

[방법 행과 sequence별 빈칸을 포함한 layout](layout.md).
