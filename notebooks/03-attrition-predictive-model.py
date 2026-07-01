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
    
    # Store a copy of the original dataframe to export later with our predictions
    original_df = df.copy()
    
    # Print columns for debugging
    print(f"📌 Found columns in dataset: {df.columns.tolist()}")
    
    # Dynamically find the target column
    target_col = 'Attrition'
    if target_col not in df.columns:
        if 'Flight_Risk' in df.columns:
            target_col = 'Flight_Risk'
        elif 'Left' in df.columns:
            target_col = 'Left'
        elif 'Attrition_Flag' in df.columns:
            target_col = 'Attrition_Flag'
        else:
            raise ValueError("❌ Target column not found! Please check the printed columns above.")
            
    print(f"🎯 Using '{target_col}' as the target variable to predict.")

    # Drop the Employee ID (it doesn't help predict attrition)
    if 'Employee_ID' in df.columns:
        df = df.drop('Employee_ID', axis=1)
    
    # Convert Target string/boolean to 1 and 0 safely
    if df[target_col].dtype == 'object':
        df[target_col] = df[target_col].replace({'Yes': 1, 'No': 0, 'True': 1, 'False': 0})
    elif df[target_col].dtype == bool:
        df[target_col] = df[target_col].astype(int)
        
    df[target_col] = df[target_col].astype('float32')
    
    # Dynamically One-Hot Encode ALL categorical (text) columns
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
    if categorical_cols:
        df = pd.get_dummies(df, columns=categorical_cols, drop_first=True)
    
    # Split features (X) and target (y)
    X_df = df.drop(target_col, axis=1).astype('float32')
    y_df = df[target_col]

    # Convert to PyTorch Tensors and push straight to the GPU (VRAM)
    X = torch.tensor(X_df.values, dtype=torch.float32, device=device)
    y = torch.tensor(y_df.values, dtype=torch.float32, device=device).view(-1, 1)

    # Normalize continuous data mathematically using GPU Tensors
    X_mean = X.mean(dim=0)
    X_std = X.std(dim=0)
    X = (X - X_mean) / (X_std + 1e-7) 

    # Split into 80% Training Data, 20% Testing Data
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    print(f"✅ Training on {len(X_train):,} records | Testing on {len(X_test):,} records")

    # ==========================================
    # 2. NEURAL NETWORK ARCHITECTURE
    # ==========================================
    class AttritionNet(nn.Module):
        def __init__(self, input_size):
            super().__init__()
            self.layer1 = nn.Linear(input_size, 32)
            self.relu1 = nn.ReLU()
            self.layer2 = nn.Linear(32, 16)
            self.relu2 = nn.ReLU()
            self.output = nn.Linear(16, 1)
            self.sigmoid = nn.Sigmoid()

        def forward(self, x):
            x = self.relu1(self.layer1(x))
            x = self.relu2(self.layer2(x))
            x = self.sigmoid(self.output(x))
            return x

    model = AttritionNet(X.shape[1]).to(device)
    criterion = nn.BCELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.01)

    # ==========================================
    # 3. CUDA TRAINING LOOP
    # ==========================================
    print("\n🧠 Commencing Neural Network Training (GPU Accelerated)...")
    epochs = 500
    
    start_time = time.time()
    for epoch in range(epochs):
        predictions = model(X_train)
        loss = criterion(predictions, y_train)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        if (epoch + 1) % 100 == 0:
            print(f"Epoch {epoch+1:3d}/{epochs} | Loss: {loss.item():.4f}")
            
    train_time = time.time() - start_time
    print(f"⚡ Training completed in {train_time:.2f} seconds!")

    # ==========================================
    # 4. MODEL EVALUATION
    # ==========================================
    print("\n🎯 Evaluating Model on unseen Test Data...")
    
    with torch.no_grad():
        test_predictions = model(X_test)
        predicted_classes = (test_predictions > 0.5).float()
        correct_predictions = (predicted_classes == y_test).sum().item()
        accuracy = (correct_predictions / len(y_test)) * 100

    print(f"🏆 Final Model Accuracy: {accuracy:.2f}%\n")

    # ==========================================
    # 5. FEATURE IMPORTANCE (Permutation Method)
    # ==========================================
    print("🔍 Analyzing Key Drivers of Attrition (Permutation Importance)...")
    
    # Turn off gradient calculation for the analysis
    with torch.no_grad():
        feature_names = X_df.columns.tolist()
        importances = {}
        
        for i in range(X_test.shape[1]):
            # Clone test data to avoid modifying the original
            X_test_shuffled = X_test.clone()
            
            # Shuffle only the current column (destroying its relationship with the target)
            shuffle_idx = torch.randperm(X_test.shape[0])
            X_test_shuffled[:, i] = X_test_shuffled[shuffle_idx, i]
            
            # Test the model with this "broken" column
            shuffled_preds = model(X_test_shuffled)
            shuffled_classes = (shuffled_preds > 0.5).float()
            shuffled_acc = (shuffled_classes == y_test).sum().item() / len(y_test) * 100
            
            # The larger the accuracy drop, the more important the feature was
            importance_score = accuracy - shuffled_acc
            importances[feature_names[i]] = importance_score
            
        # Sort and print the top 5 most critical features
        sorted_importances = sorted(importances.items(), key=lambda item: item[1], reverse=True)
        print("\n🔝 Top 5 Drivers of Employee Attrition:")
        for rank, (feature, imp) in enumerate(sorted_importances[:5], 1):
            # Ignore features that actually improved the score when scrambled (noise)
            if imp > 0:
                print(f"  {rank}. {feature:<20} (Impact Score: {imp:.2f})")
        print("\n")

    # ==========================================
    # 6. EXPORT PREDICTIONS FOR POWER BI
    # ==========================================
    print("💾 Generating Flight Risk scores for all employees...")
    
    with torch.no_grad():
        # Ask the trained model to predict the risk for the entire dataset
        all_predictions = model(X).cpu().numpy()
        
    # Append the raw percentage to the original dataframe
    original_df['Predicted_Flight_Risk_%'] = (all_predictions * 100).round(2)
    
    # Save the new dataset
    export_filename = 'scored_hr_dataset.csv'
    original_df.to_csv(export_filename, index=False)
    
    print(f"✅ Success! Predictions saved to '{export_filename}'.")
    print("📈 You can now import this file into Power BI to visualize the Flight Risk for every employee!\n")

if __name__ == "__main__":
    train_attrition_model()