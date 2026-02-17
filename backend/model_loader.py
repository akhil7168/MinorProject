import tensorflow as tf
import joblib
import os
import numpy as np
class ModelLoader:
    _instance = None
    model = None
    scaler = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelLoader, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self.model is None:
            self.model = None
        if self.scaler is None:
            self.scaler = None
    
    def load_model(self, model_path: str, scaler_path: str):
        if self.model is None:
            print(f"Loading model from {model_path}...")
            # Check if files exist
            if not os.path.exists(model_path):
                 print(f"Model file not found at {model_path}. Please train the model first.")
                 raise FileNotFoundError(f"Model not found at {model_path}")
            
            try:
                self.model = tf.keras.models.load_model(model_path)
                print("Model loaded.")
            except Exception as e:
                print(f"Error loading model: {e}")
                raise e
            
        if self.scaler is None:
            print(f"Loading scaler from {scaler_path}...")
            if not os.path.exists(scaler_path):
                print(f"Scaler file not found at {scaler_path}")
                raise FileNotFoundError(f"Scaler not found at {scaler_path}")
                
            try:
                self.scaler = joblib.load(scaler_path)
                print("Scaler loaded.")
            except Exception as e:
                 print(f"Error loading scaler: {e}")
                 raise e

    def predict(self, features: list):
        if self.model is None or self.scaler is None:
            raise RuntimeError("Model or Scaler not loaded. Train the model first.")
            
        # Preprocess features
        features_array = np.array(features).reshape(1, -1)
        
        # Scale
        scaled_features = self.scaler.transform(features_array)
        
        # Reshape for CNN/LSTM (1, features, 1)
        # Note: Model expects (sample, time_steps, features) for LSTM or (sample, features, channels) for CNN
        # Our model was Conv1D with input_shape=(features, 1)
        model_input = scaled_features.reshape((1, scaled_features.shape[1], 1))
        
        # Predict
        prediction = self.model.predict(model_input)
        return prediction[0][0]

model_loader = ModelLoader()
