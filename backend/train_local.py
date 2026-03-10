import os
import sys
import logging
from pathlib import Path
import time
import numpy as np

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.loader import load_cicids2017
from data.preprocessor import full_pipeline
from models.cnn_model import CNNModel
from config import get_settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("train_local")

def main():
    settings = get_settings()
    
    # Path to the actual CICIDS-2017 dataset
    data_dir = Path("data/Dataset/MachineLearningCSV/MachineLearningCVE")
    if not data_dir.exists():
        logger.error(f"Data directory not found: {data_dir.absolute()}")
        return

    logger.info("Loading CICIDS-2017 dataset...")
    # NOTE: It might take a minute since there are 8 large CSV files
    X, y, feature_names = load_cicids2017(data_dir)
    
    logger.info("Preprocessing data...")
    scaler_path = settings.MODELS_DIR / "cnn_scaler.pkl"
    # We use a subset or fast mode if needed? Just full pipeline.
    data = full_pipeline(
        X, y, feature_names,
        mode="multiclass",
        balance_strategy="class_weight",
        scaler_path=scaler_path
    )
    
    X_train = data["X_train"]
    X_val = data["X_val"]
    X_test = data["X_test"]
    y_train = data["y_train"]
    y_val = data["y_val"]
    y_test = data["y_test"]
    num_classes = data["num_classes"]
    num_features = data["num_features"]

    logger.info(f"Building model (features={num_features}, classes={num_classes})...")
    model = CNNModel()
    model.build(
        input_shape=(num_features,),
        num_classes=num_classes,
        dropout_rate=0.3
    )
    
    logger.info("Training model...")
    # Fast training configuration
    config = {
        "epochs": 5, 
        "batch_size": 1024,
        "learning_rate": 0.001,
        "loss_fn": "focal",
        "early_stopping_patience": 2,
        "class_weights": data["class_weights"]
    }
    
    start_time = time.time()
    history = model.train(
        X_train, y_train, X_val, y_val,
        config=config
    )
    logger.info(f"Training took {time.time() - start_time:.2f} seconds.")
    
    logger.info("Evaluating on test set...")
    metrics = model.evaluate(X_test, y_test)
    logger.info(f"Test Accuracy: {metrics.get('accuracy')}")
    logger.info(f"Test F1 Macro: {metrics.get('f1_macro')}")
    
    logger.info("Saving model...")
    model_path = settings.MODELS_DIR / "cnn_model.h5"
    model.save(model_path)
    
    logger.info("Exporting to TFLite...")
    try:
        tflite_path = settings.MODELS_DIR / "cnn_model.tflite"
        model.export_tflite(tflite_path)
    except Exception as e:
        logger.error(f"TFLite export failed: {e}")

    logger.info("✅ Training pipeline completed successfully!")

if __name__ == "__main__":
    main()
