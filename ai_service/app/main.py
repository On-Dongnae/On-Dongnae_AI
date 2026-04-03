from __future__ import annotations

from functools import lru_cache
from io import BytesIO
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import JSONResponse
from PIL import Image

app = FastAPI(title="OnDongne AI Service", version="1.0.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@lru_cache
def get_torch_module():
    import torch
    return torch


@lru_cache
def get_clip_components():
    torch = get_torch_module()
    from transformers import CLIPModel, CLIPProcessor

    model_name = "openai/clip-vit-base-patch32"
    model = CLIPModel.from_pretrained(model_name)
    processor = CLIPProcessor.from_pretrained(model_name)
    model.eval()
    model.to("cpu")

    return {
        "torch": torch,
        "model": model,
        "processor": processor,
        "device": "cpu",
    }


@lru_cache
def get_yolo_model():
    from ultralytics import YOLO
    return YOLO("yolov8n.pt")


@lru_cache
def get_verification_model():
    model_path = Path("models/verification_final_decision_clf.joblib")
    if not model_path.exists():
        raise FileNotFoundError(f"verification model not found: {model_path}")
    return joblib.load(model_path)


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


def build_clip_prompts(mission_description: str, content: str) -> list[str]:
    prompts = []

    if mission_description.strip():
        prompts.append(mission_description.strip())

    if content.strip():
        prompts.append(content.strip())

    prompts.extend([
        "사용자가 실제로 미션을 수행한 인증 사진",
        "지역 선행 활동을 인증하는 장면",
        "미션과 관련된 객체나 행동이 포함된 이미지",
        "미션과 무관한 일반 사진",
    ])

    return prompts


def compute_clip_match_score(image: Image.Image, mission_description: str, content: str) -> dict[str, Any]:
    components = get_clip_components()
    torch = components["torch"]
    model = components["model"]
    processor = components["processor"]
    device = components["device"]

    prompts = build_clip_prompts(mission_description, content)

    inputs = processor(
        text=prompts,
        images=image,
        return_tensors="pt",
        padding=True,
    )
    inputs = {k: v.to(device) for k, v in inputs.items()}

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
    detected_classes = []
    person_count = 0

    object_presence = {
        "trash_bag_detected": 0,
        "recyclable_item_detected": 0,
        "recycle_bin_detected": 0,
        "litter_picker_detected": 0,
    }

    if result.boxes is not None:
        classes = result.boxes.cls.tolist()
        for cls_id in classes:
            cls_name = names[int(cls_id)]
            detected_classes.append(cls_name)

            if cls_name == "person":
                person_count += 1

            if cls_name in ["backpack", "handbag", "suitcase", "bag"]:
                object_presence["trash_bag_detected"] = 1
            if cls_name in ["bottle", "cup"]:
                object_presence["recyclable_item_detected"] = 1
            if cls_name in ["trash can"]:
                object_presence["recycle_bin_detected"] = 1
            if cls_name in ["umbrella", "baseball bat", "sports ball"]:
                object_presence["litter_picker_detected"] = 1

    return {
        "person_count": person_count,
        "detected_classes": detected_classes,
        "object_presence": object_presence,
    }


def infer_predicted_activity_class(
    mission_type: str,
    clip_match_score: float,
    detected_classes: list[str],
    person_count: int,
) -> tuple[str, float]:
    """
    학습 모델에 넣을 predicted_activity_class / confidence 추정
    """
    if mission_type == "group_cleanup":
        if person_count >= 2 or "trash can" in detected_classes:
            return "group_cleanup", max(0.7, clip_match_score)
        return "invalid", min(0.5, clip_match_score)

    if mission_type == "recycling":
        if "bottle" in detected_classes or "trash can" in detected_classes:
            return "recycling", max(0.7, clip_match_score)
        return "invalid", min(0.5, clip_match_score)

    if mission_type == "jogging_group":
        if person_count >= 2:
            return "jogging_group", max(0.7, clip_match_score)
        return "invalid", min(0.5, clip_match_score)

    if mission_type == "kindness_activity":
        return "kindness_activity", max(0.6, clip_match_score)

    if mission_type == "energy_saving":
        return "energy_saving", max(0.6, clip_match_score)

    return "invalid", min(0.5, clip_match_score)


def build_feature_row(
    mission_type: str,
    content: str,
    clip_match_score: float,
    predicted_activity_class: str,
    activity_class_confidence: float,
    person_count_pred: int,
    object_presence: dict[str, int],
    image_quality_score_value: float,
    mission_match_flag: int,
) -> pd.DataFrame:
    row = {
        "mission_type": mission_type,
        "description_text": content,
        "clip_match_score": clip_match_score,
        "predicted_activity_class": predicted_activity_class,
        "activity_class_confidence": activity_class_confidence,
        "person_count_pred": person_count_pred,
        "trash_bag_detected": object_presence["trash_bag_detected"],
        "recyclable_item_detected": object_presence["recyclable_item_detected"],
        "recycle_bin_detected": object_presence["recycle_bin_detected"],
        "litter_picker_detected": object_presence["litter_picker_detected"],
        "image_quality_score": image_quality_score_value,
        "text_length": len(content.strip()),
        "mission_match_flag": mission_match_flag,
    }
    return pd.DataFrame([row])


def rule_based_fallback(
    clip_match_score: float,
    person_count_pred: int,
    object_presence: dict[str, int],
    content: str,
) -> tuple[str, float]:
    score = 0.0
    score += clip_match_score * 0.55

    if person_count_pred >= 1:
        score += 0.15
    if any(v == 1 for v in object_presence.values()):
        score += 0.15
    if len(content.strip()) >= 10:
        score += 0.10

    score = round(min(score, 0.99), 4)

    if score >= 0.75:
        return "APPROVED", score
    return "REJECTED", score


def predict_final_status(feature_df: pd.DataFrame) -> tuple[str, float]:
    try:
        model = get_verification_model()

        pred = model.predict(feature_df)[0]

        confidence = 0.0
        if hasattr(model, "predict_proba"):
            probs = model.predict_proba(feature_df)[0]
            confidence = float(max(probs))
        else:
            confidence = 0.8

        label = str(pred).upper()

        if label == "APPROVED":
            return "APPROVED", round(confidence, 4)
        if label == "NEEDS_REVIEW":
            return "REJECTED", round(confidence, 4)
        if label == "REJECTED":
            return "REJECTED", round(confidence, 4)

        return "REJECTED", round(confidence, 4)

    except Exception:
        row = feature_df.iloc[0].to_dict()
        return rule_based_fallback(
            clip_match_score=float(row["clip_match_score"]),
            person_count_pred=int(row["person_count_pred"]),
            object_presence={
                "trash_bag_detected": int(row["trash_bag_detected"]),
                "recyclable_item_detected": int(row["recyclable_item_detected"]),
                "recycle_bin_detected": int(row["recycle_bin_detected"]),
                "litter_picker_detected": int(row["litter_picker_detected"]),
            },
            content=str(row["description_text"]),
        )


@app.post("/predict/verification-from-images")
async def predict_verification_from_images(
    mission_type: str = Form(...),
    mission_description: str = Form(""),
    content: str = Form(""),
    files: list[UploadFile] = File(...),
):
    try:
        clip_scores = []
        quality_scores = []
        all_detected_classes = []
        max_person_count = 0

        merged_object_presence = {
            "trash_bag_detected": 0,
            "recyclable_item_detected": 0,
            "recycle_bin_detected": 0,
            "litter_picker_detected": 0,
        }

        best_prompt = ""

        for file in files:
            image_bytes = await file.read()
            image = safe_open_image(image_bytes)

            q_score = image_quality_score(image)
            quality_scores.append(q_score)

            clip_result = compute_clip_match_score(image, mission_description, content)
            clip_scores.append(clip_result["clip_match_score"])
            if not best_prompt:
                best_prompt = clip_result["best_matching_prompt"]

            yolo_result = run_yolo_detection(image)
            all_detected_classes.extend(yolo_result["detected_classes"])
            max_person_count = max(max_person_count, yolo_result["person_count"])

            for k, v in yolo_result["object_presence"].items():
                if v == 1:
                    merged_object_presence[k] = 1

        avg_clip_score = round(sum(clip_scores) / len(clip_scores), 4) if clip_scores else 0.0
        avg_quality_score = round(sum(quality_scores) / len(quality_scores), 4) if quality_scores else 0.0

        predicted_activity_class, activity_class_confidence = infer_predicted_activity_class(
            mission_type=mission_type,
            clip_match_score=avg_clip_score,
            detected_classes=all_detected_classes,
            person_count=max_person_count,
        )

        mission_match_flag = 1 if avg_clip_score >= 0.5 else 0

        feature_df = build_feature_row(
            mission_type=mission_type,
            content=content,
            clip_match_score=avg_clip_score,
            predicted_activity_class=predicted_activity_class,
            activity_class_confidence=activity_class_confidence,
            person_count_pred=max_person_count,
            object_presence=merged_object_presence,
            image_quality_score_value=avg_quality_score,
            mission_match_flag=mission_match_flag,
        )

        recommended_status, confidence_score = predict_final_status(feature_df)

        return JSONResponse(
            content={
                "mission_type": mission_type,
                "mission_description": mission_description,
                "content": content,
                "clip_match_score": avg_clip_score,
                "best_matching_prompt": best_prompt,
                "person_count": max_person_count,
                "detected_classes": all_detected_classes,
                "object_presence": merged_object_presence,
                "image_quality_score": avg_quality_score,
                "predicted_activity_class": predicted_activity_class,
                "activity_class_confidence": round(activity_class_confidence, 4),
                "recommended_status": recommended_status,
                "confidence_score": confidence_score,
                "is_verified": recommended_status == "APPROVED",
            }
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": "verification_prediction_failed",
                "detail": str(e),
            },
        )
