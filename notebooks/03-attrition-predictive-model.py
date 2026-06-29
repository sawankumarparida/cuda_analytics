import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
import time

def train_attrition_model():
    print("🚀 Initializing CUDA Deep Learning Environment...")
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"🖥️  Using Compute Device: {device}\n")

    # ==========================================
    # 1. DATA PREPARATION (Pandas -> PyTorch)
    # ==========================================
    print("📊 Loading and Preprocessing Data...")
    df = pd.read_csv('enterprise_hr_dataset.csv')
    
    # Drop the Employee ID (it doesn't help predict attrition)
    df = df.drop('Employee_ID', axis=1)
    
    # Convert 'Yes'/'No' string to 1 and 0
    df['Attrition'] = df['Attrition'].map({'Yes': 1, 'No': 0})
    
    # One-Hot Encode the categorical 'Department' column
    df = pd.get_dummies(df, columns=['Department'], drop_first=True)
    
    # Split features (X) and target (y)
    # Force boolean columns (from get_dummies) to float32 before tensor conversion
    X_df = df.drop('Attrition', axis=1).astype('float32')
    y_df = df['Attrition'].astype('float32')

    # Convert to PyTorch Tensors and push straight to the GPU (VRAM)
    X = torch.tensor(X_df.values, dtype=torch.float32, device=device)
    y = torch.tensor(y_df.values, dtype=torch.float32, device=device).view(-1, 1)

    # Normalize continuous data mathematically using GPU Tensors
    # (Subtract mean and divide by standard deviation so large salaries don't overpower small ratings)
    X_mean = X.mean(dim=0)
    X_std = X.std(dim=0)
    X = (X - X_mean) / (X_std + 1e-7) # Add tiny number to prevent division by zero

    # Split into 80% Training Data, 20% Testing Data
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    print(f"✅ Training on {len(X_train):,} records | Testing on {len(X_test):,} records")

    # ==========================================
    # 2. NEURAL NETWORK ARCHITECTURE
    # ==========================================
    # We define a Multi-Layer Perceptron (MLP)
    class AttritionNet(nn.Module):
        def __init__(self, input_size):
            super().__init__()
            # Hidden Layer 1: Takes input features, outputs to 32 neurons
            self.layer1 = nn.Linear(input_size, 32)
            self.relu1 = nn.ReLU() # Activation function
            
            # Hidden Layer 2: 32 neurons down to 16 neurons
            self.layer2 = nn.Linear(32, 16)
            self.relu2 = nn.ReLU()
            
            # Output Layer: 16 neurons down to 1 prediction (0 to 1)
            self.output = nn.Linear(16, 1)
            self.sigmoid = nn.Sigmoid() # Squeezes final answer between 0% and 100%

        def forward(self, x):
            x = self.relu1(self.layer1(x))
            x = self.relu2(self.layer2(x))
            x = self.sigmoid(self.output(x))
            return x

    # Instantiate the model and push it to the GPU
    input_features = X.shape[1]
    model = AttritionNet(input_features).to(device)

    # Loss Function: Binary Cross Entropy (Standard for Yes/No classification)
    criterion = nn.BCELoss()
    # Optimizer: Adam (Automatically adjusts learning rate)
    optimizer = optim.Adam(model.parameters(), lr=0.01)

    # ==========================================
    # 3. CUDA TRAINING LOOP
    # ==========================================
    print("\n🧠 Commencing Neural Network Training (GPU Accelerated)...")
    epochs = 500
    
    start_time = time.time()
    for epoch in range(epochs):
        # 1. Forward Pass: The model guesses who will quit
        predictions = model(X_train)
        
        # 2. Calculate Loss: How wrong were the guesses?
        loss = criterion(predictions, y_train)
        
        # 3. Backward Pass: Backpropagation (Updating weights using GPU calculus)
        optimizer.zero_grad() # Clear old math
        loss.backward()       # Calculate new math (gradients)
        optimizer.step()      # Update the neural network parameters
        
        # Print progress every 100 epochs
        if (epoch + 1) % 100 == 0:
            print(f"Epoch {epoch+1:3d}/{epochs} | Loss: {loss.item():.4f}")
            
    train_time = time.time() - start_time
    print(f"⚡ Training completed in {train_time:.2f} seconds!")

    # ==========================================
    # 4. MODEL EVALUATION
    # ==========================================
    print("\n🎯 Evaluating Model on unseen Test Data...")
    
    # Turn off gradient tracking to save memory while testing
    with torch.no_grad():
        test_predictions = model(X_test)
        # If the model predicts > 0.5 (50%), we count it as a "Yes" they will quit
        predicted_classes = (test_predictions > 0.5).float()
        
        # Calculate how many it got exactly right
        correct_predictions = (predicted_classes == y_test).sum().item()
        accuracy = (correct_predictions / len(y_test)) * 100

    print(f"🏆 Final Model Accuracy: {accuracy:.2f}%\n")

if __name__ == "__main__":
    train_attrition_model()