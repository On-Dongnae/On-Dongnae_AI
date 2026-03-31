import redis
from app.core.config import settings

_redis = redis.Redis(host=settings.redis_host, port=settings.redis_port, db=settings.redis_db, decode_responses=True)

def get_redis():
    return _redis
