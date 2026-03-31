from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.verification import ActivityVerification

def create(db: Session, **kwargs) -> ActivityVerification:
    obj = ActivityVerification(**kwargs)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def list_all(db: Session) -> list[ActivityVerification]:
    return list(db.scalars(select(ActivityVerification).order_by(ActivityVerification.id.desc())))
