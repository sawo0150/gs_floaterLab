# exp03-E — strict end-to-end packet-budget ERCB interaction

날짜: 2026-09-15
상태: **완료 — starvation 완화는 재현, compute-matched PSNR 이득은 미재현**

## 질문

3dgs-custom exp03에서 관측된 저예산 ERCB 이득을 online tracking, causal view
arrival, native topology가 함께 작동하는 VIGS end-to-end에서도 실제 Adam budget을
맞춰 재현할 수 있는가?

## 구현과 계약

전체 `max_steps`를 초반에 소진하면 후반 view가 굶으므로, 성공적으로 ingest된 causal
mapping packet마다 `q`개의 physical B1 Adam credit을 해제하는
`--mapping_replay_steps_per_packet`을 추가했다. Credit은 해당 packet 이후에만 보이며
EOS 뒤에는 사용하지 않는다. 기본값 0은 기존 동작과 같다.

첫 joint-pool pair에서 ERCB가 KF/dense 비율까지 바꿔 final Gaussian 수가 14% 갈리는
문제를 발견했다. 이후에는 parameter-free causal population residual clock으로 두 arm의
KF/dense 역할을 맞추고, keyframe RR은 공유한 채 dense 내부 순서만 RR/interval ERCB로
바꾸는 `--mapping_interval_ercb_role_stratified`를 사용했다. 하나의 mapping loop이며
별도 polish worker는 없다.

- selector: RR vs relative-floor interval ERCB(`K=8`, `rho=.5`, `gamma=log3`)
- fixed-arrival dense: stride5/offset2/max1
- KF: RGBD+normal/full topology; dense: RGB appearance+opacity
- online tracking/native topology, fixed 1.5x sensor budget, fixed held-out mapping 제외
- post-EOS update 0, phase/topology cutoff 0, background polish 0
- VIGS commits: packet credit `a00d74ea`, role stratification `3dee95e5`
- 검증: `py_compile`, interval selector CPU test **10/10 pass**

## 결과

Primary metric은 fixed held-out PSNR이다. Delta는 `ERCB - RR`이다.

### UTMM square-1

| q | Seed | RR | ERCB | Delta | Adam RR/ERCB | KF RR/ERCB | dense RR/ERCB | late dense RR/ERCB |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 15 | 0 | 19.2049 | 19.1044 | -0.1005 | 1012/1009 | 434/433 | 578/576 | 0.82/1.54 |
| 15 | 1 | 19.0798 | 19.1519 | +0.0720 | 1008/1011 | 433/435 | 575/576 | 0.61/1.36 |
| 15 | 2 | 19.1995 | 19.2102 | +0.0107 | 1006/1008 | 432/434 | 574/574 | 1.04/1.29 |
| **15 평균** | — | **19.1614** | **19.1555** | **-0.0059 (2/3 승)** | 1008.7/1009.3 | 433.0/434.0 | 575.7/575.3 | **0.82/1.39** |
| 5 | 0 | 17.7801 | 17.7537 | -0.0263 | 336/338 | 171/172 | 165/166 | 0.39/0.39 |

q15에서 ERCB는 마지막 dense cohort service를 3/3, 평균 69.6% 높였지만 PSNR 평균은
`-0.0059dB`로 동률이다. SSIM 평균은 `+0.00175`, LPIPS는 `+0.00134`(낮을수록
좋으므로 악화)였다. 더 낮은 q5도 PSNR 동률이다. 모든 run은 topology event 수가
pair 내 동일했고 zero-tail을 통과했다.

Role stratification 전 q15 joint-pool seed0은 Adam `1010/1012`로 비슷했지만 KF/dense가
`428/582` 대 `413/599`, Gaussian이 `156,989/135,004`로 갈렸고 delta는
`-0.1837dB`였다. 이는 heterogeneous supervision 역할을 섞은 confounded 결과다.

### RPNG table_07 무재튜닝 전이

RPNG table_01은 exp03-C에서 frontend pose SVD가 붕괴했으므로, 기존 vanilla가 완주한
table_07에 같은 selector 숫자를 전이했다.

| q | RR | ERCB | Delta | Adam RR/ERCB | KF/dense RR | KF/dense ERCB | topology | Gaussian RR/ERCB | 판정 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 15 | 23.9427 | 19.3717 | -4.5710 | 1623/1329 | 613/1010 | 493/836 | 4/3 | 442,357/351,130 | service/topology 불일치, 제외 |
| 5 | 23.1830 | 23.9167 | +0.7337 | 819/979 | 369/450 | 419/560 | 3/3 | 369,795/390,261 | +160 Adam 혼입, 제외 |
| **3** | **22.3267** | **21.5324** | **-0.7943** | **612/612** | **306/306** | **306/306** | **2/2** | **471,560/472,750** | **유효 compute-matched pair, ERCB 패배** |

q15/q5는 released credit을 wall budget 안에 모두 처리하지 못했고 selector↔topology↔step
cost 폐루프로 실제 service가 달라졌다. 따라서 양수였던 q5는 ERCB 근거가 아니다. q3는
Adam, source role, topology event가 정확히 같고 Gaussian 수도 0.25% 차이라 유효한
end-to-end 저예산 pair지만 ERCB가 `-0.7943dB`였다. 모든 완주 run은 deadline/EOS 뒤
update 0회다.

## 판정

**NOT REPRODUCED.** Interval ERCB가 late-view starvation을 줄이는 동작은 확인했지만,
그 자체가 online-pose/native-topology VIGS의 held-out PSNR 수렴 가속을 보장하지 않았다.
Compute-matched 근거는 UTMM q15 평균 동률과 RPNG q3 명확한 음수다. q60 control은 낮은
예산 gate가 실패했으므로 실행하지 않았다.

고정 pose/init/topology의 homogeneous RGB replay에서는 selection count 부족이 학습
잔여량의 유효 proxy였지만, VIGS에서는 KF geometry/topology와 noisy dense appearance의
한계이득이 다르다. 따라서 이 결과를 뒤집기 위한 scene별 K/rho/q sweep은 하지 않는다.
다음 방법 축은 coverage debt만이 아니라 pose 신뢰도 또는 실제 residual/learning-progress
utility를 함께 쓰되, 같은 causal packet credit과 role-matched 계약으로 검증하는 것이다.

원본 artifact는
`results/ERCB_ablation/exp03-E_packet_budget_interaction/`에 보존한다.
