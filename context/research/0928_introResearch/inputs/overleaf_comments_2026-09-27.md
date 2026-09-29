---
schema_version: 1.3
tool_version: 0.22.1
project_id: 6a9c1b93c9b98e33cf8e5770
project_title: "CVPR2027-chsong's intern"
pulled_at: 2026-09-27T14:09:52+00:00
thread_count: 18
open_count: 18
resolved_count: 0
tracked_change_count: 0
stale_anchor_count: 0
file_count: 1
reviewer_count: 1
companion_json: comments.json
companion_agents: agents.md
---

# Overleaf comments — CVPR2027-chsong's intern

Stable IDs like `C001` are assigned in file → line order. Cite them when asking an AI to address specific comments. The full structured data is in `comments.json` next to this file.

## Summary

- **Threads:** 18 (18 open, 0 resolved)
- **Tracked changes:** 0
- **Most active reviewers:** 송채현 / 학생 / 기계항공공학부 ­ (20)
- **Addressed:** 0 of 18 ([the list is at the end](#still-to-address))

### § Introduction

**Line 7** — 1 comment

> …ntroduction} \label{sec:intro} % chaehyeon: 아래 첫 두문단은 요약해서 한문단으로 써보세요. **▸3D Gaussian Splatting (3DGS) has established itself as a highly effective representation for photorealistic novel view synthesis~\cite{kerbl20233dgs}. By modeling scenes with explicit, colored Gaussian primitives and rendering them via a tile-based differentiable rasterizer, it provides a compelling combination of high visual fidelity and real-time rendering speeds. Consequently, 3DGS is increasingly utilized across a diverse range of visual applications.◂** To achieve this level of quality, the representation requires careful…

**C001** _open · 1 reply_ — “3D Gaussian Splatting (3DGS) has established itself as a highly effective rep…”
- **송채현 / 학생 / 기계항공공학부 ­** · 2026-09-20 01:55 UTC:
  > 3dgs에대한 설명을 자세하게 하기 보다는
  > 
  > 여러 mapping representation (point cloud, mesh, surfels 등등) 중 3dgs가 같는 장점위주로 적어주세요.
  > 
  > 지금은 introduction 시작이 novel view synthesis 논문 같아요;;'
  > 
  > 예)
  > 3DGS 는 실시간으로 novle view에서 dense한 image reconstruction이 가능하다는 점에서 다른  represnetation 애 비해 ~한  장점을 갖는다.
  - ↳ **송채현 / 학생 / 기계항공공학부 ­** · 2026-09-20 06:14 UTC: 여기서 VLA같은 최신 트렌드도 언급되었으면 해요. vision기반 action이나 decision 프로세스가 중요하지는 만큼 vision input을 만들수 있는 map의 가치는 올라가니깐요.

**Line 8** — 1 comment

> …s increasingly utilized across a diverse range of visual applications. **▸To achieve this level of quality, the representation requires careful optimiz◂** ation of numerous parameters—including position, scale, rotation, colo…

**C002** _open_ — “To achieve this level of quality, the representation requires careful optimiz”
- **송채현 / 학생 / 기계항공공학부 ­** · 2026-09-20 01:56 UTC: Good

**Line 10** — 2 comments

> …wever, autonomous robots and wearable augmented-reality systems (e.g., **▸Aria glasses◂** ) are fundamentally bound to the present moment. For these active agen…

**C003** _open_ — “Aria glasses”
- **송채현 / 학생 / 기계항공공학부 ­** · 2026-09-20 06:05 UTC: citation

**C004** _open · 1 reply_ — “high reconstruction quality achieved only after an exhaustive offline refinem…”
- **송채현 / 학생 / 기계항공공학부 ­** · 2026-09-20 06:12 UTC:
  > 문장이 좀 이상.
  > high reconstruction quality 가 inadequate가 아니라 exhaustive offline refinement stag가 inadequate인거 아닐까요? 주어랑 동사가 제대로 매치되어있는지 확인필요
  - ↳ **송채현 / 학생 / 기계항공공학부 ­** · 2026-09-20 06:13 UTC: achieved only after~ 은 부사절이기 때문에 문장에서는 중요도가 떨어지는 부분입니다. 강조하고자 하는걸 주어로 넣어주세요

**Line 11** — 1 comment

> …hotometric and geometric convergence} for practical field deployments. **▸Regardless of the specific hardware environment, the system is forced to make a newly observed region structurally and visually reliable as quickly as possible under whatever computational budget is given.◂** % ------------ 여기까지가 한문단 Building a reliable online Gaussian map inher…

**C005** _open_ — “Regardless of the specific hardware environment, the system is forced to make…”
- **송채현 / 학생 / 기계항공공학부 ­** · 2026-09-20 06:49 UTC:
  > 이렇게 쓰면 fast gs optimiation논문처럼 느껴지는데 (실험이 gs optimization 이 몇초 걸리는지 테스해야할것 같고..)
  > 
  > online이라는 느낌이 별로 없어요. online이기 때문에 replay buffer나 sampling을 어떻게 해야 효율적인지 이런부분이 나타나는건데 gs optimization 과정만 빠르게 한 논문같아요.
  > 
  > 또 as quickly as possible 이나 whatever 이런 표현이 되게 쎈 표현이라 정말 무조건 그래야하나? 라는 의문을 갖게하네요

**Line 14** — 3 comments

> …online Gaussian map inherently requires two complementary objectives: **▸establishing a geometrically sound starting point and rapidly optimizing it under strict computational limits.◂** Recent advancements have approached these goals from various angles. F…

**C006** _open_ — “establishing a geometrically sound starting point and rapidly optimizing it u…”
- **송채현 / 학생 / 기계항공공학부 ­** · 2026-09-20 07:09 UTC: 뒷 문단은 1. frame selection, 2. geometry maintainense에 다루고 잇는데 여기선 strating point랑 rapid optimization을 언급하고  있음. 유기적으로 연결되게 같은걸 말해야해요

**C007** _open_ — “geometrically sound starting point”
- **송채현 / 학생 / 기계항공공학부 ­** · 2026-09-20 06:52 UTC: 표현 이상함

**C008** _open_ — “rapidly optimizing it”
- **송채현 / 학생 / 기계항공공학부 ­** · 2026-09-20 06:52 UTC: rapid optimization

**Line 15** — 1 comment

> …ing point and rapidly optimizing it under strict computational limits. **▸Recent advancements have approached these goals from various angles. For instance, EDGS~\cite{edgs} demonstrates that dense image correspondences can provide a robust geometric initialization, laying the groundwork for high-quality reconstruction. At the optimizer level, 3DGS-LM introduces second-order solvers to accelerate convergence~\cite{hollein2025gslm}, while systems like CaRtGS and PGSR incorporate allocation strategies and geometric consistencies to maximize the efficiency of available compute~\cite{cartgs, chen2024pgsr}.◂** While these approaches successfully highlight the necessity of learnin…

**C009** _open_ — “Recent advancements have approached these goals from various angles. For inst…”
- **송채현 / 학생 / 기계항공공학부 ­** · 2026-09-20 06:54 UTC:
  > 너무 related work처럼 써있어요. introduction에서는 method의 이름을 언급하기보다는 method의 원리 위주로 설명하고 분류해서 citation을 한번에 달아주는형태가 좋습니다. 
  > method가 아닌 approaches에 집중해서 작성해주세요

**Line 22** — 1 comment

> …p optimization. While bounding computation to local keyframe windows ( **▸as seen in MonoGS and HI-SLAM2◂** ~\cite{matsuki2024monogs,zhang2025hislam2}) efficiently reuses selecte…

**C010** _open_ — “as seen in MonoGS and HI-SLAM2”
- **송채현 / 학생 / 기계항공공학부 ­** · 2026-09-20 06:59 UTC: METHOD 언급이 꼭 필요한게 아니면 CITATION만 해도 충분해요

**Line 23** — 2 comments

> …y delaying the convergence of recently added regions. Hence, achieving **▸rapid◂** photometric improvement requires decoupling the mapping-view set from…

**C011** _open_ — “rapid”
- **송채현 / 학생 / 기계항공공학부 ­** · 2026-09-20 06:57 UTC: rapid라는 단어가 너무 자주 쓰이는데 다른 동의어를 활용해보세요

**C012** _open_ — “By dynamically coupling the inclusion of new observations to actual completed…”
- **송채현 / 학생 / 기계항공공학부 ­** · 2026-09-20 07:06 UTC: 문장이 너무 길고 필요없는 수동태들이 문장을 vague하게 만들어요. 깔끔하게 다듬어보세요

**Line 25** — 3 comments

> …bring the appearance of newly observed regions to high quality sooner. **▸A strong geometric starting point is essential, but it does not guarantee tha◂** t structures remain accurate during subsequent color-driven optimizati…

**C013** _open_ — “A strong geometric starting point is essential, but it does not guarantee tha”
- **송채현 / 학생 / 기계항공공학부 ­** · 2026-09-20 07:22 UTC:
  > 이 문단이 좀 붕 떠요. 앞이나 뒤에서 fast convergence를 얘기하는데 이 문단만 geometric accuracy를 얘기하고 있어서.
  > 
  > 저희가 원하는게 과연 fast convergnece인지, geomtry를 유지한체 fast convergence인지 논문의 방향성에 대해 확실히 해야할필요가 잇어요.
  > 
  > 저는 후가자 나을것 같은데 convergence 속도만 중요시 하면geomtry가 어긋나도 psnr이런거 높게 만들수 잇거든요.  근데 그게 좋은 mapping이 아니니 이런부분을 앞에서 제대로 다뤄주어야 할것 같네요

**C014** _open_ — “starting point”
- **송채현 / 학생 / 기계항공공학부 ­** · 2026-09-20 07:07 UTC:
  > 저자들만 아는 학계에서 주로 쓰는 단어가 아님. 이런 단어를 주의해야 해요.
  > 
  > initalization인지 optimization parameter인지 제대로 설명해주세요

**C015** _open_ — “surface”
- **송채현 / 학생 / 기계항공공학부 ­** · 2026-09-20 07:40 UTC: citation 달아주세요

**Line 27** — 3 comments

> …ble positional gradients~\cite{yu2024gof, guedon2023sugar, pagas2026}. **▸To achieve this fast convergence within a bounded online budget◂** , we build upon a DROID-SLAM-based frontend~\cite{teed2021droid}. Whil…

**C016** _open_ — “To achieve this fast convergence within a bounded online budget”
- **송채현 / 학생 / 기계항공공학부 ­** · 2026-09-20 07:41 UTC: 앞문단에서는 geometry 얘기를 했는데 갑자기 fast convergene가 다시 등장

**C017** _open_ — “DROID-SLAM-based frontend~\cite{teed2021droid}”
- **송채현 / 학생 / 기계항공공학부 ­** · 2026-09-20 07:43 UTC:
  > 이게 핵심일까요? 우리가 어떤걸 제안하는지 처음 말해주는 문단인데 너무 약해요. 앞에서 언급한 문제들을 전부 해결하는 방법론이 제시되어야 하는데 너무 specific한 method가 나와있어요.
  > 
  > 여기 첫 문장에서는 어떻게 fast convergence랑 geometric accurcay를 동시에 잡았는지에 대해 설명을 해야해요

**C018** _open_ — “While recent works have explored dense geometric initialization~\cite{edgs},…”
- **송채현 / 학생 / 기계항공공학부 ­** · 2026-09-20 07:45 UTC: 앞에서 했던얘기를 반복함. 이문단에서는 기존 work의 문제나 previous work들을 설명하는게 아니라 우리가 멀 제안하는지 설명을 effective하게 작성해야함

## Still to address

0 of 18 done, going by what is resolved in Overleaf.

- [ ] **C001** “3D Gaussian Splatting (3DGS) has established its…” — Introduction — 송채현 / 학생 / 기계항공공학부 ­
- [ ] **C002** “To achieve this level of quality, the representa…” — Introduction — 송채현 / 학생 / 기계항공공학부 ­
- [ ] **C003** “Aria glasses” — Introduction — 송채현 / 학생 / 기계항공공학부 ­
- [ ] **C004** “high reconstruction quality achieved only after…” — Introduction — 송채현 / 학생 / 기계항공공학부 ­
- [ ] **C005** “Regardless of the specific hardware environment,…” — Introduction — 송채현 / 학생 / 기계항공공학부 ­
- [ ] **C006** “establishing a geometrically sound starting poin…” — Introduction — 송채현 / 학생 / 기계항공공학부 ­
- [ ] **C007** “geometrically sound starting point” — Introduction — 송채현 / 학생 / 기계항공공학부 ­
- [ ] **C008** “rapidly optimizing it” — Introduction — 송채현 / 학생 / 기계항공공학부 ­
- [ ] **C009** “Recent advancements have approached these goals…” — Introduction — 송채현 / 학생 / 기계항공공학부 ­
- [ ] **C010** “as seen in MonoGS and HI-SLAM2” — Introduction — 송채현 / 학생 / 기계항공공학부 ­
- [ ] **C011** “rapid” — Introduction — 송채현 / 학생 / 기계항공공학부 ­
- [ ] **C012** “By dynamically coupling the inclusion of new obs…” — Introduction — 송채현 / 학생 / 기계항공공학부 ­
- [ ] **C013** “A strong geometric starting point is essential,…” — Introduction — 송채현 / 학생 / 기계항공공학부 ­
- [ ] **C014** “starting point” — Introduction — 송채현 / 학생 / 기계항공공학부 ­
- [ ] **C015** “surface” — Introduction — 송채현 / 학생 / 기계항공공학부 ­
- [ ] **C016** “To achieve this fast convergence within a bounde…” — Introduction — 송채현 / 학생 / 기계항공공학부 ­
- [ ] **C017** “DROID-SLAM-based frontend~\cite{teed2021droid}” — Introduction — 송채현 / 학생 / 기계항공공학부 ­
- [ ] **C018** “While recent works have explored dense geometric…” — Introduction — 송채현 / 학생 / 기계항공공학부 ­
