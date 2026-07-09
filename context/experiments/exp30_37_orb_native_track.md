# exp30~37 — OpenMAVIS(ORB) 데이터셋으로 갈아탄 재현 트랙

- **날짜**: 2026-07-09~
- **배경**: exp08~29는 전부 MPS(Aria 자체 SLAM) pose + MPS 62.6만 init을 썼다. 이 연구실의 목표는 **OpenMAVIS(우리 SLAM)**로 완전히 옮기는 것. exp30~37은 새로 재구축한 데이터셋(`data/03_rgb_3dgs_full`, OpenMAVIS pose 1303장 + ORB 7,205 init)에서 지금까지의 방법들을 하나씩 재현하는 트랙이다.
- **⚠ 비교 주의**: exp08(MPS)과 exp30(ORB) 등은 pose/init 출처가 완전히 다르므로 **직접 비교 금지**. 이 트랙 안에서는 exp30이 자체 기준선이다.
- **anchor는 native 재생성** (세션 간 좌표 변환 불필요) — `scripts/anchors/build_native_anchors_neworb.py` (일반, obs≥3) / `build_native_anchors_neworb_highconf.py` (고confidence, obs≥10 & found_ratio≥0.5). 상세 배경은 [exp27](exp27_anchor_init.md) 참조.

## 실험 목록

| Exp | 설정 | init/anchor | PSNR@7k | PSNR@30k | Gaussians@30k | \|Z\|>4m | 학습시간 | 상태 |
|---|---|---|---:|---:|---:|---:|---:|---|
| **exp30** | baseline (plateau 없음) | ORB 원본 7,205 | 29.183 | **32.906** | 147,620 | 269 | 15.8분 | **완료 — 이 트랙의 기준선** |
| exp31 | anchor를 init으로 | 일반 anchor 7,108 (obs≥3: SLAM 6,543 + virtual 565) | 29.011 | 32.671 | 143,330 | 71 | 17.6분 | 완료 |
| exp32 | plateau 기본 tau + λ0.01 (exp19 설정) | ORB 원본 + 일반 anchor로 당김 | 28.938 | 32.903 | 148,585 | - | 36.6분 | 완료 |
| exp33 | plateau enlarged tau + λ0.10→0.03 (exp25 설정) | ORB 원본 + 일반 anchor로 당김 | 28.989 | 32.536 | 146,872 | 33 | 26.9분 | 완료 |
| exp34 | anchor를 init으로 (고confidence) | 고confidence anchor 1,438 (obs≥10&found_ratio≥0.5: SLAM 646 + virtual 792) | 28.308 | 31.970 | 119,443 | 23 | 9.8분 | 완료 |
| exp35 | plateau 기본 tau, 고confidence anchor | ORB 원본 + 고confidence anchor로 당김 | - | - | - | - | - | 진행 중 |
| exp36 | plateau enlarged tau, 고confidence anchor | ORB 원본 + 고confidence anchor로 당김 | - | - | - | - | - | 대기 |
| exp37 | **dense confidence+monodepth init** | dense init 148,564 (SLAM core 6,543 + monodepth 완성 142,021) | - | - | - | - | - | 대기 |

> 표는 각 run 완료 시 갱신. 학습시간은 START~DONE 벽시계 기준 (다른 실험과 GPU 동시 사용 없었던 구간만). 최신 진행 상황은 이 파일 갱신 이력 참조.

## 학습 시간 메모

- init만 있고 plateau 없는 run(exp30/31/34)이 plateau 있는 run(exp32/33)보다 훨씬 짧다 — plateau loss 자체의 오버헤드(전 Gaussian-anchor 거리 계산)가 상당함을 시사.
- exp34(9.8분)가 exp31(17.6분)보다 짧은 이유: 최종 Gaussian 수가 119,443 vs 143,330으로 더 적음 — init point가 적으면(1,438 vs 7,108) densification도 덜 일어나 학습이 빨라짐.

## anchor/init 종류 정리 (헷갈리기 쉬움)

| 이름 | 개수 | 만드는 법 | 쓰는 실험 |
|---|---:|---|---|
| ORB 원본 | 7,205 | SLAM이 뽑은 map point 그대로 | exp30, exp32/33/35/36의 init |
| 일반 anchor | 7,108 | obs≥3 필터 + kNN 고립점 제거 + monodepth로 빈틈 시딩(30cm voxel, 16px stride, 최소간격 50cm) | exp31 init, exp32/33 plateau 당기는 힘 |
| 고confidence anchor | 1,438 | obs≥10 & found_ratio≥0.5로 더 엄격히 필터 + 같은 시딩 | exp34 init, exp35/36 plateau 당기는 힘 |
| dense init | 148,564 | SLAM core(obs≥3, 6,543) + depth 보정은 고confidence 점으로만 피팅 + 촘촘한 voxel(5cm)·stride(4px), 최소간격 제약 없음 | exp37 init 전용 (plateau 없음) |

## 질문별 답 (완료된 것만)

- **exp30 자체 기준**: OpenMAVIS 데이터로 아무 개선 없이 학습하면 32.906dB. 이게 이 트랙 전체의 기준점.
- **⚠ run-to-run 노이즈 확인됨**: exp30을 동시에 두 번 독립 실행했다가(중복 버그, 아래 사고 기록 참조) 우연히 비교 가능해짐 — 완전히 같은 설정인데 32.671 vs 32.906, **0.24dB 차이**. 이후 실험 비교 시 ±0.2dB 안팎은 유의미한 차이로 보지 말 것.
- **⚠ MPS 트랙과 반대 패턴 (exp32 vs exp33)**: MPS 트랙(Round 7)에서는 enlarged tau(exp25)가 최선이고 기본 tau(exp19)가 열세였는데, ORB 트랙은 **정반대**다 — 기본 tau(exp32, 32.903)가 baseline(32.906)과 동급인 반면 enlarged tau(exp33, 32.536)는 -0.37dB 손해를 본다. 단, enlarged tau가 floater는 확실히 더 잘 잡는다 (|Z|>4m: exp33=33개 vs exp31=71개, Z 최댓값이 pop2_zclip 상한 2.0m에 정확히 클립됨). **"tau를 키워야 좋다"는 결론이 데이터셋에 따라 다르다는 뜻 — MPS와 ORB의 anchor 밀도/분포 차이(ORB가 훨씬 sparse)가 원인일 가능성.** exp35/36(고confidence anchor)과 비교하면 원인 분리에 도움될 것.
- **exp31 vs exp34 (anchor 선별 기준의 효과, init으로 쓸 때)**: 일반 anchor(7,108pts, obs≥3) init인 exp31이 32.671, 고confidence anchor(1,438pts, obs≥10&fr≥0.5) init인 exp34가 31.970 — **일반 anchor가 +0.7dB 더 좋다.** floater는 고confidence 쪽이 더 적다(23개 vs 71개)지만 그 차이보다 화질 손해가 크다. 점 개수가 적어 densification이 덜 되고(최종 Gaussian 119k vs 143k) 커버리지가 부족했던 것으로 보임 — "confidence보다 개수/커버리지가 init 품질에 더 중요"할 가능성.

## 사고 기록 (2026-07-09)

exp30~33 자동 체인 launcher(`wait_and_chain.sh`)가 `pgrep -f`로 exp29 종료를 감지하려다 **자기 자신의 부모 프로세스 커맨드라인과 오매칭**돼 무한 대기에 빠짐. 수동으로 부모만 kill했는데 자식이 살아남아 있다가 부모 사망 후 정상 감지 로직이 풀리며 **똑같은 exp30~33을 또 한 번 실행** — 결과적으로 동일 실험이 두 세트 동시에 GPU를 나눠쓰며 돌아감. 발견 즉시 중복 체인 kill + 중복 결과 폴더 삭제, 하나만 남김. 위 "run-to-run 노이즈" 항목은 이 사고의 부산물로 얻은 관찰.

## 다음 갱신 시 채울 것

- exp31~37 완료되는 대로 표 갱신, INDEX.md 한 줄 추가, STATUS.md 최신 흐름 갱신.
- 핵심 질문: exp31 vs exp34 (anchor 밀도/선별 기준의 효과), exp32/33 vs exp35/36 (plateau에서 anchor confidence 기준의 효과), exp37 vs exp30/31/34 (dense init이 sparse init/anchor init보다 나은지).
