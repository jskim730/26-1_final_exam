# ====================== Setup ======================
# Multiple Linear Regression: Predict a continuous target from MULTIPLE input features.
# Hypothesis:  y_hat = theta_0 + theta_1 * x_1 + theta_2 * x_2 + theta_3 * x_3 + theta_4 * x_4

import numpy as np

from sklearn.datasets import make_regression
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error


# ====================== Generate Dataset ======================
# make_regression creates a synthetic linear regression problem.
# Here we use 4 informative features, so the underlying relationship has
# 5 parameters in total: theta_0 (intercept) + theta_1..theta_4 (one per feature).

n_samples  = 400
n_features = 4                       # 4 features -> parameters theta_1, theta_2, theta_3, theta_4

X, y = make_regression(
    n_samples=n_samples,
    n_features=n_features,           # multiple features for multiple linear regression
    noise=10.0,                      # Gaussian noise std added to y
    bias=100.0,
    random_state=42,
)

print("=" * 60)
print("Dataset: synthetic (make_regression)")
print("=" * 60)
print(f"  X shape:  {X.shape}")
print(f"  y shape:  {y.shape}")
print()


# ====================== Train/Test Split ======================
# Hold out 20% of the data to estimate generalization to unseen inputs.
# random_state fixes the split so results are reproducible across runs.
# Use the SAME split so the MSE values are comparable.

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print(f"  Train size:  {X_train.shape[0]}")
print(f"  Test size:   {X_test.shape[0]}")
print()


# ============================================================
# Multiple Linear Regression (using scikit-learn)
# ============================================================

# ====================== Train the Model ======================
# Fit scikit-learn's LinearRegression on the training data. With the default
# fit_intercept=True, the intercept theta_0 is learned automatically and the
# coefficients theta_1..theta_4 (one per feature) are stored in model.coef_.

model = LinearRegression()
model.fit(X_train, y_train)

theta_0 = model.intercept_
theta_1, theta_2, theta_3, theta_4 = model.coef_

print("-" * 60)
print("Multiple Linear Regression (scikit-learn)")
print("-" * 60)
print("  Learned hypothesis:")
print(f"    y_hat = {theta_0:.4f} "
      f"+ {theta_1:.4f}*x1 "
      f"+ {theta_2:.4f}*x2 "
      f"+ {theta_3:.4f}*x3 "
      f"+ {theta_4:.4f}*x4")


# ====================== Predict & Evaluate ======================
# Predict on the held-out test set and report the mean squared error.

y_pred = model.predict(X_test)
mse_sklearn = mean_squared_error(y_test, y_pred)
print(f"  Test MSE: {mse_sklearn:.4f}")
print()


# ============================================================
# Multiple Linear Regression via Gradient Descent (from scratch)
# ============================================================

# ======================  Train the Model ======================
# Implement batch gradient descent from scratch (NumPy only).
# We prepend a column of ones to X so that the intercept theta_0 is learned as
# just another weight: X_aug = [1, x1, x2, x3, x4], theta = [t0, t1, t2, t3, t4].
#
#   - Hypothesis:  y_hat = X_aug @ theta
#   - MSE loss:    J(theta) = (1/n) * sum( (y_hat - y)^2 )
#   - Gradient:    grad     = (2/n) * X_aug^T @ (y_hat - y)
#   - Update:      theta   <- theta - learning_rate * grad

def add_bias(X):
    """Prepend a column of ones for the intercept term."""
    return np.hstack([np.ones((X.shape[0], 1)), X])

X_train_aug = add_bias(X_train)
X_test_aug = add_bias(X_test)

learning_rate = 0.05
n_iterations = 5000
n = X_train_aug.shape[0]

# Initialize all parameters to zero.
theta = np.zeros(X_train_aug.shape[1])

for it in range(n_iterations):
    y_hat = X_train_aug @ theta
    error = y_hat - y_train
    grad = (2.0 / n) * (X_train_aug.T @ error)
    theta = theta - learning_rate * grad

print("-" * 60)
print("Multiple Linear Regression via Gradient Descent (from scratch)")
print("-" * 60)
print(f"  learning_rate = {learning_rate}, n_iterations = {n_iterations}")
print("  Learned hypothesis:")
print(f"    y_hat = {theta[0]:.4f} "
      f"+ {theta[1]:.4f}*x1 "
      f"+ {theta[2]:.4f}*x2 "
      f"+ {theta[3]:.4f}*x3 "
      f"+ {theta[4]:.4f}*x4")


# ====================== Predict & Evaluate ======================
# Predict on the test set with the learned parameters and compute the MSE.

y_pred_gd = X_test_aug @ theta
mse_gd = np.mean((y_pred_gd - y_test) ** 2)
print(f"  Test MSE: {mse_gd:.4f}")
print()
