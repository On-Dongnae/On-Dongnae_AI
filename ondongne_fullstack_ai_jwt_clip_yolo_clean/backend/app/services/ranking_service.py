from redis import Redis

def get_personal_ranking(redis_client: Redis, top_n: int = 50):
    items = redis_client.zrevrange("ranking:personal", 0, top_n - 1, withscores=True)
    return [{"user_id": int(k), "score": int(v)} for k, v in items]


def get_region_ranking(redis_client: Redis, region: str, top_n: int = 50):
    items = redis_client.zrevrange(f"ranking:region:{region}", 0, top_n - 1, withscores=True)
    return [{"user_id": int(k), "score": int(v)} for k, v in items]
