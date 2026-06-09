# Lecture 15. Normal Mapping & Tessellation — 시험 정리 노트

> 큰 그림: **"적은 vertex로 디테일을 표현"** 하는 두 가지 전략
> - **Normal Mapping** → 실제 geometry는 안 바꾸고 **normal(법선)만 속여서** 음영(shading)으로 디테일 표현
> - **Displacement Mapping (+ Tessellation)** → 실제 geometry(vertex 위치)를 **진짜로 변형**해서 디테일 표현

---

## 1. 왜 필요한가 — Bumpy surfaces

벽돌벽·포장도로처럼 울퉁불퉁한(bumpy) 표면을 사실적으로 렌더링하고 싶다.

| 방식 | 장점 | 단점 |
|---|---|---|
| **High-resolution mesh** | 진짜 geometric bump, silhouette, self-shadowing 표현 가능 | vertex 수 ↑ → CPU→GPU 전송량(memory bandwidth) ↑, vertex processing 비용 ↑ |
| **Low-resolution mesh + texture** | 렌더링 비용 저렴 | **색만 바뀔 뿐, lighting은 여전히 거친(coarse) surface normal로 계산** → 음영에 bump가 안 나타남 |

**핵심 포인트(시험 단골):** high-res와 low-res의 결정적 차이는 **normal 데이터**다.
- Low-res 표면은 평평해서 각 점의 normal이 거의 같음 → 빛을 받아도 음영 변화가 없음.
- 즉, "텍스처는 color($m_d$)만 바꾸고, normal은 안 바꾼다"는 게 한계.

---

## 2. Normal Map 생성 (Generation)

### 2-1. 아이디어
High-res surface의 normal을 **미리 계산(pre-compute)해서 텍스처에 저장** → 이게 **normal map**.
런타임에는 low-res mesh(= **base surface**)에 이 normal map을 입혀 lighting 계산.
→ vertex 수를 안 늘리고도 렌더링 품질 ↑.

### 2-2. Image → Height map
- **height map**: 보통 아티스트가 제작하거나 이미지에서 추정.
- 이미지를 grayscale로 변환 → **grayscale 값을 높이(height)로 해석**.

### 2-3. Height map → Normal map
$(x, y, h(x,y))$ 지점의 normal을, 이웃 점들의 높이 차이로 구함 (red·green 벡터의 cross product).

- x방향 높이차: **δh_x = h(x+1, y) − h(x−1, y)**
- y방향 높이차: **δh_y = h(x, y+1) − h(x, y−1)**
- 두 접선 방향 벡터: red = (2, 0, δh_x), green = (0, 2, δh_y)
- **normal = (−2·δh_x, −2·δh_y, 4) / ‖(−2·δh_x, −2·δh_y, 4)‖**  ← red × green 정규화

### 2-4. Normal map visualization (range conversion)
normal 성분 $(n_x, n_y, n_z)$는 **[−1, 1]** 범위. 텍스처의 RGB는 **[0, 1]** 범위 → 변환 필요.

- **R = (n_x + 1)/2,  G = (n_y + 1)/2,  B = (n_z + 1)/2**  (저장/encoding)
- 복원(decoding): **n = 2·(R,G,B) − 1**
- 대부분 z성분(파란색 B)이 크므로 normal map이 **전체적으로 푸르스름하게** 보임.

---

## 3. Normal Map 사용법 (How to use)

1. Polygon mesh를 rasterize → texture coordinate로 normal map 접근.
2. $(s, t)$ 위치의 normal을 **filtering**으로 얻음.
3. Diffuse 항: **max(n · l, 0) · s_d ⊗ m_d**
   - **n**: normal map에서 fetch한 법선
   - **m_d**: image texture에서 fetch한 diffuse 색
   - **l**: light vector

---

## 4. Tangent-Space Normal Mapping (가장 중요)

### 4-1. Normal mapping = texturing
텍스처를 여러 표면에 붙이듯, normal map도 평면·곡면 등 **다양한 표면에 붙일 수 있어야** 함.

### 4-2. 핵심 문제 — 공간 불일치 (space inconsistency)
- normal map에서 fetch한 **normal은 tangent space** 벡터.
- **light는 보통 world space** 벡터.
- 따라서 `dot(normal, light)`나 `PhongShading(n, L)`를 그냥 하면 **틀린 결과**.
- 이유: 서로 다른 좌표계의 벡터끼리 dot product를 하기 때문 (→ **Discussion 1 답**).

### 4-3. Tangent space {T, B, N}
표면의 한 점에서 정의되는 **orthonormal(정규직교) 3벡터**:
- **T** (Tangent, 접선)
- **B** (Bitangent, 종접선)
- **N** (Normal, 법선)

- **N**: modeling 단계에서 vertex마다 정의됨 (per-vertex).
- **T, B**: 계산해서 구해야 함. **texture coordinate 방향**에 맞춰 T를 정함.
- normal map에서 fetch한 $n(s_q, t_q)$가 **tangent space에서 (0,0,1)인 $N_q$를 대체**함.
- 어떤 점이든, normal map의 normal은 **그 점의 tangent space에서 정의된 것**으로 간주.

### 4-4. T, B 계산 (삼각형 edge & UV로 유도)
세 vertex $P_0, P_1, P_2$, 텍스처 좌표 $(U_i, V_i)$. 두 edge:

- E1 = ΔU1·T + ΔV1·B   (ΔU1 = U1−U0, ΔV1 = V1−V0)
- E2 = ΔU2·T + ΔV2·B

행렬 형태:

```
[ E1 ]   [ ΔU1  ΔV1 ] [ T ]
[ E2 ] = [ ΔU2  ΔV2 ] [ B ]
```

역행렬로 T, B를 구함:

```
[ T ]   [ ΔU1  ΔV1 ]⁻¹ [ E1 ]
[ B ] = [ ΔU2  ΔV2 ]    [ E2 ]
```

2×2 역행렬 전개 (det = ΔU1·ΔV2 − ΔV1·ΔU2):

- **T = (ΔV2·E1 − ΔV1·E2) / det**
- **B = (−ΔU2·E1 + ΔU1·E2) / det**

### 4-5. 불일치 해결 — 두 가지 방법 (Discussion 2 답)
| 방법 | Pros |
|---|---|
| **normal → world space로 변환** | lighting 계산이 보통 world space에서 이뤄짐 → shader 구현이 단순해지는 면 있음 |
| **light → tangent space로 변환** | tangent space는 pre-computed + per-vertex 요소 → **light를 vertex shader에서 변환** 가능 → 연산 비용 ↓ |

- **"보편적으로 더 나은 방법은 없다"**가 정답 포인트.
- 본 강의는 **tangent-space-light** 방식으로 설명하지만, 많은 **modern renderer는 sampled normal을 pixel shader에서 world space로 변환**함.

### 4-6. 실제 처리 흐름 (tangent-space-light)
1. per-vertex **TBN basis를 pre-compute**, vertex array에 저장 → vertex shader로 전달.
2. vertex shader가 T, B, N을 **world space로 변환** 후, 그걸로 행렬 구성.
3. **world-space light를 per-vertex tangent space로 회전(rotate)**.
4. tangent space 안에서 normal(n)과 light로 lighting 계산.

### 4-7. Tangent normal map 장단점
- **장점**
  - **Object-independent**: 객체의 위치/방향에 안 묶임 → 여러 객체에 **재사용 가능** (asset library, 다양한 방향의 인스턴스에 유리).
  - **deforming surface(예: 캐릭터 피부)**에서도 잘 작동 — normal이 표면 자체 기준으로 계산되기 때문.
- **단점**
  - 일관된 tangent space를 계산·유지해야 함 → 모델 제작 + shading 연산이 복잡해짐.
  - **UV가 갈라지는 seam**이나 **mirror된 geometry**에서 문제 발생.

---

## 5. Hardware Tessellation

GPU가 primitive 하나를 **다수의 작은 primitive로 분할**.

### 5-1. 파이프라인 (순서 암기)
```
Input Assembler → Vertex Shader → [Hull Shader] → [Tessellator] → [Domain Shader]
→ Geometry Shader → Rasterizer → Pixel Shader → Output Merger
```
- 새로 추가된 **programmable** 단계 2개: **Hull Shader, Domain Shader**
- 새로 추가된 **fixed(hard-wired)** 단계 1개: **Tessellator**

### 5-2. Vertex Shader & Hull Shader
- **VS**: 더 이상 space change(좌표계 변환)를 담당하지 않음.
  - tessellation을 쓰면 **clip-space vertex position을 Domain shader가 계산** (VS가 아님).
- **HS**: tessellator가 필요로 하는 **state를 선언**.
  - control point 개수, patch face 타입, partitioning 방식, **tessellation factor** 등.

### 5-3. Tessellator (= primitive generator)
- patch를 subdivide → **barycentric 좌표**로 표현되는 작은 점들 생성.
- **fixed-function** 단계 — user shader code 실행 안 함. tessellation factor만 주면 triangle/quad patch 위에 domain 좌표 생성.
- 제약: **한 invocation당 vertex 1개만 생성**, **vertex를 drop 못 함**.
- **Inner / Outer tessellation level**로 분할 밀도 제어
  (`gl_TessLevelInner[]`, `gl_TessLevelOuter[]`).

### 5-4. Domain Shader
- Hull shader가 넘긴 vertex 위치를 **bilinear patch의 control point**로 사용.
- $(u, v, w)$로 patch를 평가 → **3D 점** 반환. 텍스처 좌표도 같은 방식으로 보간.
- triangle patch barycentric 평가:
  - **vertex position = P[0]·u + P[1]·v + P[2]·w**  (단, u + v + w = 1)

---

## 6. Displacement Mapping

- Normal mapping은 base surface의 **실제 geometry를 안 바꿈** → silhouette은 여전히 평평.
- **Displacement mapping + Tessellation**이 이걸 해결:
  1. Tessellation 하드웨어가 base surface를 먼저 **tessellate**.
  2. tessellated vertex들을 **displacement vector 방향으로 displace(이동)**.

### 처리 흐름 (paved-ground 예시)
- 입력 = **patch(= base surface)**, triangle 또는 quad.
- **Hull shader**: quad를 base surface로 받아 → tessellation level 결정 → tessellator로 전달.
- **Tessellator**: quad domain을 2D triangle mesh로 분할.
- **Domain shader**: 2D mesh의 vertex마다 실행 → quad를 bilinear patch로 보고 $(u,v)$로 점 평가 → **height map으로 displace**.

### Results 수치 예 (강의 슬라이드)
- base surface = 16 quads → quad 1개가 **722 triangles**로 tessellate → height map으로 수직 변위 → high-frequency mesh 음영 처리.
- 비교 예: original 6,895 triangles vs 단순화 689 triangles + normal mapping → 적은 폴리곤으로 비슷한 디테일.

---

## 7. 핵심 공식 암기 노트 (Cheatsheet)

> 시험 직전 이 부분만 빠르게 훑기.

**① Height map → 높이차**
- δh_x = h(x+1, y) − h(x−1, y)
- δh_y = h(x, y+1) − h(x, y−1)

**② Normal 계산 (cross product 결과)**
- n = (−2·δh_x, −2·δh_y, 4) / ‖(−2·δh_x, −2·δh_y, 4)‖
- (유도: (2,0,δh_x) × (0,2,δh_y) = (−2δh_x, −2δh_y, 4))

**③ Normal ↔ RGB 변환**
- 저장: R = (n_x+1)/2, G = (n_y+1)/2, B = (n_z+1)/2   [−1,1] → [0,1]
- 복원: n = 2·(R,G,B) − 1

**④ Diffuse 항**
- max(n · l, 0) · s_d ⊗ m_d
- 전체 Phong: max(n·l, 0)·s_d⊗m_d + (max(r·v, 0))^sh·s_s⊗m_s + s_a⊗m_a + m_e

**⑤ Tangent space basis 대체**
- tangent space에서 N_q = (0, 0, 1) → normal map의 n(s_q, t_q)가 이를 대체

**⑥ T, B 유도**
- E1 = ΔU1·T + ΔV1·B,  E2 = ΔU2·T + ΔV2·B
- [T; B] = [ΔU1 ΔV1; ΔU2 ΔV2]⁻¹ · [E1; E2]
- det = ΔU1·ΔV2 − ΔV1·ΔU2
- T = (ΔV2·E1 − ΔV1·E2) / det
- B = (−ΔU2·E1 + ΔU1·E2) / det

**⑦ Domain shader 평가 (triangle, barycentric)**
- vertex position = P[0]·u + P[1]·v + P[2]·w   (u + v + w = 1)

---

## 8. 토론/서술형 대비 (Discussion Q&A)

**Q1. `PhongShading(N_q, L)` 또는 `PhongShading(n(s_q,t_q), L)`로 올바른 음영이 안 나오는 이유는?**
A. normal map의 normal은 **tangent space**, light(L)은 보통 **world space**에 정의됨. 서로 다른 좌표계의 벡터로 dot product를 하므로 결과가 틀림. → **normal mapping은 이 공간 불일치를 먼저 해결해야 함.**

**Q2. 공간 불일치를 해결하는 두 가지 방법과 각 장점은?**
A.
- normal을 world space로 변환 → lighting을 보통 world에서 하므로 shader 구현이 단순.
- light를 tangent space로 변환 → tangent space는 pre-computed·per-vertex라 **vertex shader에서 변환** 가능 → 비용 ↓.
- **보편적으로 더 우월한 방법은 없음.** (단, 현대 렌더러는 pixel shader에서 normal을 world로 변환하는 경향)

**Q3. Normal mapping과 Displacement mapping의 결정적 차이?**
A. Normal mapping은 normal만 바꿔 **음영으로만** 디테일 표현(geometry 불변, silhouette 평평). Displacement mapping은 tessellation으로 **실제 vertex를 변위**시켜 진짜 geometry·silhouette을 생성.

**Q4. Tessellator의 특성 3가지?**
A. ① fixed-function(셰이더 코드 실행 X), ② tessellation factor 기반으로 barycentric 좌표 생성, ③ invocation당 vertex 1개만 생성·drop 불가.

---

### 한 줄 요약 체인
bumpy 표현 필요 → high-res는 비쌈 → **normal map**으로 normal만 저장(저렴) → 단, **tangent vs world 공간 불일치** → **TBN basis**로 해결 → 그래도 silhouette은 평평 → **tessellation + displacement**로 실제 geometry 변위.
