import numpy as np
import os
import joblib
from data_loader import DataLoader
from model import build_model
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping

# Configuration
# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data")
MODEL_SAVE_PATH = os.path.join(BASE_DIR, "saved_model")
BATCH_SIZE = 64
EPOCHS = 20

def train():
    # 1. Load Data
    print("Loading Data...")
    loader = DataLoader(data_path=DATA_PATH)
    try:
        # Load all data
        df = loader.load_data(sample_size=None) 
        X, y = loader.preprocess(df)
        
        # Reshape for CNN/LSTM: (samples, features, 1)
        X = X.reshape((X.shape[0], X.shape[1], 1))
        
        # Split data
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        print(f"Training Data Shape: {X_train.shape}")
        print(f"Test Data Shape: {X_test.shape}")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return
    except Exception as e:
        print(f"An unexpected error occurred during data loading: {e}")
        return

    # 2. Build Model
    input_shape = (X_train.shape[1], 1)
    model = build_model(input_shape)
    
    # 3. Train Model
    if not os.path.exists(MODEL_SAVE_PATH):
        os.makedirs(MODEL_SAVE_PATH)
        
    callbacks = [
        ModelCheckpoint(os.path.join(MODEL_SAVE_PATH, 'best_model.h5'), save_best_only=True, monitor='val_loss'),
        EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
    ]
    
    print("Starting Training...")
    history = model.fit(
        X_train, y_train,
        validation_split=0.1,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        callbacks=callbacks
    )
    
    # 4. Evaluate
    loss, accuracy = model.evaluate(X_test, y_test)
    print(f"Test Accuracy: {accuracy*100:.2f}%")
    
    # 5. Save Scaler for Inference
    joblib.dump(loader.scaler, os.path.join(MODEL_SAVE_PATH, 'scaler.pkl'))
    print("Scaler saved.")

if __name__ == "__main__":
    train()
