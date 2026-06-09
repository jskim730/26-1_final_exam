# Point-Based Rendering → Gaussian Splatting 시험 정리

> Computer Graphics Lecture 10 (Prof. H. Kang) 핵심 정리본
> 구성: ① 큰 그림 → ② Point-Based Rendering → ③ Gaussian 기초 → ④ 3D Gaussian Splatting → ⑤ **공식 암기 모음** → ⑥ 연습문제 풀이

---

## 0. 한눈에 보는 큰 그림

이 강의의 핵심 논리 흐름은 **"메쉬의 한계 → 점으로 표현 → 점을 부드럽게 만들려면 splat → splat을 Gaussian으로 → 학습 가능한 3D 표현(3DGS)"** 입니다.

```
Triangle Mesh (한계)
   └→ Point / Surfel 표현
        └→ Splatting (점을 disc로 그려 구멍 메우기)
             └→ EWA Filtering (aliasing 잡기, Gaussian 사용)
                  └→ 3D Gaussian Splatting (학습 가능한 explicit 표현)
```

핵심 관통 개념: **"3D에서 splat을 만들고 2D에서 blend한다"** — 이 원리는 고전 point-based rendering부터 최신 3DGS까지 동일합니다. disc가 ellipse로, ellipse가 Gaussian으로 바뀐 것뿐입니다.

---

## 1. Point-Based Rendering

### 1.1 왜 Point-Based Rendering인가 (동기)

전통적으로 3D는 **polygon mesh**로 표현했지만 두 가지 문제가 있습니다.

- **Micro-polygon overhead**: 메쉬가 조밀해지면(예: +8M polys) 삼각형마다 setup/rasterization 부담이 커짐
  - *CPU load*: geometry 관리 (loading, transforming, culling, sorting)
  - *GPU load*: triangle rasterizing
- **Point cloud의 대중화**: 3D 스캐너가 거대한 point cloud를 직접 생성 → 일관된 triangle mesh를 만드는 건 느리고 어려움 → **mesh 없이 point cloud를 바로 시각화하는 primitive**가 필요

### 1.2 Triangles vs Points

| | Triangles | Points (point-based) |
|---|---|---|
| 장점 | 단순/효율, HW 파이프라인 지원, 성숙한 알고리즘 | connectivity 불필요 → 자료구조 단순, mesh 유지보수 회피 |
| 단점 | connectivity·manifold 유지 필요, UV parametrization 필요, LOD·압축 어려움 | **구멍(gap) 발생, smoothness·blending 새 과제** |

> 핵심 전환: **piecewise linear function → delta distribution**. 표면을 여러 위치의 "점 샘플(delta)"로 보는 것. connectivity를 버리는 대신 gap filling/smoothness라는 새 문제가 생김.

### 1.3 Surfel (Surface Element)

점이 단순 좌표 $(x,y,z)$만 가지면 음영도 못 넣고 구멍도 못 메움. 그래서 표면의 작은 patch를 기술하는 **surfel** 도입.

```c
struct ExtendedSurfel {
    vec3  position;  // 3D 위치
    vec3  normal;    // 표면 방향 (→ lighting/shading 가능)
    vec3  color;     // diffuse color / reflectance
    float radius;    // patch 크기 (→ gap filling 가능)
};
```

- **normal** → 조명/음영 계산 가능
- **radius** → 작은 disc로 그려서 점 사이 빈틈 메움
- 각 surfel은 점이 아니라 작은 **disc/ellipsoid("splat")** 로 렌더링됨

### 1.4 Point Rendering Pipeline (4단계 — 순서 암기!)

```
Projection → Shading → Visibility → Image Reconstruction
```

1. **Projection**: 삼각형 전체가 아니라 **각 점/surfel을 개별적으로** perspective/orthographic 변환. 텍스처 lookup에 의존하지 않고 attribute(위치·normal·색)를 그대로 들고 파이프라인 통과.
2. **Shading**: per-point shading. 각 점의 normal·material로 Phong 등 표준 조명식 평가.
3. **Visibility**: 어떤 점이 frontmost(가림 없음)인지 결정. 같은 픽셀에 두 점이 떨어지면 **카메라에 가까운(depth가 작은) 점** 선택 → mesh 없이 occlusion 처리.
4. **Image Reconstruction**: "point-cloudy"한 느낌(구멍)을 없애는 단계. splatting/elliptical weighting으로 부드러운 표면을 만들고 anti-aliasing 등 필터 추가.

### 1.5 Splatting

**핵심 정의**: `splat = colored point primitive × alpha mask`

- **colored point**: 각 점은 base color $c$
- **alpha mask** $w(x,y)$: 보통 **2D Gaussian**. 점이 주변 픽셀에 얼마나 기여하는지(영향력 범위)를 나타냄
- **splat primitive**:

$$\text{splat}(x,y) = c \cdot w(x,y)$$

**Additive alpha blending** (여러 splat이 한 픽셀에서 겹칠 때):

$$c(x,y) = \frac{\sum_i c_i\, w_i(x,y)}{\sum_i w_i(x,y)}$$

- $\sum w_i$가 1이 아닐 수 있음(점 분포가 불규칙) → **normalization 필수**
- normalize 안 하면 겹침 수에 따라 영역이 너무 밝거나 어두워짐

**Extended Z-buffering**: 보통은 가장 가까운 depth 하나만 저장하고 뒤를 버림. 하지만 splat은 같은 픽셀에 약간씩 다른 depth로 여러 개 겹칠 수 있으므로, **z-threshold** 범위 안의 splat은 버리지 않고 **누적(accumulate)**.

### 1.6 Filtering for Reconstruction (EWA)

**왜 필요한가 (aliasing)**:
- splatting = 점을 screen space의 작은 disc(footprint)로 그리는 것
- projection 때문에 object space의 **원(circle) → screen space의 타원(ellipse)** (표면 곡률 + 기울어진 투영각)
- ellipse footprint들이 겹치고, fine detail에서 jagged/shimmering artifact 발생 → 단순히 blob을 찍는 게 아니라 **reconstruction-and-resampling** 전략 필요

**Screen space EWA (Elliptical Weighted Average) filtering**:

$$c(x,y) = \sum_k c_k\, r_k\big(m^{-1}(x,y)\big) \otimes h(x,y)$$

| 기호 | 의미 |
|---|---|
| $c(x,y)$ | 최종 픽셀 색 |
| $c_k$ | reconstruction kernel color |
| $r_k$ | **reconstruction kernel (filter)**: 이산 surfel로부터 연속 이미지를 복원하는 footprint |
| $m^{-1}(x,y)$ | **warping function**: 투영(object→screen)에 따른 kernel 변형 (역사상) |
| $h(x,y)$ | **low-pass filter (isotropic)**: 픽셀 격자용 anti-aliasing 필터, 고주파 제거 |
| $\otimes$ | **convolution**: 두 필터를 결합 |

**왜 Gaussian을 쓰나** → Gaussian은 **linear warping과 convolution에 대해 닫혀(closed) 있음**:
- linear 변환(예: perspective)을 적용해도 결과는 여전히 (타원형) Gaussian
- 두 Gaussian을 convolution해도 결과는 다시 Gaussian
- 즉, 변환·필터마다 복잡한 별도 공식이 필요 없음 → 계산이 단순

**Magnification vs Minification**:
- **Magnification(확대)**: 투영된 footprint가 큼 → anti-aliasing 덜 필요
- **Minification(축소)**: 많은 디테일이 작은 영역에 뭉침 → **low-pass filtering 필요**
- EWA는 local footprint에 맞게 필터를 적응 → jagged edge, flickering, shimmering 감소

---

## 2. Gaussian 기초 (Multivariate Gaussian)

### 2.1 Univariate Gaussian (1D)

평균 $\mu$, 분산 $\sigma^2$:

$$p(x;\mu,\sigma^2) = \frac{1}{\sqrt{2\pi}\,\sigma}\exp\!\left(-\frac{1}{2\sigma^2}(x-\mu)^2\right)$$

### 2.2 Multivariate Gaussian (n차원)

$$p(x;\mu,\Sigma) = \frac{1}{(2\pi)^{n/2}\,|\Sigma|^{1/2}}\exp\!\left(-\frac{1}{2}(x-\mu)^T \Sigma^{-1}(x-\mu)\right)$$

- mean vector $\mu = \begin{bmatrix}\mu_x \\ \mu_y\end{bmatrix}$
- covariance matrix $\Sigma = \begin{bmatrix}\sigma_x^2 & \rho\sigma_x\sigma_y \\ \rho\sigma_x\sigma_y & \sigma_y^2\end{bmatrix}$
- $\sigma_x,\sigma_y$: 각 축 표준편차, $\rho$: x–y 상관계수, $|\Sigma|$: $\Sigma$의 행렬식(determinant)

### 2.3 Covariance가 Gaussian 모양을 결정한다 (시각적 직관)

| $\Sigma$ 형태 | 의미 | 2D 모양 |
|---|---|---|
| **Diagonal** ($\rho=0$) | 차원 간 상관 없음 | 축에 정렬된 ellipse |
| **Off-diagonal** ($\rho\neq0$) | 변수 간 상관 있음 | **기울어진(tilted) ellipse** |

> 이 직관이 3DGS의 핵심: 각 Gaussian의 **covariance가 splat의 늘어남(stretch)·기울기(rotation)** 를 결정.

---

## 3. 3D Gaussian Splatting (3DGS)

> 출처: Kerbl et al., *"3D Gaussian Splatting for Real-Time Radiance Field Rendering"* (2023)

### 3.0 왜 배우는가 / 무엇인가

- **장면 표현의 최첨단**: mesh/voxel(복잡) → Gaussian(단순)
- Flexible & Compact: 가볍지만 high-fidelity → real-time 적합
- Differentiable & Optimizable: mesh/voxel보다 미분 쉬움 → 학습 기반 그래픽스 가능
- Real-time: GPU에서 매우 빠름 (VR/게임)
- **정의**: 3D 점 데이터를 polygon이 아니라 수많은 fuzzy blob(Gaussian)으로 그리는 **rasterization 기법**. 각 Gaussian = `{Position, Covariance, Color, Alpha}`. Covariance가 stretch·scale을 담당.

### 3.1 전체 파이프라인 (큰 4단계)

```
1) SfM (COLMAP)         : 여러 이미지 → 카메라 pose + point cloud
2) Convert Points→Gaussians : 점을 Gaussian으로 초기화
3) Training (Optimize)  : 렌더↔실제사진 비교, SGD로 파라미터 갱신 + Densify/Prune
4) Differentiable Rasterization : Project→Sort→Blend → 최종 이미지
```

루프 구조: `SfM Points → Initialization → 3D Gaussians ⇄ (Projection / Adaptive Density Control) → Differentiable Tile Rasterizer → Image` (Operation Flow ↔ Gradient Flow)

### 3.2 Structure from Motion (SfM)

여러 2D 이미지로부터 3D 구조 복원 (인간의 양안 시차를 모방).

1. 서로 다른 각도의 이미지 여러 장 촬영
2. 각 이미지에서 feature point를 찾고 이미지 간 **매칭 → correspondence** 구성
3. correspondence로 **두 번째 카메라의 상대 pose** 추정
4. 추정된 pose로 매칭된 feature를 **triangulation → 3D 좌표** 추정
5. point cloud(3D 구조)와 camera parameter를 함께 **refine**

> **COLMAP** 라이브러리 사용: Correspondence Search(Feature Extraction → Matching → Geometric Verification) → Incremental Reconstruction(Initialization → Image Registration → Triangulation → Bundle Adjustment → Outlier Filtering).

### 3.3 Convert Points → Gaussians (초기화)

각 Gaussian의 초기값:

1. **Position**: SfM 점 위치 그대로
2. **Covariance**: isotropic Gaussian으로 초기 추정. 가장 가까운 3점까지의 평균 거리 사용

$$d_{avg} = \frac{\|p-p_1\| + \|p-p_2\| + \|p-p_3\|}{3}$$

$$\Sigma = d_{avg}^2 \begin{bmatrix}1&0&0\\0&1&0\\0&0&1\end{bmatrix}$$

  → 초기 Gaussian이 가장 가까운 세 이웃 사이 공간을 대략 덮음
3. **Alpha** = 1, **Color**: 이미지에서 얻되 **Spherical Harmonics(SH)** 로 정의

### 3.4 색상 설정 (Spherical Harmonics, SH)

- **Flat color**(여러 이미지 픽셀 평균)는 카메라가 움직여도 안 변함 → view-dependent 효과 표현 불가
- **SH**: 구(sphere) 위 함수를 위한 수학적 basis. SH 계수를 Gaussian에 붙이면 **시점에 따른 색 변화**를 근사

**SH 계수**:
- 단일 (R,G,B) 대신 R·G·B 각 채널마다 SH 계수 집합 보유
- degree $n=l=2$ → 채널당 **9개** 계수 ($l=0$:1, $l=1$:3, $l=2$:5 → 1+3+5=9)
- degree(band) $l$이 높을수록 복잡한 패턴 표현(보통 $l=2$로 충분)
- 각 $l$에 대해 order $m \in \{-l,\dots,+l\}$

**View direction** $v \to (r,\theta,\phi)$, $Y_k(v)$를 $k$번째 SH basis라 할 때:

$$R(v) = \sum_{k=0}^{8} c_{rk}\, Y_k(v)$$

(R/G/B 각각, total loss는 모든 각도/이미지에 대해 합산)

**SH basis 함수표** (좌표: $x=r\sin\theta\cos\phi,\ y=r\sin\theta\sin\phi,\ z=r\cos\theta,\ r=\sqrt{x^2+y^2+z^2}$)

| | $m=-2$ | $m=-1$ | $m=0$ | $m=1$ | $m=2$ |
|---|---|---|---|---|---|
| $l=0$ | | | $\frac12\sqrt{\frac1\pi}$ | | |
| $l=1$ | | $\frac12\sqrt{\frac3\pi}\frac yr$ | $\frac12\sqrt{\frac3\pi}\frac zr$ | $\frac12\sqrt{\frac3\pi}\frac xr$ | |
| $l=2$ | $\frac12\sqrt{\frac{15}\pi}\frac{yx}{r^2}$ | $\frac12\sqrt{\frac{15}\pi}\frac{yz}{r^2}$ | $\frac14\sqrt{\frac5\pi}\frac{2z^2-x^2-y^2}{r^2}$ | $\frac12\sqrt{\frac{15}\pi}\frac{zx}{r^2}$ | $\frac12\sqrt{\frac{15}\pi}\frac{x^2-y^2}{r^2}$ |

- **초기화**: Gaussian 생성과 동시에 SH 계수도 (0 근처/작은 random) 초기화
- **최적화**: SH 계수는 position·opacity·covariance와 **함께(unified)** 학습 루프에서 최적화

### 3.5 Training (Optimization)

**Iterative optimization** (목표 화질 달성까지 반복):
```
Render → Compare(렌더 vs GT) → (가끔) Split/Clone/Prune → Render → ...
```

**Loss function** — 두 metric을 blend:
- **L1 loss**: 픽셀 차이
- **D-SSIM**: 구조적 유사도(structural similarity)

$$L = (1-\lambda)\,L_1 + \lambda\,L_{\text{D-SSIM}}$$

**SGD tweak** — 모든 Gaussian 파라미터를 한 번에 gradient descent로 갱신:
- Position (정렬 개선), Covariance (크게=넓게 / 작게=디테일), Color·Alpha (실제 사진에 맞춤)

**⚠️ Covariance는 직접 최적화하지 않는다**:
- covariance는 **positive semi-definite**일 때만 물리적 의미가 있음
- SGD는 유효한(PSD) 행렬을 보장하도록 제약하기 어려움
- 따라서 **scaling matrix $S$ + rotation matrix $R$** 로 분해해서 표현:

$$\Sigma = R\,S\,S^T R^T$$

**Adaptive Density Control — Densification** (Gaussian 추가):
- 언제? **Under-reconstruction**(디테일 부족, 빈 영역) / **Over-reconstruction**(너무 넓게 덮어 부정확)
- **Clone**: under-reconstruction → Gaussian 복제 후 약간 이동(coverage 2배)
- **Split**: over-reconstruction → 큰 Gaussian을 작은 두 개로 분할(가까이 배치)

**Adaptive Density Control — Pruning** (Gaussian 제거):
- **Low opacity**: $\alpha$가 임계값(예: $0.001$) 미만
- **너무 큰 Gaussian**: world/screen space에서 과도하게 큰 것

**알고리즘 의사코드 (Adaptive Density Control)**:
```
M ← SfM Points                       ▷ Positions
S, C, A ← InitAttributes()           ▷ Covariances, Colors, Opacities
i ← 0
while not converged do
    V, Î ← SampleTrainingView()      ▷ Camera V and Image
    I ← Rasterize(M, S, C, A, V)     ▷ Alg.2
    L ← Loss(I, Î)
    M, S, C, A ← Adam(∇L)            ▷ Backprop & Step
    if IsRefinementIteration(i) then
        for all Gaussians (μ, Σ, c, α) do
            if α < ε or IsTooLarge(μ,Σ) then RemoveGaussian()   ▷ Pruning
            if ∇pL > τp then                                     ▷ Densification
                if ‖S‖ > τs then SplitGaussian(...)   ▷ Over-reconstruction
                else            CloneGaussian(...)    ▷ Under-reconstruction
    i ← i + 1
```

### 3.6 Differentiable Gaussian Rasterization (7단계 — 순서 암기!)

> "왜 differentiable? → 렌더 결과와 GT 차이를 각 Gaussian 파라미터로 backprop해야 하므로, alpha blending 등 모든 연산이 유효한 gradient를 만들어야 함."

```
1) Frustum culling      : 시야 밖 Gaussian 제거 (헛계산 방지)
2) Project              : camera+perspective 변환 → 3D Gaussian을 2D ellipse로
3) Create Tiles         : w×h 화면을 타일(예: 16×16)로 분할
4) Duplicate + Keys     : 각 ellipse가 겹치는 타일마다 복제
                          L = Gaussian 참조 리스트
                          K = 정렬용 key (depth + tile ID)
5) Sort by Keys         : L+K를 globally sort → front-to-back 보장
6) Identify Tile Ranges : R = 각 타일이 정렬배열의 어느 구간인지(start/end index) 저장
7) Blend in tile        : 타일별로 픽셀마다 front-to-back alpha blending → 이미지 I
```

**Front-to-back alpha blending** (가장 가까운 layer부터):

초기값 $C_{out}=0,\ \alpha_T=1$, $i=1$(가장 가까움)부터 $i=n$(가장 멈)까지:

$$C_{out} \leftarrow C_{out} + \alpha_T\,\alpha_i\,C_i$$
$$\alpha_T \leftarrow \alpha_T\,(1-\alpha_i)$$

- $\alpha_T$(transmittance) = 뒤쪽 layer가 아직 기여할 수 있는 "남은 투명도"
- $\alpha_T \approx 0$ 이면 뒤쪽 layer는 더 blend할 필요 없음 (early termination)

**왜 sorting이 필요한가**: 같은 픽셀에 여러 splat이 겹칠 때 기여가 대칭이 아님 — 뒤쪽 splat은 앞 splat이 남긴 transmittance를 통해서만 기여해야 함.
**왜 per-pixel sort가 아니라 tile-based sort인가**: 완전한 per-pixel 정렬은 너무 비쌈. tile 단위 그룹핑이 GPU에서 locality·병렬효율이 좋아 정확성과 속도의 균형이 좋음.

### 3.7 한계점 (Limitations)

- **정적 장면 가정**: 움직이는 물체는 view 간 모순된 증거(conflicting multi-view evidence) → 블러
- **카메라 보정/pose 의존**: 카메라가 어긋나면 잘못된 geometry를 설명하도록 최적화 → 블러/misplaced splats
- **Floaters / 늘어진 splat**: geometric constraint 부족 시 Gaussian이 빈 공간으로 떠다니거나 부자연스럽게 늘어남
- **어려운 appearance 효과**: 투명도, 반사(reflection), 굴절(refraction), 미관측 영역 — 관측 이미지만으로 안정적인 3D 해가 유일하게 결정되지 않음 (예: MirrorGaussian 등 후속 연구)

---

## 4. ⭐ 핵심 공식 암기 모음 (Cheat Sheet)

> 시험 직전 이 섹션만 봐도 되도록 압축.

**[1] Splat primitive**
$$\text{splat}(x,y) = c \cdot w(x,y) \quad (w:\ \text{2D Gaussian alpha mask})$$

**[2] Additive alpha blending (정규화)**
$$c(x,y) = \frac{\sum_i c_i\, w_i(x,y)}{\sum_i w_i(x,y)}$$

**[3] EWA filtering**
$$c(x,y) = \sum_k c_k\, r_k\big(m^{-1}(x,y)\big) \otimes h(x,y)$$
$$c_k:\text{색},\ r_k:\text{recon. kernel},\ m^{-1}:\text{warping},\ h:\text{low-pass},\ \otimes:\text{convolution}$$

**[4] Univariate Gaussian**
$$p(x;\mu,\sigma^2) = \frac{1}{\sqrt{2\pi}\,\sigma}\exp\!\left(-\frac{(x-\mu)^2}{2\sigma^2}\right)$$

**[5] Multivariate Gaussian**
$$p(x;\mu,\Sigma) = \frac{1}{(2\pi)^{n/2}|\Sigma|^{1/2}}\exp\!\left(-\tfrac12 (x-\mu)^T\Sigma^{-1}(x-\mu)\right)$$

**[6] 2D Covariance matrix**
$$\Sigma = \begin{bmatrix}\sigma_x^2 & \rho\sigma_x\sigma_y \\ \rho\sigma_x\sigma_y & \sigma_y^2\end{bmatrix}\quad(\rho=0:\text{축정렬 ellipse},\ \rho\neq0:\text{tilted ellipse})$$

**[7] Isotropic 초기 covariance**
$$d_{avg}=\frac{\|p-p_1\|+\|p-p_2\|+\|p-p_3\|}{3},\qquad \Sigma = d_{avg}^2\,I_3$$

**[8] Covariance 분해 (PSD 보장)**
$$\Sigma = R\,S\,S^T R^T \quad (R:\text{rotation},\ S:\text{scaling})$$

**[9] Spherical Harmonics 색**
$$R(v) = \sum_{k=0}^{8} c_{rk}\, Y_k(v)\quad(l=0,1,2 \Rightarrow \text{채널당 9 계수})$$
- $Y_0 = \frac12\sqrt{\frac1\pi}$
- $l=1$: $\frac12\sqrt{\frac3\pi}\cdot\frac{\{y,\,z,\,x\}}{r}$ (m=-1,0,+1 순)

**[10] Loss function**
$$L = (1-\lambda)L_1 + \lambda\,L_{\text{D-SSIM}}$$

**[11] Front-to-back alpha blending** (초기 $C_{out}=0,\ \alpha_T=1$)
$$C_{out} \leftarrow C_{out} + \alpha_T\alpha_i C_i,\qquad \alpha_T \leftarrow \alpha_T(1-\alpha_i)$$

**[순서 암기]**
- Point Rendering Pipeline: **Projection → Shading → Visibility → Image Reconstruction**
- Differentiable Rasterizer: **Cull → Project → Tile → Duplicate(L,K) → Sort → TileRange(R) → Blend**
- 3DGS 전체: **SfM → Points→Gaussians → Train(Render·Compare·Densify/Prune) → Rasterize**
- Densification: **Clone**=under-reconstruction, **Split**=over-reconstruction

---

## 5. 연습문제 & 풀이

### Q1. Point-based rendering에 관한 옳은 설명은?
1. projected surfel radius가 너무 작으면 점 사이에 구멍이 생긴다.
2. 점은 XYZ만 있으면 되므로 point-based는 항상 triangle mesh보다 메모리를 적게 쓴다.
3. 표준 OpenGL은 점을 못 그리므로 custom 하드웨어가 필요하다.
4. surfel은 position·normal·color와 함께 종종 polygonal connectivity도 가진다.

**정답: ①**
- ② ✗: 부드러운 표면엔 수백만 점 필요 → indexed mesh(공유 vertex)/압축보다 메모리가 더 클 수 있음
- ③ ✗: OpenGL은 point primitive를 지원. 고품질엔 shader가 필요할 수 있으나 기본 point projection은 일반 GPU에서 동작
- ④ ✗: surfel은 **connectivity가 없다** (이것이 point-based의 핵심)

### Q2. 2D Gaussian의 분해 — 빈칸 채우기

$\Sigma$가 diagonal일 때, 결합 정규화 상수 $\frac{1}{2\pi\sigma_1\sigma_2}$를 두 개의 1D Gaussian으로 분리:

$$p = \frac{1}{\boxed{\sqrt{2\pi}\,\sigma_1}}\exp\!\left(-\tfrac{(x_1-\mu_1)^2}{2\sigma_1^2}\right)\cdot \frac{1}{\boxed{\sqrt{2\pi}\,\sigma_2}}\exp\!\left(-\tfrac{(x_2-\mu_2)^2}{2\sigma_2^2}\right)$$

**정답: 두 빈칸 = $\sqrt{2\pi}\,\sigma_1$ , $\sqrt{2\pi}\,\sigma_2$**
(확인: $\frac{1}{\sqrt{2\pi}\sigma_1}\cdot\frac{1}{\sqrt{2\pi}\sigma_2} = \frac{1}{2\pi\sigma_1\sigma_2}$ ✓)
→ diagonal covariance면 다변량 Gaussian이 두 독립 1D Gaussian의 곱으로 분리됨.

### Q3. $R(\omega)$ 계산 ($l=0,1$ 두 band)
조건: $\omega=(x,y,z)=\left(\tfrac{1}{\sqrt3},\tfrac{1}{\sqrt3},\tfrac{1}{\sqrt3}\right)$ (정규화 → $r=1$), $C=[0.5,\,-0.2,\,0.1,\,0.7]$

basis 값 ($r=1$, $x=y=z=\tfrac{1}{\sqrt3}$):
$$Y(\omega) = \left(\tfrac{1}{2\sqrt\pi},\ \sqrt{\tfrac{3}{4\pi}}\,y,\ \sqrt{\tfrac{3}{4\pi}}\,z,\ \sqrt{\tfrac{3}{4\pi}}\,x\right)$$

각 $l=1$ 항: $\sqrt{\tfrac{3}{4\pi}}\cdot\tfrac{1}{\sqrt3} = \sqrt{\tfrac{1}{4\pi}} = \tfrac{1}{2\sqrt\pi}$ → **네 basis 모두 $\tfrac{1}{2\sqrt\pi}$**

$$R(\omega) = C^T Y(\omega) = \frac{1}{2\sqrt\pi}(0.5 - 0.2 + 0.1 + 0.7) = \frac{1}{2\sqrt\pi}\cdot 1.1$$

$$\boxed{R(\omega) = \frac{11}{20\sqrt\pi} \approx 0.310}$$

(분해 확인: $\tfrac{1}{4\sqrt\pi} - \tfrac{1}{10\sqrt\pi} + \tfrac{1}{20\sqrt\pi} + \tfrac{7}{20\sqrt\pi} = \tfrac{5-2+1+7}{20\sqrt\pi} = \tfrac{11}{20\sqrt\pi}$)

### Q4. Adaptive density control(split/clone)를 완전히 제거하면?

**1) 최종 이미지에 미치는 영향**
- **split 없음** → 디테일 영역에서 흐림/거친 근사. 큰 Gaussian 하나로는 fine edge·thin structure를 못 잡음
- **clone 없음** → 얇거나 과소표현된 영역(가는 물체, 부분 스캔)에 Gaussian이 추가 안 됨 → **구멍/patchy coverage**

**2) 학습 시간·메모리 영향**
- **학습 시간**: 새 Gaussian을 다듬는 반복이 없어 더 빨리 수렴할 수도 있음. 단, 큰 영역이 계속 부실하면 하나의 Gaussian으로 여러 오류를 고치려다 **학습이 정체(stall)** 될 수 있음
- **메모리**: 새 splat이 안 생기고 pruning으로 줄기만 하므로 Gaussian 수가 거의 유지/감소 → **메모리 사용 감소**

---

### 시험 직전 30초 체크리스트
- [ ] disc→ellipse→Gaussian로 이어지는 "3D splat, 2D blend" 한 문장
- [ ] Point pipeline 4단계 / Rasterizer 7단계 순서
- [ ] alpha blending 정규화식 vs front-to-back 누적식 구분
- [ ] covariance를 왜 $RSS^TR^T$로 분해하는가 (PSD)
- [ ] Clone=under, Split=over / Prune 기준 2개(low α, too large)
- [ ] SH: $l=2$면 채널당 9 계수, view-dependent color 목적
- [ ] EWA = reconstruction kernel ⊗ low-pass, Gaussian은 warping·convolution에 closed
