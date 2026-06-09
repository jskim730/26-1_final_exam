# Lecture 14. Advanced Physics-based Character Control — 시험 정리

> 핵심 한 줄: **"이 클립을 똑같이 따라가라(tracking)" 에서 "이 데이터셋의 스타일처럼 자연스럽게 움직여라(style matching)" 로의 전환.**
> 그 전환을 가능하게 하는 도구가 **GAIL** 의 아이디어이고, 그것을 모션 스타일에 적용한 것이 **AMP** 다.

---

## 0. 전체 스토리라인 (먼저 흐름부터 외우기)

이 강의는 "왜 AMP인가" 를 설명하기 위해 **GAIL의 이론적 토대를 거쳐 다시 AMP로 돌아오는** 구조다. 흐름 자체가 시험에 나오기 좋다.

1. **문제 제기**: Tracking 기반 제어(DeepMimic)는 예쁜 모션을 만들지만, 데이터가 크고 다양하고 비구조적(unstructured)이면 한계.
2. **모방학습 분류**: 전문가에게서 배우는 법 → BC / IRL / GAIL.
3. **GAIL**: reward를 직접 복원하지 않고 **discriminator** 로 모방. 그 본질은 **occupancy measure 매칭**.
4. **이론**: occupancy measure → expected cumulative cost → 직접 매칭은 불가능 → 완화된 목적함수 → apprenticeship learning → 한계.
5. **다시 AMP로**: discriminator를 reward로 쓰자는 GAIL의 핵심 아이디어를 **모션 스타일**에 적용.
6. **AMP의 변형**: `D(s,a)` → `D(sₜ, sₜ₊₁)`, reward = task reward + style reward.
7. **구조 / 안정화 / 결과**.

---

## 1. 도입 — 왜 AMP가 필요한가?

**Tracking 기반 physics control의 부담 (3가지):**
- 수동으로 설계한 **imitation reward** 필요
- 따라갈 **reference clip** 필요
- 모션 선택·플래닝을 위한 **추가 장치(machinery)** 필요

→ 데이터셋이 **크고(large), 다양하고(diverse), 비구조적(unstructured)** 이 되면 이 방식은 실용성을 잃는다.

**AMP의 질문:** raw 모션 클립으로부터 **일반적인 모션 스타일 prior** 를 배울 수 있는가?

**핵심 전환 (Key shift):**
- "이 클립을 추적해라" → "이 스타일로 자연스럽게 움직여라"
- high-level task와 모션 데이터셋만 주면, 에이전트가 **클립 라벨이나 순서 지정 없이** 스킬을 조합한다.

---

## 2. Physics Control Pipeline — PD Controller

AMP도 표준적인 physics 제어 루프를 사용한다.
- 정책(policy)은 **목표 관절 위치(target joint positions)** 를 출력
- **PD controller** 가 이 목표를 시뮬레이터 안에서 **토크(torque)** 로 변환

**PD 제어 식 (제어공학 기본형):**
- 오차: $e(t) = r(t) - m(t)$  (목표 $r$ − 측정값 $m$)
- 비례항: $P = K_p \, e(t)$
- 미분항: $D = K_d \, \dfrac{de(t)}{dt}$

> 직관: $P$ 는 "지금 얼마나 틀렸나", $D$ 는 "얼마나 빨리 틀어지고 있나(감쇠)". 둘을 합해 토크를 만든다.

---

## 3. Adversarial Imitation — "what" 과 "how" 의 분리

**DeepMimic = tracking 기반 imitation.** AMP의 비판:
- 다양한 모션셋에는 잘 확장되지 않는다 → clip selection, synchronization, error-metric 설계가 모두 부담.
- 그래서 문제를 재정의: "정확한 target pose를 따라가라" → **"이 데이터셋의 모션처럼 보이면서 task를 풀어라."**

### 전문가로부터 배우는 3가지 방법

| 방법 | 핵심 | 장점 | 단점 |
|---|---|---|---|
| **BC** (Behavioral Cloning) | expert action을 라벨 데이터로 보고 supervised learning | 단순·효율적 | 작은 오차가 미관측 상태로 끌고 가 **compounding error** 발생 |
| **IRL** (Inverse RL) | expert가 최적화하는 **숨은 reward/cost를 추론** | 더 원리적(왜 그렇게 행동?), 새 상황에 일반화(의도 이해) | reward 추론 후 RL까지 풀어야 해서 **어렵고 비쌈** |
| **GAIL** | **discriminator 기반 목적함수**를 학습 | hand-crafted reward 불필요, IRL을 명시적으로 풀지 않음 → **실용적** | (적대적 학습이라 불안정할 수 있음) |

> 시험 포인트: BC의 단점은 "compounding error", IRL의 단점은 "reward 추론 + RL 이중고", GAIL은 "둘을 우회하는 실용적 방법".

---

## 4. GAIL — Generative Adversarial Imitation Learning

**구조:** discriminator가 expert 행동 vs policy 행동을 구분하려 하고, policy는 그것을 **속이도록(fool)** 학습.

```
Expert trajectories (s,a) ┐
                          ├→ Discriminator D ("Expert? or Policy?") → Reward from D → Policy update
Policy rollouts    (s,a) ┘                                                              ↑__________|
```

- **Expert trajectories**: 데이터셋에서 온 (s,a) 시퀀스
- **Policy rollouts**: 현재 학습 policy가 환경과 상호작용하며 만든 (s,a) 시퀀스
- **Discriminator**: 분류기(classifier)

**두 단계를 번갈아 수행 (alternating):**
1. Discriminator를 **supervised learning** 으로 학습 → expert와 learner의 (s,a)를 구분
2. Policy를 **reinforcement learning** 으로 학습 → discriminator를 속여서 expert 행동에 가까워지도록

---

## 5. Occupancy Measure (점유 측도) — GAIL의 핵심 개념 ⭐

GAIL은 **한 순간의 action 하나를 베끼는 것이 아니라**, 시간에 걸쳐 expert 같은 **trajectory**를 만들게 한다. 그 핵심 객체가 **occupancy measure**.

**정의:**
$$\rho_\pi(s,a) = \pi(a|s) \sum_{t=0}^{\infty} \gamma^t \, \Pr(s_t = s \mid \pi)$$

- $\pi(a|s)$ : 정책 자체 (상태 s에서 a를 고를 확률)
- $\gamma^t$ : discount factor (시간 할인)
- $\Pr(s_t = s\mid\pi)$ : 정책 $\pi$ 를 따를 때 시각 t에 상태 s에 있을 확률

> 의미: **"상태 s를 얼마나 자주 방문하고, 거기 있을 때 action a를 얼마나 자주 고르나?"** = 할인된 방문 빈도(discounted visitation frequency).

**직관:** 정책은 (1) 특정 상태에 더 자주 가게 만들고, (2) 그 상태에서 특정 action을 더 자주 고른다. occupancy measure는 이 둘을 합쳐 정책의 **전체 행동 패턴**을 포착한다.

→ 따라서 **imitation = learner의 방문 패턴을 expert의 방문 패턴에 맞추는 것** ($\rho_\pi \approx \rho_{exp}$).

---

## 6. Expected Cumulative Cost (기대 누적 비용)

occupancy measure를 cost와 연결하면:

$$\mathbb{E}_\pi[c(s,a)] = \sum_{s,a} \rho_\pi(s,a)\, c(s,a)$$

- $c(s,a)$ : local cost (어떤 (s,a)가 비싸고 싼지)
- $\rho_\pi(s,a)$ : occupancy measure (그 (s,a)를 얼마나 자주 방문하는지)
- → **local cost들의 가중합**, 가중치가 곧 occupancy measure.

**왜 중요한가 (시험 포인트):**
- 고비용 영역에 오래 머무는 정책 → 누적 비용 높음
- 저비용 영역에 오래 머무는 정책 → 누적 비용 낮음
- **두 정책의 occupancy measure가 같으면, 어떤 cost function에 대해서도 expected cumulative cost가 같다.** ← 핵심 정리

### 예제 (미로)

두 (s,a): 올바른 복도 $(s_{safe}, a_{forward})$ vs 막다른 길 $(s_{trap}, a_{wander})$
- cost: $c(s_{safe},a_{forward})=0.2$, $c(s_{trap},a_{wander})=3.0$
- Expert occupancy: $4.0,\ 0.1$ / Learner occupancy: $1.5,\ 1.2$

| | 계산 | 누적 비용 |
|---|---|---|
| Expert | $4.0(0.2)+0.1(3.0)$ | **1.1** |
| Learner | $1.5(0.2)+1.2(3.0)$ | **3.9** |

→ learner는 trap에 너무 오래 머무름 → trap 체류를 줄이는 방향으로 정책 업데이트.

---

## 7. cost는 어디서 오는가? — IRL vs GAIL의 철학

문제: **참 cost function은 알 수 없다** → expected cumulative cost를 직접 최소화 불가능.

- **IRL의 입장:** "expert는 어떤 숨은 cost에 대해 최적이다. 그 cost를 추론하고, 그걸로 RL을 돌리자."
- **GAIL의 입장:** "최종 목표가 expert처럼 행동하는 정책이라면, cost를 명시적으로 복원하지 말고 **정책을 직접 배우면 안 되나?**"

---

## 8. Practical Occupancy Matching (실용적 점유 매칭)

**learning target이 바뀐다:** 알 수 없는 cost를 최소화 → **expert occupancy measure에 맞추기.**
- demonstration은 cost 라벨이 아니라 **행동 샘플** $(s_0,a_0),(s_1,a_1),\dots$
- 참 cost $c(s,a)$를 알려주지 않고, expert가 어떤 (s,a)를 자주 방문하는지($\rho_{exp}$)만 알려준다.

**왜 정확한 매칭은 불가능한가:**
- naive하게 $\rho_\pi(s,a)=\rho_{exp}(s,a)$ for **every** $(s,a)$ 를 요구하면,
- expert 데이터는 유한 → 많은 (s,a)가 미관측 → $S\times A$ 전체에 대한 제약은 **intractable**.

**완화된 목적함수 (soft mismatch penalty):**
$$\min_\pi \; d_\psi(\rho_\pi, \rho_{exp}) - H(\pi)$$

- $d_\psi(\rho_\pi,\rho_{exp})$ : 두 정책(점유 측도) 사이의 차이 → 이걸 최소화
- $H(\pi)$ : 정책의 **엔트로피**, 정책을 너무 빨리 결정론적으로 만들지 않도록 방지

### 엔트로피 $H(\pi)$ 보충

$$H(\pi) = \mathbb{E}_\pi[-\log \pi(a|s)] = -\sum_a \pi(a|s)\log\pi(a|s)$$

- 정책이 불확실(고르게 분포)할수록 **높고**, 결정론적일수록 **낮다**.

| 정책 | 확률 | 엔트로피 |
|---|---|---|
| 결정론적 | $\pi(a_1)=1.0,\ \pi(a_2)=0.0$ | $H=0$ |
| 적당히 확신 | $\pi(a_1)=0.8,\ \pi(a_2)=0.2$ | $H\approx 0.500$ |
| 완전 불확실 | $\pi(a_1)=0.5,\ \pi(a_2)=0.5$ | $H\approx 0.693$ |

> 확률을 action들에 고르게 펼칠수록 엔트로피가 높다.

---

## 9. Apprenticeship Learning (도제 학습)

직접 $d_\psi(\rho_\pi,\rho_{exp})$를 최소화하기 어려운 이유:
- **분포 미지**: $\rho_\pi, \rho_E$ 가 명시적으로 주어지지 않음
- **고차원 연속 공간**: 분포 거리 계산에 모든 (s,a) 적분 필요 → 실제로는 intractable
- **학습 신호 부재**: 스칼라 거리값만으로는 어떤 action을 늘리고 줄일지 모름 → gradient 없음

→ 점유 mismatch를 **cost/reward 신호로 변환**할 방법이 필요 → **Apprenticeship Learning**: imitation을 분포 매칭이 아니라 **reward 기반 학습**으로 공식화.

**방식:**
- reward를 선형 가정: $r(s,a) = \omega^\top \phi(s,a)$
- 이 reward로 정책 최적화 → 그 결과 정책이 expert에 더 가까워지도록 reward 업데이트
- $w$ 를 찾되: **expert → low cost, learner → high cost**
- reward와 policy를 번갈아 업데이트하면 정책이 점점 expert처럼 됨

**한계 (→ AMP로 가는 이유):**
- $\phi(s,a)$ 가 **hand-crafted feature** → expert 행동이 이 feature로 표현 안 되면 정책이 expert를 못 따라감
- 구조: **feature → reward → policy** → **feature 설계가 나쁘면 실패**

---

## 10. 연습문제 (반드시 손으로 풀어보기) 📝

**Q.** 상태 $s$ 하나와 action $a_1, a_2$. 가정:
- $\Pr(s_0=s)=1,\ \Pr(s_1=s)=0.5,\ \Pr(s_2=s)=0.25$
- $\gamma = 0.9$
- 상태 $s$ 에서 $\pi(a_1|s)=0.8,\ \pi(a_2|s)=0.2$
- $\rho_\pi(s,a_1)$ 를 구하라.

**A.** 공식 $\rho_\pi(s,a)=\pi(a|s)\sum_{t=0}^{\infty}\gamma^t\Pr(s_t=s|\pi)$ 적용:

$$\rho_\pi(s,a_1) = 0.8 \times (1 + 0.9\times0.5 + 0.9^2\times0.25)$$
$$= 0.8 \times (1 + 0.45 + 0.2025) = 0.8 \times 1.6525 = \boxed{1.322}$$

> 풀이 순서: ① $\pi(a_1|s)=0.8$ 를 앞에 빼두기 → ② 방문확률을 $\gamma^t$ 로 할인해 합 → ③ 곱하기.

---

## 11. 다시 AMP로 — Discriminator를 Reward로

Apprenticeship의 hand-crafted feature 한계를 극복: reward를 명시적으로 정의하는 대신, **expert vs policy를 구분하는 모델(discriminator)** 을 학습.

$$r(s,a) = -\log\big(1 - D(s,a)\big)$$

- $D(s,a)$ : discriminator (신경망, 매우 유연 → feature 한계 극복)
- discriminator는 **local signal** 제공, policy는 RL로 **장기 효과**를 고려
- **더 expert 같을수록 → $D$ ↑ → reward ↑**
- GAIL = GAN 프레임워크 기반의 imitation learning 알고리즘
- discriminator는 occupancy measure 매칭을 근사하는 **learned regularizer** 역할
  - (Regularizer = 목적함수에 더해져 바람직하지 않은 행동에 패널티를 주고 선호 해로 유도하는 항)

**한 페이지 요약 (논리 사슬):**
expert 데이터는 있는데 참 reward는 모름 → RL엔 reward가 필요 → IRL/apprenticeship으로 추론 시도 → feature 기반 reward는 표현력 한계 → 목표를 **occupancy matching** 으로 재정의 → 분포 직접 매칭은 어려움 → mismatch를 **학습 가능한 reward 신호** 로 변환 → **GAIL이 discriminator로 이것을 달성하고 policy를 RL로 학습.**

---

## 12. Core Idea of AMP — Task Reward + Style Reward ⭐

AMP는 GAIL의 "discriminator를 학습된 reward로 쓴다"는 아이디어를 빌리되, **타겟을 바꾼다**: 하나의 reference 클립을 추적하는 대신, **데이터셋의 일반적 스타일처럼 보이게** 한다.

**AMP의 reward:**
$$r_t = \omega^G r_t^G + \omega^S r_t^S$$

| 항 | 이름 | 의미 |
|---|---|---|
| $r_t^G$ | **Task (goal) reward** | 무엇을 할지 (예: 전진, 타겟 도달). "무엇(what)"만 알려주고 자연스러움은 모름 |
| $r_t^S$ | **Style reward** | 어떻게 움직일지 (how). **모션 클립으로부터 자동으로 학습** |

**Style reward = 학습된 discriminator:**
- AMP는 분류기 discriminator $D$ 를 학습 → 데이터셋 클립(real) vs 정책 모션(fake) 구분
- $D$ 가 정책 모션을 **real로 판단 → 높은 style reward**
- $D$ 가 **fake로 판단 → 낮은 style reward**

---

## 13. From GAIL to AMP — $D(s,a)$ → $D(s_t, s_{t+1})$ ⭐

| | discriminator 입력 |
|---|---|
| **GAIL** | $D(s_t, a_t)$ |
| **AMP** | $D(s_t, s_{t+1})$ |

**왜 바꾸나?**
- 모션 클립은 **시간에 따른 pose만** 담고 있고, 실제 물리적 action(토크·근력)은 없다.
- 따라서 AMP는 $D(s_t,a_t)$ 를 직접 못 쓴다.
- 대신 **"한 pose에서 다음 pose로의 전이(transition)가 실제 모션 데이터처럼 보이는가?"** 를 묻는다.

**직관 (핵심 통찰):**
- 모션의 정체성은 **action이 아니라 transition** 에 있다.
- "걷기"는 프레임 간 pose 변화로 알아볼 수 있다 — 어떤 힘이 만들었는지 몰라도.
- 질문의 전환: GAIL "expert가 이 상태에서 이 action을 했나?" → AMP "이 전이 $(s_t\to s_{t+1})$가 데이터셋스러운가?"

**이로 인한 이득 (What this buys us):**
- raw 모션 클립을 **직접** 사용 (mocap, 키프레임 애니메이션 모두 OK — pose만 관측되면)
- **synchronization 불필요** (클립 내 위치가 아니라 transition을 점수화)
- **composition이 공짜로 발생** (걷기/펀치/구르기/일어서기 섞여 있어도 어느 게 뭔지 몰라도 됨)

**비교표 (시험 단골):**

| | Tracking (DeepMimic) | GAIL on (s,a) | AMP on (s,s′) |
|---|---|---|---|
| reference action/torque 필요? | No, but needs phase | **Yes** | **No** |
| phase / clip selection 필요? | Yes | Often yes | **No** |
| raw mocap에서 동작? | 정렬 필요 | 어려움 | **Yes** |

---

## 14. AMP 아키텍처 — 전체 학습 루프

```
        ┌─────────────┐   a_t   ┌────────┐
        │ Environment │ ◄────── │ Policy │
        └──────┬──────┘         └────────┘
            s_t│                    ▲ ▲
               ▼                    │ │
  Dataset → ┌────────────┐  r_t^S   │ │
 (real)     │ Motion     │ ─────┐   │ │
            │ Prior (=D) │      ▼   │ │
            └────────────┘    ( + )→ r_t
  Task →    ┌────────────┐  r_t^G ▲  │
            │   Task     │ ───────┘  │
            │            │ ── g ─────┘
            └────────────┘
```

- **Dataset → Motion Prior**: reference 클립이 "진짜 모션"을 정의. Motion prior(=$D$)가 reference vs simulation 구분을 학습.
- **Environment → Motion Prior**: 캐릭터의 현재 전이 $D(s_t, s_{t+1})$ 를 $D$ 에 입력 → **style reward $r_t^S$** 출력 ("데이터셋처럼 보이나?").
- **Task → $r_t^G$**: task 모듈이 목표 진행도(예: 타겟까지 거리)를 확인 → task reward 출력.
- **Policy → $a_t$ → Environment**: 상태 $s_t$ 와 goal $g$ 로 조건화되어 action 출력 → action이 PD controller를 구동 → 시뮬레이터 step → 새 상태.

---

## 15. Training Stability — 3가지 안정화 기법

적대적(adversarial) 학습은 악명 높게 불안정하다. AMP는 3가지로 안정화:

1. **Least-squares discriminator** → 더 매끄러운 gradient, 정책이 계속 학습 가능
2. **Gradient penalty** → real data 근처에서 $D$ 가 잘 행동하도록 유지
3. **Replay buffer** → $D$ 가 정책의 최신 버릇(quirks)에 overfit 하지 않도록

> 암기 팁: **"최소제곱 D / 그래디언트 패널티 / 리플레이 버퍼"** = 매끄러운 gradient / 잘 행동하는 D / overfit 방지.

---

## 16. AMP 결과 — 실제로 되는가?

- **하나의 정책, 여러 스킬**: 56개 클립, 8명 actor, 434초의 비구조적 mocap → 단일 정책이 걷기·조깅·달리기를 하고 목표 속도에 따라 **자동 전이**.
- **휴머노이드 너머**: 알고리즘 변경 없이 → **59-DoF T-Rex, 64-DoF 개** 가 적절한 gait로 움직임.

> 시사점: 같은 알고리즘이 형태(morphology)와 무관하게 동작 → AMP의 일반성.

---

# 🔑 핵심 공식 암기 모음 (Cheat Sheet)

| # | 이름 | 공식 | 한 줄 의미 |
|---|---|---|---|
| 1 | PD 오차 | $e(t) = r(t) - m(t)$ | 목표 − 측정값 |
| 2 | PD 비례·미분항 | $P = K_p\,e(t),\quad D = K_d\,\dfrac{de(t)}{dt}$ | 현재 오차 / 오차 변화율 |
| 3 | **Occupancy measure** ⭐ | $\rho_\pi(s,a) = \pi(a\|s)\displaystyle\sum_{t=0}^{\infty}\gamma^t\Pr(s_t=s\|\pi)$ | 할인된 (s,a) 방문 빈도 |
| 4 | Expected cumulative cost | $\mathbb{E}_\pi[c(s,a)] = \displaystyle\sum_{s,a}\rho_\pi(s,a)\,c(s,a)$ | local cost의 점유 가중합 |
| 5 | 완화된 목적함수 | $\displaystyle\min_\pi\; d_\psi(\rho_\pi,\rho_{exp}) - H(\pi)$ | 점유 차이 최소화 + 엔트로피 유지 |
| 6 | 정책 엔트로피 | $H(\pi) = \mathbb{E}_\pi[-\log\pi(a\|s)] = -\displaystyle\sum_a \pi(a\|s)\log\pi(a\|s)$ | 행동 다양성 |
| 7 | Apprenticeship reward | $r(s,a) = \omega^\top \phi(s,a)$ | 선형·hand-crafted feature (한계점) |
| 8 | **GAIL discriminator reward** ⭐ | $r(s,a) = -\log\big(1 - D(s,a)\big)$ | D가 real로 볼수록 reward↑ |
| 9 | **AMP 총 reward** ⭐ | $r_t = \omega^G r_t^G + \omega^S r_t^S$ | task reward + style reward |
| 10 | **AMP discriminator** ⭐ | $D(s_t, s_{t+1})$ | action 대신 transition 판별 |

**숫자로 외울 것:**
- 엔트로피 값: $H(0.5,0.5)\approx0.693$, $H(0.8,0.2)\approx0.500$, $H(1.0,0.0)=0$
- 연습문제 답: $0.8\times(1+0.9\cdot0.5+0.9^2\cdot0.25)=0.8\times1.6525=1.322$
- AMP 결과 스케일: 56 클립 / 8 actor / 434초 / T-Rex 59-DoF / 개 64-DoF

---

# ⚡ 시험 직전 1분 점검 (개념 키워드)

- **BC / IRL / GAIL** 의 장단점 (compounding error / reward+RL 이중고 / 실용적)
- **GAIL 2단계**: ① supervised로 D 학습 ② RL로 policy 학습
- **Occupancy measure** 정의와 직관, "같은 occupancy → 같은 expected cost"
- 직접 매칭이 안 되는 3이유: 분포 미지 / 고차원 적분 / gradient 없음
- Apprenticeship의 한계 = **hand-crafted feature** → AMP가 신경망 D로 해결
- AMP의 두 변형: ① reward = **task + style** ② discriminator = **$D(s_t,s_{t+1})$**
- $D(s_t,s_{t+1})$ 인 이유: 모션 클립엔 **action이 없고 pose(transition)만** 있다
- AMP의 3대 안정화: **least-squares D / gradient penalty / replay buffer**
- AMP가 주는 것: raw mocap 직접 사용 / sync 불필요 / composition 공짜

> 원논문: *AMP: Adversarial Motion Priors for Stylized Physics-Based Character Control* — Peng, Ma, Abbeel, Levine, Kanazawa (UC Berkeley & SJTU)
