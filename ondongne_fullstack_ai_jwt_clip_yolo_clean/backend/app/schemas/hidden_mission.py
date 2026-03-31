from datetime import datetime
from pydantic import BaseModel

class HiddenMissionCreate(BaseModel):
    week_id: str
    title: str
    description: str
    mission_type: str
    region: str
    bonus_points: int = 0
    predicted_overall_score: float | None = None
    approve_probability: float | None = None
    ai_model_version: str | None = None

class HiddenMissionRead(BaseModel):
    id: int
    week_id: str
    title: str
    description: str
    mission_type: str
    region: str
    bonus_points: int
    predicted_overall_score: float | None = None
    approve_probability: float | None = None
    ai_model_version: str | None = None
    created_at: datetime
    model_config = {"from_attributes": True}

class HiddenMissionPredictRequest(BaseModel):
    week_id: str
    region: str
    title: str
    description: str
    season: str
    region_type: str
    weekly_condition: str
    avg_temp: float
    rainy_days: int
    outdoor_friendly_days: int
    bad_air_days: int
    mission_type: str
    proof_type: str
    is_outdoor: int
    is_group: int
    difficulty: int
    bonus_points: int
