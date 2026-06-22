# COSE361 Artificial Intelligence — Assignment #2 Report

**학번 / 이름:** `<여기에 학번>` / `<여기에 이름>`

> 본 리포트는 4개 과제(다중선형회귀, 결정트리, PCA, CNN) 각각에 대해
> (i) 작성한 코드와 간단한 설명, (ii) 결과 스크린샷, (iii) 결과 논의를 담는다.
> `📷 [스크린샷]` 표시 부분에 실제 실행 화면을 캡처해 삽입할 것.

---

## Task 1.1 — Multiple Linear Regression

### (i) 작성 코드 및 설명

**① scikit-learn 버전**

```python
model = LinearRegression()
model.fit(X_train, y_train)

theta_0 = model.intercept_
theta_1, theta_2, theta_3, theta_4 = model.coef_

y_pred = model.predict(X_test)
mse_sklearn = mean_squared_error(y_test, y_pred)
```

- `LinearRegression`은 정규방정식(normal equation)을 풀어 최적 파라미터를 한 번에 계산한다.
- `fit_intercept=True`(기본값)이므로 절편 `theta_0`(`intercept_`)와 기울기
  `theta_1..theta_4`(`coef_`)가 자동으로 학습된다.
- 예측 후 `mean_squared_error`로 테스트셋 MSE를 계산한다.

**② Gradient Descent 직접 구현 (scikit-learn 미사용)**

```python
def add_bias(X):
    return np.hstack([np.ones((X.shape[0], 1)), X])   # 절편 항을 위한 1 열 추가

X_train_aug = add_bias(X_train)
X_test_aug  = add_bias(X_test)

learning_rate = 0.05
n_iterations  = 5000
n = X_train_aug.shape[0]
theta = np.zeros(X_train_aug.shape[1])               # [t0, t1, t2, t3, t4]

for it in range(n_iterations):
    y_hat = X_train_aug @ theta
    error = y_hat - y_train
    grad  = (2.0 / n) * (X_train_aug.T @ error)       # MSE의 기울기
    theta = theta - learning_rate * grad              # 파라미터 갱신
```

- 입력 X 앞에 1 열을 붙여 절편 `theta_0`를 다른 가중치와 동일하게 학습한다.
- 손실 `J(theta) = (1/n)·Σ(y_hat − y)²`의 그래디언트 `(2/n)·Xᵀ(y_hat − y)`를 따라
  `theta`를 반복 갱신하는 배치 경사하강법이다.
- 학습률 0.05, 반복 5000회로 충분히 수렴시켰다.

### (ii) 결과

📷 **[스크린샷: 학습된 파라미터 + MSE 출력 (라이브러리 / scratch 둘 다)]**

검증된 실제 출력:

```
Multiple Linear Regression (scikit-learn)
  y_hat = 100.8134 + 46.2912*x1 + 5.5895*x2 + 78.9744*x3 + 81.2666*x4
  Test MSE: 106.3378

Multiple Linear Regression via Gradient Descent (from scratch)
  learning_rate = 0.05, n_iterations = 5000
  y_hat = 100.8134 + 46.2912*x1 + 5.5895*x2 + 78.9744*x3 + 81.2666*x4
  Test MSE: 106.3378
```

### (iii) 논의

- 두 방법의 파라미터와 테스트 MSE(**106.3378**)가 소수점 4자리까지 완전히 일치한다.
  이는 경사하강법이 정규방정식의 해(전역 최적해)로 정확히 수렴했음을 의미한다.
  선형회귀의 MSE 손실은 볼록(convex)하므로 적절한 학습률이면 유일한 최적점에 수렴한다.
- `make_regression`의 `noise=10.0`에서 비롯된 잔차가 MSE의 하한을 형성하며, 학습으로
  더 줄일 수 없는 부분이다. `bias=100.0`이 절편 `theta_0 ≈ 100.8`로 잘 복원되었다.
- 학습률을 너무 크게(예: 0.5) 하면 발산하고, 너무 작게 하면 5000회 내 수렴하지 않는다.

---

## Task 1.2 — Decision Tree

### (i) 작성 코드 및 설명

**① scikit-learn 버전**

```python
clf = DecisionTreeClassifier(criterion='gini', max_depth=3, random_state=42)
clf.fit(X_train, y_train)
acc_sklearn = accuracy_score(y_test, clf.predict(X_test))

plot_tree(clf, feature_names=feature_names, class_names=list(class_names),
          filled=True, rounded=True)
```

- 지시된 하이퍼파라미터(`gini`, `max_depth=3`, `random_state=42`)로 학습한다.
- `plot_tree`로 분할 특징/임계값/클래스 분포를 시각화한다.

**② 직접 구현 (scikit-learn 미사용) — CART 알고리즘**

```python
def gini(y):                                  # 지니 불순도 1 - Σ p_k²
    counts = np.bincount(y, minlength=n_classes)
    probs  = counts / len(y)
    return 1.0 - np.sum(probs ** 2)

def best_split(X, y):                         # 자식 가중 지니를 최소화하는 (특징, 임계값)
    best_gini = gini(y); best_idx = best_thr = None
    for feature_index in range(X.shape[1]):
        values = np.unique(X[:, feature_index])
        thresholds = (values[:-1] + values[1:]) / 2.0      # 인접 값의 중점
        for thr in thresholds:
            left = X[:, feature_index] <= thr
            yl, yr = y[left], y[~left]
            if len(yl) == 0 or len(yr) == 0: continue
            w = (len(yl)*gini(yl) + len(yr)*gini(yr)) / len(y)
            if w < best_gini:
                best_gini, best_idx, best_thr = w, feature_index, thr
    return best_idx, best_thr

def build_tree(X, y, depth=0, max_depth=3):   # 재귀적으로 분할
    node = Node(...)                          # 다수결 클래스를 leaf 예측값으로 저장
    if depth < max_depth and node.gini > 0.0:
        idx, thr = best_split(X, y)
        if idx is not None:
            ...                               # left = (<= thr), right = (> thr) 재귀
    return node
```

- `gini`: 한 노드의 불순도를 계산. **best_split**: 모든 특징 × 모든 임계값 후보(인접
  고유값의 중점)를 탐색해 두 자식의 **가중 평균 지니**를 최소화하는 분할을 찾는다.
- `build_tree`: `max_depth=3`에 도달하거나 노드가 순수(gini=0)해지거나 더 나은 분할이
  없을 때까지 재귀적으로 트리를 키운다. 예측은 leaf까지 내려가 다수결 클래스를 반환한다.

### (ii) 결과

📷 **[스크린샷: accuracy 출력 (라이브러리 / scratch) + 트리 시각화]**

- 라이브러리 트리 그림: `decision_tree_sklearn.png` (코드가 자동 저장)
- 직접 구현 트리: 들여쓰기 텍스트로 출력 (아래)

검증된 실제 출력:

```
Decision Tree (scikit-learn)      Test accuracy: 0.9386
Decision Tree (from scratch)      Test accuracy: 0.9386

[worst radius <= 16.795] (gini=0.468, samples=455)
--> True:
    [worst concave points <= 0.136] (gini=0.162, samples=304)
    --> True:
        [radius error <= 1.048] ...
            Leaf: predict 'benign' (samples=270, counts=[4, 266])
        ...
--> False:
    [texture error <= 0.473] (gini=0.100, samples=151)
    ...
        Leaf: predict 'malignant' (samples=141, counts=[141, 0])
```

### (iii) 논의

- 두 구현 모두 테스트 정확도 **0.9386(93.86%)**으로 동일하며, 첫 분할
  (`worst radius <= 16.795`)을 비롯한 트리 구조도 사실상 동일하다. 직접 구현한
  지니 기반 탐욕적(greedy) 분할이 scikit-learn의 CART와 같은 결정을 내림을 확인했다.
- `worst radius`, `worst concave points` 등 종양 크기·오목도 관련 특징이 상위 분할에
  선택되어, 악성/양성 판별에서 의학적으로도 타당한 특징이 중요함을 보여준다.
- `max_depth=3` 제약으로 일부 leaf는 완전히 순수하지 않다(예: `counts=[4, 266]`).
  깊이를 늘리면 train 정확도는 오르지만 과적합 위험이 커진다.

---

## Task 1.3 — Principal Component Analysis (PCA)

### (i) 작성 코드 및 설명

**① 표준화 + scikit-learn PCA**

```python
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)            # 각 특징을 평균 0, 분산 1로

pca = PCA(n_components=2)
X_pca = pca.fit_transform(X_scaled)
evr = pca.explained_variance_ratio_           # 각 주성분의 설명분산비
```

- PCA는 특징 스케일에 민감하므로 먼저 `StandardScaler`로 표준화한다.
- 2개 주성분으로 축소하고 `explained_variance_ratio_`로 분산 설명 비율을 구한다.

**② 직접 구현 (scikit-learn 미사용) — 공분산 고유분해**

```python
X_centered  = X_scaled - X_scaled.mean(axis=0)
cov_matrix  = np.cov(X_centered, rowvar=False)        # 공분산 행렬
eigvals, eigvecs = np.linalg.eigh(cov_matrix)         # 대칭행렬 고유분해(오름차순)

order   = np.argsort(eigvals)[::-1]                   # 고유값 내림차순 정렬
eigvals = eigvals[order]; eigvecs = eigvecs[:, order]

top2 = eigvecs[:, :2]                                  # 상위 2개 고유벡터
X_pca_scratch = X_centered @ top2                      # 데이터를 투영

evr_scratch = eigvals[:2] / eigvals.sum()              # 설명분산비
```

- 표준화 데이터의 **공분산 행렬**을 만들고 `np.linalg.eigh`로 고유값/고유벡터를 구한다.
- 고유값(=해당 방향의 분산)을 내림차순 정렬해 **상위 2개 고유벡터**에 데이터를 투영한다.
- 설명분산비는 `고유값 / 전체 고유값 합`으로 계산한다.

### (ii) 결과

📷 **[스크린샷: 설명분산비(각각 + 합계) 출력 + 산점도 (라이브러리 / scratch)]**

- 라이브러리 산점도: `pca_sklearn.png`, 직접 구현 산점도: `pca_scratch.png` (자동 저장)

검증된 실제 출력:

```
PCA (scikit-learn)     PC1: 0.7296   PC2: 0.2285   Total: 0.9581
PCA (from scratch)     PC1: 0.7296   PC2: 0.2285   Total: 0.9581
```

### (iii) 논의

- 두 구현 모두 PC1 **0.7296**, PC2 **0.2285**, 합계 **0.9581**로 일치한다. 2개 주성분만으로
  원본 4차원 분산의 **약 95.8%**를 보존하므로, Iris는 저차원으로 효과적으로 압축된다.
- 산점도에서 `setosa`는 다른 두 종과 완전히 분리되고, `versicolor`와 `virginica`는
  경계에서 약간 겹친다. 이는 분류 난이도(setosa는 매우 쉬움)와도 일치한다.
- scikit-learn과 직접 구현의 산점도는 **축 부호가 반전**될 수 있다(고유벡터의 방향은
  부호까지만 유일). 분산 설명력과 군집 구조는 동일하므로 문제되지 않는다.

---

## Task 1.4 — Convolutional Neural Networks (CNN)

> **실행 환경:** 코랩(Colab) **T4 GPU**에서 학습/평가함 (`Using device: cuda`).
> CIFAR-10 자동 다운로드 후 30 epoch 학습. 실행 코드는 제출본 `assignment2_CNN.py`와
> 동일하다(코랩 편의를 위한 GPU 확인 3줄만 추가).

### (i) 작성 코드 및 설명 (baseline 대비 변경점)

목표: **30 epoch 이내 테스트 정확도 65% 달성** (데이터셋/split 불변, augmentation 허용).
baseline(conv 2층 + FC, 증강·정규화 없음)에서 다음을 개선했다.

**① 데이터 증강 + 정규화**

```python
CIFAR10_MEAN = (0.4914, 0.4822, 0.4465)
CIFAR10_STD  = (0.2470, 0.2435, 0.2616)

transform_train = transforms.Compose([
    transforms.RandomCrop(32, padding=4, padding_mode='reflect'),  # 위치 불변성
    transforms.RandomHorizontalFlip(),                             # 좌우 불변성
    transforms.ToTensor(),
    transforms.Normalize(CIFAR10_MEAN, CIFAR10_STD),
])
transform_eval = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize(CIFAR10_MEAN, CIFAR10_STD),
])
```

**② 더 깊은 VGG풍 네트워크 + BatchNorm**

```python
def conv_block(in_ch, out_ch):
    return nn.Sequential(
        nn.Conv2d(in_ch, out_ch, 3, padding=1), nn.BatchNorm2d(out_ch), nn.ReLU(inplace=True),
        nn.Conv2d(out_ch, out_ch, 3, padding=1), nn.BatchNorm2d(out_ch), nn.ReLU(inplace=True),
        nn.MaxPool2d(2, 2))

# block1(3→32) → block2(32→64) → block3(64→128), 공간 32→16→8→4
self.classifier = nn.Sequential(
    nn.Flatten(), nn.Dropout(0.3),
    nn.Linear(128*4*4, 256), nn.ReLU(inplace=True), nn.Dropout(0.3),
    nn.Linear(256, num_classes))
```

**③ 정규화 + 학습률 스케줄**

```python
num_epochs = 30
optimizer  = optim.Adam(model.parameters(), lr=0.001, weight_decay=5e-4)
scheduler  = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=num_epochs)
# ... 매 epoch 끝에 scheduler.step()
```

- **변경 요약:** (a) RandomCrop+Flip 증강, (b) 3블록 conv + **BatchNorm**(소규모 데이터·
  30 epoch 내 수렴의 핵심), (c) weight_decay(L2) + Cosine LR 스케줄, (d) epoch 20→30.
- 8,000장 train 부분집합 과적합을 막기 위해 Dropout(0.3)과 weight decay를 병행하되,
  30 epoch 내 충분히 학습되도록 과한 정규화(예: dropout 0.5)는 피했다.

### (ii) 결과

📷 **[스크린샷: 30 epoch 학습 로그 + 최종 test accuracy]**

```
최종 Test Accuracy:  78.05 %     (목표 ≥ 65% → 달성 ✅, 약 +13%p 여유)
Best Val Accuracy:   79.95 % (epoch 30)
```

### (iii) 논의

- 최종 **테스트 정확도 78.05%**로 목표(65%)를 약 **13%p 초과** 달성했다. 검증 정확도
  79.95%(epoch 30)와 테스트 78.05%가 거의 일치해 **과적합 없이 잘 일반화**되었음을 보여준다.
- **학습 곡선이 건강하다:** train loss가 1.84 → 0.44로 꾸준히 감소하고 val accuracy는
  42% → 80%로 단조 상승하며, val loss도 1.54 → 0.58로 함께 내려간다. 8,000장의 작은
  학습 부분집합임에도 **증강(RandomCrop/Flip) + Dropout(0.3) + weight decay**가 과적합을
  억제해, train/val 손실 격차가 크게 벌어지지 않았다.
- **BatchNorm 효과**가 두드러진다: epoch 2에서 이미 val 51%, epoch 9에 65%를 돌파해
  30 epoch 제약 안에서 빠르게 수렴했다. BatchNorm 없이는 같은 epoch 수로 이 정확도에
  도달하기 어렵다.
- best epoch이 마지막(30)인 것은 **Cosine LR 스케줄**이 학습률을 0으로 천천히 낮추며
  후반 epoch에서 미세 조정을 이어갔기 때문이다. 즉 30 epoch 예산을 끝까지 활용했고,
  best-val 기준 모델 선택이 자연스럽게 마지막 가중치를 골랐다.

---

## 부록 — 실행 방법

```bash
python assignment2_multi-regression.py     # 회귀 (MSE 출력)
python assignment2_decision-tree.py        # 결정트리 (accuracy + 트리, png 저장)
python assignment2_PCA.py                  # PCA (설명분산비 + 산점도 png 저장)
python assignment2_CNN.py                  # CNN (GPU 권장, 30 epoch 로그 + test acc)
```
