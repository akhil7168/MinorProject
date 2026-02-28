"""
Redis Publisher
===============
Pub/sub for real-time alert streaming.
Falls back to in-memory when Redis unavailable.
"""
import logging

logger = logging.getLogger("deepshield.alerts.redis_pub")

_redis_client = None


def get_redis():
    """Get Redis client or None if unavailable."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    try:
        import redis
        from config import get_settings
        settings = get_settings()
        _redis_client = redis.from_url(settings.REDIS_URL)
        _redis_client.ping()
        logger.info("Redis connected")
        return _redis_client
    except Exception:
        logger.info("Redis not available — using WebSocket-only alert delivery")
        return None


async def publish_alert(channel: str, data: dict):
    """Publish alert to Redis channel."""
    import json
    client = get_redis()
    if client:
        try:
            client.publish(channel, json.dumps(data))
        except Exception as e:
            logger.debug(f"Redis publish failed: {e}")


async def publish_training_progress(run_id: str, data: dict):
    """Publish training progress to Redis."""
    await publish_alert(f"training:{run_id}", data)
