from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.user import User

def create(db: Session, **kwargs) -> User:
    obj = User(**kwargs)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def list_all(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.id.desc())))
