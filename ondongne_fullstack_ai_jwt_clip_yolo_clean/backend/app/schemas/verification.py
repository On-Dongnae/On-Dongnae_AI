from datetime import datetime
from pydantic import BaseModel

class VerificationRead(BaseModel):
    id: int
    user_id: int
    mission_type: str
    title: str
    description: str | None = None
    status: str
    ai_confidence: float | None = None
    ai_probabilities: dict | None = None
    ai_raw_result: dict | None = None
    image_urls: list[str] = []
    created_at: datetime
    model_config = {"from_attributes": True}
