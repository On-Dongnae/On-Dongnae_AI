from sqlalchemy.orm import Session
from app.repositories import user_repository
from app.schemas.user import UserCreate

def create_user(db: Session, payload: UserCreate):
    return user_repository.create(db, email=payload.email, nickname=payload.nickname, region=payload.region)

def list_users(db: Session):
    return user_repository.list_all(db)
