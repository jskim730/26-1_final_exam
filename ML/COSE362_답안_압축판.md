# Machine Learning (COSE362) — 답안 (압축판)

## Problem 1

**가정.** 각 $f^m_\theta$ 는 $C^1$ diffeomorphism이고, 따라서 $f_\theta=f^M_\theta\circ\cdots\circ f^1_\theta$ 도 $C^1$ diffeomorphism (Jacobian nonsingular). Change-of-variables theorem 적용 가능.

### (a)

임의의 measurable set $A$ 에 대해, $f_\theta$ 가 bijective이므로

$$
P(X\in A) = P\big(Z_0\in f_\theta^{-1}(A)\big) = \int_{f_\theta^{-1}(A)} p_{Z_0}(z_0)\,dz_0 .
$$

$z_0=f_\theta^{-1}(x)$ 로 치환하면 $dz_0=\left|\det\dfrac{\partial f_\theta^{-1}(x)}{\partial x}\right|dx$ 이고, $z_0\in f_\theta^{-1}(A)\iff x\in A$ 이므로

$$
\int_A p_X(x;\theta)\,dx = \int_A p_{Z_0}\!\big(f_\theta^{-1}(x)\big)\left|\det\frac{\partial f_\theta^{-1}(x)}{\partial x}\right|dx .
$$

$A$ 가 임의이므로 integrand가 일치한다:

$$
\boxed{\,p_X(x;\theta) = p_{Z_0}\!\big(f_\theta^{-1}(x)\big)\left|\det\dfrac{\partial f_\theta^{-1}(x)}{\partial x}\right| .}
$$

### (b)

Inverse는 역순 composition이므로 $z_{m-1}=(f^m_\theta)^{-1}(z_m),\ m=M,\dots,1$ (단 $z_M=x$). $f_\theta^{-1}=(f^1_\theta)^{-1}\circ\cdots\circ(f^M_\theta)^{-1}$ 에 chain rule과 $\det(AB)=\det A\det B$ 를 적용하면

$$
\left|\det\frac{\partial f_\theta^{-1}(x)}{\partial x}\right| = \prod_{m=1}^M\left|\det\frac{\partial (f^m_\theta)^{-1}(z_m)}{\partial z_m}\right|.
$$

(a)에 대입 ($p_{Z_0}(f_\theta^{-1}(x))=p_{Z_0}(z_0)$):

$$
p_X(x;\theta) = p_{Z_0}(z_0)\prod_{m=1}^M\left|\det\frac{\partial (f^m_\theta)^{-1}(z_m)}{\partial z_m}\right|.
$$

i.i.d. dataset $D$ 에 대해 $L_{\mathrm{NLL}}(\theta)=-\sum_{i=1}^N\log p_X(x^{(i)};\theta)$ 에 log를 취하면, $z_M^{(i)}=x^{(i)},\ z_{m-1}^{(i)}=(f^m_\theta)^{-1}(z_m^{(i)})$ 에 대해

$$
\boxed{\,L_{\mathrm{NLL}}(\theta) = -\sum_{i=1}^N\left[\log p_{Z_0}\!\big(z_0^{(i)}\big) + \sum_{m=1}^M\log\left|\det\frac{\partial (f^m_\theta)^{-1}(z_m^{(i)})}{\partial z_m^{(i)}}\right|\right].}
$$

---

## Problem 2

**표기.** $S(t):=\dfrac{\partial x_\theta(t)}{\partial\theta}$. $f$ 가 $C^1$ 이므로 $\dfrac{\partial\dot x_\theta}{\partial\theta}=\dot S$ 이고 $\dfrac{d}{d\theta}f=\dfrac{\partial f}{\partial x}S+\dfrac{\partial f}{\partial\theta}$.

### (a)

ODE constraint를 multiplier $\lambda(t)$ 로 결합:

$$
\mathcal{L}(\theta) = \ell\big(x_\theta(t_1)\big) - \int_{t_0}^{t_1}\lambda^\top\big(\dot x_\theta - f\big)\,dt .
$$

Integrand가 $0$ 이므로 $\nabla_\theta\mathcal{L}=\nabla_\theta J$. $\lambda$ 를 $\theta$-무관하게 두고 전개한다. Terminal term은 $S(t_1)^\top\nabla_x\ell$, integral term은 $-\int(\dot S-\frac{\partial f}{\partial x}S-\frac{\partial f}{\partial\theta})^\top\lambda\,dt$. $-\int\dot S^\top\lambda\,dt$ 에 integration by parts ($\frac{d}{dt}(S^\top\lambda)=\dot S^\top\lambda+S^\top\dot\lambda$) 를 적용해 정리하면

$$
\nabla_\theta\mathcal{L} = S(t_1)^\top\big(\nabla_x\ell-\lambda(t_1)\big) + S(t_0)^\top\lambda(t_0) + \int_{t_0}^{t_1}S^\top\Big(\dot\lambda+\big(\tfrac{\partial f}{\partial x}\big)^\top\lambda\Big)dt + \int_{t_0}^{t_1}\big(\tfrac{\partial f}{\partial\theta}\big)^\top\lambda\,dt .
$$

$S(t)$ 항을 소거하기 위해 $\lambda$ 를 $\lambda(t_1)=\nabla_x\ell,\ \dot\lambda=-\big(\frac{\partial f}{\partial x}\big)^\top\lambda$ 로 잡으면 이는 adjoint $a_\theta$ 의 정의이고, 첫째·셋째 항이 소거된다. $S(t_0)=\partial x_0(\theta)/\partial\theta$ 이므로

$$
\boxed{\,\nabla_\theta J(\theta) = \left(\frac{\partial x_0(\theta)}{\partial\theta}\right)^\top a_\theta(t_0) + \int_{t_0}^{t_1}\left(\frac{\partial f}{\partial\theta}\right)^\top a_\theta(t)\,dt .}
$$

$x_0$ 가 $\theta$-independent면 첫 항이 사라져 $\ \nabla_\theta J=\displaystyle\int_{t_0}^{t_1}\big(\partial f/\partial\theta\big)^\top a_\theta\,dt$.

### (b)

$\theta^{(k)}$ 에서: **(1)** state ODE를 $t_0\to t_1$ 적분해 trajectory와 $J$ 계산. **(2)** $a(t_1)=\nabla_x\ell(x(t_1))$. **(3)** 저장된 $x(t)$ 로 $\dot a=-\big(\frac{\partial f}{\partial x}\big)^\top a,\ \dot g=-\big(\frac{\partial f}{\partial\theta}\big)^\top a\ (g(t_1)=0)$ 를 $t_1\to t_0$ 적분 → $g(t_0)=\int(\partial f/\partial\theta)^\top a\,dt$. **(4)** $\nabla_\theta J=\big(\partial x_0/\partial\theta\big)^\top a(t_0)+g(t_0)$. **(5)** update:

$$
\boxed{\,\theta^{(k+1)}=\theta^{(k)}-\eta\,\nabla_\theta J(\theta^{(k)}).}
$$

$[x,a,g]$ 를 augmented state로 묶어 single backward integration으로 계산 (memory-efficient).

---

## Problem 3

Forward $q_\phi$ 는 inference 측, reverse $p_\theta$ 는 generative 측이다.

**Forward process.** $x_0\sim q(x_0)$ 에 매 step Gaussian noise를 더하는 fixed Markov chain:

$$
q_\phi(x_t\mid x_{t-1})=\mathcal{N}\!\big(x_t;\sqrt{1-\beta_t}\,x_{t-1},\beta_t I\big),\quad 0<\beta_t<1 .
$$

학습 대상이 아니며 reverse 학습용 supervision을 제공한다.

**Reverse process.** $x_T\sim\mathcal{N}(0,I)$ 에서 noise를 제거하는 learned Markov chain. 참 $q(x_{t-1}\mid x_t)$ 는 intractable하나 $\beta_t$ 가 작으면 근사적으로 Gaussian이므로

$$
p_\theta(x_{t-1}\mid x_t)=\mathcal{N}\!\big(x_{t-1};\mu_\theta(x_t,t),\Sigma_\theta(x_t,t)\big),\quad p_\theta(x_T)=\mathcal{N}(0,I).
$$

**Markov factorization.** Markov property $q_\phi(x_t\mid x_{0:t-1})=q_\phi(x_t\mid x_{t-1})$ 와 chain rule로

$$
q_\phi(x_{0:T})=q(x_0)\prod_{t=1}^T q_\phi(x_t\mid x_{t-1}),\qquad p_\theta(x_{0:T})=p_\theta(x_T)\prod_{t=1}^T p_\theta(x_{t-1}\mid x_t).
$$

고차원 joint가 local transition들의 product로 분해되어 tractable해진다.

**Forward → Gaussian.** $\alpha_t:=1-\beta_t,\ \bar\alpha_t:=\prod_{s=1}^t\alpha_s$. Reparameterization을 반복 대입하고 Gaussian 합의 성질을 쓰면 induction으로

$$
q(x_t\mid x_0)=\mathcal{N}\!\big(x_t;\sqrt{\bar\alpha_t}\,x_0,(1-\bar\alpha_t)I\big).
$$

$\bar\alpha_T\to0$ 이면 mean$\to0$, variance$\to1$ 이므로 $q(x_T\mid x_0)\to\mathcal{N}(0,I)$ ($x_0$ 무관). 즉 forward는 임의의 $q(x_0)$ 를 standard Gaussian으로 transport한다.

**Reverse → sample.** $x_T\sim\mathcal{N}(0,I)$ 후 $x_{t-1}\sim p_\theta(x_{t-1}\mid x_t)$ 를 $t=T,\dots,1$ 반복. $\theta$ 는 ELBO를 최대화하여 학습하며, 이는 각 step의 $p_\theta(x_{t-1}\mid x_t)$ 를 forward posterior $q(x_{t-1}\mid x_t,x_0)$ 에 맞추는 KL term들의 합으로 분해된다. 학습된 reverse는 noise를 data로 바꾸는 transport map이 되어 $x_0$ 가 $q(x_0)$ 의 sample을 닮는다.

**$q(x_0)$ vs $\mathcal{N}(0,I)$.** $q(x_0)$ 는 참 data distribution으로 복잡·multimodal하고 closed form을 모르며 sample만 주어진다. $\mathcal{N}(0,I)$ 는 단순·고정 reference로 sampling/density가 자명하다. 핵심 차이는 $q(x_0)$ 에서는 직접 sampling할 수 없지만 $\mathcal{N}(0,I)$ 에서는 가능하다는 점이며, diffusion은 forward의 supervision으로 reverse를 학습해 "noise $\to$ data" generative map을 얻는다.
