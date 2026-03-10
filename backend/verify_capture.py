import os
import sys
import logging
import asyncio
import numpy as np
from pathlib import Path

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from inference.engine import inference_engine
from inference.realtime_inferrer import RealtimeInferrer
from data.feature_engineer import engineer_flow_features
from config import get_settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("verify_capture")

async def main():
    settings = get_settings()
    
    # Check if models exist
    model_path = settings.MODELS_DIR / "cnn_model.h5"
    if not model_path.exists():
        logger.error("Model not found!")
        return
        
    logger.info("Loading inference engine models...")
    # Since we don't have DB models registered in local test, we inject it directly
    from models.cnn_model import CNNModel
    import joblib
    
    scaler_path = settings.MODELS_DIR / "cnn_scaler.pkl"
    model = CNNModel()
    model.load(model_path)
    
    inference_engine.models["cnn"] = model
    inference_engine.scalers["cnn"] = joblib.load(scaler_path)
    inference_engine._loaded = True
    
    logger.info("Initializing RealtimeInferrer...")
    inferrer = RealtimeInferrer(inference_engine, window_size=5)
    
    logger.info("Simulating incoming packets...")
    # Generate mock packets
    for i in range(15):
        mock_packet = {
            "size": np.random.randint(40, 1500),
            "timestamp": float(i) * 0.1,
            "direction": "fwd" if i % 2 == 0 else "bwd",
            "protocol": "TCP",
            "flags": "SA" if i % 3 == 0 else "A",
            "header_length": 20,
            "window_size": 1024
        }
        
        # In actual pipeline, 100 packets make a flow. We just simulate flow stats directly
        # and push them to the realtime inferrer which buffers by sliding window.
        flow_features = engineer_flow_features([mock_packet])
        
        # Realtime_inferrer expects a dict of numeric features
        # Some values like total_bytes scale up. Let's send the features
        logger.info(f"Adding flow {i+1} to buffer...")
        result = inferrer.add_flow(flow_features)
        
        if result:
            logger.info(f"Real-time prediction result for window {i+1}: {result}")
            
    logger.info("✅ Real-time inference verification completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
