from __future__ import annotations

import datetime as dt
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
AI_ROOT = SCRIPT_DIR.parent
sys.path.append(str(AI_ROOT))

from app.backend_client import post_hidden_mission

from datetime import date

from app.backend_client import create_hidden_mission


def generate_hidden_mission():
    today = date.today().isoformat()

    mission = {
        "name": "오늘의 AI 히든 미션",
        "description": "주변 환경에 맞는 작은 선행을 실천하고 인증해보세요.",
        "point_amount": 300,
        "start_date": today,
        "end_date": today,
    }
    return mission


def main():
    mission = generate_hidden_mission()

    result = create_hidden_mission(
        name=mission["name"],
        description=mission["description"],
        point_amount=mission["point_amount"],
        start_date=mission["start_date"],
        end_date=mission["end_date"],
    )

    print("[OK] hidden mission created")
    print(result)


if __name__ == "__main__":
    main()


def build_hidden_mission() -> dict:
    today = dt.date.today().isoformat()
    return {
        "name": "우중 산책 미션",
        "description": "비 오는 날, 우산과 함께 빗소리를 들으며 10분간 산책하고 인증하세요!",
        "point_amount": 300,
        "start_date": today,
        "end_date": today,
    }


def main() -> None:
    mission = build_hidden_mission()
    response = post_hidden_mission(
        name=mission["name"],
        description=mission["description"],
        point_amount=mission["point_amount"],
        start_date=mission["start_date"],
        end_date=mission["end_date"],
    )
    print(response)


if __name__ == "__main__":
    main()
