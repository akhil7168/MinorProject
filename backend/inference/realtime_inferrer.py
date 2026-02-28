"""
Realtime Inferrer
=================
Streaming inference using sliding window for continuous traffic analysis.
"""
import logging
import numpy as np

logger = logging.getLogger("deepshield.inference.realtime")


class RealtimeInferrer:
    """Sliding window inference for streaming traffic."""

    def __init__(self, engine, window_size: int = 10):
        self.engine = engine
        self.window_size = window_size
        self.buffer = []

    def add_flow(self, features: dict) -> dict | None:
        """
        Add a flow to the buffer.
        Returns prediction when buffer reaches window_size.
        """
        self.buffer.append(features)

        if len(self.buffer) >= self.window_size:
            result = self._process_window()
            self.buffer = self.buffer[1:]  # Slide by 1
            return result
        return None

    def _process_window(self) -> dict:
        """Process current window through models."""
        import asyncio
        feature_keys = list(self.buffer[0].keys())
        X = np.array(
            [[f.get(k, 0) for k in feature_keys] for f in self.buffer],
            dtype=np.float32
        ).reshape(1, self.window_size, -1)

        # Use the last flow's features for single-sample prediction
        last_features = self.buffer[-1]
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run, self.engine.infer_single(last_features)
                    )
                    return future.result(timeout=5)
            else:
                return loop.run_until_complete(self.engine.infer_single(last_features))
        except Exception as e:
            logger.error(f"Realtime inference failed: {e}")
            return {"error": str(e)}

    def reset(self):
        """Clear the buffer."""
        self.buffer = []
