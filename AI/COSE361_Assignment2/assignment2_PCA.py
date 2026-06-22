# ====================== Setup ======================
# Principal Component Analysis (PCA): Reduce high-dimensional data to a few
# uncorrelated directions (principal components) that capture the most variance.
# Here we project the 4-feature Iris data down to 2 principal components so the
# data can be visualized in a single 2D scatter plot.

import numpy as np
import matplotlib.pyplot as plt

from sklearn.datasets import load_iris
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA


# ====================== Load Dataset ======================
# load_iris returns the classic Iris dataset: 150 samples, 4 numeric features
# (sepal length, sepal width, petal length, petal width) and 3 species
# (setosa, versicolor, virginica) encoded as integer labels 0 / 1 / 2.
# We keep X (features) for PCA and y (target) only for coloring the plots.

iris = load_iris()
X = iris.data                        # features, shape (150, 4)
y = iris.target                      # species labels (0, 1, 2), shape (150,)
feature_names = iris.feature_names   # names of the 4 features
target_names  = iris.target_names    # names of the 3 species

print("=" * 60)
print("Dataset: Iris (load_iris)")
print("=" * 60)
print(f"  X shape:   {X.shape}")
print(f"  y shape:   {y.shape}")
print(f"  Features:  {list(feature_names)}")
print(f"  Species:   {list(target_names)}")
print()


# ====================== Standardize Features ======================
# Scale every feature to zero mean and unit variance so that no single feature
# dominates the principal components just because of its units/scale.

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)


# ============================================================
# PCA (using scikit-learn)
# ============================================================

# ====================== Fit PCA & Transform ======================
# Reduce the standardized 4D data to 2 principal components.

pca = PCA(n_components=2)
X_pca = pca.fit_transform(X_scaled)


# ====================== Explained Variance ======================
# explained_variance_ratio_ gives the fraction of total variance per component.

evr = pca.explained_variance_ratio_
print("-" * 60)
print("PCA (scikit-learn)")
print("-" * 60)
print(f"  Explained variance ratio  PC1: {evr[0]:.4f}")
print(f"  Explained variance ratio  PC2: {evr[1]:.4f}")
print(f"  Total (PC1 + PC2):             {evr.sum():.4f}")
print()


# ====================== Visualize ======================
# Scatter the 2D projection, colored by the true species.

def scatter_pca(X_2d, title, filename):
    plt.figure(figsize=(8, 6))
    for label, name in enumerate(target_names):
        mask = y == label
        plt.scatter(X_2d[mask, 0], X_2d[mask, 1], label=name, alpha=0.8)
    plt.xlabel("PC1")
    plt.ylabel("PC2")
    plt.title(title)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(filename, dpi=120)
    print(f"  Scatter plot saved to {filename}")

scatter_pca(X_pca, "Iris PCA (scikit-learn)", "pca_sklearn.png")
print()


# ============================================================
# PCA (from scratch, using NumPy)
# ============================================================

# ====================== Implement PCA & Transform ======================
# Manual PCA via the covariance-matrix eigendecomposition.

# X_scaled already has zero column mean, but subtract again to be explicit.
X_centered = X_scaled - X_scaled.mean(axis=0)

# Covariance matrix (rowvar=False -> columns are variables/features).
cov_matrix = np.cov(X_centered, rowvar=False)

# np.linalg.eigh returns eigenvalues in ASCENDING order (symmetric matrix).
eigvals, eigvecs = np.linalg.eigh(cov_matrix)

# Sort descending by eigenvalue and keep the top 2 eigenvectors as columns.
order = np.argsort(eigvals)[::-1]
eigvals = eigvals[order]
eigvecs = eigvecs[:, order]

top2 = eigvecs[:, :2]
X_pca_scratch = X_centered @ top2


# ====================== Explained Variance ======================
# Each eigenvalue is the variance along its component; ratio = eigval / total.

total_var = eigvals.sum()
evr_scratch = eigvals[:2] / total_var
print("-" * 60)
print("PCA (from scratch)")
print("-" * 60)
print(f"  Explained variance ratio  PC1: {evr_scratch[0]:.4f}")
print(f"  Explained variance ratio  PC2: {evr_scratch[1]:.4f}")
print(f"  Total (PC1 + PC2):             {evr_scratch.sum():.4f}")
print()


# ====================== Visualize ======================
# Same scatter plot for the from-scratch projection (sign flips vs sklearn OK).

scatter_pca(X_pca_scratch, "Iris PCA (from scratch)", "pca_scratch.png")
print()
