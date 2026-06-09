# Lecture 11. Euler Transforms & Quaternions — 시험 정리

> 컴퓨터 그래픽스 (Prof. H. Kang) / Euler 회전과 Quaternion 핵심 정리
> 구성: ① 개념 정리 → ② **핵심 공식 암기 시트** → ③ 연습문제 풀이

---

## 0. 한눈에 보는 큰 그림

3D 방향(orientation)을 표현하는 3가지 방법과 그 관계를 먼저 잡고 가면 전체 흐름이 보입니다.

| 표현 방법 | 저장 형태 | 장점 | 단점 |
|---|---|---|---|
| **Euler angles** | 각도 3개 $(\theta_1,\theta_2,\theta_3)$ | 직관적, 계층 변환에 효율적 | gimbal lock, 보간(interpolation) 이상, 순서 의존 |
| **Rotation matrix** | $3\times3$ 행렬 (9개) | 변환 합성 쉬움 | 저장 비효율, 수치 오차 누적 |
| **Quaternion** | 실수 4개 $(x,y,z,w)$ | singularity 없음, 부드러운 보간, 미분 간단 | 직관성 떨어짐 |

핵심 메시지: **Euler angle의 한계(gimbal lock + 보간 문제)를 극복하기 위해 quaternion을 쓴다.** 현대 게임 엔진·AR/VR·렌더러는 카메라/오브젝트/관절 방향을 모두 unit quaternion으로 저장합니다.

---

# Part 1. Euler Transforms

## 1.1 Euler transform & Euler angles

주축(principal axes)을 중심으로 물체를 **연속해서** 회전시키면 임의의 방향(orientation)에 도달합니다. 이렇게 방향을 결정하는 방법이 **Euler transform**이고, 그때의 회전각 $(\theta_1, \theta_2, \theta_3)$이 **Euler angles**입니다.

세 회전행렬을 곱하면(concatenate) 하나의 방향 행렬이 됩니다.
$$R_y(-30°)\,R_x(30°)\,R_z(60°) = M$$

## 1.2 Intrinsic vs Extrinsic

- **Intrinsic (body-fixed, 내재적):** 물체 **자기 자신의 축**을 기준으로 회전. 한 번 돌리면 그 물체의 나머지 축들은 더 이상 world axis와 평행하지 않게 됨.
- **Extrinsic (world-fixed, 외재적):** 고정된 world 축 기준으로 회전.

**캐릭터 애니메이션은 보통 intrinsic을 사용**하는데, 이유는:
1. **직관적** — "팔꿈치를 자기 X축으로 굽히고, 전완을 자기 Z축으로 비튼다"가 곧 intrinsic.
2. **계층 변환(hierarchical transform)에 효율적** — scene graph의 각 노드가 자기 공간 기준 각도+이동만 저장하면 됨. 부모가 움직여도 자식의 Euler triplet을 world 축으로 다시 쓸 필요 없이 행렬 곱만 하면 됨.

## 1.3 회전 순서(order)는 중요하다

회전은 **교환법칙이 성립하지 않음**(non-commutative). 같은 각도 $\theta_1,\theta_2,\theta_3$라도 **적용 순서가 다르면 결과 방향이 다름.**

> 그래서 "ZYX (yaw→pitch→roll)" 같은 **sequence를 먼저 정해야** 함. 한번 정하면 모든 triplet은 그 순서로만 해석됨.

예: "ZYX" sequence → Euler angle $(\psi, \theta, \phi)$
- Z축으로 $\psi$ 회전 (yaw)
- Y축으로 $\theta$ 회전 (pitch)
- X축으로 $\phi$ 회전 (roll)

## 1.4 Gimbal — 물리적 기원

"Euler angles"라는 용어는 실제 물리 장치인 **gimbal**에서 유래.
- 짐벌 = 3개의 nested ring(frame)으로 된 기계 장치. 각 ring은 한 축으로 회전. 바깥 ring이 중간 ring을, 중간이 안쪽을, 안쪽이 payload(예: 카메라)를 운반.
- 각 ring = 1 rotational degree of freedom. 각 ring이 자기 bearing을 가져 축들이 기계적으로 독립.

## 1.5 Keyframe animation (보간의 배경)

- **Keyframe:** 핵심 프레임에만 키 데이터(위치 $p$, 방향 $\theta$)를 지정. 사이 프레임(in-between)은 런타임에 자동 보간(interpolation)으로 생성.
- 선형 보간(linear interpolation):
$$p(t) = (1-t)\,p_0 + t\,p_1, \qquad \theta(t) = (1-t)\,\theta_0 + t\,\theta_1$$
- **higher-order interpolation**을 쓰면 더 부드러운(smooth) 애니메이션을 얻음.

## 1.6 Euler angle의 문제점 (1) — 보간 이상 / 축 왜곡

- Euler angle은 **축을 따라서만** 회전시킴.
- 한 번 회전(예: $(60,30,45)$)하고 나면 **회전축(gimbal axis)이 왜곡**됨. 그 뒤 다시 "Y축으로 회전"하려면 한 축만으로는 불가능 → **두세 축이 동시에 움직여야** 목표에 도달.
- 결과적으로 두 Euler 회전 사이의 보간이 어색하게 나옴 ("rotation along Y cannot be replayed correctly").

## 1.7 Euler angle의 문제점 (2) — Gimbal Lock ⭐

- **Gimbal lock:** 다차원 메커니즘에서 **자유도(degree of freedom) 하나를 잃는 현상.** 3D 회전이 2D 공간으로 축퇴(degenerate)됨.
- **발생 조건:** sequence $A \to B \to C$에서 **중간 회전 $B = \pm90°$**일 때.
- **직관:** 중간 회전이 90°가 되면 첫 번째 축과 세 번째 축이 **같은 방향으로 정렬**되어, 서로 다른 두 회전이 같은 효과를 냄 → 한 자유도 상실.

**Gimbal lock 예시** ($R(\beta,\alpha,\gamma)=R_Z(\gamma)R_X(\alpha)R_Y(\beta)$에서 $\alpha=90°$):

$R_A(30°,90°,0°)$와 $R_B(0°,90°,30°)$가 **동일한 최종 행렬**이 됨:
$$R_A = R_B = \begin{bmatrix} \sqrt3/2 & 0 & 1/2 \\ 1/2 & 0 & -\sqrt3/2 \\ 0 & 1 & 0 \end{bmatrix}$$

즉 서로 다른 입력 $(30,90,0)$과 $(0,90,30)$이 구분되지 않음 → 자유도 손실.

---

# Part 2. Background for Quaternion (복소수 → Euler 공식)

## 2.1 복소수와 2D 벡터

복소수 $z = a + bi$ ($a$: real part, $bi$: imaginary part, $i^2=-1$)는 평면의 벡터/점을 표현 가능.
- 벡터 $v=(a,b)$ ↔ 복소수 $z = a+ib$
- 덧셈/스칼라곱 모두 벡터 연산과 호환.

## 2.2 복소수 곱으로 2D 회전

벡터 $(x,y)$를 $\theta$만큼 회전:
$$\begin{pmatrix}x'\\y'\end{pmatrix} = \begin{pmatrix}\cos\theta & -\sin\theta \\ \sin\theta & \cos\theta\end{pmatrix}\begin{pmatrix}x\\y\end{pmatrix}$$

이는 복소수 곱으로 표현됨:
$$z' = (\cos\theta + i\sin\theta)(x+iy) = e^{i\theta}(x+iy)$$
$e^{i\theta}$는 단위 길이라 곱해도 modulus $\|z\|$는 보존되고 argument(각도)만 $\theta$만큼 바뀜.

## 2.3 Euler's formula 유도 (Taylor series)

테일러 급수:
$$e^x = 1 + \frac{x}{1!} + \frac{x^2}{2!} + \frac{x^3}{3!} + \cdots$$
$$\sin x = \frac{x}{1!} - \frac{x^3}{3!} + \frac{x^5}{5!} - \cdots, \qquad \cos x = 1 - \frac{x^2}{2!} + \frac{x^4}{4!} - \cdots$$

$x = i\theta$ 대입, $i$의 거듭제곱 cycle ($i^0=1, i^1=i, i^2=-1, i^3=-i, \dots$)을 이용해 실수부/허수부로 정리하면:
$$\boxed{\,e^{i\theta} = \cos\theta + i\sin\theta\,}$$

## 2.4 $qp$ 형태로 본 회전

$(x,y)$를 $p = x+yi$로, 회전각 $\theta$에 대해 unit-length 복소수 $q = \cos\theta + \sin\theta\, i$로 정의하면:
$$qp = (\cos\theta + \sin\theta\,i)(x+yi) = (x\cos\theta - y\sin\theta) + (x\sin\theta + y\cos\theta)i$$
→ 실수부/허수부가 곧 회전된 좌표. (이 $qp$ 구조가 quaternion 회전의 2D 버전)

---

# Part 3. Quaternion

## 3.1 Quaternion이란

- **1843년 William R. Hamilton**이 복소수를 일반화하여 3D 회전을 기술하는 quaternion을 발견.
- 개념적으로 quaternion은 **임의 축(arbitrary axis)에 대한 axis-angle 회전**을 표현.

## 3.2 Quaternion 대수 (algebra) ⭐

quaternion은 4-tuple: $q = q_0 + q_1 i + q_2 j + q_3 k$ ($q_i$는 실수).

기저(basis) 항등식:
$$i^2 = j^2 = k^2 = -1$$
$$ij = k,\quad ji = -k$$
$$jk = i,\quad kj = -i$$
$$ki = j,\quad ik = -j$$

**곱셈은 비가환(non-commutative).** 부호 규칙 (순환 다이어그램 $i \to j \to k \to i$):
- **시계방향(clockwise):** 양수 (+) — 예: $ij=k$
- **반시계방향(counterclockwise):** 음수 (−) — 예: $ji=-k$
- **자기 자신(self):** 음수 (−) — 예: $i^2=-1$

## 3.3 덧셈과 곱셈

**덧셈** (성분별):
$$(q_0+q_1i+q_2j+q_3k)+(p_0+p_1i+p_2j+p_3k) = (q_0{+}p_0)+(q_1{+}p_1)i+(q_2{+}p_2)j+(q_3{+}p_3)k$$

**곱셈** (scalar-first $q_0+q_1i+q_2j+q_3k$ 기준):
$$
\begin{aligned}
qp = \;& (q_0p_0 - q_1p_1 - q_2p_2 - q_3p_3) \\
&+ (q_0p_1 + q_1p_0 + q_2p_3 - q_3p_2)\,i \\
&+ (q_0p_2 + q_2p_0 - q_1p_3 + q_3p_1)\,j \\
&+ (q_0p_3 + q_3p_0 + q_1p_2 - q_2p_1)\,k
\end{aligned}
$$

## 3.4 Conjugate, Norm, Inverse ⭐

(복소수 $z=a+bi$에서: $z^*=a-bi$, $|z|=\sqrt{a^2+b^2}$, $z^{-1}=z^*/|z|^2$의 일반화)

$$q^* = q_0 - q_1 i - q_2 j - q_3 k$$
$$|q| = \sqrt{q_0^2 + q_1^2 + q_2^2 + q_3^2}$$
$$qq^* = q_0^2 + q_1^2 + q_2^2 + q_3^2 = |q|^2$$
$$q^{-1} = \frac{q^*}{|q|^2}$$

성질:
- $(q^*)^* = q$
- $(pq)^* = q^* p^*$ (순서 뒤집힘 — reverse order)

---

# Part 4. Quaternions for Rotation ⭐⭐

## 4.1 벡터와 회전의 표현

- **3D 벡터 $(x,y,z)$ = pure quaternion** (실수부 0):
$$p = 0 + xi + yj + zk$$
- **회전 = unit quaternion** ($\|q_R\|=1$):
$$q_R = q_0 + q_1 i + q_2 j + q_3 k, \qquad \|q_R\|=1$$

## 4.2 Axis-angle encoding ⭐ (가장 중요)

축 $\hat{n}=(\hat n_x, \hat n_y, \hat n_z)$ (unit vector)에 대해 $\theta$만큼 회전하는 quaternion:
$$
q = \cos\frac{\theta}{2} + (\hat n_x i + \hat n_y j + \hat n_z k)\sin\frac{\theta}{2}
= e^{\frac{\theta}{2}(\hat n_x i + \hat n_y j + \hat n_z k)}
$$

역으로 quaternion에서 축/각 복원:
$$\hat{n} = \frac{(q_1, q_2, q_3)}{\sqrt{q_1^2+q_2^2+q_3^2}} \quad (\theta=0일 때만 \text{ undefined})$$
$$\theta = 2\arccos(q_0)$$

> $q_0$ = scalar part, $q_1 i + q_2 j + q_3 k$ = vector part.
> **반각($\theta/2$)이 들어가는 것**이 핵심 포인트! (sandwich product에서 양쪽으로 곱하기 때문)

## 4.3 Sandwich product (conjugation operation) ⭐

벡터 $A$를 $B$로 회전 (rotation quaternion $q_R$):
$$\boxed{\,q_B = q_R\, q_A\, q_R^*\,}$$

(여기서 $q_A, q_B$는 pure quaternion, $q_R$은 unit quaternion)

## 4.4 회전 결과 공식 (Rodrigues 형태) ⭐

$qpq^*$를 전개하면 (단, $p$는 pure quaternion, $q=(\,\hat u\sin\tfrac\theta2,\ \cos\tfrac\theta2\,)$):
$$
\boxed{\,p' = (\hat u\cdot p_v)\,\hat u + \cos\theta\,\big(p_v - (\hat u\cdot p_v)\hat u\big) + \sin\theta\,(\hat u\times p_v)\,}
$$

기하학적 분해:
- $(\hat u\cdot p_v)\hat u$ : 축 방향 성분(회전해도 불변)
- $p_v - (\hat u\cdot p_v)\hat u$ : 축에 수직인 성분
- $\cos\theta(\cdots) + \sin\theta(\hat u\times p_v)$ : 수직 성분이 평면 내에서 $\theta$ 회전

## 4.5 Hamilton product (vector-first 규칙)

게임엔진/셰이더/SIMD는 보통 $(x,y,z,w)$ 순서(**vector-first**)를 씀. $p=(p_v,p_w)$, $q=(q_v,q_w)$일 때:

성분 형태:
$$
\begin{aligned}
pq = \;& (p_xq_w + p_yq_z - p_zq_y + p_wq_x)\,i \\
&+ (-p_xq_z + p_yq_w + p_zq_x + p_wq_y)\,j \\
&+ (p_xq_y - p_yq_x + p_zq_w + p_wq_z)\,k \\
&+ (-p_xq_x - p_yq_y - p_zq_z + p_wq_w)
\end{aligned}
$$

벡터 형태 (외적·내적 이용):
$$qp = (\,p_v\times q_v + q_w p_v + p_w q_v,\ \ p_w q_w - p_v\cdot q_v\,)$$

## 4.6 여러 회전의 합성 (Multiple quaternions) ⭐

$p$를 $q$로 회전 후 다시 $r$로 회전:
$$r(qpq^*)r^* = (rq)\,p\,(q^*r^*) = (rq)\,p\,(rq)^*$$
→ **합성 회전 = $rq$** (행렬처럼 곱으로 합성, 단 순서 주의: 나중에 적용하는 게 왼쪽).

## 4.7 Quaternion과 Negation ⭐

> "$\hat u$ 축으로 $\theta$ 회전" = "$-\hat u$ 축으로 $-\theta$ 회전"

따라서 **$q$와 $-q$는 같은 회전**을 나타냄 (double cover, q-ambiguity). → 보간 시 더 짧은 경로 선택을 위해 부호를 맞춰주기도 함.

---

# Part 5. Quaternion ↔ Rotation Matrix

## 5.1 Quaternion → $3\times3$ Rotation Matrix $M$

일반형:
$$
M = \begin{bmatrix}
q_0^2+q_1^2-q_2^2-q_3^2 & 2(q_1q_2 - q_0q_3) & 2(q_0q_2+q_1q_3) \\
2(q_0q_3+q_1q_2) & q_0^2-q_1^2+q_2^2-q_3^2 & 2(q_2q_3-q_0q_1) \\
2(q_1q_3-q_0q_2) & 2(q_0q_1+q_2q_3) & q_0^2-q_1^2-q_2^2+q_3^2
\end{bmatrix}
$$

unit quaternion($\|q\|^2=q_0^2+q_1^2+q_2^2+q_3^2=1$)이면 대각 성분 단순화 가능:
$$
M = 2\cdot\begin{bmatrix}
q_0^2+q_1^2-0.5 & q_1q_2-q_0q_3 & q_0q_2+q_1q_3 \\
q_0q_3+q_1q_2 & q_0^2+q_2^2-0.5 & q_2q_3-q_0q_1 \\
q_1q_3-q_0q_2 & q_0q_1+q_2q_3 & q_0^2+q_3^2-0.5
\end{bmatrix}
$$

## 5.2 Rotation Matrix → Quaternion (trace 방법) ⭐

먼저 **trace**(대각합):
$$\text{Trace}(M) = M_{11}+M_{22}+M_{33} = 4q_0^2 - 1$$

각 성분의 크기:
$$|q_0| = \sqrt{\frac{\text{Trace}(M)+1}{4}}$$
$$|q_1| = \sqrt{\frac{M_{11}}{2} + \frac{1-\text{Trace}(M)}{4}}$$
$$|q_2| = \sqrt{\frac{M_{22}}{2} + \frac{1-\text{Trace}(M)}{4}}$$
$$|q_3| = \sqrt{\frac{M_{33}}{2} + \frac{1-\text{Trace}(M)}{4}}$$

> 주의: 위 식은 **크기(절댓값)**만 줌. 부호는 off-diagonal 성분으로 결정 (예: $M_{32}-M_{23}=4q_0q_1$ 등을 이용).

---

# Part 6. 핵심 공식 암기 시트 (Cheat Sheet) 📌

> 시험 직전 이 부분만 보면 됩니다.

### ▶ Euler / Gimbal
- 회전 합성은 **비가환** → sequence 먼저 정하기
- **Gimbal lock 조건: 중간 회전 = $\pm90°$** (자유도 1 손실, 3D→2D 축퇴)
- 선형 보간: $\;p(t)=(1-t)p_0+tp_1,\quad \theta(t)=(1-t)\theta_0+t\theta_1$

### ▶ 복소수 / Euler 공식
- $\;e^{i\theta} = \cos\theta + i\sin\theta$
- 2D 회전: $\;z' = e^{i\theta}(x+iy)$
- 2D 회전행렬: $\begin{pmatrix}\cos\theta & -\sin\theta \\ \sin\theta & \cos\theta\end{pmatrix}$

### ▶ Quaternion 기저
- $\;i^2=j^2=k^2=-1$
- $\;ij=k,\ jk=i,\ ki=j$ (시계방향 +)
- $\;ji=-k,\ kj=-i,\ ik=-j$ (반시계 −)

### ▶ Conjugate / Norm / Inverse
- $\;q^* = q_0 - q_1i - q_2j - q_3k$
- $\;|q| = \sqrt{q_0^2+q_1^2+q_2^2+q_3^2}$
- $\;q^{-1} = q^*/|q|^2$
- $\;(pq)^* = q^*p^*$

### ▶ 회전용 Quaternion (★최빈출★)
- **Axis-angle:** $\;q = \cos\dfrac{\theta}{2} + (\hat n_x i + \hat n_y j + \hat n_z k)\sin\dfrac{\theta}{2}$
- 벡터 → pure quaternion: $\;p=(0,\ x,y,z)$ 즉 실수부 0
- **Sandwich product:** $\;q_B = q_R\,q_A\,q_R^*$
- **Rodrigues:** $\;p' = (\hat u\cdot p_v)\hat u + \cos\theta\,(p_v-(\hat u\cdot p_v)\hat u) + \sin\theta\,(\hat u\times p_v)$
- 합성: $\;(rq)\,p\,(rq)^*$ → 합성회전 $=rq$
- **$q$와 $-q$는 같은 회전**

### ▶ Quaternion ↔ Matrix
- Trace: $\;\text{Trace}(M)=4q_0^2-1$
- $\;|q_0|=\sqrt{\dfrac{\text{Trace}(M)+1}{4}}$
- $\;|q_i|=\sqrt{\dfrac{M_{ii}}{2}+\dfrac{1-\text{Trace}(M)}{4}}\quad(i=1,2,3)$

### ▶ 자주 쓰는 값
| $\theta$ | $\theta/2$ | $\cos(\theta/2)$ | $\sin(\theta/2)$ |
|---|---|---|---|
| $90°$ | $45°$ | $\frac{\sqrt2}{2}$ | $\frac{\sqrt2}{2}$ |
| $120°$ | $60°$ | $\frac12$ | $\frac{\sqrt3}{2}$ |
| $180°$ | $90°$ | $0$ | $1$ |

---

# Part 7. 연습문제 풀이

### Q1. Euler 채널 선형보간 각속도
**문제:** robotic joint가 $(\psi,\theta,\phi)=(10,20,30)$에서 $(100,-40,80)$으로 정확히 50 ms에 이동. 각 Euler channel을 선형보간할 때 ms당 각속도(°/ms)는?

**풀이:**
$$\Delta\psi = 100-10 = 90°,\quad \Delta\theta = -40-20 = -60°,\quad \Delta\phi = 80-30 = 50°$$
$$\frac{\Delta}{\Delta t}:\quad \frac{90}{50}=1.8,\quad \frac{-60}{50}=-1.2,\quad \frac{50}{50}=1.0\ \text{ (°/ms)}$$
**답:** $\;\dot\psi=1.8,\ \dot\theta=-1.2,\ \dot\phi=1.0$ °/ms

---

### Q2. 복소수 회전각 구하기
**문제:** $z_o = 3+2i$를 $z_f = -3-2i$로 회전시키는 각 $\theta$ ($0<\theta<2\pi$)?

**풀이:**
$$e^{i\theta} = \frac{z_f}{z_o} = \frac{-3-2i}{3+2i} = \frac{-(3+2i)}{3+2i} = -1$$
$$-1 = \cos\theta + i\sin\theta \;\Rightarrow\; \cos\theta=-1,\ \sin\theta=0$$
**답:** $\;\theta = 180° = \pi$

---

### Q3. 3D 회전 (sandwich product)
**문제:** 벡터 $(0,1,0)$을 축 $(1,0,1)$에 대해 $90°$ 회전.

**(a) 회전 quaternion $q=(q_x,q_y,q_z,q_w)$:**
축을 정규화:
$$\hat u = \frac{(1,0,1)}{\|(1,0,1)\|} = \left(\tfrac{1}{\sqrt2},\,0,\,\tfrac{1}{\sqrt2}\right)$$
$$q = \left(\sin45°\,\hat u,\ \cos45°\right) = \left(\tfrac{1}{\sqrt2}\cdot\tfrac{1}{\sqrt2},\ 0,\ \tfrac{1}{\sqrt2}\cdot\tfrac{1}{\sqrt2},\ \tfrac{\sqrt2}{2}\right) = \left(\tfrac12,\,0,\,\tfrac12,\,\tfrac{\sqrt2}{2}\right)$$

**(b) 회전될 벡터의 pure quaternion $p$:**
$$p = (0,\,1,\,0,\,0)$$

**(c) 회전 결과 $qpq^*$:**
$$qpq^* = \left(\tfrac12 i + \tfrac12 k + \tfrac{\sqrt2}{2}\right)(j)\left(-\tfrac12 i - \tfrac12 k + \tfrac{\sqrt2}{2}\right) = \left(-\tfrac{\sqrt2}{2},\ 0,\ \tfrac{\sqrt2}{2},\ 0\right)$$
**답:** 회전된 벡터 $= \left(-\dfrac{\sqrt2}{2},\,0,\,\dfrac{\sqrt2}{2}\right)$

> 검산 (Rodrigues): $\hat u\cdot p=0$, $\cos90°=0$, $\sin90°=1$, $\hat u\times p = (-\tfrac{1}{\sqrt2},0,\tfrac{1}{\sqrt2})$ → $p' = (-\tfrac{\sqrt2}{2},0,\tfrac{\sqrt2}{2})$ ✓

---

### Q4-1. Unit length 검증
**문제:** $q = \left(\tfrac{\sqrt2}{2}, 0, 0, \tfrac{\sqrt2}{2}\right) = \omega + xi + yj + zk$ 가 unit인지 확인.

**풀이:**
$$\|q\|^2 = \left(\tfrac{\sqrt2}{2}\right)^2 + 0 + 0 + \left(\tfrac{\sqrt2}{2}\right)^2 = \tfrac12 + \tfrac12 = 1 \;\Rightarrow\; \|q\|=1 \checkmark$$

---

### Q4-2. Rotation matrix → quaternion 추출
**문제:** $R = \begin{bmatrix} 0 & -1 & 0 \\ 1 & 0 & 0 \\ 0 & 0 & 1 \end{bmatrix}$ 에서 quaternion 추출.
(이 $R$은 z축 기준 $90°$ 회전 행렬)

**풀이:**
$$\text{Trace}(R) = 0+0+1 = 1$$
$$|q_0| = \sqrt{\tfrac{1+1}{4}} = \sqrt{\tfrac12} = \tfrac{\sqrt2}{2}$$
$$|q_1| = \sqrt{\tfrac{M_{11}}{2}+\tfrac{1-1}{4}} = \sqrt{\tfrac{0}{2}} = 0$$
$$|q_2| = \sqrt{\tfrac{M_{22}}{2}+\tfrac{1-1}{4}} = \sqrt{\tfrac{0}{2}} = 0$$
$$|q_3| = \sqrt{\tfrac{M_{33}}{2}+\tfrac{1-1}{4}} = \sqrt{\tfrac{1}{2}} = \tfrac{\sqrt2}{2}$$

부호 결정: $M_{21}-M_{12} = 1-(-1) = 2 = 4q_0q_3 \Rightarrow q_0q_3 = \tfrac12 > 0$ (같은 부호).
**답 (scalar-first):** $\;q = \left(\tfrac{\sqrt2}{2},\,0,\,0,\,\tfrac{\sqrt2}{2}\right)$ → z축 $90°$ 회전, Q4-1의 quaternion과 동일 ✓

---

## 시험 대비 체크리스트 ✅
- [ ] Euler vs Quaternion 장단점 비교 설명 가능
- [ ] **Gimbal lock 발생 조건 (중간 회전 ±90°)** 즉답 가능
- [ ] Intrinsic vs Extrinsic 구분
- [ ] 회전 비가환성 + 순서 중요성 설명
- [ ] $e^{i\theta}=\cos\theta+i\sin\theta$ 유도(테일러) 흐름
- [ ] quaternion 기저 곱셈표 ($ij=k$ 등) 암기
- [ ] **axis-angle 인코딩 $\cos\tfrac\theta2 + \hat n\sin\tfrac\theta2$** (반각 주의!)
- [ ] **sandwich product $q_Rq_Aq_R^*$** 손계산
- [ ] conjugate/norm/inverse 공식
- [ ] quaternion ↔ matrix 양방향 변환 (trace 공식)
- [ ] $q = -q$ 동일 회전
