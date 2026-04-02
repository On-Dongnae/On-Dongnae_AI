from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from typing import Any

import requests

BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8080")
BACKEND_API_TOKEN = os.getenv("BACKEND_API_TOKEN", "")

def _headers() -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if BACKEND_API_TOKEN:
        headers["Authorization"] = f"Bearer {BACKEND_API_TOKEN}"
    return headers

@dataclass
class PendingVerificationItem:
    id: int
    userMissionId: int
    status: str
    content: str
    imageUrls: list[str]
    verifiedAt: str | None = None

def fetch_pending_verifications() -> list[PendingVerificationItem]:
    response = requests.get(
        f"{BACKEND_BASE_URL}/api/admin/verifications",
        params={"status": "PENDING"},
        headers=_headers(),
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    data = payload.get("data", [])
    return [PendingVerificationItem(**item) for item in data]

def patch_ai_result(verification_id: int, status: str, confidence: float, reason: str) -> dict[str, Any]:
    response = requests.patch(
        f"{BACKEND_BASE_URL}/api/admin/verifications/{verification_id}/ai-result",
        json={"status": status, "confidence": confidence, "reason": reason},
        headers=_headers(),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()

def post_hidden_mission(name: str, description: str, point_amount: int, start_date: str, end_date: str) -> dict[str, Any]:
    response = requests.post(
        f"{BACKEND_BASE_URL}/api/admin/missions",
        json={
            "type": "AI_HIDDEN",
            "name": name,
            "description": description,
            "pointAmount": point_amount,
            "startDate": start_date,
            "endDate": end_date,
        },
        headers=_headers(),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()

def download_image_urls(image_urls: list[str]) -> list[str]:
    paths: list[str] = []
    for url in image_urls[:3]:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        suffix = os.path.splitext(url)[1] or ".jpg"
        fd, path = tempfile.mkstemp(suffix=suffix)
        with os.fdopen(fd, "wb") as f:
            f.write(response.content)
        paths.append(path)
    return paths
