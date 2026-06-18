# COSE361 인공지능 — Lecture 24: Recurrent Neural Networks
## 시험 예상 문제집

> 강의안(Sangmin Lee, Spring 2026)의 개념·수식·응용을 기반으로 구성했습니다.
> 먼저 **정답·해설을 가리고** 풀어본 뒤, 마지막 섹션에서 채점하세요.
>
> **계산 문제용 tanh 참고표**
> | z | −2 | −1 | −0.5 | 0 | 0.5 | 1 | 1.3 | 2 |
> |---|----|----|------|---|-----|---|-----|---|
> | tanh(z) | −0.96 | −0.76 | −0.46 | 0 | 0.46 | 0.76 | 0.86 | 0.96 |

---

## 출제 범위 한눈에 보기
- RNN의 기본 아이디어와 recurrence relation
- 입출력 구성(one-to-one / one-to-many / many-to-one / many-to-many)과 응용
- Vanilla RNN forward pass / character-level language model
- Backpropagation Through Time(BPTT)과 vanishing/exploding gradient
- LSTM의 게이트 구조와 gradient 개선 원리
- Seq2Seq Encoder-Decoder와 teacher forcing

---

# Part 1. 개념 이해 (객관식·단답형)

**문제 1 (객관식).** RNN이 sequential data를 효과적으로 다룰 수 있는 핵심 메커니즘은?
1. 매 time step마다 서로 다른 파라미터를 학습한다
2. 시퀀스가 처리되는 동안 갱신되는 내부 상태(internal state)를 유지한다
3. 입력 전체를 한 번에 받아 한 번만 연산한다
4. 출력층이 입력 길이에 따라 자동으로 늘어난다

**문제 2 (단답형).** 다음 recurrence relation에서 각 기호의 의미를 쓰시오.
$$h_t = f_W(h_{t-1}, x_t)$$
(a) $h_t$  (b) $h_{t-1}$  (c) $x_t$  (d) $f_W$

**문제 3 (서술형).** RNN이 "모든 time step에서 같은 함수와 같은 파라미터 집합"을 사용하는 것의 **장점**을 두 가지 이상 서술하시오.

**문제 4 (매칭).** 다음 입출력 구성과 응용 예시를 알맞게 연결하시오.

| 구성 | | 응용 |
|---|---|---|
| (a) one-to-many | | ① Text sentiment analysis |
| (b) many-to-one | | ② Machine translation |
| (c) many-to-many | | ③ Image captioning |

**문제 5 (수식 작성).** Vanilla RNN의 hidden state 갱신식과 출력식을 bias 항을 포함하여 쓰시오.

---

# Part 2. 계산 문제 (Forward Pass)

**문제 6.** 다음 조건의 Vanilla RNN에 대해 한 time step을 계산하시오. (bias = 0)
$$W_{hh}=\begin{bmatrix}1 & -1\\ 0 & 2\end{bmatrix},\quad
W_{xh}=\begin{bmatrix}2 & 0\\ -1 & 1\end{bmatrix},\quad
h_{t-1}=\begin{bmatrix}1\\0\end{bmatrix},\quad
x_t=\begin{bmatrix}0\\1\end{bmatrix}$$
(a) tanh 적용 전 값(pre-activation) $z = W_{hh}h_{t-1}+W_{xh}x_t$ 를 구하시오.
(b) $h_t = \tanh(z)$ 를 참고표를 이용해 구하시오.
(c) $W_{hy}=\begin{bmatrix}1 & 1\end{bmatrix},\ b_y=0$ 일 때 $y_t = W_{hy}h_t + b_y$ 를 구하시오.

**문제 7 (character-level LM 해석).**
Vocabulary `[h, e, l, o]`, one-hot 인코딩 `h:[1,0,0,0]`, `e:[0,1,0,0]`, `l:[0,0,1,0]`, `o:[0,0,0,1]`.
학습 시퀀스 "hello"에서 첫 입력 "h"에 대한 output layer 값이 $[1.0,\ 4.1,\ -3.0,\ 2.2]$ 였다.
(a) 이 시점에서 모델이 예측하는 다음 문자는? (근거 포함)
(b) 정답(target) 문자는 "e"이다. 예측은 정답과 일치하는가?
(c) 같은 입력 문자 "l"이 세 번째·네 번째 step에서 **서로 다른 출력**을 만들 수 있는 이유를 설명하시오.

**문제 8 (test-time generation).** 강의안에서는 "At test time, the model generates characters one by one, using its previous predictions as input"이라고 한다. 이 방식을 학습(training) 시점과 비교하여 설명하시오.

---

# Part 3. Gradient Flow (BPTT·핵심)

**문제 9 (유도).** $h_t = \tanh(W_{hh}h_{t-1} + W_{xh}x_t)$ 일 때, $\dfrac{\partial h_t}{\partial h_{t-1}}$ 를 유도하시오.

**문제 10 (서술형·중요).** 전체 손실의 gradient는
$$\frac{\partial L_T}{\partial W} = \frac{\partial L_T}{\partial h_T}\left(\prod_{t=2}^{T}\frac{\partial h_t}{\partial h_{t-1}}\right)\frac{\partial h_1}{\partial W}$$
로 표현된다. 이 식에서 **vanishing gradient**와 **exploding gradient**가 발생하는 메커니즘을 설명하시오.

**문제 11 (객관식).** tanh의 미분값 $\tanh'(\cdot)$ 이 vanishing gradient를 "거의 항상" 유발하는 이유로 옳은 것은?
1. $\tanh'$ 의 최댓값이 1이고 대부분 구간에서 1보다 작기 때문
2. $\tanh'$ 가 항상 1보다 크기 때문
3. $\tanh'$ 가 음수 값을 가지기 때문
4. $\tanh'$ 가 입력과 무관하게 상수이기 때문

**문제 12 (서술형).** 비선형성을 제거하면 $\dfrac{\partial L_T}{\partial W} = \dfrac{\partial L_T}{\partial h_T} W_{hh}^{\,T-1} \dfrac{\partial h_1}{\partial W}$ 이 된다.
$W_{hh}$ 의 **largest singular value**를 기준으로 vanishing/exploding 조건을 각각 쓰고, singular value가 의미하는 바를 간단히 설명하시오.

**문제 13 (매칭/객관식).** 다음 문제와 대표 해결책을 연결하시오.
(a) Exploding gradient — ( )
(b) Vanishing gradient — ( )
① RNN 아키텍처 변경(예: LSTM)  ② Gradient clipping(norm이 너무 크면 스케일 조정)

---

# Part 4. LSTM

**문제 14 (단답형).** LSTM의 세 가지 게이트 이름과 각각의 역할(한 줄)을 쓰시오.
(a) $i_t$  (b) $f_t$  (c) $o_t$

**문제 15 (빈칸/수식).** 다음 LSTM 수식의 빈칸을 채우시오. ($\odot$: element-wise 곱)
$$i_t = \sigma(W_{xi}x_t + W_{hi}h_{t-1}+b_i),\quad f_t = \sigma(W_{xf}x_t + W_{hf}h_{t-1}+b_f)$$
$$c_t = \underline{\quad(1)\quad} \odot c_{t-1} + \underline{\quad(2)\quad}\odot \tanh(W_{xc}x_t + W_{hc}h_{t-1}+b_c)$$
$$o_t = \sigma(W_{xo}x_t + W_{ho}h_{t-1}+b_o),\quad h_t = \underline{\quad(3)\quad}\odot \tanh(\underline{\quad(4)\quad})$$

**문제 16 (계산).** 다음 게이트 값이 주어졌을 때 $c_t$ 와 $h_t$ 를 구하시오. (참고표 사용)
$$c_{t-1}=[1,\ 2],\ f_t=[0.5,\ 0.5],\ i_t=[1,\ 0],\ g_t=\tanh(\cdots)=[0.8,\ -0.4],\ o_t=[1,\ 0.5]$$

**문제 17 (서술형·중요).** LSTM이 vanilla RNN의 vanishing gradient 문제를 완화할 수 있는 이유를, **cell state $c_t \to c_{t-1}$ 의 backpropagation 경로** 관점에서 설명하시오. 강의안에서 언급한 ResNet과의 유사점도 포함하시오.

---

# Part 5. Seq2Seq & Machine Translation

**문제 18 (서술형·중요).** 기계 번역에 naive many-to-many RNN을 그대로 적용할 때의 **근본적 문제점**을 두 가지 측면에서 서술하시오.

**문제 19 (객관식).** Seq2Seq Encoder-Decoder 구조가 위 문제를 해결하는 방식으로 옳은 것은?
1. 입력과 출력 길이를 항상 같게 맞춘다
2. Encoder가 입력 전체를 hidden state로 압축하고, Decoder가 임의 길이의 출력을 생성한다
3. 입력 단어마다 즉시 대응되는 출력 단어를 하나씩 만든다
4. 출력층을 제거하여 길이 문제를 회피한다

**문제 20 (단답형).** Seq2Seq에서 Encoder는 일반적인 RNN과 구조상 무엇이 다른가?

**문제 21 (서술형).** Teacher forcing이란 무엇이며, **training 시점**과 **inference 시점**에서 Decoder의 입력이 어떻게 달라지는지 설명하시오.

---

# Part 6. 종합·심화

**문제 22 (서술형).** Multilayer(stacked) RNN에서 "depth-wise"로 쌓는다는 것의 의미를 설명하시오. (time-wise 전개와 구분하여)

**문제 23 (서술형).** Computational graph 관점에서 one-to-many에는 두 가지 case가 있다.
(a) Case 1과 (b) Case 2가 후속 step에서 각각 무엇을 입력으로 받는지 설명하시오.

**문제 24 (참/거짓 + 근거).** 다음 진술의 참/거짓을 판단하고 근거를 쓰시오.
"Vanilla RNN에서 모든 time step의 $\partial L_t/\partial W$ 를 더한 것이 $\partial L/\partial W$ 이며, 긴 시퀀스일수록 초기 step으로 전파되는 gradient가 안정적으로 커진다."

---
---

# ✅ 정답 및 해설

**1.** **②**. RNN의 핵심 아이디어는 "RNNs have an internal state that is updated as a sequence is processed". 매 step 같은 파라미터를 공유하므로 ①은 틀림.

**2.** (a) $h_t$: 현재 step의 새로운 상태(new state) (b) $h_{t-1}$: 직전 step의 상태(old state) (c) $x_t$: 현재 step의 입력 벡터 (d) $f_W$: 파라미터 $W$를 갖는 함수(매 step 동일).

**3.** ① **파라미터 수가 시퀀스 길이와 무관**하게 고정되어 효율적이고 과적합 위험이 줄어든다. ② 학습하지 않은 **임의 길이의 시퀀스에도 일반화**하여 적용할 수 있다. ③ 위치에 무관하게 동일한 패턴을 인식할 수 있다(weight sharing). (두 가지 이상이면 정답)

**4.** (a)–③ image captioning(이미지 1개 → 단어 시퀀스), (b)–① sentiment analysis(단어 시퀀스 → 감정 클래스 1개), (c)–② machine translation(시퀀스 → 시퀀스).

**5.**
$$h_t = \tanh(W_{hh}h_{t-1} + W_{xh}x_t + b_h),\qquad y_t = W_{hy}h_t + b_y$$

**6.**
(a) $W_{hh}h_{t-1}=\begin{bmatrix}1\\0\end{bmatrix}$, $W_{xh}x_t=\begin{bmatrix}0\\1\end{bmatrix}$ → $z=\begin{bmatrix}1\\1\end{bmatrix}$
(b) $h_t = [\tanh(1),\ \tanh(1)] = [0.76,\ 0.76]$
(c) $y_t = 1\cdot0.76 + 1\cdot0.76 = 1.52$

**7.**
(a) output layer의 **argmax**가 예측. $[1.0, 4.1, -3.0, 2.2]$ 의 최댓값은 index 1(=4.1) → 문자 **"e"**.
(b) **일치한다**(예측 "e" = target "e").
(c) 출력 $y_t = W_{hy}h_t$ 는 hidden state $h_t$ 에 의존한다. 같은 입력 "l"이라도 그 시점까지 처리된 시퀀스가 다르면 $h_{t-1}$, 따라서 $h_t$ 가 달라지므로 출력도 달라질 수 있다. (RNN이 "맥락"을 기억하는 핵심)

**8.** **Training**: 정답 시퀀스가 주어지므로 각 step의 입력으로 **실제 정답 문자**(ground truth)를 넣는다. **Test/Inference**: 정답이 없으므로 직전 step에서 **모델이 예측한 문자**를 다음 step의 입력으로 사용해, 한 글자씩 자기회귀적으로 생성한다.

**9.**
$$\frac{\partial h_t}{\partial h_{t-1}} = \tanh'(W_{hh}h_{t-1} + W_{xh}x_t)\cdot W_{hh}$$
(연쇄법칙: tanh의 도함수 × 내부 함수의 $h_{t-1}$ 에 대한 미분 $W_{hh}$).

**10.** gradient는 $\prod_{t} \tanh'(\cdot)W_{hh}$ 형태로 **여러 step에 걸쳐 곱**해진다.
- **Vanishing**: 각 인자의 크기가 1보다 작으면, 곱이 step 수에 따라 지수적으로 0에 가까워져 초기 step으로 갈수록 gradient가 소실 → 장기 의존성 학습 실패.
- **Exploding**: 각 인자의 크기가 1보다 크면, 곱이 지수적으로 발산하여 학습이 불안정해짐(수치 overflow).

**11.** **①**. $\tanh'(z)=1-\tanh^2(z)$ 로 최댓값이 $z=0$ 에서 1이고 그 외에는 항상 1보다 작다. 따라서 곱이 누적될수록 1보다 작은 값이 곱해져 vanishing 쪽으로 작용한다.

**12.** 선형 가정에서는 $W_{hh}^{\,T-1}$ 이 핵심.
- **largest singular value > 1** → **exploding gradients**
- **largest singular value < 1** → **vanishing gradients**
- Singular value는 행렬이 벡터를 주축 방향으로 **얼마나 늘리거나 줄이는지**(stretch/shrink) 나타내는 척도다.

**13.** (a)–② Gradient clipping (exploding 대응: norm이 임계값보다 크면 스케일 다운), (b)–① 아키텍처 변경(vanishing 대응: LSTM 등 게이트 구조 도입).

**14.**
(a) $i_t$: **Input gate** — 새 입력을 cell에 얼마나 쓸지(write) 결정.
(b) $f_t$: **Forget gate** — 이전 cell 정보를 얼마나 지울지(erase) 결정.
(c) $o_t$: **Output gate** — cell 정보를 hidden state로 얼마나 드러낼지(reveal) 결정.

**15.** (1) $f_t$  (2) $i_t$  (3) $o_t$  (4) $c_t$
즉 $c_t = f_t \odot c_{t-1} + i_t \odot \tanh(\cdots)$, $\ h_t = o_t \odot \tanh(c_t)$.

**16.**
$c_t = f_t \odot c_{t-1} + i_t \odot g_t = [0.5{\times}1,\ 0.5{\times}2] + [1{\times}0.8,\ 0{\times}(-0.4)] = [0.5, 1.0] + [0.8, 0] = [\mathbf{1.3,\ 1.0}]$
$h_t = o_t \odot \tanh(c_t) = [1{\times}\tanh(1.3),\ 0.5{\times}\tanh(1.0)] \approx [\mathbf{0.86,\ 0.38}]$

**17.** Cell state의 backprop 경로($c_t \to c_{t-1}$)는 **forget gate와의 곱셈, 그리고 덧셈**만으로 구성된다(중간에 $W_{hh}$ 반복 행렬곱이나 tanh' 압축이 끼지 않음). 이 **additive highway** 덕분에 gradient가 멀리까지 비교적 손실 없이 흐를 수 있어 vanishing이 완화된다. 이는 **ResNet의 skip connection**이 덧셈 경로로 gradient를 보존하는 것과 같은 원리다.

**18.** Naive many-to-many는 입력과 출력의 **1:1 대응(input length = output length)** 을 가정한다. 그러나 ① **문장 길이가 언어마다 다르고**(예: 스페인어 6단어 → 영어 6단어가 항상 성립하지 않음), ② **어순이 달라** 입력 $x_t$ 와 출력 $\hat y_t$ 를 같은 시점에 정렬할 수 없다. 따라서 잘못된 단어가 강제 정렬된다.

**19.** **②**. Encoder가 입력 전체를 하나의 hidden state(context)로 압축하고, Decoder가 그로부터 길이에 구애받지 않는 출력을 생성하여 입력/출력 길이를 분리(decouple)한다.

**20.** Encoder는 **출력층(output layer)이 없는 표준 RNN**이다. 출력을 내지 않고 입력 시퀀스를 hidden state로 인코딩하는 역할만 한다.

**21.** **Teacher forcing**: Decoder 학습 시 직전 step의 **모델 예측이 아니라 실제 정답 토큰**을 다음 step 입력으로 넣는 기법.
- **Training**: 입력으로 ground-truth 토큰 사용(`<bos> → bonjour → le → ...` 의 정답 시퀀스). 빠르고 안정적인 학습.
- **Inference**: 정답이 없으므로 **모델이 방금 출력한 토큰**을 다음 입력으로 사용(자기회귀 생성).

**22.** **depth-wise stacking**은 한 layer의 hidden state 출력을 **같은 time step에서 다음 layer의 입력**으로 올려, RNN 층을 수직으로 여러 개 쌓는 것이다. time-wise 전개(같은 층을 시간축으로 펼침)와 달리 **표현력(깊이)** 을 늘린다. 결과적으로 시간축(가로)과 깊이축(세로) 양방향으로 확장된다.

**23.**
(a) **Case 1**: 첫 step 이후의 입력으로 **0 벡터(zeros)** 를 넣는다.
(b) **Case 2**: 첫 step 이후의 입력으로 **직전 step의 출력 $y$** 를 다시 넣는다(autoregressive). 이미지 캡셔닝·시퀀스 생성에서 흔히 쓰임.

**24.** **거짓**. 앞부분("$\partial L/\partial W = \sum_t \partial L_t/\partial W$")은 옳지만, 뒷부분이 틀렸다. 긴 시퀀스일수록 $\prod \tanh'(\cdot)W_{hh}$ 가 누적되어 초기 step으로 전파되는 gradient는 **안정적으로 커지는 것이 아니라**, 보통 1보다 작은 인자들의 곱으로 인해 **vanishing(소실)** 되거나(주로) 반대로 exploding으로 불안정해진다.

---

### 시험 직전 핵심 암기 체크리스트
- [ ] $h_t=\tanh(W_{hh}h_{t-1}+W_{xh}x_t+b_h)$, $\ y_t=W_{hy}h_t+b_y$
- [ ] 4가지 I/O 구성 ↔ 응용(captioning / sentiment / translation)
- [ ] $\partial h_t/\partial h_{t-1}=\tanh'(\cdot)W_{hh}$ → 곱의 누적이 vanishing/exploding 원인
- [ ] Exploding → **clipping**, Vanishing → **아키텍처 변경(LSTM)**
- [ ] LSTM 5식: $i_t, f_t, c_t, o_t, h_t$ 와 게이트 역할
- [ ] cell state의 **덧셈 경로** → gradient 개선(≈ ResNet)
- [ ] Seq2Seq: encoder(출력층 없음) → context → decoder, **teacher forcing**
