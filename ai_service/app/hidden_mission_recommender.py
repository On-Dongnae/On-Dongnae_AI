from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd

try:
    import joblib
except Exception:
    joblib = None


BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "models"

from datetime import datetime


def get_current_season() -> str:
    month = datetime.now().month
    if month in [3, 4, 5]:
        return "spring"
    if month in [6, 7, 8]:
        return "summer"
    if month in [9, 10, 11]:
        return "autumn"
    return "winter"

@dataclass
class HiddenMissionContext:
    season: str
    region_type: str
    weather_summary: str
    weekly_condition: str
    avg_temp: float
    rainy_days: int
    outdoor_friendly_days: int
    bad_air_days: int


def _safe_load(path: Path):
    if not path.exists() or joblib is None:
        return None
    try:
        return joblib.load(path)
    except Exception:
        return None


APPROVE_MODEL = _safe_load(MODEL_DIR / "hidden_mission_approve_clf.joblib")
SCORE_MODEL = _safe_load(MODEL_DIR / "hidden_mission_score_regressor.joblib")


def _condition_tags(ctx: HiddenMissionContext) -> Dict[str, bool]:
    return {
        "rainy": ctx.rainy_days >= 3 or "rain" in ctx.weekly_condition.lower(),
        "outdoor_good": ctx.outdoor_friendly_days >= 4 and ctx.bad_air_days <= 1 and ctx.rainy_days <= 1,
        "indoor_recommended": ctx.bad_air_days >= 3 or ctx.rainy_days >= 4,
        "hot": ctx.avg_temp >= 27,
        "cold": ctx.avg_temp <= 5,
        "park_area": ctx.region_type.lower() in {"park", "park_area", "green", "campus"},
        "residential": ctx.region_type.lower() in {"residential", "apartment", "housing"},
    }


def generate_candidates(ctx: HiddenMissionContext) -> List[Dict[str, Any]]:
    tags = _condition_tags(ctx)
    cands: List[Dict[str, Any]] = []

    def add(title, desc, mission_type, is_outdoor, is_group, difficulty, bonus):
        cands.append({
            "mission_title": title,
            "mission_description": desc,
            "season": ctx.season,
            "region_type": ctx.region_type,
            "weather_summary": ctx.weather_summary,
            "weekly_condition": ctx.weekly_condition,
            "avg_temp": ctx.avg_temp,
            "rainy_days": ctx.rainy_days,
            "outdoor_friendly_days": ctx.outdoor_friendly_days,
            "bad_air_days": ctx.bad_air_days,
            "mission_type": mission_type,
            "is_outdoor": bool(is_outdoor),
            "is_group": bool(is_group),
            "difficulty": int(difficulty),
            "bonus_points": int(bonus),
        })

    add(
        "분리배출 실천 미션",
        "오늘 집이나 학교에서 재활용품을 분리배출하고 정리한 뒤 인증하세요.",
        "recycling", False, False, 1, 150
    )
    add(
        "대기전력 차단 미션",
        "사용하지 않는 전자기기의 전원을 끄거나 멀티탭을 정리해 대기전력을 줄이고 인증하세요.",
        "energy_saving", False, False, 1, 140
    )

    if tags["rainy"]:
        add(
            "우산 산책 미션",
            "비 오는 날 우산을 쓰고 10분 이상 산책하거나 이동하면서 안전하게 외출한 뒤 인증하세요.",
            "walking", True, False, 2, 220
        )
        add(
            "실내 정리 미션",
            "비 오는 날 집 안 공용공간이나 책상 위를 정리하고 전후 상태를 인증하세요.",
            "indoor_care", False, False, 1, 180
        )

    if tags["outdoor_good"]:
        add(
            "플로깅 산책 미션",
            "동네를 15분 이상 걸으며 쓰레기 5개 이상을 줍고 인증하세요.",
            "group_cleanup", True, False, 2, 260
        )
        add(
            "이웃 인사 미션",
            "동네 이웃이나 상점 직원에게 먼저 인사하고 배려 행동을 1회 이상 실천한 뒤 인증하세요.",
            "kindness", True, False, 1, 170
        )
        add(
            "계단 이용 미션",
            "가까운 층 이동 시 엘리베이터 대신 계단을 이용하고 인증하세요.",
            "healthy_action", True, False, 1, 150
        )

    if tags["indoor_recommended"]:
        add(
            "실내 공기 관리 미션",
            "실내 환기 가능한 시간에 환기하고, 공기정리 또는 청소 행동을 1회 이상 실천한 뒤 인증하세요.",
            "indoor_care", False, False, 1, 180
        )
        add(
            "에너지 절약 미션",
            "조명 끄기, 대기전력 차단, 절전모드 설정 중 2가지 이상 실천하고 인증하세요.",
            "energy_saving", False, False, 1, 170
        )

    if tags["park_area"]:
        add(
            "공원 정리 미션",
            "공원이나 산책로 주변에서 쓰레기를 3개 이상 줍고 인증하세요.",
            "group_cleanup", True, False, 2, 220
        )
        add(
            "공원 걷기 미션",
            "공원이나 산책로를 15분 이상 걷고 인증하세요.",
            "walking", True, False, 1, 170
        )

    if tags["residential"]:
        add(
            "공용공간 정리 미션",
            "집 주변 공용공간이나 현관 주변을 정리하고 인증하세요.",
            "residential_kindness", False, False, 1, 160
        )
        add(
            "층간 배려 실천 미션",
            "조용한 시간대 지키기, 엘리베이터 양보, 문 잡아주기 중 하나를 실천하고 인증하세요.",
            "residential_kindness", False, False, 1, 140
        )

    if tags["hot"]:
        add(
            "텀블러 사용 미션",
            "외출 시 일회용컵 대신 텀블러나 개인 물병을 사용하고 인증하세요.",
            "eco_action", False, False, 1, 180
        )
        add(
            "시원한 물 나눔 미션",
            "주변 사람에게 물이나 음료를 건네는 배려 행동을 실천하고 인증하세요.",
            "kindness", False, False, 2, 200
        )

    if tags["cold"]:
        add(
            "따뜻한 배려 미션",
            "주변 사람에게 문을 잡아주거나 자리 양보 등 작은 배려 행동을 실천하고 인증하세요.",
            "kindness", False, False, 1, 180
        )
        add(
            "실내 절전 미션",
            "난방 중 불필요한 전기기기 사용을 줄이고 인증하세요.",
            "energy_saving", False, False, 1, 160
        )

    seen = set()
    uniq = []
    for c in cands:
        if c["mission_title"] in seen:
            continue
        seen.add(c["mission_title"])
        uniq.append(c)

    return uniq


def _heuristic_score(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in df.iterrows():
        score = 0.4
        mission_type = str(row["mission_type"]).lower()

        if row["rainy_days"] >= 3 and mission_type in {"indoor_care", "energy_saving", "recycling"}:
            score += 0.18

        if row["outdoor_friendly_days"] >= 4 and bool(row["is_outdoor"]):
            score += 0.20

        if row["bad_air_days"] >= 3 and bool(row["is_outdoor"]):
            score -= 0.20

        if row["region_type"] == "residential" and mission_type in {"recycling", "residential_kindness", "energy_saving"}:
            score += 0.08

        if row["region_type"] in {"park_area", "park", "green", "campus"} and mission_type in {"walking", "group_cleanup"}:
            score += 0.10

        if row["difficulty"] <= 2:
            score += 0.05

        if row["bonus_points"] >= 180:
            score += 0.04

        score = max(0.01, min(0.99, score))
        rows.append({
            "approve_prob": round(score, 4),
            "predicted_score": round(score * 5.0, 4),
        })

    return pd.DataFrame(rows)


def rank_candidates(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    df = pd.DataFrame(candidates)

    if APPROVE_MODEL is not None and SCORE_MODEL is not None:
        try:
            approve_probs = APPROVE_MODEL.predict_proba(df)
            score_preds = SCORE_MODEL.predict(df)

            if approve_probs.shape[1] >= 2:
                approve_col = approve_probs[:, 1]
            else:
                approve_col = approve_probs[:, 0]

            df["approve_prob"] = [round(float(x), 4) for x in approve_col]
            df["predicted_score"] = [round(float(x), 4) for x in score_preds]
        except Exception:
            aux = _heuristic_score(df)
            df["approve_prob"] = aux["approve_prob"]
            df["predicted_score"] = aux["predicted_score"]
    else:
        aux = _heuristic_score(df)
        df["approve_prob"] = aux["approve_prob"]
        df["predicted_score"] = aux["predicted_score"]

    df["final_rank_score"] = df["approve_prob"] * 0.6 + (df["predicted_score"] / 5.0) * 0.4
    df = df.sort_values(by="final_rank_score", ascending=False).reset_index(drop=True)
    return df.to_dict(orient="records")


def recommend_hidden_mission(payload: Dict[str, Any]) -> Dict[str, Any]:
    ctx = HiddenMissionContext(
        season=payload["season"],
        region_type=payload["region_type"],
        weather_summary=payload["weather_summary"],
        weekly_condition=payload["weekly_condition"],
        avg_temp=float(payload["avg_temp"]),
        rainy_days=int(payload["rainy_days"]),
        outdoor_friendly_days=int(payload["outdoor_friendly_days"]),
        bad_air_days=int(payload["bad_air_days"]),
    )
    candidates = generate_candidates(ctx)
    ranked = rank_candidates(candidates)
    top = ranked[0] if ranked else None
    return {
        "input_context": payload,
        "recommended_mission": top,
        "candidate_count": len(ranked),
        "candidates": ranked,
    }


def recommend_one_hidden_mission(
    weather_summary: str,
    weekly_condition: str,
    avg_temp: float,
    rainy_days: int,
    outdoor_friendly_days: int,
    bad_air_days: int,
) -> Dict[str, Any]:
    season = get_current_season()
    ctx = HiddenMissionContext(
        season=season,
        region_type="city",
        weather_summary=weather_summary,
        weekly_condition=weekly_condition,
        avg_temp=avg_temp,
        rainy_days=rainy_days,
        outdoor_friendly_days=outdoor_friendly_days,
        bad_air_days=bad_air_days,
    )

    candidates = generate_candidates(ctx)
    ranked = rank_candidates(candidates)
    top = ranked[0] if ranked else None

    if top:
        return {
            "hidden_mission_name": top.get("mission_title", "히든 미션"),
            "description": top.get("mission_description", "상세 설명이 없습니다."),
            "predicted_reward_score": int(top.get("predicted_score", 300)),
            "approve_prob": round(float(top.get("approve_prob", 0.0)), 4)
        }
    return {
        "hidden_mission_name": "기본 히든 미션",
        "description": "다양한 활동을 통해 포인트를 얻어보세요.",
        "predicted_reward_score": 300,
        "approve_prob": 0.0
    }