from sqlalchemy.orm import Session
from app.models.point_log import PointLog

def create(db: Session, **kwargs) -> PointLog:
    obj = PointLog(**kwargs)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj
