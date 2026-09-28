# 전체 댓글 대화록

프로젝트: CVPR2027-chsong's intern

전체 스레드 18개. 위치가 연결되지 않은 스레드도 포함. 원본: [comments.json](comments.json).

## C001 — open

Thread ID: `6aaf3d009b43b2475f000001`

연결 원문:

> 3D Gaussian Splatting (3DGS) has established itself as a highly effective representation for photorealistic novel view synthesis~\cite{kerbl20233dgs}. By modeling scenes with explicit, colored Gaussian primitives and rendering them via a tile-based differentiable rasterizer, it provides a compelling combination of high visual fidelity and real-time rendering speeds. Consequently, 3DGS is increasingly utilized across a diverse range of visual applications. 

**송채현 / 학생 / 기계항공공학부 ­ · comment · 2026-09-20T01:55:13.051000+00:00**

3dgs에대한 설명을 자세하게 하기 보다는

여러 mapping representation (point cloud, mesh, surfels 등등) 중 3dgs가 같는 장점위주로 적어주세요.

지금은 introduction 시작이 novel view synthesis 논문 같아요;;'

예)
3DGS 는 실시간으로 novle view에서 dense한 image reconstruction이 가능하다는 점에서 다른  represnetation 애 비해 ~한  장점을 갖는다. 

**송채현 / 학생 / 기계항공공학부 ­ · reply · 2026-09-20T06:14:39.003000+00:00**

여기서 VLA같은 최신 트렌드도 언급되었으면 해요. vision기반 action이나 decision 프로세스가 중요하지는 만큼 vision input을 만들수 있는 map의 가치는 올라가니깐요.

## C002 — open

Thread ID: `6aaf3d46a1dd417ed2000001`

연결 원문:

> To achieve this level of quality, the representation requires careful optimiz

**송채현 / 학생 / 기계항공공학부 ­ · comment · 2026-09-20T01:56:22.766000+00:00**

Good

## C003 — open

Thread ID: `6aaf77be836a280878000001`

연결 원문:

> Aria glasses

**송채현 / 학생 / 기계항공공학부 ­ · comment · 2026-09-20T06:05:50.658000+00:00**

citation

## C004 — open

Thread ID: `6aaf795fdec3dc4a09000001`

연결 원문:

> high reconstruction quality achieved only after an exhaustive offline refinement stage is inadequate

**송채현 / 학생 / 기계항공공학부 ­ · comment · 2026-09-20T06:12:48.070000+00:00**

문장이 좀 이상.
high reconstruction quality 가 inadequate가 아니라 exhaustive offline refinement stag가 inadequate인거 아닐까요? 주어랑 동사가 제대로 매치되어있는지 확인필요

**송채현 / 학생 / 기계항공공학부 ­ · reply · 2026-09-20T06:13:29.595000+00:00**

achieved only after~ 은 부사절이기 때문에 문장에서는 중요도가 떨어지는 부분입니다. 강조하고자 하는걸 주어로 넣어주세요

## C005 — open

Thread ID: `6aaf81fb5485d90e03000001`

연결 원문:

> Regardless of the specific hardware environment, the system is forced to make a newly observed region structurally and visually reliable as quickly as possible under whatever computational budget is given.
> 

**송채현 / 학생 / 기계항공공학부 ­ · comment · 2026-09-20T06:49:32.409000+00:00**

이렇게 쓰면 fast gs optimiation논문처럼 느껴지는데 (실험이 gs optimization 이 몇초 걸리는지 테스해야할것 같고..)

online이라는 느낌이 별로 없어요. online이기 때문에 replay buffer나 sampling을 어떻게 해야 효율적인지 이런부분이 나타나는건데 gs optimization 과정만 빠르게 한 논문같아요.

또 as quickly as possible 이나 whatever 이런 표현이 되게 쎈 표현이라 정말 무조건 그래야하나? 라는 의문을 갖게하네요

## C007 — open

Thread ID: `6aaf82974ad6477033000001`

연결 원문:

>  geometrically sound starting point

**송채현 / 학생 / 기계항공공학부 ­ · comment · 2026-09-20T06:52:07.611000+00:00**

표현 이상함

## C008 — open

Thread ID: `6aaf82aaddce0267ab000001`

연결 원문:

> rapidly optimizing it

**송채현 / 학생 / 기계항공공학부 ­ · comment · 2026-09-20T06:52:26.913000+00:00**

rapid optimization

## C009 — open

Thread ID: `6aaf833fbe94653016000001`

연결 원문:

> Recent advancements have approached these goals from various angles. For instance, EDGS~\cite{edgs} demonstrates that dense image correspondences can provide a robust geometric initialization, laying the groundwork for high-quality reconstruction. At the optimizer level, 3DGS-LM introduces second-order solvers to accelerate convergence~\cite{hollein2025gslm}, while systems like CaRtGS and PGSR incorporate allocation strategies and geometric consistencies to maximize the efficiency of available compute~\cite{cartgs, chen2024pgsr}. 

**송채현 / 학생 / 기계항공공학부 ­ · comment · 2026-09-20T06:54:56.415000+00:00**

너무 related work처럼 써있어요. introduction에서는 method의 이름을 언급하기보다는 method의 원리 위주로 설명하고 분류해서 citation을 한번에 달아주는형태가 좋습니다. 
method가 아닌 approaches에 집중해서 작성해주세요

## C011 — open

Thread ID: `6aaf83e18c9b890d3b000001`

연결 원문:

> rapid

**송채현 / 학생 / 기계항공공학부 ­ · comment · 2026-09-20T06:57:38.312000+00:00**

rapid라는 단어가 너무 자주 쓰이는데 다른 동의어를 활용해보세요

## C010 — open

Thread ID: `6aaf84632c58703873000001`

연결 원문:

> as seen in MonoGS and HI-SLAM2

**송채현 / 학생 / 기계항공공학부 ­ · comment · 2026-09-20T06:59:48.402000+00:00**

METHOD 언급이 꼭 필요한게 아니면 CITATION만 해도 충분해요

## C012 — open

Thread ID: `6aaf85eca4e3011f61000001`

연결 원문:

> By dynamically coupling the inclusion of new observations to actual completed optimization work and meticulously balancing training opportunities across views, a limited computational budget can be strictly directed to bring the appearance of newly observed regions to high quality sooner.

**송채현 / 학생 / 기계항공공학부 ­ · comment · 2026-09-20T07:06:21.372000+00:00**

문장이 너무 길고 필요없는 수동태들이 문장을 vague하게 만들어요. 깔끔하게 다듬어보세요

## C014 — open

Thread ID: `6aaf86361b20903c22000001`

연결 원문:

>  starting point

**송채현 / 학생 / 기계항공공학부 ­ · comment · 2026-09-20T07:07:35.258000+00:00**

저자들만 아는 학계에서 주로 쓰는 단어가 아님. 이런 단어를 주의해야 해요.

initalization인지 optimization parameter인지 제대로 설명해주세요

## C006 — open

Thread ID: `6aaf86b43432a942e7000001`

연결 원문:

> establishing a geometrically sound starting point and rapidly optimizing it under strict computational limits. 

**송채현 / 학생 / 기계항공공학부 ­ · comment · 2026-09-20T07:09:41.404000+00:00**

뒷 문단은 1. frame selection, 2. geometry maintainense에 다루고 잇는데 여기선 strating point랑 rapid optimization을 언급하고  있음. 유기적으로 연결되게 같은걸 말해야해요

## C013 — open

Thread ID: `6aaf89a15ff4131337000001`

연결 원문:

> A strong geometric starting point is essential, but it does not guarantee tha

**송채현 / 학생 / 기계항공공학부 ­ · comment · 2026-09-20T07:22:10.310000+00:00**

이 문단이 좀 붕 떠요. 앞이나 뒤에서 fast convergence를 얘기하는데 이 문단만 geometric accuracy를 얘기하고 있어서.

저희가 원하는게 과연 fast convergnece인지, geomtry를 유지한체 fast convergence인지 논문의 방향성에 대해 확실히 해야할필요가 잇어요.

저는 후가자 나을것 같은데 convergence 속도만 중요시 하면geomtry가 어긋나도 psnr이런거 높게 만들수 잇거든요.  근데 그게 좋은 mapping이 아니니 이런부분을 앞에서 제대로 다뤄주어야 할것 같네요

## C015 — open

Thread ID: `6aaf8dd25419380080000001`

연결 원문:

> surface

**송채현 / 학생 / 기계항공공학부 ­ · comment · 2026-09-20T07:40:03.436000+00:00**

citation 달아주세요

## C016 — open

Thread ID: `6aaf8e3c9f1fb328dd000001`

연결 원문:

> To achieve this fast convergence within a bounded online budget

**송채현 / 학생 / 기계항공공학부 ­ · comment · 2026-09-20T07:41:48.867000+00:00**

앞문단에서는 geometry 얘기를 했는데 갑자기 fast convergene가 다시 등장

## C017 — open

Thread ID: `6aaf8ea899ee881711000001`

연결 원문:

> DROID-SLAM-based frontend~\cite{teed2021droid}

**송채현 / 학생 / 기계항공공학부 ­ · comment · 2026-09-20T07:43:37.409000+00:00**

이게 핵심일까요? 우리가 어떤걸 제안하는지 처음 말해주는 문단인데 너무 약해요. 앞에서 언급한 문제들을 전부 해결하는 방법론이 제시되어야 하는데 너무 specific한 method가 나와있어요.

여기 첫 문장에서는 어떻게 fast convergence랑 geometric accurcay를 동시에 잡았는지에 대해 설명을 해야해요

## C018 — open

Thread ID: `6aaf8efdc8ecc863f2000001`

연결 원문:

> While recent works have explored dense geometric initialization~\cite{edgs}, efficient second-order solvers~\cite{hollein2025gslm}, and compute-aware optimization allocations~\cite{cartgs, chen2024pgsr}, translating these foundations into continuous map improvement requires strict control over which observations enter training.

**송채현 / 학생 / 기계항공공학부 ­ · comment · 2026-09-20T07:45:02.246000+00:00**

앞에서 했던얘기를 반복함. 이문단에서는 기존 work의 문제나 previous work들을 설명하는게 아니라 우리가 멀 제안하는지 설명을 effective하게 작성해야함

## 변경 제안

구조화된 변경 제안 0개는 comments.json의 tracked_changes에 보존되어 있습니다.
