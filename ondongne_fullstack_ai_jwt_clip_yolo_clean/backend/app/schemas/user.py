from datetime import datetime
from pydantic import BaseModel, EmailStr

class SignupRequest(BaseModel):
    email: EmailStr
    nickname: str
    region: str
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserRead(BaseModel):
    id: int
    email: EmailStr
    nickname: str
    region: str
    total_points: int
    created_at: datetime

    model_config = {"from_attributes": True}
