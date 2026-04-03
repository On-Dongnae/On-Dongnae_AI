import json
from app.hidden_mission_recommender import recommend_hidden_mission

payload = {
    "season": "spring",
    "region_type": "residential",
    "weather_summary": "이번 주는 비가 자주 오고 기온은 선선하며 야외활동 가능한 날은 적습니다.",
    "weekly_condition": "rainy",
    "avg_temp": 14.0,
    "rainy_days": 4,
    "outdoor_friendly_days": 2,
    "bad_air_days": 0
}

result = recommend_hidden_mission(payload)

print("=== TOP RECOMMENDATION ===")
print(json.dumps(result["recommended_mission"], ensure_ascii=False, indent=2))
print("\n=== TOP 5 CANDIDATES ===")
print(json.dumps(result["candidates"][:5], ensure_ascii=False, indent=2))
