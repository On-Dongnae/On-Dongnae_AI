from pathlib import Path
import hashlib
import json
import httpx
from redis import Redis
from app.core.config import settings


def _cache_key(prefix: str, payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return f"{prefix}:{hashlib.sha256(raw.encode()).hexdigest()}"


def predict_hidden_mission(redis_client: Redis, payload: dict):
    key = _cache_key("ai:hidden", payload)
    cached = redis_client.get(key)
    if cached:
        return json.loads(cached)
    with httpx.Client(timeout=60.0) as client:
        res = client.post(f"{settings.ai_service_url}/predict/hidden-mission", json=payload)
        res.raise_for_status()
        data = res.json()
    redis_client.setex(key, 3600, json.dumps(data, ensure_ascii=False))
    return data


def predict_verification_from_images(redis_client: Redis, mission_type: str, description_text: str, image_paths: list[str]):
    key = _cache_key("ai:verification", {"mission_type": mission_type, "description_text": description_text, "image_paths": image_paths})
    cached = redis_client.get(key)
    if cached:
        return json.loads(cached)

    files = []
    handles = []
    try:
        for path in image_paths:
            fh = open(Path(path), "rb")
            handles.append(fh)
            files.append(("files", (Path(path).name, fh, "image/jpeg")))
        with httpx.Client(timeout=180.0) as client:
            res = client.post(
                f"{settings.ai_service_url}/predict/verification-from-images",
                data={"mission_type": mission_type, "description_text": description_text},
                files=files,
            )
            res.raise_for_status()
            data = res.json()
        redis_client.setex(key, 1800, json.dumps(data, ensure_ascii=False))
        return data
    finally:
        for fh in handles:
            fh.close()
