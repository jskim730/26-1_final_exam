# Machine Learning (COSE362) — 답안

> 강의안·손필기의 표기와 유도 방식을 그대로 따른다.

## Problem 1

**가정.** 각 $f^m_\theta$ 는 $C^1$ diffeomorphism이고, 따라서 $f_\theta = f^M_\theta\circ\cdots\circ f^1_\theta$ 도 $C^1$ diffeomorphism (Jacobian nonsingular). $x,z$ 는 continuous이고 같은 차원 $d$ 이다.

### (a)

임의의 measurable set $A$ 에 대해, $f_\theta$ 가 bijective이므로 $f_\theta(Z_0)\in A \iff Z_0\in f_\theta^{-1}(A)$ 이고

$$
P(X\in A) = P\big(Z_0\in f_\theta^{-1}(A)\big) = \int_{f_\theta^{-1}(A)} p_{Z_0}(z_0)\,dz_0 .
$$

volume element의 변환을 본다. $g_\theta := f_\theta^{-1}$ 로 두고 $x$ 근방을 linearize하면

$$
g_\theta(x+\Delta x) \approx g_\theta(x) + J_{g_\theta}(x)\,\Delta x, \qquad J_{g_\theta}(x) = \frac{\partial f_\theta^{-1}(x)}{\partial x},
$$

이므로 $x$ 에서의 미소 변위 $\Delta x$ 는 $z=g_\theta(x)$ 에서 $\Delta z \approx J_{g_\theta}(x)\,\Delta x$ 로 대응한다. $\mathbb{R}^d$ 에서 행렬 $A$ 가 만드는 평행육면체(parallelotope)의 부피가 $|\det A|$ 배이므로, $x$ 의 미소 부피 $dx$ 는 $z$ 에서

$$
dz = \left|\det \frac{\partial f_\theta^{-1}(x)}{\partial x}\right| dx
$$

로 변환된다. 이를 위 적분에 대입하면 ($z_0$ 가 $f_\theta^{-1}(A)$ 를 훑을 때 $x$ 는 $A$ 를 훑는다)

$$
P(X\in A) = \int_A p_{Z_0}\!\big(f_\theta^{-1}(x)\big)\left|\det \frac{\partial f_\theta^{-1}(x)}{\partial x}\right| dx .
$$

$P(X\in A)=\int_A p_X(x;\theta)\,dx$ 이고 $A$ 가 임의이므로 integrand가 일치한다:

$$
\boxed{\,p_X(x;\theta) = p_{Z_0}\!\big(f_\theta^{-1}(x)\big)\left|\det\frac{\partial f_\theta^{-1}(x)}{\partial x}\right| .}
$$

$\blacksquare$

### (b)

$f_\theta = f^M_\theta\circ\cdots\circ f^1_\theta$ 의 inverse는 역순 composition $f_\theta^{-1} = (f^1_\theta)^{-1}\circ\cdots\circ(f^M_\theta)^{-1}$ 이므로, $z_M=x$ 에서 시작하여

$$
\boxed{\,z_{m-1} = (f^m_\theta)^{-1}(z_m),\qquad m=M,\dots,1,}
$$

을 차례로 적용하면 $z_0 = f_\theta^{-1}(x)$ 가 복원된다.

$g^m := (f^m_\theta)^{-1}$ 로 두면 $f_\theta^{-1}(x) = g^1\!\big(g^2(\cdots g^M(x))\big)$ 이고, chain rule에 의해 각 factor를 대응하는 $z_m$ 에서 평가하여

$$
\frac{\partial f_\theta^{-1}(x)}{\partial x} = \frac{\partial g^1(z_1)}{\partial z_1}\cdots\frac{\partial g^M(z_M)}{\partial z_M}.
$$

$\det(AB)=\det A\,\det B$ 와 absolute value를 취하면

$$
\left|\det\frac{\partial f_\theta^{-1}(x)}{\partial x}\right| = \prod_{m=1}^M\left|\det\frac{\partial (f^m_\theta)^{-1}(z_m)}{\partial z_m}\right|.
$$

(a)에 대입 ($p_{Z_0}(f_\theta^{-1}(x))=p_{Z_0}(z_0)$):

$$
p_X(x;\theta) = p_{Z_0}(z_0)\prod_{m=1}^M\left|\det\frac{\partial (f^m_\theta)^{-1}(z_m)}{\partial z_m}\right|.
$$

i.i.d. dataset $D=\{x^{(1)},\dots,x^{(N)}\}$ 의 likelihood는 $\prod_{i=1}^N p_X(x^{(i)};\theta)$ 이고, $L_{\mathrm{NLL}}(\theta) = -\sum_{i=1}^N\log p_X(x^{(i)};\theta)$ 에 log를 취하면 ($z_M^{(i)}=x^{(i)},\ z_{m-1}^{(i)}=(f^m_\theta)^{-1}(z_m^{(i)})$)

$$
\boxed{\,L_{\mathrm{NLL}}(\theta) = -\sum_{i=1}^N\left[\log p_{Z_0}\!\big(z_0^{(i)}\big) + \sum_{m=1}^M\log\left|\det\frac{\partial (f^m_\theta)^{-1}(z_m^{(i)})}{\partial z_m^{(i)}}\right|\right].}
$$

$\blacksquare$

---

## Problem 2

**가정.** $f$ 는 $(x,\theta)$ 에 대해 $C^1$, $\ell$ 은 differentiable.

### (a)

**Sensitivity ODE.** $S_\theta(t) := \dfrac{\partial x_\theta(t)}{\partial\theta}\in\mathbb{R}^{d\times p}$ 로 둔다. state ODE $\dot x_\theta = f(x_\theta(t),t,\theta)$ 를 $\theta$ 로 미분하고 미분 순서를 교환하면 ($C^1$)

$$
\dot S_\theta(t) = \frac{\partial f}{\partial x}(x_\theta(t),t,\theta)\,S_\theta(t) + \frac{\partial f}{\partial\theta}(x_\theta(t),t,\theta).
$$

**Gradient의 표현.** $J(\theta)=\ell(x_\theta(t_1))$ 이므로 chain rule과 adjoint terminal condition $a_\theta(t_1)=\nabla_x\ell(x_\theta(t_1))$ 에 의해

$$
\nabla_\theta J(\theta) = S_\theta(t_1)^\top\,\nabla_x\ell(x_\theta(t_1)) = S_\theta(t_1)^\top a_\theta(t_1). \tag{$\ast$}
$$

**핵심 단계.** $S_\theta(t)^\top a_\theta(t)$ 를 미분하고 sensitivity ODE와 주어진 adjoint ODE $\dot a_\theta = -\big(\frac{\partial f}{\partial x}\big)^\top a_\theta$ 를 대입하면

$$
\begin{aligned}
\frac{d}{dt}\big(S_\theta(t)^\top a_\theta(t)\big)
&= \dot S_\theta^\top a_\theta + S_\theta^\top \dot a_\theta \\
&= \Big(\tfrac{\partial f}{\partial x}S_\theta + \tfrac{\partial f}{\partial\theta}\Big)^\top a_\theta - S_\theta^\top\big(\tfrac{\partial f}{\partial x}\big)^\top a_\theta \\
&= S_\theta^\top\big(\tfrac{\partial f}{\partial x}\big)^\top a_\theta + \big(\tfrac{\partial f}{\partial\theta}\big)^\top a_\theta - S_\theta^\top\big(\tfrac{\partial f}{\partial x}\big)^\top a_\theta
= \Big(\frac{\partial f}{\partial\theta}\Big)^\top a_\theta .
\end{aligned}
$$

($S_\theta^\top\big(\frac{\partial f}{\partial x}\big)^\top a_\theta$ 항이 상쇄된다.)

**적분.** 양변을 $t_0$ 에서 $t_1$ 까지 적분하면

$$
S_\theta(t_1)^\top a_\theta(t_1) - S_\theta(t_0)^\top a_\theta(t_0) = \int_{t_0}^{t_1}\Big(\frac{\partial f}{\partial\theta}\Big)^\top a_\theta(t)\,dt .
$$

$(\ast)$ 와 $S_\theta(t_0)=\dfrac{\partial x_0(\theta)}{\partial\theta}$ 를 대입하면

$$
\boxed{\,\nabla_\theta J(\theta) = \left(\frac{\partial x_0(\theta)}{\partial\theta}\right)^\top a_\theta(t_0) + \int_{t_0}^{t_1}\left(\frac{\partial f}{\partial\theta}(x_\theta(t),t,\theta)\right)^\top a_\theta(t)\,dt .}
$$

$x_0$ 가 $\theta$ 와 independent하면 $\dfrac{\partial x_0(\theta)}{\partial\theta}=0$ 이므로

$$
\boxed{\,\nabla_\theta J(\theta) = \int_{t_0}^{t_1}\left(\frac{\partial f}{\partial\theta}(x_\theta(t),t,\theta)\right)^\top a_\theta(t)\,dt .}
$$

$\blacksquare$

### (b)

현재 parameter $\theta^{(k)}$ 에서 한 번의 gradient descent step:

**Forward propagation.** state ODE를 $t_0\to t_1$ 로 적분하여 $x_\theta(t_1)$ 을 얻고 $J(\theta^{(k)})=\ell(x_\theta(t_1))$, $a(t_1)=\nabla_x\ell(x_\theta(t_1))$ 을 계산한다:

$$
x_\theta(t_1) = \mathrm{ODESolve}\big(f(x(t),t,\theta^{(k)}),\, x_0(\theta^{(k)}),\, t_0,\, t_1\big).
$$

**Backward propagation.** $[x,\,a,\,g]$ 를 augmented state로 묶어 $t_1\to t_0$ 로 한 번에 적분한다:

$$
\begin{bmatrix} x(t_0) \\[2pt] a(t_0) \\[2pt] g(t_0) \end{bmatrix}
= \mathrm{ODESolve}\!\left(
\begin{bmatrix} f(x(t),t,\theta^{(k)}) \\[2pt] -\big(\frac{\partial f}{\partial x}\big)^\top a(t) \\[2pt] -\big(\frac{\partial f}{\partial\theta}\big)^\top a(t) \end{bmatrix},\
\begin{bmatrix} x(t_1) \\[2pt] a(t_1) \\[2pt] \mathbf{0}_{|\theta|} \end{bmatrix},\
t_1,\ t_0\right),
$$

여기서 $g(t_0) = \displaystyle\int_{t_0}^{t_1}\big(\tfrac{\partial f}{\partial\theta}\big)^\top a\,dt$ 이다.

**Gradient & update.** (a)에 의해 $\nabla_\theta J(\theta^{(k)}) = \big(\tfrac{\partial x_0(\theta^{(k)})}{\partial\theta}\big)^\top a(t_0) + g(t_0)$ ($x_0$ fixed면 $g(t_0)$) 이고,

$$
\boxed{\,\theta^{(k+1)} = \theta^{(k)} - \eta\,\nabla_\theta J(\theta^{(k)}) .}
$$

순방향 intermediate activation을 저장할 필요가 없어 memory-efficient하다.

---

## Problem 3

Forward $q_\phi$ 는 inference(encoding) 측, reverse $p_\theta$ 는 generative(decoding) 측이다.

**Markov chain & factorization.** stochastic process $(x_0,x_1,\dots,x_T)$ 가 Markov property $q_\phi(x_t\mid x_{0:t-1}) = q_\phi(x_t\mid x_{t-1})$ 를 만족하므로, chain rule of probability와 결합하면

$$
q_\phi(x_{0:T}) = q(x_0)\prod_{t=1}^T q_\phi(x_t\mid x_{t-1}).
$$

reverse도 Markov ($p_\theta(x_{t-1}\mid x_{t:T}) = p_\theta(x_{t-1}\mid x_t)$) 이므로

$$
p_\theta(x_{0:T}) = p_\theta(x_T)\prod_{t=1}^T p_\theta(x_{t-1}\mid x_t).
$$

Markov 가정 덕분에 $T{+}1$ 개 high-dimensional 변수의 joint가 단순 local transition들의 product로 분해되어 tractable해진다.

**Forward process.** $x_0\sim q(x_0)$ 에 매 step Gaussian noise를 더하는 fixed Markov chain:

$$
q_\phi(x_t\mid x_{t-1}) = \mathcal{N}\big(x_t;\,\sqrt{\alpha_t}\,x_{t-1},\,(1-\alpha_t)I\big),\qquad \alpha_t = 1-\beta_t .
$$

variance schedule $\{\beta_t\}$ (linear/cosine) 은 $q_\phi(x_T)\sim\mathcal{N}(0,I)$ 이 되도록 고정 선택되며, forward 자체는 학습 대상이 아니다 (reverse 학습용 supervision 제공).

**Forward가 data를 Gaussian으로 push (Property #1).** reparameterization $x_t = \sqrt{\alpha_t}\,x_{t-1} + \sqrt{1-\alpha_t}\,\varepsilon_t,\ \varepsilon_t\sim\mathcal{N}(0,I)$ 를 recursive하게 대입하면

$$
x_t = \sqrt{\alpha_t\alpha_{t-1}\cdots\alpha_1}\,x_0 + \sum_{s=1}^t \sqrt{(1-\alpha_s)\textstyle\prod_{i=s+1}^t\alpha_i}\;\varepsilon_s .
$$

$\bar\alpha_t := \prod_{s=1}^t\alpha_s$, $c_{s,t}:=\sqrt{(1-\alpha_s)\prod_{i=s+1}^t\alpha_i}$ 로 두면 $x_t = \sqrt{\bar\alpha_t}\,x_0 + \sum_{s=1}^t c_{s,t}\varepsilon_s$. 독립 Gaussian의 합이므로 variance는 telescoping에 의해

$$
\sum_{s=1}^t c_{s,t}^2 = \sum_{s=1}^t (1-\alpha_s)\prod_{i=s+1}^t\alpha_i = 1 - \prod_{i=1}^t\alpha_i = 1-\bar\alpha_t ,
$$

따라서

$$
q(x_t\mid x_0) = \mathcal{N}\big(x_t;\,\sqrt{\bar\alpha_t}\,x_0,\,(1-\bar\alpha_t)I\big).
$$

schedule을 $\bar\alpha_T\to0$ 이 되도록 잡으면 mean $\to 0$, variance $\to I$ 이므로 $q(x_T\mid x_0)\to\mathcal{N}(0,I)$ ($x_0$ 무관). 즉 forward는 임의의 data distribution $q(x_0)$ 를 standard Gaussian으로 transport한다.

**Reverse process.** $p_\theta(x_T)=\mathcal{N}(0,I)$ 에서 시작해 noise를 제거하는 learned Markov chain:

$$
p_\theta(x_{t-1}\mid x_t) = \mathcal{N}\big(x_{t-1};\,\mu_\theta(x_t,t),\,\Sigma_\theta(x_t,t)\big).
$$

참 reverse conditional $q(x_{t-1}\mid x_t)$ 는 $q(x_0)$ 에 대한 marginalization

$$
q(x_{t-1}\mid x_t) = \frac{\int q_\phi(x_{0:T})\,dx_{0:t-2,\,t+1:T}}{\int q_\phi(x_{0:T})\,dx_{0:t-2,\,t:T}}
$$

을 요구하여 intractable하다 ($q(x_0)$ 가 복잡하기 때문). 그러나 $\beta_t$ 가 작으면 그것이 근사적으로 Gaussian이므로 위와 같이 parametrize하여 학습한다. generation은 $x_T\sim\mathcal{N}(0,I)$ 후 $x_{t-1}\sim p_\theta(x_{t-1}\mid x_t)$ 를 $t=T,\dots,1$ 반복하여 $q(x_0)$ 의 sample을 닮은 $x_0$ 를 얻는다.

**$q(x_0)$ vs $\mathcal{N}(0,I)$.** $q(x_0)$ 는 training data가 추출된 참(true) data distribution으로 복잡·multimodal하고 closed form을 모르며 sample만 주어진다. $\mathcal{N}(0,I)$ 는 단순·고정 reference로 sampling/density가 자명하며, forward chain의 종착점이자 reverse chain의 출발점이다. 핵심 차이는 $q(x_0)$ 에서는 직접 sampling할 수 없지만 $\mathcal{N}(0,I)$ 에서는 가능하다는 점이며, diffusion은 forward의 supervision으로 reverse를 학습해 "noise $\to$ data" generative map을 실현한다.
