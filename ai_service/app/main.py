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
    return Image.open(BytesIO(file_bytes)).convert('RGB')

def image_quality_score(image: Image.Image) -> float:
    w,h = image.size
    area = w*h
    if area >= 1280*720: return 0.95
    if area >= 640*480: return 0.8
    if area >= 320*240: return 0.6
    return 0.3

def build_clip_prompts(mission_type: str) -> list[str]:
    prompt_map = {
        'group_cleanup': ['여러 사람이 야외에서 쓰레기를 줍는 장면','동네에서 단체로 플로깅하는 장면','쓰레기봉투를 들고 정리 활동을 하는 사람들'],
        'recycling': ['재활용품을 분리수거하는 장면','분리수거함 앞에서 재활용품을 정리하는 장면','플라스틱이나 캔을 분리 배출하는 장면'],
        'jogging_group': ['여러 사람이 함께 조깅하는 장면','야외에서 단체로 달리기 하는 사람들','운동복을 입고 함께 달리는 장면'],
        'kindness_activity': ['사람이 누군가를 돕는 장면','이웃에게 물건을 전달하는 장면','배려와 도움을 주는 활동 장면'],
        'energy_saving': ['실내에서 전기 절약을 실천하는 장면','불을 끄거나 멀티탭을 정리하는 장면','에너지 절약을 위해 전원을 차단하는 장면'],
    }
    return prompt_map.get(mission_type,['지역 선행 활동을 인증하는 장면','사람이 좋은 행동을 실천하는 장면'])

def compute_clip_match_score(image: Image.Image, mission_type: str) -> dict[str, Any]:
    c = get_clip_components(); torch=c['torch']; model=c['model']; processor=c['processor']
    prompts = build_clip_prompts(mission_type)
    inputs = processor(text=prompts, images=image, return_tensors='pt', padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
        probs = outputs.logits_per_image.softmax(dim=1).cpu().numpy()[0]
    idx = int(probs.argmax())
    return {'clip_match_score': float(probs[idx]), 'best_matching_prompt': prompts[idx]}

def run_yolo_detection(image: Image.Image) -> dict[str, Any]:
    model = get_yolo_model(); results = model(image, verbose=False); result = results[0]; names = result.names
    detected_classes=[]; person_count=0
    object_presence={'trash_bag':0,'recyclable_item':0,'recycle_bin':0,'litter_picker':0}
    if result.boxes is not None:
        for cls_id in result.boxes.cls.tolist():
            cls_name = names[int(cls_id)]; detected_classes.append(cls_name)
            if cls_name=='person': person_count += 1
            if cls_name in ['backpack','handbag','suitcase','bag']: object_presence['trash_bag']=1
            if cls_name in ['bottle','cup']: object_presence['recyclable_item']=1
            if cls_name in ['trash can']: object_presence['recycle_bin']=1
            if cls_name in ['sports ball','baseball bat','umbrella']: object_presence['litter_picker']=1
    return {'person_count': person_count, 'detected_classes': detected_classes, 'object_presence': object_presence}

@app.post('/predict/hidden-mission')
def predict_hidden_mission(payload: HiddenMissionRequest):
    models = get_hidden_models()
    row = pd.DataFrame([payload.model_dump()])
    row['combined_text'] = row['mission_title'] + ' ' + row['mission_description'] + ' ' + row['weather_summary']
    X = models['preprocessor'].transform(row)
    approve = float(models['approve_clf'].predict_proba(X)[0][1])
    overall = float(models['score_reg'].predict(X)[0])
    return {'approve_probability': round(approve,4), 'predicted_overall_score': round(overall,4)}

@app.post('/predict/verification-from-images')
async def predict_verification_from_images(mission_type: str = Form(...), description_text: str = Form(''), files: list[UploadFile] = File(...)):
    try:
        all_detected=[]; max_person_count=0
        merged={'trash_bag':0,'recyclable_item':0,'recycle_bin':0,'litter_picker':0}
        clip_scores=[]; best_prompts=[]; quality_scores=[]
        for file in files:
            content = await file.read(); image = safe_open_image(content)
            quality_scores.append(image_quality_score(image))
            clip_result = compute_clip_match_score(image, mission_type)
            clip_scores.append(clip_result['clip_match_score']); best_prompts.append(clip_result['best_matching_prompt'])
            yolo = run_yolo_detection(image)
            max_person_count=max(max_person_count,yolo['person_count']); all_detected.extend(yolo['detected_classes'])
            for k,v in yolo['object_presence'].items():
                if v == 1: merged[k]=1
        avg_clip = sum(clip_scores)/len(clip_scores) if clip_scores else 0.0
        avg_quality = sum(quality_scores)/len(quality_scores) if quality_scores else 0.0
        df = pd.DataFrame([{
            'mission_type': mission_type,
            'description_text': description_text,
            'clip_match_score': avg_clip,
            'predicted_activity_class': mission_type,
            'activity_class_confidence': avg_clip,
            'person_count_pred': max_person_count,
            'trash_bag_detected': merged['trash_bag'],
            'recyclable_item_detected': merged['recyclable_item'],
            'recycle_bin_detected': merged['recycle_bin'],
            'litter_picker_detected': merged['litter_picker'],
            'image_quality_score': avg_quality,
            'text_length': len(description_text.strip()),
            'mission_match_flag': 1 if avg_clip >= 0.3 else 0,
        }])
        clf = get_final_decision_model()
        pred = clf.predict(df)[0]
        probs = clf.predict_proba(df)[0]
        labels = list(clf.classes_)
        return JSONResponse(content={
            'mission_type': mission_type,
            'clip_match_score': round(avg_clip,4),
            'best_matching_prompt': best_prompts[0] if best_prompts else '',
            'person_count': max_person_count,
            'detected_classes': all_detected,
            'object_presence': merged,
            'image_quality_score': round(avg_quality,4),
            'text_length': len(description_text.strip()),
            'recommended_status': pred,
            'confidence_score': round(float(max(probs)),4),
            'class_probabilities': {labels[i]: round(float(probs[i]),4) for i in range(len(labels))}
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={'error':'prediction_failed','detail':str(e)})
