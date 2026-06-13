# Lecture 17 — Vision-Language-Action (VLA) Models 서술형 시험 대비 정리

> **이 강의의 한 줄 요약**: VLA는 *모방학습(Imitation Learning, IL)을 foundation model 위에서 대규모로 확장*한 것이다. 고전 IL이 "백지 상태에서 한 task만" 배운다는 근본 한계를 인터넷 사전학습 지식으로 극복했지만, "전문가를 베끼기만 한다"는 IL의 천장은 그대로 물려받는다. 그 천장을 넘는 일이 바로 다음 단계인 강화학습(RL)이다.

> **서술형 답안 작성 팁**: 모든 답안은 가급적 **① 왜 이게 등장했나(배경/동기) → ② 핵심 아이디어/메커니즘 → ③ 남는 문제점 → ④ 어떻게 확장되나** 순서로 엮어 쓰면 점수가 잘 나온다. 아래 정리도 이 4단 구조를 의식하고 작성했다.

---

## 0. 전체 논리 흐름 (이 한 장이 강의의 뼈대)

```
[고전 IL]  BC → DAgger / IRL / GAIL
   │  공통 약점 1: covariate shift (오류가 복합됨, O(T²ε))
   │  공통 약점 2: 한 task를 백지에서 학습, 세상 지식이 없음
   ▼
[Foundation Model Recipe]  대규모 인터넷 데이터로 pretrain → 소량 데이터로 fine-tune
   │  + Action Chunking (H개 action을 한 번에 예측 → 결정 지평을 T/H로 단축)
   ▼
[VLA]  사전학습된 vision-language model을 가져와 "행동(act)"을 가르침
   │  Vision encoder → LLM backbone → Action head
   │  Action head 방식이 두 갈래로 분기:
   │     - Discrete tokens : RT-2(2023), OpenVLA(2024)
   │     - Continuous      : pi-zero(2024, flow matching), GR00T N1(2025, dual-system)
   │  남는 한계: 전문가를 베끼기만 함 → 시연 이상으로 못 감
   ▼
[다음 단계]  RL / DPO / GRPO 로 "무엇이 더 좋은가"의 신호를 주어 시연을 넘어서게 함
```

이 흐름에서 **각 단계가 바로 앞 단계의 약점을 고치는 방식으로 등장한다**는 점이 핵심 서사다.

---

## Part 1. 모방학습에서 VLA로

### 1.1 Behavior Cloning (BC) — 출발점

- **아이디어**: 모방을 그냥 지도학습(supervised learning)으로 본다. 전문가의 (state, action) 쌍 데이터셋이 주어지면, 각 state에서 전문가의 action을 출력하도록 policy를 학습한다. 즉 state가 입력, 전문가 action이 정답 label인 **분류(classification) 또는 회귀(regression)** 문제다.
- **목적함수**:

$$\hat{\theta} = \arg\min_{\theta}\ \mathbb{E}_{(s,a)\sim D}\big[-\log \pi_\theta(a\mid s)\big]$$

- **장점**: 단순(simple)하고 안정적(stable)이며 **환경과의 상호작용이 전혀 필요 없다**(no environment interaction). 그래서 IL의 기본 출발점이다.
- **이 단순함이 숨기는 치명적 약점이 바로 covariate shift**다.

### 1.2 Covariate Shift — 핵심 실패 (서술형 최빈출)

- **메커니즘**: BC는 *전문가가 방문한 state만* 학습한다. policy가 작은 오류를 한 번 내는 순간, 학습에서 본 적 없는(unfamiliar) state에 떨어진다. 거기엔 학습 신호가 없으니 더 큰 오류를 내고, 점점 전문가 영역에서 멀어진다.
- **복합(compounding)되는 이유**: 한 번의 실수가 다음 state를 더 낯설게 만들고, 그래서 다음 실수의 확률이 더 커진다. **오류가 누적·증폭**된다.
- 그림으로: 전문가 궤적(학습에서 본 state) ↔ 작은 오류 → 학습자가 미관측 state로 표류(drift).

### 1.3 왜 오류가 제곱으로 커지나 — Quadratic Bound

- 학습된 state에서 policy가 실수할 확률을 최대 $\varepsilon$ 이라 하자.
- 각 실수가 agent를 낯선 state로 밀어내고 거기서 또 실수할 수 있으므로, 한 episode 동안 비용이 누적된다.
- 전체 오류는 horizon $T$에 대해 **선형이 아니라 제곱(quadratic)** 으로 증가한다:

$$\text{total error} \le O(T^2\varepsilon)$$

- **직관**: 실수가 *시작될 수 있는* 시점이 $T$개 있고, 각 실수가 이후 최대 $T$ step의 표류 비용을 일으킨다 → $T \times T = T^2$.
- 이 제곱 폭증이 **나이브한 모방의 가장 중요한 단일 약점**이며, 이후 모든 방법은 이걸 길들이려 한다.

### 1.4 DAgger / IRL / GAIL — covariate shift에 대한 세 가지 대응

서로 다른 각도에서 같은 문제(분포 불일치)를 공격한다.

| 방법 | 핵심 아이디어 | covariate shift를 푸는 방식 |
|---|---|---|
| **DAgger** | 학습자가 실제로 방문하는 state를 모으고 거기서 전문가에게 정답을 물음 | **학습 분포와 테스트 분포를 일치**시킴 (online으로 expert query) |
| **Inverse RL (IRL)** | action을 베끼지 않고, 전문가가 최적화하던 **보상(reward)을 추론** 후 그걸로 plan | 보상 기반이라 **분포 밖(off-distribution)에서 더 잘 일반화** |
| **GAIL** | 전문가 vs 학습자를 구분하는 discriminator를 두고, 학습자가 그걸 속이게 함 | **행동 분포 전체(whole distribution)를 매칭** (adversarial) |

- 셋 모두 표류(drift)는 줄이지만, **공통으로 남는 더 큰 한계**가 있다 (다음 절).

### 1.5 셋이 공유하는 한계 — "백지에서, 한 task만"

- 지금까지의 모든 방법은 **하나의 policy를, 하나의 task에 대해, 거의 백지(from scratch)에서** 학습한다.
- 로봇의 세상 지식은 *시연(demonstration) 집합에 나타난 것이 전부*다.
- "빨간 컵 집기"를 배웠다면, mug·bottle이나 "파란색(blue)"이라는 단어의 의미를 전혀 모른다. **본 적이 없기 때문**이다.
- 세상 전체를 덮을 만큼의 로봇 시연을 모으는 것은 **현실적으로 불가능할 만큼 비싸다**.
- 대조적으로 인간 학습자는 시작 전에 이미 사물과 지시의 의미를 안다.
- **빠진 재료(missing ingredient)**: 로봇이 시연을 보기 *전에* 미리 학습된, **넓고 재사용 가능한 세상 지식**.

### 1.6 Foundation Model Recipe — 해법의 청사진

- 대규모 언어/비전-언어 모델이 비슷한 문제를 이미 풀었다. 표준 레시피:
  1. **Pretrain**: 방대하고 다양한 인터넷 데이터로 언어·이미지의 일반 지식을 흡수.
  2. **Fine-tune / align**: 작고 정제된 데이터로 원하는 행동을 유도.
- 사전학습 모델은 이미 수천 개 객체와 단어 의미를 알기 때문에, fine-tuning에는 task별 데이터가 *훨씬 적게* 든다.
- **이 강의의 핵심 질문**: 이 레시피를 *로봇 제어*에 그대로 적용할 수 있는가? → **그게 VLA의 발상**. 사전학습된 vision-language model에서 출발해 "행동하기"를 가르친다.

### 1.7 Action Chunking — 현대 VLA가 재사용하는 필수 트릭

- **표준 policy**: 한 step에 action 하나 예측.
- **Action chunking**: 미래 action을 **짧은 시퀀스로 한 번에** 예측.

$$A_t = (a_t,\ a_{t+1},\ \dots,\ a_{t+H-1})$$

- $H$ = chunk length(한 번에 예측하는 미래 action 수). 로봇은 chunk 전체를 실행한 뒤 다시 예측 → **$H$ step마다 한 번만 결정**한다.
- **왜 도움이 되나 (서술형 포인트)**: $H$개 action에 commit하면 *유효 결정 지평(effective horizon)이 $T$ → $T/H$로 단축*된다. 1.3에서 오류는 지평의 **제곱**으로 자랐으므로, 지평을 줄이면 **복합 오류가 직접적으로 줄어든다**.
- **ACT (Action Chunking with Transformers)**: 이 기법으로 *단 몇 분의 시연*만으로 섬세한 조작(manipulation)에서 80–90% 성공률 달성.
- **가져갈 것**: 현대 VLA 대부분은 단일 action이 아니라 **action chunk**를 예측한다.

---

## Part 2. VLA Models

### 2.1 VLA란 무엇인가

- VLA = **로봇 제어를 위한 foundation model**.
- **입력**: 로봇이 실제로 가진 것 — 장면의 카메라 이미지 + 자연어 지시(language instruction).
- **출력**: 로봇 action — 예: end-effector 이동, joint 명령.
- 즉 policy가 손으로 설계한 저차원 state가 아니라 **풍부한 지각(perception) + 언어**에 조건화된다:

$$a = \pi_\theta(\text{image},\ \text{language})$$

- 결정적으로, 이미 **인터넷 규모의 image-text 데이터로 사전학습된 모델 위에** 얹어진다.

### 2.2 VLA의 해부 — 세 building block (파이프라인)

```
[Vision encoder] → [LLM backbone] → [Action head]
 image patches      vision+language     robot actions
                    fuse & reason
```

- **Vision encoder**: 이미지를 모델이 추론할 수 있는 patch embedding으로 변환. (로봇의 "눈")
- **LLM backbone**: image token + language token을 **하나의 시퀀스로 융합·추론**. 사전학습에서 물려받은 세상 지식이 여기 산다.
- **Action head**: backbone 출력을 **실행 가능한 로봇 명령**으로 변환. ← *VLA 계열을 가르는 핵심 설계 지점*.

#### Building Block 1 — Vision Encoder
- 원시 픽셀 → embedding 시퀀스. 거대 이미지 데이터로 사전학습되어 객체·질감·공간 배치를 이미 표현.
- 상보적 강점을 조합:
  - **SigLIP**: 이미지-텍스트 정렬(align) 학습 → 특징이 **의미(semantics)** 를 담음 ("이것은 컵이다").
  - **DINOv2**: 자기지도(self-supervised) 학습 → 특징이 **세밀한 공간·기하(geometry)** 정보를 담음 (정밀 제어에 유용).
  - 일부 VLA는 둘을 **융합(fuse)** 해 의미와 기하를 동시에 확보.

#### Building Block 2 — LLM Backbone
- 보통 사전학습된 (vision-)language model인 대형 transformer.
- image embedding + tokenized instruction을 한 시퀀스로 함께 처리.
- 여기에 **문법·객체 이름·관계·상식 추론** 등 세상 지식이 들어 있어, 로봇은 언어 이해를 시연에서 처음부터 배울 필요가 없다.
- 대표 backbone: **Llama 2, PaliGemma** 등 수십억(few-billion) 파라미터급 open VLM.

#### Building Block 3 — Action Head (핵심 설계 과제)
- language model이 로봇 제어기로 *변신*하는 지점.
- **중심 난제**: language model은 **이산 토큰(discrete token)** 으로 말하지만, 로봇은 **연속 공간(continuous space)** (joint angle·위치)에서 움직인다. 이산 토큰과 연속 운동을 잇는 방식이 VLA 계열을 가른다.
- 지배적 해법이 두 갈래로 갈린다 → 강의의 나머지를 조직.

### 2.3 Action을 만드는 두 가지 길 (비교표 — 서술형 핵심)

| 구분 | **Discretize actions (이산화)** | **Continuous actions (연속)** |
|---|---|---|
| 방식 | 연속 action 범위(예: −1.0 ~ +1.0)를 고정 구간(bin)으로 나눠 **각 bin을 별개의 text token**으로 취급 | 로봇 제어 명령을 **양자화하지 않은 정확한 부동소수 연속 벡터**로 직접 출력 |
| 모델 구조 | 기존 LM 구조와 Softmax를 **변경 없이 그대로** 사용 | Diffusion/Flow matching 같은 **별도 모듈**이 필요 |
| 장점 | 선택지(왼쪽 vs 오른쪽)를 서로 다른 bin에 확률을 줘 **쉽게 모델링** | 정밀한 물리값 출력 → **유체처럼 매끄럽고 빠른(50Hz+) 실시간 제어**, 미래 action 시퀀스를 **한 번의 forward로 전부** 생성 → 시간적으로 매끈 |
| 단점 | 고정 box로 반올림 → **움직임이 거칠고(choppy)**, 토큰을 하나씩 생성 → **속도 제한** | 표준 회귀로는 복잡한 인간 행동을 못 다룸 → **별도 생성 모듈 필요** |
| 대표 모델 | **RT-2, OpenVLA** | **pi-zero, GR00T N1** |

### 2.4 RT-2 (2023) — "Action을 또 하나의 언어로"

- **배경/의의**: Google DeepMind. 로봇 제어를 **텍스트 생성**으로 다루며 VLA 패러다임을 열었다. (closed model)
- 대형 VLM(**PaLI-X, PaLM-E**) 위에서, **웹 비전-언어 task와 로봇 시연을 함께(co-fine-tune)** 학습.
- **Co-training 트릭**: 로봇 action을 배우는 *와중에도* 웹 QA를 계속 연습 → **세상 지식을 잊지 않음**. 결과적으로 *이미지 묘사도, 로봇 명령도* 둘 다 하는 단일 모델.
- **action → token 변환**: 각 연속 action 차원(x, y, z 위치, 회전, gripper)을 **256개 bin**으로 분할 → 각 bin을 정수로 적어 한 action이 짧은 숫자 문자열("12 200 5 …")이 되고 token 단위로 예측.
- action이 그냥 token이라 **입출력 포맷이 변하지 않음** → 웹 사전학습이 직접 전이.
- **성과**: **emergent semantic generalization** — 어떤 로봇 시연에서도 본 적 없는 객체에 대한 지시를 따른다.

### 2.5 OpenVLA (2024) — 오픈소스 VLA

- **배경**: RT-2가 비공개라 동일 능력의 *오픈 모델*이 필요 → OpenVLA.
- 누구나 다운로드·실행·fine-tune 가능한 **70억(7B) 파라미터 VLA**.
- RT-2처럼 **이산화된 action token**을 예측 → **7-D end-effector 명령**으로 디코딩해 실행.
- **아키텍처**: `SigLIP + DINOv2 (vision encoder) → projector → Llama 2 7B (backbone) → action token`. 융합 인코더로 **의미(SigLIP) + 세밀 공간(DINOv2)** 동시 확보.
- **데이터**: **Open X-Embodiment**의 실제 로봇 궤적 약 **97만(970,000)** 개로 학습. 다양한 task와 로봇 몸체(robot body)에 걸침.
- **성과**: RT-2-X(55B)보다 **7배 작은데도 절대 성공률 16.5%p 앞섬**. **LoRA**로 소비자용 단일 GPU에서 fine-tune 가능 → 보통 연구실도 VLA에 접근.

### 2.6 왜 Action Token을 넘어서나 (continuous로 가는 동기)

- 256 bin 이산화는 편리하지만 실제 비용이 있다:
  - **거칢(Coarse)**: bin이 정밀도를 버려 *플러그 삽입·천 접기* 같은 섬세한 task에 손해.
  - **느림(Slow)**: token을 하나씩 예측 → **제어 주파수 제한**.
- 많은 실제 task는 **매끄럽고·고주파·고정밀** 운동이 필요한데 token 예측이 못 따라간다.
- → **action을 연속으로 유지하고, diffusion 계열 생성 모델로 만드는** 새로운 action head로 전환.

### 2.7 pi-zero (2024) — Flow Matching으로 연속 action

- **출처/발상**: Physical Intelligence. action을 토큰화하지 않고 **연속으로 유지**.
- 사전학습된 VLM(**PaliGemma**)에서 출발해 **별도의 action expert**를 붙임.
- action expert는 **flow matching**(diffusion 계열)으로 학습: **랜덤 노이즈를, 점진적 denoising을 통해 깨끗한 action chunk로 바꾸는** 법을 배움.
- **$H = 50$개** 미래 action을 한 번에 예측 → **최대 50Hz** 매끄러운 제어 → *빨래 개기(fold laundry)* 가 가능할 만큼 빠름.

#### Flow Matching, 직관적으로
```
random noise → (denoise, 여러 step) → clean action chunk
```
- 노이즈에서 시작해 작은 step을 여러 번 밟아 매끄럽고 유효한 action chunk에 도달.
- **연속·고주파 운동**을 만들고, **똑같이 좋은 여러 방법(multimodality)** 을 자연스럽게 표현.
- **후속**: **pi-zero-FAST**(빠른 token 변형 추가), **pi-0.5**(open-world 일반화 개선).
- 요지: RT-2·OpenVLA와 **같은 사전학습 두뇌**, 단 action head만 이산 토큰 대신 **연속 생성형**.

### 2.8 NVIDIA GR00T N1 (2025) — 휴머노이드용 foundation model

- **목표**: 범용(generalist) 휴머노이드 로봇을 위한 open foundation model.
- **정의적 특징 = dual-system 설계** (인간의 빠른/느린 인지 이론에서 영감).
- **데이터 전략**: 실제 로봇 궤적 + 인간 영상(human video) + **대량의 합성(synthetic) 데이터**의 이질적 혼합. NVIDIA가 수십만 개 합성 궤적을 생성. → 로봇학의 중심 병목인 **"실제 로봇 데이터가 희소·고비용"** 문제를 정면 공략.

#### Dual-System Architecture
```
[System 2 (slow)]  Vision-language reasoning  --plan-->  [System 1 (fast)]  Diffusion transformer
 장면+지시 해석, 무엇을 할지 계획                          plan을 실시간 motor 명령으로
```
- **System 2 (생각)**: 보고 들은 것을 해석하고 무엇을 할지 결정.
- **System 1 (행동)**: **diffusion transformer**로 유체 같은 실시간 motor 명령 생성.
- 두 시스템은 **긴밀히 결합되어 end-to-end로 함께(jointly) 학습** → 추론과 행동이 같이 향상.
- **embodiment-specific encoder**가 각 로봇의 고유한 joint를 **공유 공간(shared space)** 으로 매핑 → **한 모델이 여러 몸체를 제어**.

### 2.9 네 모델 나란히 보기 (요약표 — 암기 핵심)

| 모델 | Backbone | Action 표현 | 연도 / 비고 |
|---|---|---|---|
| **RT-2** | PaLI-X / PaLM-E | **이산 action token** (autoregressive) | 2023, closed, **VLA 시작** |
| **OpenVLA** | SigLIP+DINOv2 / Llama 2 7B | **이산 action token** | 2024, open, **97만 궤적** |
| **pi-zero** | PaliGemma 3B | **연속 chunk via flow matching** | 2024, dexterous, **50Hz** |
| **GR00T N1** | VLM (System 2) | **Diffusion transformer (System 1)** | 2025, humanoid, **dual-system** |

- **추세(서술형 단골 결론)**: 초기 VLA는 action을 토큰화해 **LLM을 그대로 재사용**했고, 최신 VLA는 더 매끄럽고 섬세한 제어를 위해 **연속 생성형 head를 추가**한다.

### 2.10 VLA는 어떻게 학습되나

근본적으로 VLA도 여전히 **모방(imitation)**: 관측이 주어졌을 때 전문가 action의 likelihood를 최대화.

**(1) Token 모델 (RT-2, OpenVLA)** — action token에 대한 일반 **next-token prediction**:

$$\max_{\theta}\ \mathbb{E}_{(o,a)\sim D}\big[\log \pi_\theta(a\mid o)\big]$$

- $o$는 카메라 이미지 + 언어 지시를 묶은 관측, $a$는 (chunk일 수 있는) action.
- 언어 모델을 학습하는 것과 **같은 cross-entropy loss**, 단지 단어 대신 action token에 대해.

**(2) Continuous 모델 (pi-zero, GR00T)** — **denoising 목적함수**:

$$\min_{\theta}\ \mathbb{E}\Big[\big\| v_\theta(A_t^{\tau},\ o)\ -\ u(A_t) \big\|^2\Big]$$

- 노이즈가 낀 action chunk를 주고, 그걸 깨끗하게 만드는 **denoising 방향(flow)** 을 예측하게 함.
- 직관: 노이즈를 깨끗한 action chunk $A_t$로 바꾸는 flow를 배움.

**공통점**: loss는 다르지만 **정신은 동일** — 둘 다 단지 *전문가를 재현하라*고 가르친다. 그리고 둘 다 **인터넷 규모 사전학습 위에** 세워져 있고, 이것이 VLA의 일반화 능력의 원천이다.

### 2.11 큰 그림 — Scaled-Up Imitation (서술형 종합 문제 대비)

- 한 발 물러서 보면 VLA의 정체는 **foundation-model 두뇌로 확장된 모방학습**.
- 학습 신호는 여전히 **"전문가를 베껴라"** — BC와 정확히 같다.
- **바뀐 것은 출발점**: 백지 네트워크가 아니라 *이미 이미지와 언어를 이해하는 모델*에서 시작.
- 그 사전학습 지식 덕에 VLA는 로봇 시연을 훨씬 넘어서는 **새 객체·새 지시에 일반화**한다.
- 이것이 강의 처음에 추구하던 보상 — **고전 IL의 "백지에서" 한계를 탈출**하는 것.

### 2.12 VLA의 한계 (서술형 단골)

- VLA는 모방학습의 **근본적 천장**을 그대로 물려받는다: **시연만큼만 잘할 수 있다**.
- 모방에는 *더 좋다/나쁘다*의 개념이 없다 — 베끼기만 하므로 **시연자(demonstrator)를 능가할 수 없다**.
- **긴 지평(long-horizon)** task — 여러 단계를 연결해야 하는 — 에 약하다.
- 학습 데이터에 없던 **드물거나 새로운(rare/novel) 상황**을 잘 못 다룬다.
- **자기 실수에서 우아하게 복구(recover)** 할 내장된 방법이 없다.
- → 이 한계를 넘으려면 *전문가가 무엇을 했나*가 아니라 **무엇이 좋은가(what is good)** 의 신호가 필요하다.

### 2.13 다음 단계 — RL로 천장을 넘기

- "무엇이 좋은가"의 신호를 주는 것이 바로 **강화학습(RL)** — 보상(reward)과 선호(preference)를 통해.
- 강의의 나머지는 모방 → 강화학습으로 루프를 닫는다:
  - **다음 강의**: **DPO, GRPO** — 선호·보상으로 모델을 직접 정렬(align)하는 두 현대 기법.
  - **그 후**: 이 기법들로 **VLA를 fine-tune** → 시연을 넘어 스스로 개선.
- **서사 정리**: *모방이 로봇에게 베끼기를 가르쳤다면, 강화학습은 개선하기를 가르친다.*

---

## 부록 A. 예상 서술형 문제 & 답안 골격

> 실제 답안에서는 각 항목을 문단으로 풀어 쓰되, 아래 키워드를 빠짐없이 엮으면 된다.

**Q1. Behavior Cloning의 covariate shift 문제를 설명하고, 오류가 horizon에 대해 제곱으로 증가하는 이유를 서술하라.**
- BC는 supervised learning이라 *전문가가 방문한 state만* 본다 → 작은 오류 → 미관측 state → 학습 신호 없음 → 더 큰 오류 → **복합(compounding)**.
- 실수 시작 가능 시점 $T$개 × 각 실수당 최대 $T$ step 표류 → $O(T^2\varepsilon)$. *선형이 아닌 제곱*임을 강조.

**Q2. DAgger, IRL, GAIL이 covariate shift를 각각 어떤 방식으로 완화하는지 비교하라.**
- DAgger: 학습자 방문 state에서 expert query → **학습/테스트 분포 일치**.
- IRL: action 대신 **reward 추론** 후 plan → off-distribution 일반화.
- GAIL: discriminator로 **행동 분포 전체 매칭** (adversarial).
- 셋 다 drift는 줄이나 **백지·단일 task·세상 지식 부재**라는 공통 한계는 못 푼다 → VLA 동기로 연결.

**Q3. Action chunking이 무엇이며 왜 compounding error를 줄이는지 수식과 함께 설명하라.**
- $A_t=(a_t,\dots,a_{t+H-1})$, $H$ step마다 한 번 결정 → 유효 지평 $T \to T/H$.
- 오류가 지평의 제곱으로 자라므로 지평 단축이 **직접적으로** 오류를 줄임. ACT 80–90% 사례.

**Q4. VLA의 세 building block을 설명하고, action head가 왜 핵심 설계 과제인지 논하라.**
- Vision encoder(SigLIP=의미, DINOv2=기하) → LLM backbone(세상 지식·융합 추론) → action head.
- 핵심 난제: **이산 토큰(LM) vs 연속 운동(로봇)** 의 간극 → 이 간극을 메우는 방식(discrete vs continuous)이 VLA 계열을 가름.

**Q5. Discrete action과 continuous action 방식을 장단점 중심으로 비교하고, 대표 모델을 들어라.**
- Discrete(RT-2, OpenVLA): LM·Softmax 그대로, 선택지 모델링 쉬움 / 거칠고 느림.
- Continuous(pi-zero, GR00T): 정밀·고주파·한 번에 chunk 생성 / 회귀로는 부족 → diffusion·flow matching 모듈 필요.

**Q6. RT-2가 VLA 패러다임에서 가지는 의의를 co-training, action 토큰화, emergent generalization 관점에서 서술하라.**
- 로봇 제어를 텍스트 생성으로 봄(패러다임 개시). 256 bin 토큰화로 **입출력 포맷 불변 → 웹 사전학습 직접 전이**. co-fine-tune으로 세상 지식 유지. 결과: 미관측 객체 지시 수행(**emergent semantic generalization**).

**Q7. OpenVLA의 설계 선택(인코더 융합, 데이터, 효율성)이 가지는 의미를 논하라.**
- SigLIP+DINOv2 융합(의미+기하), Open X-Embodiment 97만 궤적, RT-2-X(55B)보다 7배 작고 +16.5%p, LoRA 단일 GPU fine-tune → **접근성**.

**Q8. 토큰 기반 VLA의 한계를 지적하고 pi-zero가 이를 어떻게 해결하는지 flow matching과 함께 설명하라.**
- 토큰: coarse(정밀도 손실) + slow(저주파). pi-zero: PaliGemma + action expert, **flow matching으로 노이즈→clean chunk**, $H=50$, 50Hz, multimodality 표현.

**Q9. GR00T N1의 dual-system 구조와 데이터 전략이 해결하려는 문제를 서술하라.**
- System 2(느린 VL 추론·계획) + System 1(빠른 diffusion transformer 실행), end-to-end joint 학습, embodiment encoder로 다중 몸체. 데이터: real+human video+대량 synthetic → **실로봇 데이터 희소·고비용** 병목 공략.

**Q10. "VLA는 scaled-up imitation"이라는 명제를 학습 목적함수와 한계, 다음 단계(RL)와 함께 종합 논술하라.**
- 신호는 여전히 "전문가 모방"(token: cross-entropy / continuous: denoising). 바뀐 건 출발점(사전학습 두뇌) → 새 객체·지시 일반화. 한계: 시연 천장(능가 불가, long-horizon·rare·복구 약함). → "무엇이 좋은가" 신호=RL/DPO/GRPO로 시연을 넘어섬.

---

## 부록 B. 한 줄 핵심 정리 (최종 점검용)

- **Covariate shift**: BC가 본 state만 알아서 작은 오류가 미관측 영역으로 표류·복합됨.
- **Quadratic bound**: $O(T^2\varepsilon)$ — 시작점 $T$ × 표류 $T$.
- **DAgger/IRL/GAIL**: 분포일치 / 보상추론 / 분포매칭. 공통 한계는 백지·단일·무지식.
- **Foundation recipe**: pretrain(인터넷) → fine-tune(소량).
- **Action chunking**: $A_t=(a_t,\dots,a_{t+H-1})$, 지평 $T\to T/H$.
- **VLA**: $a=\pi_\theta(\text{image, language})$, 사전학습 VLM 위의 로봇 제어 foundation model.
- **3 blocks**: vision encoder(SigLIP+DINOv2) → LLM backbone(Llama2/PaliGemma) → action head.
- **두 갈래**: discrete token(RT-2, OpenVLA) vs continuous(pi-zero, GR00T N1).
- **RT-2**: 2023, closed, action을 텍스트로(256 bin), emergent generalization.
- **OpenVLA**: 2024, open 7B, 97만 궤적, RT-2-X 대비 작고 강함, LoRA.
- **pi-zero**: 2024, flow matching, $H=50$, 50Hz.
- **GR00T N1**: 2025, dual-system(S2 추론+S1 diffusion), synthetic 데이터.
- **학습**: token=cross-entropy(next-token), continuous=denoising flow.
- **본질**: scaled-up imitation — 베끼기. **천장**: 시연 못 넘음. **돌파구**: RL(DPO/GRPO).
