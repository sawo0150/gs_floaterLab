# 발표 수식 정의 — v003

논문 자체는 수정하지 않았다. 수식은 논문 §3.1과 §3.2의 개별 view count 정식화를 발표용으로 축약했다.

## 3.1

`N(t) - N0 ≈ S(t) / κ`

N: 학습 pool 크기, S: 완료된 GPU mapping update 수, κ: 새 view당 필요한 update 수.
후보가 충분하고 허용량만큼 즉시 추가하는 경우의 비례 관계다.
정확한 상한은 `Nmax(t) = min(M(t), N0 + floor(S(t)/κ))`이며
M은 현재까지 도착한 사용 가능한 view 수다. GPU utilization/벽시계 시간과 비례한다고 주장하지 않는다.

## 3.2

이 발표에서 normalized variance는 **후보 수 N으로 정규화한 절반 분산**이다.
평균 count의 제곱으로 나누는 CV² 또는 exp76의 mean-normalized interval service와 다르다.
사용자가 정규화 방식까지 지정하지 않았으므로, 원고의 count-softmax 유도를 유지하는 N 정규화를 채택했다.

`Vnorm(n) = (1/(2N)) Σ_i (n_i - mean(n))²`

한 선택 전후 후보 집합을 고정하면

`Δ_i Vnorm = (n_i - mean(n) + (1 - 1/N)/2) / N`.

목적함수:

`min_{p ∈ simplex} E_{i~p}[Δ_i Vnorm(n)] - τ H(p)`, `H(p) = -Σ_i p_i log p_i`, `τ > 0`.

최소화이므로 entropy 항의 부호는 음수다. 이미 정해진 현재 분산만 목적함수에 넣으면
p에 의존하지 않아 count-aware 해를 얻을 수 없다. 따라서 선택 후 분산의 **기대 변화량**을 쓴다.

정상조건을 풀면 모든 후보에 공통인 항이 소거되어

`p_i = softmax_i(-n_i/(N τ)) = exp(-β n_i) / Σ_j exp(-β n_j)`, `β = 1/(N τ)`.

논문의 비정규화 potential Φ=(1/2)Σ(n_i-mean(n))²와 같은 분포군이며 temperature를
스케일 변환한 것이다. pool이 변해도 β를 고정하려면 τ는 1/(Nβ)로 달라진다.
β=1/τ라는 기존 원고 관계를 그대로 가져오면 안 된다.

도식 A–D는 여기서는 개별 view 선택 횟수다. interval/frame-size weight 및 mean-service
정규화 구현 전체와 동일하다는 주장은 하지 않는다. 블록 비복원 추출은 남은 후보에서
조건부 softmax를 적용하며, 그림의 예시 순서는 실제 측정값이 아니다.

## 편집

수식 원문은 build_ppt.py와 equations/equations.json에 보존한다.
수식만 360 dpi PNG이며 텍스트·도식은 기존처럼 native PowerPoint 요소다.
수식을 바꾸려면 equation(...)의 LaTeX 문자열을 수정하고 재빌드한다.
