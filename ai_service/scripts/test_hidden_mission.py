import joblib
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "models"

approve_model = joblib.load(MODEL_DIR / "hidden_mission_approve_clf.joblib")
score_model = joblib.load(MODEL_DIR / "hidden_mission_score_regressor.joblib")

sample = pd.DataFrame([
    {
        "mission_title": "우중 산책 미션",
        "mission_description": "비 오는 날 우산을 쓰고 10분간 동네를 산책하며 주변 풍경을 기록해보세요.",
        "season": "spring",
        "region_type": "residential",
        "weather_summary": "이번 주는 비가 자주 오고 기온이 선선합니다.",
        "weekly_condition": "rainy",
        "avg_temp": 14.0,
        "rainy_days": 4,
        "outdoor_friendly_days": 2,
        "bad_air_days": 0,
        "mission_type": "walking",
        "is_outdoor": True,
        "is_group": False,
        "difficulty": 2,
        "bonus_points": 200
    }
])

approve_prob = approve_model.predict_proba(sample)[0]
pred_score = score_model.predict(sample)[0]

print("approve probabilities =", approve_prob)
print("predicted score =", round(float(pred_score), 4))