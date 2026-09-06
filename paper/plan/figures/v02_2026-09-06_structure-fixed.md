# Figure 명세 v02 (2026-09-06) — 구조 확정 반영

> 각 그림이 **무엇을 증명하는가**를 먼저 적는다. 예쁜 그림이 아니라 근거가 목적이다.
> claim 번호는 `plan/claims/CURRENT.md` 기준.
> **6그림 → 5그림.** 같은 조판(CVPR 9쪽)인 chen2026cover가 2표 3그림이다.

## v01에서 바뀐 것

| | v01 | v02 |
|---|---|---|
| 개수 | 6 | **5** (Fig.5 entropy·count spread를 Table 3의 열로 흡수) |
| Fig.3 위치 | §4 | **§3.1 안** — in-method evidence. 독자가 법칙을 읽는 자리에서 검증됨 |
| Fig.4 위치 | §4.3 독립 소절 | §4.1의 run-in `Rate robustness.` (소절 폐지, 실험은 유지) |
| 용어 | admission / cardinality / membership / ordering | **view growth / count balancing / carving** |

## 명세

| # | 이름 | 무엇을 증명하나 | claim | 출처 | 어느 절 | 형식 | 상태 |
|---|---|---|---|---|---|---|---|
| Fig.1 | Teaser | view growth와 count balancing을 분리하면 같은 wall-time에서 더 좋은 지도를 얻는다 | A4 | P02, P03 | §1 | **2단** strip. 좌: 개념도 / 중: 렌더 비교 / 우: PSNR-vs-walltime | 미착수 |
| Fig.2 | System diagram | 세 결정이 실제로 분리된 모듈이다 | A1 | (도식) | §3.0 | 1단. GPU service → credit → quota → views → block order | 미착수 |
| Fig.3 | **View-growth trace** | 실측 증가가 법칙과 일치하고 pool 크기와 무관하다 | B1, B4 | P01 | **§3.1 안** | 1단. x=wall time, y=누적 admission. 법칙선 + 실측 + baseline(gate) | 미착수 |
| Fig.4 | **Rate invariance** | GPU가 2배 빠르면 증가도 2배. pace를 바꿔도 품질이 유지된다 | **B2** | **P02** | §4.1 | 1단 2패널. (a) S(t)당 증가: 5090 vs 5070Ti 겹침 (b) pace 0.75–2.0×에서 PSNR range | 미착수 |
| Fig.5 | Floater 정성 비교 | carve가 free-space Gaussian을 실제로 줄인다 | D3 | P04 | §4.2 | 1단. 같은 시점 렌더 + PLY 단면. carve off / v7 / 이식판 | 팀원 |

## 폐기된 그림

| v01 | 어디로 갔나 |
|---|---|
| Fig.5 Entropy & count spread | **Table 3의 열로** — `ρ_H`, `selection CV`, `lifetime mid/first`. lmrs Table 2처럼 교란축(K)과 기여축(β)을 같은 표에 놓는 편이 그림보다 강하다 |

## 그림 원칙

- **Fig.4가 이 논문의 핵심 그림이다.** C1을 정의하는 성질(완료가 박자를 만든다 =
  credit-based flow control)을 검증하는 유일한 실험이고, 5090+5070Ti 2대를 가진 것이
  그대로 셋업이 된다. 두 GPU가 **같은 trace·같은 config**임을 캡션에 명시.
- **Fig.3은 §3 안에 둔다.** cartgs(Fig.2를 문제 서술 안에, Fig.4b를 해법 서술 안에)와
  taming3dgs(Fig.2b를 §3.2 안에) 둘 다 정량 근거를 Method 안에 넣는다.
  과기글 IMRaD에는 없는 CS 학회 관행이다.
- 모든 품질 축은 **held-out** PSNR. train/KF PSNR을 그림에 쓰지 않는다.
- wall-time 축이 있는 그림은 **어느 머신인지** 캡션에 적는다.
- Fig.3과 Fig.4는 같은 P01/P02 run에서 나오므로 축 단위를 통일한다.
- 1단 4개 + 2단 1개(teaser). 2단을 더 늘리면 8쪽에 안 들어간다.

## 아직 안 정한 것

- Fig.1 teaser에 정성 렌더를 넣을지, 정량 곡선만 넣을지
- exp72의 실패(lifetime 균등화)를 어디에 보일지
  → 현재 방침: **Table 3의 `lifetime mid/first` 열**로 표에 남기고, §3.2 문단 5에서
  scope guard로 서술한다. 그림으로 그리지 않는다.
