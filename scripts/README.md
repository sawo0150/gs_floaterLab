# scripts/

| 폴더 | 성격 | 내용 |
|---|---|---|
| `pipeline/` | 데이터 생성 | 원본 VRS → OpenMAVIS SLAM → RGB 3DGS 학습 데이터 (`run_full_pipeline.sh`, 상세는 `data/README.md`) |
| `experiments/` | 실험 실행 | `run_expNN_*.sh` (학습 30k). 결과는 `results/experiments/`에 생성됨 |
| `diagnostic/` | 진단 | Round 진단 스크립트 (zlayer/perturbation/plateau 시각화 등) + `run_round*.sh`. 출력은 `results/diagnostic/`, `results/rounds/` |
| `analysis/` | 결과 분석 | `read_psnr.py` (tfevents에서 PSNR 추출), plateau coverage/검증 |
| `anchors/` | 앵커 생성 | monodepth 추론(`inference_monodepth.py`), plateau 앵커 저장(`save_anchors_v3_v4.py`) |

## 규칙

- 새 실험 스크립트는 `experiments/run_expNN_이름.sh`로 만들고, 출력 루트는 `results/experiments/`로 한다 (기존 스크립트 복사 권장).
- 실험 완료 후 문서 갱신 규칙은 `context/README.md` 참조 (exp 카드 + INDEX + STATUS).
- `read_psnr.py`는 새 exp를 추가하면 EXPS 리스트에 prefix를 등록해야 한다.
