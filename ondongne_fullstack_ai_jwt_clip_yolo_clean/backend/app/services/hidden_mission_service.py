import json
from sqlalchemy.orm import Session
from app.repositories import hidden_mission_repository
from app.schemas.hidden_mission import HiddenMissionCreate

CACHE_TTL_SECONDS = 60 * 60 * 24 * 7

def _cache_key(week_id: str) -> str:
    return f"hidden_mission:{week_id}"


def create_hidden_mission(db: Session, redis_client, payload: HiddenMissionCreate):
    obj = hidden_mission_repository.create(
        db,
        week_id=payload.week_id,
        title=payload.title,
        description=payload.description,
        mission_type=payload.mission_type,
        region=payload.region,
        bonus_points=payload.bonus_points,
        predicted_overall_score=payload.predicted_overall_score,
        approve_probability=payload.approve_probability,
        ai_model_version=payload.ai_model_version,
    )
    redis_client.set(_cache_key(payload.week_id), json.dumps({
        "id": obj.id,
        "week_id": obj.week_id,
        "title": obj.title,
        "description": obj.description,
        "mission_type": obj.mission_type,
        "region": obj.region,
        "bonus_points": obj.bonus_points,
        "predicted_overall_score": obj.predicted_overall_score,
        "approve_probability": obj.approve_probability,
        "ai_model_version": obj.ai_model_version,
        "created_at": obj.created_at.isoformat(),
    }), ex=CACHE_TTL_SECONDS)
    return obj


def get_hidden_mission_by_week(db: Session, redis_client, week_id: str):
    cached = redis_client.get(_cache_key(week_id))
    if cached:
        return json.loads(cached)
    obj = hidden_mission_repository.get_by_week_id(db, week_id)
    if not obj:
        return None
    redis_client.set(_cache_key(week_id), json.dumps({
        "id": obj.id,
        "week_id": obj.week_id,
        "title": obj.title,
        "description": obj.description,
        "mission_type": obj.mission_type,
        "region": obj.region,
        "bonus_points": obj.bonus_points,
        "predicted_overall_score": obj.predicted_overall_score,
        "approve_probability": obj.approve_probability,
        "ai_model_version": obj.ai_model_version,
        "created_at": obj.created_at.isoformat(),
    }), ex=CACHE_TTL_SECONDS)
    return obj
