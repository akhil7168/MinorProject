import os
import sys
import logging
from pathlib import Path
import numpy as np
import joblib

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.cnn_model import CNNModel
from config import get_settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("verify_model")

def main():
    settings = get_settings()
    
    model_path = settings.MODELS_DIR / "cnn_model.h5"
    scaler_path = settings.MODELS_DIR / "cnn_scaler.pkl"
    tflite_path = settings.MODELS_DIR / "cnn_model.tflite"
    
    if not model_path.exists() or not scaler_path.exists():
        logger.error("Model or Scaler not found in models_saved!")
        return
        
    logger.info("Loading Scaler...")
    scaler = joblib.load(scaler_path)
    
    logger.info("Loading Keras Model...")
    model = CNNModel()
    model.load(model_path)
    
    logger.info(model.get_model_summary())
    
    # Create some dummy features matching the number of features in CICIDS-2017 (assumed ~60-70 after cleaning)
    # The scaler expects exactly the same number of features that were used during training
    num_features = scaler.n_features_in_
    dummy_data = np.random.rand(5, num_features).astype(np.float32)
    
    logger.info("Scaling dummy data...")
    dummy_scaled = scaler.transform(dummy_data)
    
    logger.info("Running inference on Keras model...")
    predictions = model.predict(dummy_scaled)
    predicted_classes = np.argmax(predictions, axis=1)
    
    for i, (pred, cls) in enumerate(zip(predictions, predicted_classes)):
        logger.info(f"Sample {i}: Predicted Class {cls}, Probabilities: {pred}")

    # Verify TFLite model 
    if tflite_path.exists():
        logger.info("Testing TFLite Model...")
        import tensorflow as tf
        interpreter = tf.lite.Interpreter(model_path=str(tflite_path))
        interpreter.allocate_tensors()
        
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        
        # Test first sample
        sample = dummy_scaled[0:1]
        interpreter.set_tensor(input_details[0]['index'], sample)
        interpreter.invoke()
        tflite_pred = interpreter.get_tensor(output_details[0]['index'])
        logger.info(f"TFLite Output for Sample 0: {tflite_pred}, Class: {np.argmax(tflite_pred)}")
    else:
        logger.warning("TFLite model not found.")

    logger.info("✅ Verification completed successfully!")

if __name__ == "__main__":
    main()
