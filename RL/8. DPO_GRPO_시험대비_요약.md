# Lecture 18 — DPO and GRPO 서술형 시험 대비 정리

> **이 강의의 한 줄 요약**: 사전학습 LM은 *유창(fluent)하지만 도움이 되지(helpful)는 않다*. 인간 선호에 맞추는 표준 레시피가 **RLHF**(SFT → reward model → RL/PPO)인데, 이게 *reward model·RL loop·critic* 때문에 무겁다. **DPO**는 reward model과 RL loop를 통째로 없애 정렬(alignment)을 *하나의 지도학습 손실*로 바꾸고, **GRPO**는 RL은 유지하되 *critic만 제거*해 advantage를 *샘플 그룹의 통계*로 추정한다. 둘 다 같은 RLHF 목적함수에서 출발해 **버릴 부분만 다르게 고른다**.

> **서술형 답안 작성 팁**: ① 왜 등장했나(RLHF의 어떤 부담을 더나) → ② 핵심 아이디어·유도 → ③ 장단점 → ④ 어디에 쓰이고 어디로 확장되나 순으로 엮어라. 특히 **DPO 유도(파티션 함수 소거)** 와 **GRPO의 group-relative advantage**는 수식을 동반한 서술이 단골이다.

> **이전 강의(Lecture 17)와의 연결**: VLA = *scaled-up imitation* → 전문가 시연을 베끼기만 해서 *시연 이상으로 못 간다*. "무엇이 더 좋은가"의 신호(보상·선호)를 주는 도구가 바로 DPO/GRPO이고, 다음 강의에서 이걸로 VLA를 fine-tune해 시연을 넘어서게 한다.

---

## 0. 전체 논리 흐름 (이 한 장이 강의의 뼈대)

```
[문제]  사전학습 LM은 유창하나 helpful/honest/safe 하지 않음
        → 인간 선호에 정렬(align)할 방법이 필요
   ▼
[RLHF]  3단계 파이프라인
   1) SFT       : 시연 모방 → 출발 정책 π_ref (reference policy)
   2) Reward Model : 선호쌍으로 보상 r 학습 (Bradley-Terry)
   3) RL (PPO)  : 보상 최대화 + KL 제약(π_ref에서 안 멀어지게)
   │  부담 3가지: ① reward model(별도 대형망) ② RL loop(online, 불안정) ③ critic(value net)
   ▼
[두 가지 경량화] — 같은 RLHF 목적함수에서 "버릴 부분"만 다르게 선택
   ┌── DPO  : reward model + RL loop 통째 제거 → 선호쌍에 대한 1개 지도학습 손실 (offline)
   └── GRPO : RL은 유지, critic만 제거 → advantage를 group 통계로 추정 (online)
   ▼
[다음]  이 도구들로 VLA를 fine-tune → 시연을 넘어 개선
        "모방=베끼기, RL=개선하기"로 코스의 루프를 닫음
```

핵심 서사: **RLHF가 강력하지만 무겁다 → DPO와 GRPO는 각각 그 무게의 다른 부분을 덜어낸다.** 무엇을 *왜* 버리는지가 모든 비교의 축이다.

---

## 1. 동기와 RLHF (공통 배경)

### 1.1 왜 정렬(Alignment)이 필요한가
- 사전학습 LM은 인터넷 규모 텍스트에서 *다음 토큰 예측*을 매우 잘한다 → **유창(fluent)**.
- 그러나 유창함 ≠ **helpful·honest·safe**. 모델은 *인간이 실제로 어떤 답을 선호하는지* 모른다.
- 예: 질문을 받으면, 웹 텍스트가 흔히 그러듯 *답하는 대신 또 다른 질문을 이어가기도* 한다.
- 필요한 것: 원시 텍스트를 모방하는 게 아니라 **인간 선호에 정렬**시키는 방법. 원조 레시피가 **RLHF**(Reinforcement Learning from Human Feedback).

### 1.2 RLHF 3단계 파이프라인

| 단계 | 이름 | 하는 일 | 산출물 |
|---|---|---|---|
| 1 | **SFT** (supervised fine-tune) | 고품질 시연을 모방(=우리가 배운 imitation learning) | **reference policy $\pi_{\text{ref}}$** |
| 2 | **Reward Model** | 인간 선호로부터 보상 함수 학습 | 보상 $r(x,y)$ |
| 3 | **RL (PPO)** | 학습된 보상 최대화 + SFT 근처 유지 | 정렬된 정책 |

**Stage 1 — SFT**: 사전학습 모델에서 시작해 *원하는 행동의 고품질 시연*으로 fine-tune. 인간이 쓴 응답의 likelihood 최대화. 좋은 답의 **형식·스타일**은 가르치지만, 시연자가 보여준 것만 알고 **두 답을 순위 매기지 못한다**. 결과로 견고한 출발 정책 $\pi_{\text{ref}}$를 얻는다.

**Stage 2 — Reward Model**: 선호를 포착하려고 인간이 같은 prompt에 대한 두 응답을 비교해 더 나은 쪽을 고른다 → **선호쌍(preference pair)**: 승자 $y_w$, 패자 $y_l$ (prompt $x$). $y_w$가 $y_l$을 이길 확률을 **Bradley-Terry 모델**로 모델링:

$$P(y_w > y_l \mid x) = \sigma\big(r(x, y_w) - r(x, y_l)\big)$$

- 직관: 보상 격차가 클수록 승자가 더 확신 있게 선호됨(sigmoid가 확률로 압축). 관측된 인간 선택의 likelihood를 최대화해 $r$을 학습.

**Stage 3 — KL 제약 RL**: 학습된 보상을 PPO로 최대화. 단, 순수 보상 최대화는 *언어를 벗어나 reward model을 악용(exploit)*하게 만들므로, SFT reference에서 멀어지지 않도록 **KL 페널티**를 추가:

$$\max_{\pi}\ \mathbb{E}_{x\sim D,\ y\sim\pi}\big[r(x,y)\big]\ -\ \beta\, D_{\text{KL}}\big(\pi(y\mid x)\,\|\,\pi_{\text{ref}}(y\mid x)\big)$$

- $\beta$가 trade-off 조절: **높은 $\beta$** → reference에 가깝게 유지(보수적), **낮은 $\beta$** → 보상을 더 강하게 추격.
- **이 KL 제약 목적함수가 RLHF의 심장이며, DPO가 그대로 재사용하는 바로 그 식이다.** (서술형 핵심)

### 1.3 RLHF는 강력하지만 무겁다 (DPO/GRPO의 출발점)
세 가지 실질적 통증:
1. **별도 reward model** — 학습·저장해야 하는 추가 대형 네트워크.
2. **full RL loop + online sampling** — 복잡하고 튜닝이 불안정.
3. **PPO의 value network(critic)** — 메모리상 또 하나의 모델 복사본.

→ 두 현대 기법이 각각 이 부담의 다른 부분을 제거하며 강의의 두 축을 이룬다.
- **DPO**: reward model과 RL loop를 *통째로 제거* → 정렬을 *하나의 지도학습 손실*로.
- **GRPO**: 보상 기반 RL은 유지하되 *critic을 제거* → advantage를 *샘플 그룹*에서 추정.

---

## 2. Direct Preference Optimization (DPO)

### 2.1 선호 데이터의 모습
- RLHF의 reward model이 쓰던 *같은 종류*의 선호 데이터로 학습.
- 각 예시 = 한 prompt + 두 후보 응답 + 어느 쪽이 나은지의 인간 라벨.
  - 예: prompt "하늘이 왜 파란지 설명하라" / 승자 $y_w$ = 빛의 산란을 명확·정확·간결히 설명 / 패자 $y_l$ = 모호하거나 일부 틀리거나 장황.
- **수치 점수(numeric score)는 전혀 필요 없고, 상대적 판단 $y_w > y_l$만 필요.**
- 절대 평점보다 **수집이 싸고 신뢰도가 높다** — 사람은 *점수 매기기보다 비교를 더 일관되게* 하기 때문.

### 2.2 DPO의 한 문장 아이디어
- 질문: reward model을 학습하거나 RL을 돌리지 *않고* **바로 그 RLHF 목적함수**를 최적화할 수 있나?
- 답: 가능. 결과는 선호쌍에 대한 **하나의 분류(classification)형 손실**.
- reward model 없음, 학습 중 sampling 없음, value network 없음, clipping 없음 — 그냥 지도학습 손실.
- **트릭 = 변수 변환(change of variables)**: 보상을 *정책 자신*으로 표현 → **reward model이 소거**된다.

### 2.3 유도 4단계 (★서술형 최빈출 — 통째로 설명할 수 있어야 함)

**Step 1 — 최적 정책의 닫힌 형태(closed form)**
Stage 3의 KL 제약 목적함수는 알려진 최적해를 갖는다:

$$\pi^*(y\mid x) = \frac{1}{Z(x)}\ \pi_{\text{ref}}(y\mid x)\ \exp\!\Big(\tfrac{1}{\beta}\, r(x,y)\Big)$$

- 의미: reference 정책을 *지수화된 보상*으로 재가중(reweight)한 뒤, 분배함수(partition function) $Z(x)$로 재정규화.
- **문제**: $Z(x)$는 *가능한 모든 응답*에 대해 합하므로 직접 계산이 불가능. (이래서 나이브한 접근은 여전히 RL이 필요)

**Step 2 — 보상을 정책으로 표현 (로그 취해 재배열, 단순 대수)**

$$r(x,y) = \beta \log\frac{\pi^*(y\mid x)}{\pi_{\text{ref}}(y\mid x)} + \beta \log Z(x)$$

- 핵심 재매개변수화(reparameterization): 보상이 이제 *정책과 reference만으로* 쓰였다.
- 골치 아픈 $Z(x)$가 아직 남았지만 — **$Z(x)$는 prompt $x$에만 의존하고 응답 $y$에는 의존하지 않는다.** 이 한 가지 사실이 다음 단계를 가능케 한다.

**Step 3 — 분배함수가 소거된다**
Step 2의 보상식을 Stage 2의 Bradley-Terry 모델에 대입. BT는 *같은 prompt $x$*에 대한 **보상 차이** $r(x,y_w) - r(x,y_l)$만 사용한다. $Z(x)$는 $x$에만 의존하므로 승자·패자에 **동일** → 차이에서 **상쇄**된다:

$$P(y_w > y_l \mid x) = \sigma\!\left(\beta\log\frac{\pi^*(y_w\mid x)}{\pi_{\text{ref}}(y_w\mid x)} - \beta\log\frac{\pi^*(y_l\mid x)}{\pi_{\text{ref}}(y_l\mid x)}\right)$$

- 계산 불가능하던 $Z(x)$가 사라지고, **별도 reward model의 필요도 함께 사라진다.**

**Step 4 — DPO 손실**
최적 정책 $\pi^*$를 *학습 가능한 정책 $\pi_\theta$*로 바꾸고, 관측된 선호의 likelihood를 최대화(=NLL 최소화):

$$\mathcal{L}_{\text{DPO}} = -\,\mathbb{E}_{(x,y_w,y_l)\sim D}\left[\log\sigma\!\left(\beta\log\frac{\pi_\theta(y_w\mid x)}{\pi_{\text{ref}}(y_w\mid x)} - \beta\log\frac{\pi_\theta(y_l\mid x)}{\pi_{\text{ref}}(y_l\mid x)}\right)\right]$$

- 이것은 **선호쌍에 대한 이진 분류 손실**일 뿐 — 보통의 gradient descent로 학습 가능.
- $\beta\log\dfrac{\pi_\theta(y\mid x)}{\pi_{\text{ref}}(y\mid x)}$ 항이 **암묵적 보상(implicit reward)** 역할 → *정책 자신이 reward model이 하던 역할을 대신*한다.

### 2.4 DPO 손실이 실제로 하는 일 (직관)
gradient descent가 정책을 다음과 같이 민다:
- 선호 응답 $y_w$의 확률을 reference 대비 **증가**.
- 비선호 응답 $y_l$의 확률을 reference 대비 **감소**.
- **reference 정책이 업데이트를 고정(anchor)** → RLHF의 KL 페널티가 하던 역할을 그대로 수행.
- 따라서 DPO는 RLHF와 **같은 KL 제약 목적함수**를 최적화하되, *선호에 대한 직접적 지도학습 손실*로 한다.
- reward model·sampling·RL 불안정성 없음 → 이래서 정렬용으로 폭발적으로 인기를 끌었다.

### 2.5 RLHF vs DPO 한눈에
```
RLHF (3단계):  선호쌍 → reward model → RL loop(PPO) → 정렬 모델
DPO  (1단계):  선호쌍 → 하나의 지도학습 손실 → 정렬 모델
```
- **장점**: 더 단순, 안정적, 완전 offline, reward model·critic 불필요.
- **단점**: **online exploration이 없다** → 품질이 *선호 데이터셋에 의해 상한이 정해지고*, 그 데이터에 **과최적화(over-optimize)** 될 수 있다.

---

## 3. Group Relative Policy Optimization (GRPO)

### 3.1 복습: PPO는 critic이 필요하다 (제거 대상의 정체)
- PPO는 각 action의 **advantage 추정치**로 정책을 개선.
- 그 advantage를 계산하려고 두 번째 네트워크 **value function(critic)** 을 학습 — 기대 return을 예측.
- critic은 *별도의 대형 모델* → 메모리 일부를 두 배로, 자체 학습 불안정도 추가.
- **학습 초기 critic은 부정확** → 만들어내는 advantage가 **noisy**, 정책을 불안정화할 수 있다.
- **이 critic이 바로 GRPO가 제거하려는 특정 부품**이며, PPO의 나머지 기계장치는 유지한다.

### 3.2 다른 절단(cut): RL은 유지, critic은 버린다
- DPO는 *보상 기반 RL 자체*를 없앴다. GRPO는 **반대 절단** — 보상 RL은 유지, *critic만* 제거.
- PPO는 advantage(어떤 action이 기대보다 얼마나 더 나은가)로 정책을 갱신:

$$L_{\text{PPO}} = \mathbb{E}\big[\min\big(\rho_t A_t,\ \text{clip}(\rho_t, 1-\varepsilon, 1+\varepsilon)\,A_t\big)\big]$$

- 여기서 $A_t$를 value network(critic)가 추정 → 비싸고 불안정.
- **GRPO의 질문: critic 없이 advantage를 추정할 수 있나?**

### 3.3 GRPO의 핵심 아이디어 — 그룹 안에서 비교
- 각 prompt에 대해 현재 정책에서 **응답 그룹 전체**를 샘플링한 뒤, 보상으로 *전부 채점*:
```
prompt q ─┬─ response o1 → r1
          ├─ response o2 → r2
          ├─ response o3 → r3
          └─ response o4 → r4
advantage = "그룹 평균보다 얼마나 위인가"
```
- **그룹 자신의 평균 보상이 baseline** → value network가 필요 없다.
- 그룹 평균 위 응답은 강화(reinforce), 아래 응답은 억제(suppress).

### 3.4 Group-Relative Advantage (★핵심 수식)
$G$개 응답을 샘플링해 보상을 모으고, 응답 $i$의 advantage를 **그룹 안에서 표준화**:

$$A_i = \frac{r_i - \text{mean}(r_1, \dots, r_G)}{\text{std}(r_1, \dots, r_G)}$$

- **평균을 빼는 것** = baseline 역할, **표준편차로 나누는 것** = scale 자동 정규화.
- 이것이 **value network 전체를 그룹 보상에 대한 단순 통계량으로 대체**한다.
- 또한 reward model이 *같은 prompt의 응답들을 비교*하며 학습되는 방식과도 잘 맞는다.

### 3.5 GRPO 목적함수
group-relative advantage를 PPO식 clipped 목적함수에 넣고 그룹에 대해 평균:

$$\mathcal{L}_{\text{GRPO}} = \mathbb{E}\left[\frac{1}{G}\sum_{i=1}^{G}\min\big(\rho_i A_i,\ \text{clip}(\rho_i, 1-\varepsilon, 1+\varepsilon)\,A_i\big)\ -\ \beta\, D_{\text{KL}}\big(\pi_\theta \| \pi_{\text{ref}}\big)\right]$$

- 비율 $\rho_i$는 새 정책 / 옛 정책 확률을 비교, **clipping이 각 업데이트를 작게 유지** — PPO와 정확히 동일.
- reference로의 **KL 페널티**가 너무 멀리 표류하지 않게 함 — RLHF와 동일.
- **사라진 것은 critic 하나뿐**, 나머지는 모두 PPO를 그대로 따른다.

### 3.6 critic을 버리는 게 왜 도움이 되나
- PPO의 critic은 학습해야 하는 별도 네트워크이고 *학습 초기에 크게 틀릴* 수 있다.
- 보상이 **희소(sparse)** 할 때(긴 답 끝에 점수 하나) 나쁜 critic은 *noisy하고 진동(oscillating)하는 advantage*를 주입.
- GRPO의 baseline은 *실제로 샘플된 보상의 경험적 평균* → **근사(approximation)도 없고 bootstrapping 오차도 없다**. (서술형 포인트)
- **장점**: 메모리 절약(value-net 복사본 없음), 더 단순한 학습, 내장된 보상 정규화.
- **비용**: prompt마다 *여러 응답을 샘플*해야 함 → compute 증가. 팀들은 보통 작은 그룹 크기 $G \approx 4$로 시작.

### 3.7 실전: DeepSeek
- GRPO는 **DeepSeekMath**에서 도입, **DeepSeek-R1** 추론(reasoning) 모델 학습에 사용.
- **검증 가능한 보상(verifiable reward)** — 정답을 자동으로 확인할 수 있는 **수학·코드** — 에 특히 강하다.
- DeepSeek-R1은 GRPO를 *주 RL 단계*로 써서 frontier 모델급 추론 성능에 도달하면서도 **open-weight** 유지.
- 실전 메모: advantage가 전적으로 *그룹 내 비교*에 의존하므로 보통 **큰 배치 + prompt당 많은 샘플** 사용.

---

## 4. DPO vs GRPO 비교 (★대조형 서술 핵심)

| 항목 | **DPO** | **GRPO** |
|---|---|---|
| 무엇을 제거하나 | **reward model + RL loop** | **critic (value network)** |
| 필요한 데이터 | 선호쌍 (offline) | prompt + 보상 (online sampling) |
| On/Off-policy | **Off-policy** (지도학습) | **On-policy** (RL) |
| 가장 적합한 곳 | 일반적 선호 정렬 | 검증 가능 task (수학·코드) |
| 대표 사례 | 오픈소스 chat 정렬 | DeepSeek-R1 추론 |

- **둘 다 같은 RLHF 목적함수에서 출발**하며, 단지 *버릴 부품을 다르게 고를 뿐*이다. (이 한 줄이 종합 서술의 결론)

---

## 부록 A. 예상 서술형 문제 & 답안 골격

> 답안은 키워드를 문단으로 풀어 쓰되, 가급적 수식을 한 번씩 인용하면 좋다.

**Q1. 사전학습 LM이 "유창하지만 도움이 되지 않는다"는 말의 의미와, RLHF 3단계가 이를 어떻게 해결하는지 서술하라.**
- 유창=다음 토큰 예측을 잘함, 그러나 인간이 선호하는 답이 뭔지 모름(질문에 또 질문으로 답하는 예). RLHF: SFT(형식·스타일 모방, $\pi_{\text{ref}}$) → reward model(선호쌍으로 *순위* 학습) → PPO(보상 최대화 + KL 제약으로 $\pi_{\text{ref}}$ 근처 유지).

**Q2. RLHF의 세 가지 실질적 부담을 설명하고, DPO와 GRPO가 각각 어느 부분을 제거하는지 대비하라.**
- 부담: ① reward model(별도 대형망) ② online RL loop(불안정) ③ critic(메모리·불안정). DPO=①+②(RL 자체) 제거 → 1개 지도학습 손실. GRPO=③(critic) 제거, RL은 유지 → group baseline. *둘 다 같은 목적함수, 버릴 부품만 다름*.

**Q3. (★) DPO가 reward model 없이 RLHF 목적함수를 최적화하는 과정을 유도와 함께 설명하라.**
- Step1: KL 제약 최적해 $\pi^*=\frac{1}{Z(x)}\pi_{\text{ref}}\exp(\frac1\beta r)$, 단 $Z(x)$ 계산 불가.
- Step2: 로그·재배열로 $r(x,y)=\beta\log\frac{\pi^*}{\pi_{\text{ref}}}+\beta\log Z(x)$. **$Z(x)$는 $x$에만 의존**.
- Step3: Bradley-Terry는 *보상 차이*만 사용 → $Z(x)$가 승자·패자에 동일 → **상쇄**. reward model도 불필요.
- Step4: $\pi^*\to\pi_\theta$ 치환, NLL 최소화 = **선호쌍 이진 분류 손실** $\mathcal{L}_{\text{DPO}}$. $\beta\log\frac{\pi_\theta}{\pi_{\text{ref}}}$가 *암묵적 보상*.

**Q4. DPO 손실이 정책을 어떻게 갱신하며, reference policy가 어떤 역할을 하는지 직관적으로 설명하라.**
- $y_w$ 확률↑(ref 대비), $y_l$ 확률↓(ref 대비). reference가 업데이트를 anchor → *RLHF의 KL 페널티와 같은 역할*. 곧 같은 KL 제약 목적함수를 직접 지도학습으로 푸는 것.

**Q5. DPO의 장점과 한계를 RLHF와 비교해 논하라.**
- 장점: 단순·안정·완전 offline, reward model/critic 불필요. 한계: *online exploration 없음* → 품질이 선호 데이터셋에 상한, *과최적화* 위험.

**Q6. PPO에서 critic의 역할과 문제점을 설명하고, GRPO가 이를 어떻게 대체하는지 서술하라.**
- critic=advantage용 value net, 별도 대형망·초기 부정확→noisy advantage. GRPO: prompt당 $G$개 샘플의 보상으로 **그룹 평균=baseline**, $A_i=\frac{r_i-\text{mean}}{\text{std}}$로 표준화 → critic 불필요. 경험적 평균이라 *근사·bootstrapping 오차 없음*.

**Q7. Group-relative advantage 수식의 각 항(평균 빼기, std로 나누기)이 갖는 의미를 설명하라.**
- 평균 빼기=baseline(분산 감소), std 나누기=scale 자동 정규화. value net을 *단순 통계량*으로 대체. reward model이 같은 prompt 응답을 비교하는 방식과 정합.

**Q8. GRPO의 목적함수가 PPO와 어디가 같고 어디가 다른지 서술하라.**
- 같음: ratio $\rho_i$ + clipping(작은 업데이트), reference로의 KL 페널티. 다름: critic 기반 $A_t$ 대신 *group-relative $A_i$*, 그룹 평균. *critic만 사라지고 나머지는 PPO 그대로*.

**Q9. GRPO를 critic 없이 쓰는 것의 이득과 비용을 설명하고, DeepSeek 사례와 연결하라.**
- 이득: 메모리↓, 단순, 내장 정규화, 근사 오차 없음. 비용: prompt당 다중 샘플 → compute↑($G\approx4$ 시작). DeepSeekMath 도입, DeepSeek-R1의 주 RL 단계, *검증 가능 보상(수학·코드)*에 강함, open-weight로 frontier급 추론.

**Q10. (종합) DPO와 GRPO는 "같은 RLHF 목적함수에서 버릴 부품만 다르게 고른다"는 명제를 데이터·on/off-policy·적합 task 관점에서 논술하라.**
- 출발점 동일(KL 제약 보상 최대화). DPO=reward model+RL 제거, 선호쌍 offline, off-policy 지도학습, 일반 선호 정렬. GRPO=critic 제거, prompt+보상 online, on-policy RL, 검증 가능 task. → 다음 단계: 둘로 VLA를 fine-tune해 *시연의 천장*을 넘김.

---

## 부록 B. 한 줄 핵심 정리 (최종 점검용)

- **정렬 동기**: LM은 fluent하나 helpful/honest/safe 아님 → 인간 선호에 맞춰야 함.
- **RLHF**: SFT($\pi_{\text{ref}}$) → reward model(Bradley-Terry) → PPO(보상 최대화 + $\beta$·KL 제약).
- **RLHF 목적함수**: $\max_\pi \mathbb{E}[r] - \beta D_{\text{KL}}(\pi\|\pi_{\text{ref}})$ — DPO가 재사용하는 심장.
- **RLHF 부담**: reward model + RL loop + critic.
- **DPO 트릭**: 변수 변환으로 보상을 정책으로 표현 → $Z(x)$가 $x$에만 의존 → BT의 보상 차이에서 **상쇄**.
- **DPO 손실**: 선호쌍 이진 분류, $\beta\log\frac{\pi_\theta}{\pi_{\text{ref}}}$ = 암묵적 보상. 장점=단순·안정·offline, 단점=데이터 상한·과최적화.
- **GRPO 동기**: PPO critic이 비싸고 초기 부정확 → noisy advantage.
- **GRPO advantage**: $A_i=\dfrac{r_i-\text{mean}}{\text{std}}$ (그룹 내 표준화) → critic 대체, bootstrapping 없음.
- **GRPO 목적함수**: PPO clipped + KL, critic만 제거. 비용=prompt당 다중 샘플($G\approx4$).
- **GRPO 실전**: DeepSeekMath/R1, 검증 가능 보상(수학·코드)에 강함, open-weight.
- **DPO vs GRPO**: 제거 대상(reward+RL vs critic) / 데이터(선호쌍 offline vs prompt+보상 online) / off vs on-policy / 일반 선호 vs 검증 task.
- **다음**: 둘로 VLA fine-tune → 시연을 넘어 개선. "모방=베끼기, RL=개선하기"로 루프 닫기.
