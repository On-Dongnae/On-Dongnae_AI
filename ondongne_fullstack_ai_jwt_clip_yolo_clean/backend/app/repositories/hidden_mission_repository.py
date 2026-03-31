from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.hidden_mission import HiddenMission

def create(db: Session, **kwargs) -> HiddenMission:
    obj = HiddenMission(**kwargs)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def get_by_week_id(db: Session, week_id: str) -> HiddenMission | None:
    return db.scalar(select(HiddenMission).where(HiddenMission.week_id == week_id))
