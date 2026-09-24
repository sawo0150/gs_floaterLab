# gs_floaterLab Context

OpenMAVIS `301_1253` trajectory 기반 3DGS에서 render 품질을 유지하며 floater를 줄이는 실험 워크스페이스의 knowledge base.

## 폴더 구조와 문서 3종 구분

| 폴더 | 성격 | 규칙 |
|---|---|---|
| `STATUS.md` | **살아있는 문서** | 유일한 "현재 상태". 1페이지 엄수. 항상 최신 |
| `experiments/` | **불변 기록 + campaign hub** | `README.md`에서 질문별로 탐색. `INDEX.md`는 시간순 원장 |
| `rounds/` | **불변 기록** | 진단 루프 라운드별 기록. 완결 시 봉인 |
| `knowledge/` | 참조 (갱신형) | 확정된 결론을 주제별로. 근거 exp/round 링크 필수 |
| `reference/` | 참조 (갱신형) | 경로 지도, repro 커맨드, W&B metric 설명, 논문 PDF |
| `archive/` | 봉인 | 닫힌 연구 축 + 구버전 문서. **읽을 필요 없음** |

## 읽는 순서 (새 agent / 복귀)

1. `STATUS.md` — 현재 best, 열린 질문, 다음 할 일
2. `experiments/README.md` — LIVE/SCHED/BENCH/TOPO/DENSE/ATTR campaign별 현재 결론
3. `experiments/INDEX.md` — 번호나 날짜로 과거 기록을 찾을 때만 사용
4. `knowledge/floater_populations.md` — Pop1/Pop2 구분 (이 프로젝트의 핵심 프레임)
5. `knowledge/pitfalls.md` — 피해야 할 함정
6. 실험을 돌리기 전: `reference/workspace_map.md` + `reference/repro_commands.md`

## 갱신 규칙 (실험 1개 완료 시 이 3개만)

1. `experiments/campaigns/<campaign>/<question>/`에 결과 카드를 생성한다.
   `expNNN`은 카드 metadata의 provenance ID로만 기록한다.
2. `experiments/INDEX.md`에 한 줄 추가
3. `STATUS.md` 갱신 (best 변동, 열린 질문, 최근 흐름)

Runner는 `benchmarks/online_gs/campaigns/<campaign>/`, raw result는
`results/campaigns/<campaign>/<question>/`에 둔다. 기존 flat `expNN` 경로는
source lock과 링크 보존을 위해 이동하지 않는다.

결론이 뒤집히면: `knowledge/`에서 갱신하고, 옛 기록에는 첫 줄에 `> superseded by X` 한 줄만 추가.

라운드(가설 검증 사이클)가 끝나면: `rounds/roundN_이름.md` 작성 후 봉인.

## 실험 카드 양식

```markdown
# expNN — 한 줄 이름
- 날짜 / result dir / W&B run
- 목적: 무엇을 검증하려 했나
- 설정: baseline 대비 diff만
- 결과: PSNR@7k/30k + floater 지표
- Verdict: 채택/기각/보류 + 한 줄 이유
```
