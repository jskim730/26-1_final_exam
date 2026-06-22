import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
import torchvision.transforms as transforms
from torch.utils.data import DataLoader, Subset
import random
import numpy as np

# Control randomness
seed = 123
random.seed(seed)
np.random.seed(seed)
torch.manual_seed(seed)
torch.cuda.manual_seed_all(seed)
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False

# Generator for DataLoader shuffling (keeps batch order reproducible)
loader_generator = torch.Generator()
loader_generator.manual_seed(seed)

# Device configuration (GPU if available, otherwise CPU)
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")

# Hyperparameters
learning_rate = 0.001
batch_size = 64
num_epochs = 30          # assignment cap is 30 epochs

# ==================== Data Preparation ====================

# ToTensor() converts images to tensors and scales pixel values from [0, 255] to [0, 1].
# Train and eval transforms are separated so that augmentation only applies to training.
#
# Train transform adds standard CIFAR-10 augmentation to reduce overfitting on the
# small 8,000-image training subset:
#   - RandomCrop with 4px reflection padding  -> translation invariance
#   - RandomHorizontalFlip                     -> left/right invariance
# Both transforms normalize with the CIFAR-10 channel mean/std so inputs are
# zero-centered (this is a per-pixel transform, not a change to the data split).
CIFAR10_MEAN = (0.4914, 0.4822, 0.4465)
CIFAR10_STD = (0.2470, 0.2435, 0.2616)

transform_train = transforms.Compose([
    transforms.RandomCrop(32, padding=4, padding_mode='reflect'),
    transforms.RandomHorizontalFlip(),
    transforms.ToTensor(),
    transforms.Normalize(CIFAR10_MEAN, CIFAR10_STD),
])
transform_eval = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize(CIFAR10_MEAN, CIFAR10_STD),
])

# Download and load the training data
train_dataset_cifar_full = torchvision.datasets.CIFAR10(root='./data',
                                                 train=True,
                                                 transform=transform_train,
                                                 download=True)
# Validation set comes from the training data but uses the eval transform (no augmentation)
val_dataset_cifar_full = torchvision.datasets.CIFAR10(root='./data',
                                                 train=True,
                                                 transform=transform_eval,
                                                 download=True)
# Download and load the test data
test_dataset_cifar_full = torchvision.datasets.CIFAR10(root='./data',
                                                train=False,
                                                transform=transform_eval)

# Take 10,000 samples from training set, then split into train (8,000) / val (2,000)
all_train_indices = torch.randperm(len(train_dataset_cifar_full))[:10000]
train_subset_indices_cifar = all_train_indices[:8000]
val_subset_indices_cifar = all_train_indices[8000:10000]

# Take 2,000 samples from test set
test_subset_indices_cifar = torch.randperm(len(test_dataset_cifar_full))[:2000]

train_dataset_cifar = Subset(train_dataset_cifar_full, train_subset_indices_cifar)
val_dataset_cifar = Subset(val_dataset_cifar_full, val_subset_indices_cifar)
test_dataset_cifar = Subset(test_dataset_cifar_full, test_subset_indices_cifar)

# Data loaders
train_loader = DataLoader(dataset=train_dataset_cifar,
                                batch_size=batch_size,
                                shuffle=True,
                                generator=loader_generator)
val_loader = DataLoader(dataset=val_dataset_cifar,
                              batch_size=batch_size,
                              shuffle=False)
test_loader = DataLoader(dataset=test_dataset_cifar,
                               batch_size=batch_size,
                               shuffle=False)

# ==================== Model Definition ====================

class CNN(nn.Module):
    """A compact VGG-style CNN with three conv blocks.

    Each block is [Conv-BN-ReLU] x2 followed by 2x2 max-pooling, doubling the
    channel width (32 -> 64 -> 128) while halving the spatial size
    (32 -> 16 -> 8 -> 4). BatchNorm stabilizes and speeds up training, which is
    the main reason this reaches >65% within 30 epochs on the small subset;
    dropout in the classifier head curbs overfitting.
    """
    def __init__(self, num_classes):
        super(CNN, self).__init__()

        def conv_block(in_ch, out_ch):
            return nn.Sequential(
                nn.Conv2d(in_ch, out_ch, kernel_size=3, padding=1),
                nn.BatchNorm2d(out_ch),
                nn.ReLU(inplace=True),
                nn.Conv2d(out_ch, out_ch, kernel_size=3, padding=1),
                nn.BatchNorm2d(out_ch),
                nn.ReLU(inplace=True),
                nn.MaxPool2d(kernel_size=2, stride=2),
            )

        # Input: Bx3x32x32 (Batch x Channels x Height x Width)
        self.block1 = conv_block(3, 32)     # -> Bx32x16x16
        self.block2 = conv_block(32, 64)    # -> Bx64x8x8
        self.block3 = conv_block(64, 128)   # -> Bx128x4x4

        self.classifier = nn.Sequential(
            nn.Flatten(),                   # 128*4*4 = 2048
            nn.Dropout(p=0.3),
            nn.Linear(128 * 4 * 4, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(p=0.3),
            nn.Linear(256, num_classes),
        )

    def forward(self, x):
        out = self.block1(x)
        out = self.block2(out)
        out = self.block3(out)
        out = self.classifier(out)
        return out

# Create model instance
model = CNN(num_classes=10).to(device)

# Loss and optimizer
# weight_decay adds L2 regularization; a cosine schedule anneals the learning
# rate to 0 over the 30 epochs, which improves final test accuracy.
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=learning_rate, weight_decay=5e-4)
scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=num_epochs)

# ==================== Training & Validation ====================

total_step = len(train_loader)
best_val_acc = 0.0  # Track best validation accuracy
best_epoch = 0      # Epoch at which best val acc was achieved
best_model_state = None

for epoch in range(num_epochs):
    # ---------- Training ----------
    model.train()  # Training mode
    sum_train_loss = 0.0
    for i, (images, labels) in enumerate(train_loader):
        images, labels = images.to(device), labels.to(device)

        # Forward pass
        outputs = model(images)
        loss = criterion(outputs, labels)
        sum_train_loss += loss.item()

        # Backward and optimize
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    avg_train_loss = sum_train_loss / len(train_loader)

    # ---------- Validation ----------
    model.eval()  # Evaluation mode
    sum_val_loss = 0.0
    val_correct = 0
    val_total = 0
    with torch.no_grad():
        for images, labels in val_loader:
            images, labels = images.to(device), labels.to(device)

            outputs = model(images)
            loss = criterion(outputs, labels)
            sum_val_loss += loss.item()

            predicted = outputs.argmax(dim=1)
            val_total += images.size(0)
            val_correct += (predicted == labels).sum().item()

    avg_val_loss = sum_val_loss / len(val_loader)
    val_accuracy = 100 * val_correct / val_total

    # Anneal the learning rate once per epoch.
    scheduler.step()

    # Save best model based on validation accuracy
    if val_accuracy > best_val_acc:
        best_val_acc = val_accuracy
        best_epoch = epoch + 1
        best_model_state = {k: v.clone() for k, v in model.state_dict().items()}

    print(f"Epoch [{epoch+1}/{num_epochs}] "
          f"Train Loss: {avg_train_loss:.4f} | "
          f"Val Loss: {avg_val_loss:.4f} | "
          f"Val Acc: {val_accuracy:.2f}%")

# ==================== Testing the model ====================

# Load the weights from the epoch with the best validation accuracy
print(f"\nBest validation accuracy: {best_val_acc:.2f}% (from epoch {best_epoch})")
print("Loading these weights for testing...")
model.load_state_dict(best_model_state)

model.eval() # Testing mode
with torch.no_grad():
    correct = 0
    total = 0
    for images, labels in test_loader:
        images, labels = images.to(device), labels.to(device)

        # Get predicted label
        outputs = model(images)
        predicted = outputs.argmax(dim=1)

        total += images.size(0)
        correct += (predicted == labels).sum().item()

    print(f'\nAccuracy of the model on the {len(test_dataset_cifar)} test images: {100 * correct / total:.2f} %')
