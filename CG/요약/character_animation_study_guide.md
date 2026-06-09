# 🎬 Character Animation: Representation — 시험 대비 정리

> H. Kang's Computer Graphics, Lecture 12 핵심 정리
> 구성: **Part 1 개념 정리** · **Part 2 핵심 공식 암기 노트** · **Part 3 연습문제 풀이** · **Part 4 헷갈리기 쉬운 포인트**

---

## Part 1. 개념 정리

### 1. 캐릭터 애니메이션 개요
- **Character animation** = 관절을 가진(articulated) 디지털 캐릭터의 "그럴듯한(believable) 움직임"을 만드는 것.
- 어려운 이유: 움직임이 **구조적 제약(structural constraints)**, **기하학적 일관성(geometric consistency)**, **운동 연속성(motion continuity)**을 모두 만족해야 함.
- CG가 제공하는 것: 핵심 표현(core representation), 수학·알고리즘 기반, 계산 도구.

### 2. Articulated Representation — Skeleton (골격)
캐릭터 모션을 제어하는 **계층적(hierarchical) 관절 구조**.

| 구성요소 | 정의 | 핵심 |
|---|---|---|
| **Joint (관절)** | 뼈 사이의 운동 제약 | pivot point + 허용 회전 정의, **DoF를 도입**, 변환을 자식으로 전파 |
| **Bone (뼈)** | 두 관절 사이의 **rigid segment** | 신체 부위(상완·전완 등) 표현, 부모 관절 변환을 따름, **bone space(자기 지역 좌표계)**를 가짐 |

Skeleton이 정의하는 것:
- **Topology**: parent–child 계층 구조 → **모션이 계층을 따라 어떻게 전파되는가**
- **Degrees of Freedom (DoF)**: 각 관절이 허용하는 제약된 자유도 → **어떤 모션이 물리적으로 허용되는가**

> **Root는 보통 pelvis(골반)**. 예: pelvis → spine → clavicle → upper arm → forearm → hand

핵심 관점:
- **캐릭터 포즈 = 고차원 configuration space 안의 한 점(point)**
- **캐릭터 애니메이션 = 그 공간 안의 궤적(trajectory)**

### 3. 좌표계(Coordinate Spaces) — 시험 최빈출 개념
관절이 회전했을 때 mesh가 올바르게 따라가게 하려면 다음 3가지가 필요:

1. **Reference pose (= default / bind pose)**: 애니메이션 시작 전 기준 자세. 이때 skeleton과 mesh 정렬을 **한 번** 기록.
2. **Character space (= mesh's object space)**: default pose에서 mesh 정점이 처음 정의되는 좌표계.
3. **Bone space**: 각 뼈에 붙어 있는 지역 좌표계. **정점을 해당 뼈의 bone space에 저장해 두면, 그 뼈가 회전할 때 정점이 자동으로 따라감.**

### 4. Bone ↔ Character 변환 (정적, default pose)
- **To-parent transform $M_{i,p}$**: $i$번 뼈의 정점을 **부모 뼈의 space**로 옮김.
- **Bone → Character (default pose) $M_{i,d}$**: bone space → character space.
  - $M_{i,d} = M_{i-1,d}\,M_{i,p}$, 단 $M_{1,d}=I$ (pelvis가 root)
  - 즉 to-parent 행렬들을 **위에서부터(top-down) 누적(concatenate)**.
- **Character → Bone (역변환) $M_{i,d}^{-1}$**: 우리가 애니메이션에 실제로 필요한 것.
  - $M_{i,d}^{-1} = M_{i,p}^{-1}\,M_{i-1,d}^{-1}$, 단 $M_{1,d}^{-1}=I$
  - default pose가 주어지면 $M_{i,p}$와 그 역 $M_{i,p}^{-1}$은 즉시 결정됨 → **top-down traversal로 모든 뼈의 $M_{i,d}^{-1}$ 계산 가능.**

### 5. Forward Kinematics (FK)
관절 각도(local rotation)가 주어졌을 때 정점이 character space에서 어디로 가는지 계산.

- **Local transform $M_{i,l}$**: $i$번 뼈가 자기 관절을 중심으로 하는 애니메이션 회전. 애니메이터가 포즈를 정하면 결정됨.
- **Animated transform $M_{i,a}$**: 애니메이션된 bone space → character space.
  - $M_{i,a} = M_{i-1,a}\,M_{i,p}\,M_{i,l}$, 단 $M_{1,a}=I$
  - $M_{1,a}=I$인 이유: **character space = pelvis의 bone space**. (캐릭터의 world transform은 별도로 정의됨.)
- **계산 순서**: $M_{i,l}$은 애니메이터가, $M_{i,p}$는 default pose에서 결정 → $M_{i-1,a}$만 미리 구하면 $M_{i,a}$ 계산 가능 → **top-down traversal.**

> **default pose에서는 $M_{i,l}=I$** 라서 $M_{i,a}=M_{i,d}$ 가 됨. 애니메이션은 이 자리에 실제 회전 $M_{i,l}$을 끼워 넣는 것.

### 6. Default pose → Animated pose (한 정점)
$$v' = M_{i,a}\,M_{i,d}^{-1}\,v$$
- $M_{i,d}^{-1}$: default pose의 character-space 정점 $v$를 $i$번 뼈의 bone space로 보냄.
- $M_{i,a}$: 애니메이션된 상태로 다시 character space로 가져옴 → 애니메이션 포즈의 정점 $v'$.

### 7. Skinning (스키닝)
- **Skin**: skeletal motion으로 정의되는 polygon mesh.
- **Skinning**: skeleton 변환으로부터 **각 mesh 정점의 최종 위치를 계산하는 방법**.
- **FK vs Skinning**: FK는 *뼈가 어떻게 움직이는지*, Skinning은 *그 뼈 움직임 때문에 mesh 정점이 어떻게 움직이는지* 계산.

**(1) Naïve: 1 vertex → 1 bone**
- 각 정점을 뼈 하나에만 binding.
- 관절에서 표면이 불연속 → **sharp crease(날카로운 주름)**, 뻣뻣하고 부자연스러움.

**(2) Linear Blend Skinning (LBS)** — 개선안
- 정점 하나가 **여러 뼈의 영향**을 받게 하고, **weight $\omega_i$**로 영향 강도를 표현 → 관절 근처가 부드럽게 휨.
$$v' = \sum_i \omega_i \left(M_{i,a}\,M_{i,d}^{-1}\,v\right), \qquad \left(\textstyle\sum_i \omega_i = 1\right)$$
- 예: forearm 정점 → elbow 80%, shoulder 20%.

**(3) 구현(Implementation)**
- 게임 등 실시간에서는 한 정점에 영향 주는 뼈 수 $m$을 보통 **4개 이하**로 제한.
- 보통 **vertex shader**로 구현.
- 뼈가 20개면 매 프레임 $M_i$ 20개 갱신 → **matrix palette** 테이블에 저장해 **uniform 변수**로 전달.
- **palette index**와 **blend weight**는 vertex array에 저장.

### 8. Inverse Kinematics (IK)
- **End effector**: 로봇/캐릭터 팔 끝부분.
- **FK**: 관절 각도 → end effector 포즈.
- **IK** (역과정): **원하는 end effector 포즈**가 주어졌을 때 **관절 각도**를 역산. DoF가 클 때 사용자가 end effector에만 집중 가능.

**최적화 정식화 (왜 어려운가)**
$$\min_{\theta}\;\lVert f(\theta) - x_{target}\rVert^2$$
- 고차원 비선형 최적화, 반복적 Jacobian/Hessian 계산 필요, 좋은 초기값 의존 → 무거움.
- 그래서 실시간에서는 **Heuristic IK** 선호 (계산 효율 ↑, 구현 난이도 ↓).

**CCD (Cyclic Coordinate Descent)**
- 반복적 휴리스틱. **한 번에 관절 하나씩** 회전시켜 position/orientation 오차를 줄임.
- **end effector → base(안쪽)** 방향으로 진행. 만족할 때까지 반복.
- 각 단계가 단순·지역적 → 관절당 비용 낮고 빠름.
- 단점: 긴 체인에서 수렴 느림 / 한 번에 한 관절만 돌려 **부자연·jerky 모션** / 일찍 수렴 시 일부 관절 미갱신 / 초기 포즈에 민감.

**FABRIK (Forward And Backward Reaching IK)**
- CCD의 한계 극복. **관절을 회전시키지 않고 관절 "위치"를 하나씩 조정**해 오차 최소화.
- 한 iteration = **Forward reaching(end effector→root)** + **Backward reaching(root→end effector)** 두 단계.
- **도달 가능성(reachability) 판정**: root–target 거리가 모든 inter-joint 거리 합보다 작으면 reachable, 크면 unreachable.
  $$\text{reachable} \iff \lVert p_1 - t\rVert \le d_1 + d_2 + \cdots + d_{n-1}$$
- 보간식: $\lambda_i = d_i / r_i$, 새 위치 $= (1-\lambda_i)\,p_a + \lambda_i\,p_b$ (선분 위에서 거리 $d_i$ 유지).

### 9. Parametric Human Model — SMPL
**동기**: vision / robotics / AR·VR에서는 mesh가 *주어지지 않음*. 불완전한 관측에서 body shape·pose·표면 기하를 **추정**해야 함. raw mesh(수천 vertex) 직접 최적화는 불안정·ill-posed·고차원. → **compact, expressive, differentiable**한 표현 필요.

**SMPL (A Skinned Multi-Person Linear Model)**
- pose와 shape를 동시에 모델링하는 parametric human model.
- 사람 몸을 저차원·해석 가능 벡터로 인코딩 → **compactness / expressiveness / differentiability** 제공.
- 구조: **6890 vertices, 23 joints**.
- **Shape parameter $\beta \in \mathbb{R}^{10}$**: 키·몸무게·팔다리 두께·근육 등 정적 특성.
- **Pose parameter $\theta \in \mathbb{R}^{3K},\;K=23$**: 각 관절의 상대 회전(axis-angle).

**수식**
$$M(\beta,\theta) = W\big(T_P(\beta,\theta),\; J(\beta),\; \theta,\; \mathcal{W}\big)$$

1. **Shape & pose deformation**: $\;T_P(\beta,\theta) = \hat{T} + B_S(\beta) + B_P(\theta)$
   - $\hat{T}$: T-pose template mesh (평균 인체)
   - $B_S(\beta)$: **shape blend shapes** (기하 변형/변위)
   - $B_P(\theta)$: **pose-dependent blend shapes** — 관절 회전에 따른 근육 융기·피부 접힘 보정
2. **Joint position estimation $J(\beta)$**: 관절 위치를 shape $\beta$로부터 계산 (고정 아님 — 키 큰 사람은 관절 간격이 넓어짐).
3. **Skinning**: $\theta$(관절 회전) + $\mathcal{W}$(skinning weight)로 포즈 적용. (기존 렌더링 엔진과 호환 — 예: Unity)

---

## Part 2. 핵심 공식 암기 노트 📌

> 이 부분만 따로 외우면 됩니다.

### A. 좌표 변환 (핵심 중의 핵심)

| # | 이름 | 공식 | 초기조건 |
|---|---|---|---|
| 1 | To-parent | $M_{i,p}$ : bone $i$ → parent space | — |
| 2 | Bone→Character (default) | $M_{i,d} = M_{i-1,d}\,M_{i,p}$ | $M_{1,d}=I$ |
| 3 | Character→Bone (default, 역) | $M_{i,d}^{-1} = M_{i,p}^{-1}\,M_{i-1,d}^{-1}$ | $M_{1,d}^{-1}=I$ |
| 4 | Animated (FK) | $M_{i,a} = M_{i-1,a}\,M_{i,p}\,M_{i,l}$ | $M_{1,a}=I$ |

### B. 정점 변환

- **한 정점 (default → animated)**:
$$v' = M_{i,a}\,M_{i,d}^{-1}\,v$$

- **Linear Blend Skinning (LBS)**:
$$v' = \sum_{i=1}^{m} \omega_i\, M_{i,a}\,M_{i,d}^{-1}\,v = \sum_{i=1}^{m}\omega_i M_i v,\quad M_i \equiv M_{i,a}M_{i,d}^{-1},\;\; \textstyle\sum\omega_i=1$$

### C. Inverse Kinematics

- **IK 최적화 정식화**:
$$\min_{\theta}\;\lVert f(\theta) - x_{target}\rVert^2$$

- **FABRIK 도달 가능성**:
$$\lVert p_1 - t\rVert \le \sum_{i=1}^{n-1} d_i \;\Rightarrow\; \text{reachable}$$

- **FABRIK 보간**: $\;\lambda_i = \dfrac{d_i}{r_i},\quad \text{new pos} = (1-\lambda_i)p_a + \lambda_i p_b$

### D. SMPL

$$M(\beta,\theta) = W\big(T_P(\beta,\theta),\,J(\beta),\,\theta,\,\mathcal{W}\big)$$
$$T_P(\beta,\theta) = \hat{T} + B_S(\beta) + B_P(\theta)$$
$$B_P(\theta) = C(\theta - \theta_0)\;\;(\text{단순화 모델})$$

- 차원/스펙: $\beta \in \mathbb{R}^{10}$, $\theta \in \mathbb{R}^{3K}$, $K=23$, **6890 vertices, 23 joints**.

---

## Part 3. 연습문제 풀이

### Q1. $M_{3,d}$ 구하기 (정적 변환 누적)
3.clavicle의 to-parent $=\begin{bmatrix}1&0&0\\0&1&3\\0&0&1\end{bmatrix}$, 2.spine의 to-parent $=\begin{bmatrix}1&0&2\\0&1&0\\0&0&1\end{bmatrix}$.

$M_{3,d} = M_{2,d}M_{3,p} = (M_{1,d}M_{2,p})M_{3,p} = M_{2,p}M_{3,p}$
$$M_{3,d} = \begin{bmatrix}1&0&2\\0&1&0\\0&0&1\end{bmatrix}\begin{bmatrix}1&0&0\\0&1&3\\0&0&1\end{bmatrix} = \boxed{\begin{bmatrix}1&0&2\\0&1&3\\0&0&1\end{bmatrix}}$$

### Q2. $M_{6,l}$ 와 $v_a''$ (FK 체인)
$v_a=(1,0)$ (hand space), forearm만 90° 회전.

- hand(6번)는 독립적으로 회전하지 않음 → $\;M_{6,l} = \begin{bmatrix}1&0&0\\0&1&0\\0&0&1\end{bmatrix} = I$
- upper arm space로: $\;v_a'' = M_{5,p}M_{5,l}M_{6,p}M_{6,l}\,v_a$
$$=\begin{bmatrix}1&0&4\\0&1&0\\0&0&1\end{bmatrix}\begin{bmatrix}0&-1&0\\1&0&0\\0&0&1\end{bmatrix}\begin{bmatrix}1&0&3\\0&1&0\\0&0&1\end{bmatrix}\begin{bmatrix}1\\0\\1\end{bmatrix}$$
- 단계별: $M_{6,p}v_a=(4,0,1)\to M_{5,l}(\cdots)=(0,4,1)\to M_{5,p}(\cdots)=(4,4,1)$
$$\boxed{v_a'' = (4,\,4)}$$

### Q3. LBS 블렌딩
$v=(5.5,0.2,1)$, $M_{5,d}=\begin{bmatrix}1&0&3\\0&1&0\\0&0&1\end{bmatrix}$, $M_{6,d}=\begin{bmatrix}1&0&5\\0&1&0\\0&0&1\end{bmatrix}$, $M_{5,a}=\begin{bmatrix}0&-1&3\\1&0&0\\0&0&1\end{bmatrix}$, $M_{6,a}=\begin{bmatrix}0&-1&3\\1&0&2\\0&0&1\end{bmatrix}$, $\omega_5=0.6,\omega_6=0.4$.

**① bone space로 ($M_{i,d}^{-1}v$):**
$M_{5,d}^{-1}v=(2.5,0.2,1)$, $\quad M_{6,d}^{-1}v=(0.5,0.2,1)$

**② animated 적용:**
$p_5=M_{5,a}(2.5,0.2,1)^T=(2.8,2.5,1)$
$p_6=M_{6,a}(0.5,0.2,1)^T=(2.8,2.5,1)$

**③ 블렌딩:**
$$v' = 0.6\,p_5 + 0.4\,p_6 = \boxed{(2.8,\,2.5)}$$

### Q4. CCD 한 스텝
$P_0=(0,0),P_1=(2,0),P_2=(4,0)$ (end effector), target $T=(3,2)$. 관절 $P_1$을 회전.

- $P_1\!\to\!P_2$ 길이 보존: $\lVert P_1P_2\rVert = 2$
- 목표 방향 단위벡터: $\hat u = \dfrac{T-P_1}{\lVert T-P_1\rVert} = \dfrac{(1,2)}{\sqrt5}$
- 새 위치: $P_2' = P_1 + 2\hat u = \left(2+\dfrac{2}{\sqrt5},\; \dfrac{4}{\sqrt5}\right)$
$$\boxed{P_2' = \left(2+\tfrac{2}{\sqrt5},\,\tfrac{4}{\sqrt5}\right) \approx (2.89,\,1.79)}$$

### Q5. SMPL pose corrective
$B_P(\theta)=C(\theta-\theta_0)$, $C=\begin{bmatrix}2\\-1\end{bmatrix}$, $\theta_0=0$, $\theta=0.3$.
$$B_P(\theta) = \begin{bmatrix}2\\-1\end{bmatrix}(0.3-0) = \boxed{\begin{bmatrix}0.6\\-0.3\end{bmatrix}}$$
**왜 존재?** plain LBS가 잘 표현 못 하는 **pose-dependent 표면 변형(예: 근육 bulging, 피부 접힘)**을 보정하기 위해.

---

## Part 4. 헷갈리기 쉬운 포인트 ⚠️

1. **$M_{i,d}$ vs $M_{i,a}$**: $d$=default pose(정적, 기준), $a$=animated pose(애니메이션 적용). default에서는 $M_{i,l}=I$ 이므로 $M_{i,a}=M_{i,d}$.
2. **왜 $M_{i,a}M_{i,d}^{-1}$ 순서?**: 먼저 $M_{i,d}^{-1}$로 정점을 (default 기준) bone space에 넣고, 그다음 $M_{i,a}$로 애니메이션된 위치에 다시 배치.
3. **$M_{1,a}=I$, $M_{1,d}=I$**: root(pelvis)의 bone space = character space 라서. world transform은 따로.
4. **FK ↔ Skinning**: FK = 뼈의 움직임 계산 / Skinning = 그 결과로 mesh 정점이 움직이는 것 계산.
5. **CCD ↔ FABRIK**: CCD는 **관절을 회전(각도)**, end→base 순. FABRIK은 **관절 위치를 조정(회전 없음)**, forward+backward 2단계.
6. **SMPL의 $\beta$ ↔ $\theta$**: $\beta$=shape(정적, $\mathbb{R}^{10}$), $\theta$=pose(관절 회전 axis-angle, $\mathbb{R}^{3K}$).
7. **Topology ↔ DoF**: Topology = 모션이 *어떻게 전파*되는가 / DoF = *어떤 모션이 허용*되는가.
8. **to-parent 누적 방향**: $M_{i,d}$는 위에서부터(top-down) 누적. 역변환 $M_{i,d}^{-1}$은 $M_{i,p}^{-1}$이 **앞**에 곱해짐(순서 주의).
