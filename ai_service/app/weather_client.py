from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Any

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")

print("ENV FILE =", PROJECT_ROOT / ".env")
print("OPENWEATHER_API_KEY =", OPENWEATHER_API_KEY[:6] if OPENWEATHER_API_KEY else "EMPTY")


DISTRICT_COORDS = {
    "강남구": {"lat": 37.5172, "lon": 127.0473},
    "서초구": {"lat": 37.4837, "lon": 127.0324},
    "송파구": {"lat": 37.5145, "lon": 127.1059},
    "마포구": {"lat": 37.5663, "lon": 126.9019},
    "성동구": {"lat": 37.5633, "lon": 127.0369},
    "광진구": {"lat": 37.5384, "lon": 127.0822},
    "노원구": {"lat": 37.6542, "lon": 127.0568},
    "은평구": {"lat": 37.6176, "lon": 126.9227},
    "관악구": {"lat": 37.4784, "lon": 126.9516},
    "강서구": {"lat": 37.5509, "lon": 126.8495},
}


def get_coords_from_district(district_name: str) -> Dict[str, float]:
    coords = DISTRICT_COORDS.get(district_name)
    if not coords:
        raise ValueError(f"지원하지 않는 구입니다: {district_name}")
    return coords


def get_weekly_weather_summary(district_name: str) -> Dict[str, Any]:
    if not OPENWEATHER_API_KEY:
        raise ValueError("OPENWEATHER_API_KEY가 설정되지 않았습니다.")

    coords = get_coords_from_district(district_name)
    lat = coords["lat"]
    lon = coords["lon"]

    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": "kr",
    }

    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

    items = data.get("list", [])
    if not items:
        raise ValueError("날씨 데이터를 가져오지 못했습니다.")

    temps = []
    rainy_days = set()
    outdoor_friendly_days = set()
    bad_air_days = 0

    for item in items[:40]:
        temp = item["main"]["temp"]
        temps.append(temp)

        dt_txt = item["dt_txt"]
        day_key = dt_txt.split(" ")[0]

        weather_main = item["weather"][0]["main"].lower()
        if "rain" in weather_main:
            rainy_days.add(day_key)

        if 8 <= temp <= 26 and "rain" not in weather_main:
            outdoor_friendly_days.add(day_key)

    avg_temp = sum(temps) / len(temps)
    rainy_days_count = len(rainy_days)
    outdoor_days_count = len(outdoor_friendly_days)

    if rainy_days_count >= 3:
        weekly_condition = "rainy"
        weather_summary = "이번 주는 비가 자주 와서 실내 또는 짧은 실외 활동이 적합합니다."
    elif outdoor_days_count >= 3:
        weekly_condition = "outdoor_good"
        weather_summary = "이번 주는 날씨가 좋아 야외 활동형 미션이 적합합니다."
    else:
        weekly_condition = "balanced"
        weather_summary = "이번 주는 실내외를 모두 고려한 균형형 미션이 적합합니다."

    return {
        "avg_temp": round(avg_temp, 2),
        "rainy_days": rainy_days_count,
        "outdoor_friendly_days": outdoor_days_count,
        "bad_air_days": bad_air_days,
        "weekly_condition": weekly_condition,
        "weather_summary": weather_summary,
    }


OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")

# 예시 좌표 (필요한 구 계속 추가 가능)
DISTRICT_COORDS = {
    "강남구": {"lat": 37.5172, "lon": 127.0473},
    "서초구": {"lat": 37.4837, "lon": 127.0324},
    "송파구": {"lat": 37.5145, "lon": 127.1059},
    "마포구": {"lat": 37.5663, "lon": 126.9019},
    "성동구": {"lat": 37.5633, "lon": 127.0369},
    "광진구": {"lat": 37.5384, "lon": 127.0822},
    "노원구": {"lat": 37.6542, "lon": 127.0568},
    "은평구": {"lat": 37.6176, "lon": 126.9227},
    "관악구": {"lat": 37.4784, "lon": 126.9516},
    "강서구": {"lat": 37.5509, "lon": 126.8495},
}


def get_coords_from_district(district_name: str) -> Dict[str, float]:
    coords = DISTRICT_COORDS.get(district_name)
    if not coords:
        raise ValueError(f"지원하지 않는 구입니다: {district_name}")
    return coords


def get_weekly_weather_summary(district_name: str) -> Dict[str, Any]:
    if not OPENWEATHER_API_KEY:
        raise ValueError("OPENWEATHER_API_KEY가 설정되지 않았습니다.")

    coords = get_coords_from_district(district_name)
    lat = coords["lat"]
    lon = coords["lon"]

    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": "kr",
    }

    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

    items = data.get("list", [])
    if not items:
        raise ValueError("날씨 데이터를 가져오지 못했습니다.")

    temps = []
    rainy_days = set()
    outdoor_friendly_days = set()
    bad_air_days = 0  # OpenWeather 기본 forecast에는 대기질이 없으니 일단 0 처리

    for item in items[:40]:  # 약 5일치 3시간 간격
        temp = item["main"]["temp"]
        temps.append(temp)

        dt_txt = item["dt_txt"]
        day_key = dt_txt.split(" ")[0]

        weather_main = item["weather"][0]["main"].lower()
        if "rain" in weather_main:
            rainy_days.add(day_key)

        # 야외활동 적합 단순 규칙
        if 8 <= temp <= 26 and "rain" not in weather_main:
            outdoor_friendly_days.add(day_key)

    avg_temp = sum(temps) / len(temps)
    rainy_days_count = len(rainy_days)
    outdoor_days_count = len(outdoor_friendly_days)

    if rainy_days_count >= 3:
        weekly_condition = "rainy"
        weather_summary = "이번 주는 비가 자주 와서 실내 또는 짧은 실외 활동이 적합합니다."
    elif outdoor_days_count >= 3:
        weekly_condition = "outdoor_good"
        weather_summary = "이번 주는 날씨가 좋아 야외 활동형 미션이 적합합니다."
    else:
        weekly_condition = "balanced"
        weather_summary = "이번 주는 실내외를 모두 고려한 균형형 미션이 적합합니다."

    return {
        "avg_temp": round(avg_temp, 2),
        "rainy_days": rainy_days_count,
        "outdoor_friendly_days": outdoor_days_count,
        "bad_air_days": bad_air_days,
        "weekly_condition": weekly_condition,
        "weather_summary": weather_summary,
    }