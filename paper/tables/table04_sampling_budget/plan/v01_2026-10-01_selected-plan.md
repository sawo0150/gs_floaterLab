# T4 — Update budget별 RR vs ERCB/ERVS

작성: 2026-10-01. 상태: **계획 작성 완료 / 최종 산출물 미제작**. ID는 논의용이며 최종 LaTeX 번호가 아니다.

## 목적

사용자 선택대로 기존 TeX의 예산별 sampling 비교 형태를 유지한다. 기능 제거식 ablation으로 바꾸지 않는다.

## 만들 구성

- 행: Metric / Sampling policy; 열: 15 / 30 / 60 updates per KF interval.
- RR / ERCB의 PSNR, 확보되면 SSIM/LPIPS. 전체 19 scene 평균과 dataset별 보조표를 둔다.
- 원고 기존 PSNR: RR 20.77 / 22.22 / 22.88, ERCB 21.39 / 22.33 / 23.11. 이것은 과거 fixed-topology replay 출처 확인용이며 새 최종 결과로 재선언하지 않는다.
- F9는 같은 regime·같은 run의 곡선, T4는 그 endpoint를 사용한다.
- 현재 mapper의 ERVS 15/40 결과는 별도 panel로 추가할 수 있다. 예산과 sampler가 다른 숫자를 기존 15/30/60 칸에 대입하지 않는다.

## 비교 조건과 해석

원본 runner/manifest 확인: `3dgs-custom-exp77-budget-5070ti-repro/train.py`를 exp77 wrapper가 호출한다. RR=`causal_rr`, ERCB=`relative_floor_interval_softmax_rr`, beta=log(3), block_size=8, seed0, stride20, resolution factor4, RGB-only, llffhold-8. benchmark-B는 densify_until_iter=0인 fixed-topology다. 후속 paper-figures는 densify-on이며 24 checkpoint/114 jobs다. 이것들은 현재 cumulative per-view ERVS와 동일 구현이 아니다. 원본 repo는 현 머신에 없어 내부 클래스 전체 대조·원본 commit 재실행은 아직 미완료다.

[공통 프로토콜](../../../plan/visual_assets/protocol.md) · [원본 확인 기록](../../../plan/visual_assets/source_audit.md) · [방법 후보](../../../plan/visual_assets/baseline_registry.md)

## 확인한 원본과 관련 자료

- [prepare_manifest.py](../../../../context/experiments/ERCB_ablation/benchmark-B/prepare_manifest.py)
- [manifest.json](../../../../context/experiments/ERCB_ablation/benchmark-B/evidence/manifest.json)
- [summary.md](../../../../context/experiments/ERCB_ablation/benchmark-B/summary.md)
- [run_training.py](../../../../context/experiments/exp77/run_training.py)
- [prepare_view_ordering.py](../../../../context/experiments/ERCB_ablation/paper-figures/prepare_view_ordering.py)
- [SUMMARY.md](../../../../context/experiments/campaigns/06_gain_attribution/unified_rr_ervs/SUMMARY.md)
- [SUMMARY15.md](../../../../context/experiments/campaigns/06_gain_attribution/unified_rr_ervs/SUMMARY15.md)

## 다음 제작 작업

원본 repo snapshot/hash 복원 가능 여부와 raw curves 접근을 확인한다. 기존 코드를 읽어 확인한 범위와 실행 재현을 구분해 source_audit에 기록한다. 신규 실험은 campaign-first로 만들며 과거 horizon 비율 topology schedule을 production에 이식하지 않는다.

## 산출물 및 완료 기준

- 데이터 출처: run ID, code/config hash, scene/evaluation IDs, checkpoint, budget unit을 provenance에 보존한다.
- Figure: scripts → output 검토본 → PDF 재렌더 확인 → current의 PDF/SVG/PNG/caption/provenance.
- Table: raw metric 참조 → 경량 집계 데이터 → output의 TeX/preview → 수치·단위·평균 확인 → current.
- 값이 없는 칸은 —(미측정), 실패 F, 적용 불가 NA, 목표 미도달 NR로 구별한다.
- 이번 단계는 MD 계획만 작성한다. GPU 실험·논문 TeX 삽입·휴먼테크 원본 교체는 수행하지 않았다.

## 값 미삽입 표 틀

| Metric | Policy | 15 updates/interval | 30 updates/interval | 60 updates/interval |
|---|---|---|---|---|
| PSNR ↑ | RR | — | — | — |
| PSNR ↑ | ERCB (original replay) | — | — | — |
| SSIM ↑ | RR | — | — | — |
| SSIM ↑ | ERCB (original replay) | — | — | — |
| LPIPS ↓ | RR | — | — | — |
| LPIPS ↓ | ERCB (original replay) | — | — | — |
