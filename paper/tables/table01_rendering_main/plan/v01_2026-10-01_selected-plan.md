# T1-main — Dataset 평균 rendering 비교

작성: 2026-10-01. 상태: **계획 작성 완료 / 최종 산출물 미제작**. ID는 논의용이며 최종 LaTeX 번호가 아니다.

## 목적

세로 Dataset / Method, 가로 metric 형태로 동일-work 렌더링 성능을 정리한다. Gaussian 수를 함께 보고한다.

## 만들 구성

- 열: Dataset | Method | PSNR ↑ | SSIM ↑ | LPIPS ↓ | #Gaussians (k).
- RPNG / UTMM / Aria 블록마다 방법 행을 반복한다. 각 행은 scene별 metric 평균을 다시 산술평균한 값이다.
- VIGS-SLAM/Ours를 주 비교로 두고, 추가 baseline의 측정값은 빈칸(—)으로 남긴다.
- RGB-only와 RGB+IMU를 그룹/각주로 구분한다. RGB-D 필수 방법은 같은 그룹에 넣지 않는다.
- #G는 평가 지도 checkpoint의 잔존 수 평균이다. 무조건 작을수록 좋은 metric이라는 ↓ 표시는 붙이지 않는다.
- 표의 구체적 빈칸 틀은 `layout.md`, 방법별 선정 근거는 공통 baseline registry를 참조한다.

## 비교 조건과 해석

40 renders/KF는 같은 frontend/KF stream일 때만 동일 총 학습량으로 이어진다. 전체 시스템마다 KF 수가 다르면 scene별 절대 render budget을 맞추거나 차이를 명시한다. 추가 기하 render와 Adam 횟수는 공통 계산량 기록에 남긴다. 타 논문 발표 숫자는 다른 split/해상도/후처리 조건을 감사하기 전 이 표에 채우지 않는다. 성공 scene만 조용히 바꿔 평균하지 않고 n/N와 실패/미실행을 공개한다.

[공통 프로토콜](../../../plan/visual_assets/protocol.md) · [원본 확인 기록](../../../plan/visual_assets/source_audit.md) · [방법 후보](../../../plan/visual_assets/baseline_registry.md)

## 확인한 원본과 관련 자료

- [5_results.tex](../../../latex/sec/5_results.tex)
- [SUMMARY.md](../../../../context/experiments/campaigns/06_gain_attribution/main_validation/SUMMARY.md)
- [SUMMARY.md](../../../../context/experiments/campaigns/06_gain_attribution/geometry_main_validation/SUMMARY.md)

## 다음 제작 작업

공통 scene 목록·평가 split·최종 Ours·budget을 고정하고 raw run별 metric/#G를 수집한다. T1-supp와 한 데이터 원본에서 생성한다.

## 산출물 및 완료 기준

- 데이터 출처: run ID, code/config hash, scene/evaluation IDs, checkpoint, budget unit을 provenance에 보존한다.
- Figure: scripts → output 검토본 → PDF 재렌더 확인 → current의 PDF/SVG/PNG/caption/provenance.
- Table: raw metric 참조 → 경량 집계 데이터 → output의 TeX/preview → 수치·단위·평균 확인 → current.
- 값이 없는 칸은 —(미측정), 실패 F, 적용 불가 NA, 목표 미도달 NR로 구별한다.
- 이번 단계는 MD 계획만 작성한다. GPU 실험·논문 TeX 삽입·휴먼테크 원본 교체는 수행하지 않았다.

## 표 틀

[방법 행과 sequence별 빈칸을 포함한 layout](layout.md).
