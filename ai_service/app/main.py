
from __future__ import annotations
from functools import lru_cache
from io import BytesIO
from typing import Any
import joblib, os
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from PIL import Image
import pandas as pd

app = FastAPI(title="OnDongne AI Service", version="1.0.0")
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")

class HiddenMissionRequest(BaseModel):
    season: str
    region_type: str
    weather_summary: str
    weekly_condition: str
    avg_temp: float
    rainy_days: int
    outdoor_friendly_days: int
    bad_air_days: int
    mission_title: str
    mission_description: str
    mission_type: str
    is_outdoor: bool
    is_group: bool
    difficulty: int
    bonus_points: int

@app.get('/health')
def health():
    return {'status':'ok'}

@lru_cache
def get_hidden_models():
    return {
        'preprocessor': joblib.load(os.path.join(MODELS_DIR,'hidden_mission_preprocessor.joblib')),
        'approve_clf': joblib.load(os.path.join(MODELS_DIR,'hidden_mission_approve_clf.joblib')),
        'score_reg': joblib.load(os.path.join(MODELS_DIR,'hidden_mission_score_regressor.joblib')),
    }

@lru_cache
def get_final_decision_model():
    return joblib.load(os.path.join(MODELS_DIR,'verification_final_decision_clf.joblib'))

@lru_cache
def get_torch_module():
    import torch
    return torch

@lru_cache
def get_clip_components():
    torch = get_torch_module()
    from transformers import CLIPModel, CLIPProcessor
    model_name = 'openai/clip-vit-base-patch32'
    model = CLIPModel.from_pretrained(model_name)
    processor = CLIPProcessor.from_pretrained(model_name)
    model.eval().to('cpu')
    return {'torch': torch, 'model': model, 'processor': processor}

@lru_cache
def get_yolo_model():
    from ultralytics import YOLO
    return YOLO('yolov8n.pt')

def safe_open_image(file_bytes: bytes) -> Image.Image:
    return Image.open(BytesIO(file_bytes)).convert("RGB")

def image_quality_score(image: Image.Image) -> float:
    width, height = image.size
    area = width * height
    if area >= 1280 * 720:
        return 0.95
    if area >= 640 * 480:
        return 0.8
    if area >= 320 * 240:
        return 0.6
    return 0.3

def build_clip_prompts(mission_type: str, mission_description: str = "") -> list[str]:
    mission_description = mission_description.strip()
    prompts = []
    if mission_description:
        prompts.append(mission_description)
    prompt_map = {
        "group_cleanup": [
            "여러 사람이 야외에서 쓰레기를 줍는 장면",
            "동네에서 단체로 플로깅하는 장면",
            "쓰레기봉투를 들고 정리 활동을 하는 사람들",
        ],
        "recycling": [
            "재활용품을 분리수거하는 장면",
            "분리수거함 앞에서 재활용품을 정리하는 장면",
            "플라스틱이나 캔을 분리 배출하는 장면",
        ],
        "jogging_group": [
            "여러 사람이 함께 조깅하는 장면",
            "야외에서 단체로 달리기 하는 사람들",
            "운동복을 입고 함께 달리는 장면",
        ],
        "kindness_activity": [
            "사람이 누군가를 돕는 장면",
            "이웃에게 물건을 전달하는 장면",
            "배려와 도움을 주는 활동 장면",
        ],
        "energy_saving": [
            "실내에서 전기 절약을 실천하는 장면",
            "불을 끄거나 멀티탭을 정리하는 장면",
            "에너지 절약을 위해 전원을 차단하는 장면",
        ],
    }
    prompts.extend(prompt_map.get(mission_type, [
        "지역 선행 활동을 인증하는 장면", "사람이 좋은 행동을 실천하는 장면"
    ]))
    # dedupe preserve order
    out = []
    for p in prompts:
        if p and p not in out:
            out.append(p)
    return out

def compute_clip_match_score(image: Image.Image, mission_type: str, mission_description: str = "") -> dict[str, Any]:
    components = get_clip_components()
    torch = components["torch"]
    model = components["model"]
    processor = components["processor"]

    prompts = build_clip_prompts(mission_type, mission_description)

    inputs = processor(text=prompts, images=image, return_tensors="pt", padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
        logits_per_image = outputs.logits_per_image
        probs = logits_per_image.softmax(dim=1).cpu().numpy()[0]

    best_idx = int(probs.argmax())
    best_score = float(probs[best_idx])
    best_prompt = prompts[best_idx]

    return {
        "clip_match_score": round(best_score, 4),
        "best_matching_prompt": best_prompt,
    }

def run_yolo_detection(image: Image.Image) -> dict[str, Any]:
    model = get_yolo_model()
    results = model(image, verbose=False)
    result = results[0]
    names = result.names
    detected_classes: list[str] = []
    person_count = 0

    object_presence = {
        "trash_bag": 0,
        "recyclable_item": 0,
        "recycle_bin": 0,
        "litter_picker": 0,
    }

    if result.boxes is not None:
        classes = result.boxes.cls.tolist()
        for cls_id in classes:
            cls_name = names[int(cls_id)]
            detected_classes.append(cls_name)
            if cls_name == "person":
                person_count += 1
            if cls_name in ["backpack", "handbag", "suitcase", "bag"]:
                object_presence["trash_bag"] = 1
            if cls_name in ["bottle", "cup"]:
                object_presence["recyclable_item"] = 1
            if cls_name in ["trash can"]:
                object_presence["recycle_bin"] = 1
            if cls_name in ["sports ball", "baseball bat", "umbrella"]:
                object_presence["litter_picker"] = 1

    return {
        "person_count": person_count,
        "detected_classes": detected_classes,
        "object_presence": object_presence,
    }

def rule_based_final_decision(mission_type: str, clip_match_score: float, person_count: int,
                              object_presence: dict[str, int], quality_score: float,
                              description_text: str, mission_description: str = "") -> dict[str, Any]:
    score = 0.0
    text_length = len((description_text or "").strip())
    mission_match_flag = 1 if mission_description and any(tok in (description_text or "") for tok in mission_description.split()[:3]) else 0

    score += clip_match_score * 0.45
    score += quality_score * 0.15
    if text_length >= 10:
        score += 0.10
    if mission_match_flag:
        score += 0.05

    if mission_type == "group_cleanup":
        if person_count >= 2:
            score += 0.15
        if object_presence.get("trash_bag", 0) == 1 or object_presence.get("recycle_bin", 0) == 1:
            score += 0.15
    elif mission_type == "recycling":
        if object_presence.get("recyclable_item", 0) == 1 or object_presence.get("recycle_bin", 0) == 1:
            score += 0.2
    elif mission_type == "jogging_group":
        if person_count >= 2:
            score += 0.2
    elif mission_type == "kindness_activity":
        if text_length >= 20:
            score += 0.1
    elif mission_type == "energy_saving":
        if text_length >= 15:
            score += 0.1

    score = round(min(score, 0.99), 4)
    if score >= 0.75:
        label = "APPROVED"
    elif score >= 0.5:
        label = "REJECTED"
    else:
        label = "REJECTED"

    reason = ""
    if label == "REJECTED":
        reason = f"이미지 또는 설명이 미션과 충분히 일치하지 않습니다. bestPrompt={mission_description or mission_type}"

    return {"final_label": label, "final_confidence": score, "reason": reason}

def analyze_images(images: list[Image.Image], mission_type: str, description_text: str = "", mission_description: str = "") -> dict[str, Any]:
    all_detected_classes: list[str] = []
    max_person_count = 0
    merged_object_presence = {
        "trash_bag": 0,
        "recyclable_item": 0,
        "recycle_bin": 0,
        "litter_picker": 0,
    }

    clip_scores: list[float] = []
    best_prompts: list[str] = []
    quality_scores: list[float] = []

    for image in images:
        quality = image_quality_score(image)
        quality_scores.append(quality)

        clip_result = compute_clip_match_score(image, mission_type, mission_description)
        clip_scores.append(clip_result["clip_match_score"])
        best_prompts.append(clip_result["best_matching_prompt"])

        yolo_result = run_yolo_detection(image)
        max_person_count = max(max_person_count, yolo_result["person_count"])
        all_detected_classes.extend(yolo_result["detected_classes"])

        for key, value in yolo_result["object_presence"].items():
            if value == 1:
                merged_object_presence[key] = 1

    avg_clip_score = round(sum(clip_scores) / len(clip_scores), 4) if clip_scores else 0.0
    avg_quality_score = round(sum(quality_scores) / len(quality_scores), 4) if quality_scores else 0.0

    decision = rule_based_final_decision(
        mission_type=mission_type,
        clip_match_score=avg_clip_score,
        person_count=max_person_count,
        object_presence=merged_object_presence,
        quality_score=avg_quality_score,
        description_text=description_text,
        mission_description=mission_description,
    )

    return {
        "mission_type": mission_type,
        "clip_match_score": avg_clip_score,
        "best_matching_prompt": best_prompts[0] if best_prompts else "",
        "person_count": max_person_count,
        "detected_classes": all_detected_classes,
        "object_presence": merged_object_presence,
        "image_quality_score": avg_quality_score,
        "text_length": len((description_text or "").strip()),
        "recommended_status": decision["final_label"],
        "confidence_score": decision["final_confidence"],
        "reason": decision["reason"],
    }

def analyze_verification_paths(mission_type: str, description_text: str, file_paths: list[str], mission_description: str = "") -> dict[str, Any]:
    images = []
    for path in file_paths:
        with open(path, "rb") as f:
            images.append(safe_open_image(f.read()))
    return analyze_images(images, mission_type, description_text, mission_description)

@app.post('/predict/hidden-mission')
def predict_hidden_mission(req: HiddenMissionRequest):
    models = get_hidden_models()
    text = f"{req.mission_title} {req.mission_description} {req.weather_summary}"
    df = pd.DataFrame([{
        "text": text,
        "season": req.season,
        "region_type": req.region_type,
        "weekly_condition": req.weekly_condition,
        "avg_temp": req.avg_temp,
        "rainy_days": req.rainy_days,
        "outdoor_friendly_days": req.outdoor_friendly_days,
        "bad_air_days": req.bad_air_days,
        "mission_type": req.mission_type,
        "is_outdoor": int(req.is_outdoor),
        "is_group": int(req.is_group),
        "difficulty": req.difficulty,
        "bonus_points": req.bonus_points,
    }])
    X = models['preprocessor'].transform(df)
    approve_prob = float(models['approve_clf'].predict_proba(X)[0][1])
    predicted_score = float(models['score_reg'].predict(X)[0])
    return {"approve_probability": round(approve_prob,4), "predicted_overall_score": round(predicted_score,4)}

@app.post("/predict/verification-from-images")
async def predict_verification_from_images(
    mission_type: str = Form(...),
    description_text: str = Form(""),
    mission_description: str = Form(""),
    files: list[UploadFile] = File(...),
):
    try:
        images = []
        for file in files:
            content = await file.read()
            images.append(safe_open_image(content))
        result = analyze_images(images, mission_type, description_text, mission_description)
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error":"prediction_failed","detail":str(e)})
