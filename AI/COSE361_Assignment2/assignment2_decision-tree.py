# ====================== Setup ======================
# Decision Tree Classifier: Predict a discrete class label from input features.
# A decision tree splits the data with a series of yes/no questions
# (a threshold on one feature at a time), picking the split that best
# separates the classes at each step.
#
# Splitting criterion (Gini impurity) for a node whose class probabilities
# are p_k:
#     Gini = 1 - sum_k ( p_k ** 2 )
# A lower Gini means a purer node (samples mostly belong to one class).

import numpy as np
import matplotlib.pyplot as plt

from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.metrics import accuracy_score


# ====================== Load Dataset ======================
# The Breast Cancer Wisconsin dataset is a binary classification problem:
#   - 30 numeric features computed from digitized cell-nucleus images
#   - target = 0 (malignant) or 1 (benign)

data = load_breast_cancer()
X, y = data.data, data.target
feature_names = data.feature_names       # names of the 30 input features
class_names   = data.target_names        # ['malignant', 'benign']

print("=" * 60)
print("Dataset: Breast Cancer Wisconsin (load_breast_cancer)")
print("=" * 60)
print(f"  X shape:  {X.shape}")
print(f"  y shape:  {y.shape}")
print(f"  classes:  {list(class_names)}")
print()


# ====================== Train/Test Split ======================
# Hold out 20% of the data to estimate generalization to unseen inputs.
# random_state fixes the split so results are reproducible across runs.
# stratify=y keeps the class proportions the same in the train and test sets.
# Use the SAME split so the results are comparable.

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"  Train size:  {X_train.shape[0]}")
print(f"  Test size:   {X_test.shape[0]}")
print()


# ============================================================
# Decision Tree Classifier (using scikit-learn)
# ============================================================

# ====================== Train the Model ======================
# Fit scikit-learn's DecisionTreeClassifier with the required hyperparameters.

clf = DecisionTreeClassifier(criterion='gini', max_depth=3, random_state=42)
clf.fit(X_train, y_train)


# ====================== Predict & Evaluate ======================
# Predict on the test set and report classification accuracy.

y_pred = clf.predict(X_test)
acc_sklearn = accuracy_score(y_test, y_pred)

print("-" * 60)
print("Decision Tree (scikit-learn)")
print("-" * 60)
print(f"  Test accuracy: {acc_sklearn:.4f}")
print()


# ====================== Visualize the Tree ======================
# Plot the trained tree with readable feature and class names.

plt.figure(figsize=(20, 10))
plot_tree(
    clf,
    feature_names=feature_names,
    class_names=list(class_names),
    filled=True,
    rounded=True,
    fontsize=9,
)
plt.title("Decision Tree (scikit-learn, gini, max_depth=3)")
plt.tight_layout()
plt.savefig("decision_tree_sklearn.png", dpi=120)
print("  Tree plot saved to decision_tree_sklearn.png")
print()


# ============================================================
# Decision Tree Classifier (from scratch)
# ============================================================

# ======================  Train the Model ======================
# A from-scratch CART decision tree using Gini impurity, matching the
# scikit-learn settings (criterion='gini', max_depth=3).

class Node:
    """A tree node: internal nodes store a split; leaves store a prediction."""
    def __init__(self, gini, num_samples, class_counts, predicted_class):
        self.gini = gini                      # impurity at this node
        self.num_samples = num_samples        # #samples reaching this node
        self.class_counts = class_counts      # per-class sample counts
        self.predicted_class = predicted_class  # majority class (leaf prediction)
        self.feature_index = None             # feature used to split
        self.threshold = None                 # threshold used to split
        self.left = None                      # samples with feature <= threshold
        self.right = None                     # samples with feature >  threshold


def gini(y):
    """Gini impurity of a set of labels: 1 - sum_k p_k^2."""
    m = len(y)
    if m == 0:
        return 0.0
    counts = np.bincount(y, minlength=n_classes)
    probs = counts / m
    return 1.0 - np.sum(probs ** 2)


def best_split(X, y):
    """Find the (feature, threshold) minimizing the weighted child Gini."""
    m = len(y)
    if m <= 1:
        return None, None

    best_gini = gini(y)               # only accept a split that reduces impurity
    best_idx, best_thr = None, None

    for feature_index in range(X.shape[1]):
        # Candidate thresholds = midpoints between consecutive unique values.
        values = np.unique(X[:, feature_index])
        if len(values) == 1:
            continue
        thresholds = (values[:-1] + values[1:]) / 2.0

        for thr in thresholds:
            left_mask = X[:, feature_index] <= thr
            y_left, y_right = y[left_mask], y[~left_mask]
            if len(y_left) == 0 or len(y_right) == 0:
                continue
            # Weighted average Gini of the two children.
            w_gini = (len(y_left) * gini(y_left) + len(y_right) * gini(y_right)) / m
            if w_gini < best_gini:
                best_gini = w_gini
                best_idx = feature_index
                best_thr = thr

    return best_idx, best_thr


def build_tree(X, y, depth=0, max_depth=3):
    """Recursively build the tree until max_depth / purity / no valid split."""
    counts = np.bincount(y, minlength=n_classes)
    predicted_class = int(np.argmax(counts))
    node = Node(
        gini=gini(y),
        num_samples=len(y),
        class_counts=counts,
        predicted_class=predicted_class,
    )

    # Stop if at max depth or the node is already pure.
    if depth < max_depth and node.gini > 0.0:
        idx, thr = best_split(X, y)
        if idx is not None:
            left_mask = X[:, idx] <= thr
            node.feature_index = idx
            node.threshold = thr
            node.left = build_tree(X[left_mask], y[left_mask], depth + 1, max_depth)
            node.right = build_tree(X[~left_mask], y[~left_mask], depth + 1, max_depth)
    return node


n_classes = len(class_names)
tree = build_tree(X_train, y_train, depth=0, max_depth=3)


# ====================== Predict & Evaluate ======================
# Traverse the tree per sample down to a leaf and read off the majority class.

def predict_one(node, x):
    while node.left is not None:
        if x[node.feature_index] <= node.threshold:
            node = node.left
        else:
            node = node.right
    return node.predicted_class


def predict(node, X):
    return np.array([predict_one(node, x) for x in X])


y_pred_scratch = predict(tree, X_test)
acc_scratch = accuracy_score(y_test, y_pred_scratch)

print("-" * 60)
print("Decision Tree (from scratch)")
print("-" * 60)
print(f"  Test accuracy: {acc_scratch:.4f}")
print()


# ======================  Visualize the Tree ======================
# Print the tree as an indented list of nodes (indentation encodes depth).

def print_tree(node, depth=0):
    indent = "    " * depth
    if node.left is None:                     # leaf
        print(f"{indent}Leaf: predict '{class_names[node.predicted_class]}' "
              f"(gini={node.gini:.3f}, samples={node.num_samples}, "
              f"counts={node.class_counts.tolist()})")
    else:                                     # internal node
        print(f"{indent}[{feature_names[node.feature_index]} <= {node.threshold:.3f}] "
              f"(gini={node.gini:.3f}, samples={node.num_samples})")
        print(f"{indent}--> True:")
        print_tree(node.left, depth + 1)
        print(f"{indent}--> False:")
        print_tree(node.right, depth + 1)


print("  Tree structure (indented):")
print_tree(tree)
print()
