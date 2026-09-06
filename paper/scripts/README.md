# scripts/

이 폴더의 스크립트는 전부 **저장소 최상위(`gs_floaterLab/`)에서** 실행하는 것을 전제로 한다.

```bash
cd ~/Desktop/Incremental_mapping/gs_floaterLab
./paper/scripts/<이름> ...
```

## 한눈에

| 스크립트 | 언제 쓰나 | 상태 |
|---|---|---|
| [`tex.sh`](#texsh) | 논문을 **로컬에서 빌드·미리보기** | ✅ |
| [`pagemap.sh`](#pagemapsh) | 절이 **몇 쪽 먹는지** 계획과 대조 | ✅ |
| [`sync.sh`](#syncsh) | **Overleaf 에 뭘 올려야 하는지** 확인 | ✅ |
| [`newver.sh`](#newversh) | 계획 문서의 **새 버전** 만들기 | ✅ |
| [`make_tables.py`](#make_tablespy) | 실험 CSV → **LaTeX 표** | ✅ |
| [`run_remote.sh`](#run_remotesh) | 원격 GPU에 실험 **디스패치** + manifest 생성 | ⚠ manifest만 |
| `collect_metrics.py` | 원격 로그 → `results/runs/<run_id>/metrics.csv` | ❌ 미작성 (P01 후) |

`sync_overleaf.sh` 는 **만들지 않는다.** 동기화는 사람이 직접 복사·붙여넣기 하기로 정했다
(`paper/latex/SYNC.md`). `sync.sh` 는 *무엇을* 붙여넣을지만 알려주고 전송은 하지 않는다.

### 자주 쓰는 흐름

```bash
./paper/scripts/tex.sh watch      # 터미널 하나 열어두고 계속 켜둔다
#  ... latex/sec/*.tex 를 고친다 ...
./paper/scripts/pagemap.sh        # 분량이 계획에 맞나
./paper/scripts/sync.sh status    # 됐다 싶으면 뭘 올려야 하나
#  ... Overleaf 에 붙여넣는다 ...
./paper/scripts/sync.sh mark-all
```

---

## `tex.sh`

`paper/latex/` 를 빌드해 `paper/build/main.pdf` 를 만든다.

```bash
./paper/scripts/tex.sh          # 한 번 빌드
./paper/scripts/tex.sh open     # 빌드 후 뷰어(evince)로 열기
./paper/scripts/tex.sh watch    # 파일이 바뀔 때마다 자동 재빌드 (Ctrl-C 종료)
./paper/scripts/tex.sh clean    # build/ 지우기
```

출력은 로그 수천 줄 대신 이것만 보여준다:

```
✓ main.pdf  11쪽  (13:52:01)
  ⚠ 미해결 인용·참조 6건
  ⚠ 본문 8쪽 초과 (11쪽) — CVPR 제한 확인
```

- 내부적으로 `latexmk -pdf` 를 돌리고 전체 로그는 `paper/build/latexmk.log` 에 남는다
- `build/` 는 git 에 올라가지 않는다
- **빌드 환경은 TinyTeX** (`~/.TinyTeX`, sudo 불필요). `tex.sh` 가 PATH 를 알아서 잡으므로
  셸 설정을 건드릴 필요 없다. 지우려면 `rm -rf ~/.TinyTeX`
- 새 컴퓨터에서의 설치 방법과 패키지 목록은 `paper/latex/SYNC.md` 의 "빌드 환경"
- `File \`xxx.sty' not found` 가 나오면 `tlmgr install xxx`
- `watch` 는 `inotifywait` 이 있으면 즉시, 없으면 2초 폴링으로 돈다.
  즉시 반응을 원하면 `sudo apt install inotify-tools`

## `pagemap.sh`

`build/main.pdf` 를 읽어 절마다 몇 쪽을 쓰는지 재고 `plan/outline/` 의 계획과 비교한다.
**먼저 `tex.sh` 를 돌려 PDF 가 있어야 한다.**

```bash
./paper/scripts/pagemap.sh
```

```
총 11쪽 · References 시작 p9 (그 쪽에 본문이 같이 있을 수 있음)
절                                   시작쪽     실제     계획  차이
1 Introduction                        1    1.0   1.00  +0.0
4 Experiments                         6    3.0   2.20  +0.8  ⚠
```

- 차이가 ±0.6쪽을 넘으면 `⚠`
- **절이 한 쪽을 나눠 쓰면 '실제'가 과대 계산된다.** 정확한 값이 아니라 추세를 보는 용도
- 계획값은 스크립트 안에 하드코딩돼 있다. `plan/outline/` 을 고치면 여기도 같이 고칠 것

## `sync.sh`

로컬 `paper/latex/` 와 Overleaf 사이에서 **아직 안 올린 파일**을 관리한다.
**전송은 하지 않는다** — 무엇을 붙여넣을지와 무엇이 달라졌는지만 알려준다.

```bash
./paper/scripts/sync.sh status              # 안 올린 파일 목록
./paper/scripts/sync.sh diff sec/4_method.tex   # 마지막 동기화 이후 무엇이 바뀌었나
./paper/scripts/sync.sh mark sec/4_method.tex   # 붙여넣은 뒤 기록
./paper/scripts/sync.sh mark-all            # 전부 붙여넣었을 때
./paper/scripts/sync.sh init <커밋>          # 기준 상태를 그 커밋의 latex/ 로 재설정
```

```
Overleaf 에 아직 안 올린 것 — 3 건
  (Overleaf 에서 해당 파일을 열고 로컬 내용으로 통째로 덮어쓰세요)

  [새 파일] sec/8_extra.tex
  [수정됨]  main.bib    ← ./paper/scripts/sync.sh diff main.bib
  [삭제됨]  temp.tex    (Overleaf 에서도 지울지 판단)
```

- 기준 상태는 `latex/.sync-state` (파일별 해시, **git 에 올라간다**).
  공유받은 zip 그대로로 초기화되어 있다 — 그게 Overleaf 의 실제 내용이기 때문
- `diff` 용 사본은 `paper/.sync-snapshot/` (git 제외)
- `SYNC.md` 자신과 빌드 산출물(`*.aux` `*.log` `*.pdf` 등)은 추적 대상이 아니다
- 반대로 **`make_tables.py` 가 만든 `tab/*.tex` 는 git 이 무시해도 여기엔 뜬다.**
  Overleaf 가 컴파일하려면 필요하기 때문이다. 정상이니 올린다
- ⚠ **`preamble.tex` 를 고쳤으면 반드시 같이 올릴 것.** 골격 마커 `\skel`/`\pend` 가
  거기 정의돼 있어 빠뜨리면 Overleaf 에서 컴파일이 깨진다
- 선배님들이 Overleaf 에서 직접 고치셨으면 zip 을 다시 받아 `latex/` 를 덮어쓰고
  `init` 으로 기준을 재설정한다. **덮어쓰기 전에 `status` 를 비워둘 것**

## `newver.sh`

버전 관리하는 계획 문서 폴더에 다음 버전을 만든다.

```bash
./paper/scripts/newver.sh <문서폴더> <슬러그> ["트리거"]

# 예
./paper/scripts/newver.sh paper/plan/claims after-P03 "P03 재검증 결과 반영"
./paper/scripts/newver.sh paper/sections/03_method/3-2_ercb/plan supervisor-review
```

하는 일:
1. `CURRENT.md` 가 가리키는 최신 `vNN` 을 `v(NN+1)_<오늘>_<슬러그>.md` 로 복사
2. `CURRENT.md` 심링크를 새 파일로 재지정
3. 상위 `README.md` 의 버전 이력 표에 행 추가 (변경 내용은 `TODO` 로 남음)

**만든 뒤 할 일:** 새 파일을 고치고, README 이력 표의 `TODO` 두 칸
("무엇이 바뀌었나", "폐기된 주장")을 채운다.

⚠ **버전을 올리는 기준**은 `paper/README.md` "버전 관리 규약".
오탈자·문장 다듬기는 bump 하지 말고 현재 파일을 직접 고친다.

대상 폴더: `plan/{claims,outline,figures,experiment_table,timeline}`,
`notes/naming`, `sections/*/plan`, `experiments/{protocol,P0n}/plan`

## `make_tables.py`

실험 결과 CSV 를 LaTeX 표로 바꾼다. **논문의 숫자는 반드시 이 경로로만 들어간다.**

```
results/runs/<run_id>/metrics.csv  →  results/tables/*.csv  →  latex/tab/*.tex  →  \input
```

```bash
python3 paper/scripts/make_tables.py                # results/tables/*.csv 전부
python3 paper/scripts/make_tables.py main_results   # 하나만
```

규칙:
- 헤더의 `_` 는 공백으로 바뀐다. 단 `$` 나 `\` 가 든 수식 헤더(`$\rho_H$`)는 건드리지 않는다
- `$` 나 `\` 가 든 셀은 이미 LaTeX 로 보고 이스케이프하지 않는다
- 숫자로 파싱되는 열은 오른쪽 정렬, 아니면 왼쪽 정렬
- 셀이 `**...**` 면 `\textbf{...}`
- CSV 맨 위에 `# caption: ...` 주석이 있으면 캡션으로 쓴다

⚠ **`latex/tab/*.tex` 는 생성물이라 git 에 올라가지 않는다.** 손으로 고치지 말고 CSV 를 고친다.
⚠ **git 이 무시하는 것과 Overleaf 에 올릴 것은 다르다.** 생성된 `tab/*.tex` 는 Overleaf 가
컴파일하려면 필요하므로 `sync.sh status` 에 `[새 파일]` 로 뜬다. 그건 정상이니 올린다.
⚠ **latex 에 숫자를 손으로 적지 않는다.** 재실험이 확정된 값이 여러 곳에 흩어지면 못 따라간다.

## `run_remote.sh`

원격 GPU 에 실험을 던지고 `run_id` 와 `manifest.json` 뼈대를 만든다.

```bash
./paper/scripts/run_remote.sh <Pnn> <machine> <arm> <scene> <seed>

# 예
./paper/scripts/run_remote.sh P01 fastmri-desktop token-noprepurchase aria1253 0
./paper/scripts/run_remote.sh P03 chaehyun ercb-k128-b002 aria1253rot 1
```

- `machine`: `chaehyun` (RTX 5090) | `fastmri-desktop` (RTX 5070 Ti)
- `run_id` = `<Pnn>_<날짜>_<GPU태그>_<arm>_seed<N>`
- `paper/results/runs/<run_id>/manifest.json` 에 protocol 버전과 원격 코드 커밋을 박아둔다
- 마지막에 원격 `nvidia-smi` 를 찍는다. **다른 프로세스가 있으면 죽이지 말고 기다린다**
  (`AGENTS.md` 규칙)

⚠ **아직 manifest 만 만든다.** 실제 실행 커맨드(`RUN_CMD`)는 P01 구현 후 채운다.
