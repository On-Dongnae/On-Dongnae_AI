from sqlalchemy.orm import Session
from app.repositories import verification_repository, point_log_repository
from app.models.user import User

STATUS_POINT_MAP = {"approved": 10, "needs_review": 0, "rejected": 0, "pending": 0}


def create_verification(db: Session, redis_client, payload):
    obj = verification_repository.create(
        db,
        user_id=payload.user_id,
        mission_type=payload.mission_type,
        title=payload.title,
        description=payload.description,
        status=payload.status,
        ai_confidence=payload.ai_confidence,
        ai_probabilities=payload.ai_probabilities,
    )
    redis_client.set(f"verification:status:{obj.id}", obj.status, ex=60 * 60 * 24)

    gained = STATUS_POINT_MAP.get(obj.status, 0)
    if gained > 0:
        user = db.get(User, payload.user_id)
        if user:
            user.total_points += gained
            db.commit()
            db.refresh(user)
            point_log_repository.create(db, user_id=user.id, points=gained, reason=f"verification:{obj.id}")
            redis_client.zincrby("ranking:personal", gained, str(user.id))
            redis_client.zincrby(f"ranking:region:{user.region}", gained, str(user.id))
    return obj


def list_verifications(db: Session):
    return verification_repository.list_all(db)
