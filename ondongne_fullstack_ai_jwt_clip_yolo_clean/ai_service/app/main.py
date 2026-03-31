from io import BytesIO
from pathlib import Path
import joblib
import pandas as pd
from PIL import Image
from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel

BASE = Path(__file__).resolve().parents[1]
HM_MODEL_DIR = BASE / 'models' / 'hidden_mission'
VER_MODEL_DIR = BASE / 'models' / 'verification'

app = FastAPI(title='OnDongne AI Models', version='0.3.0')

hidden_approve_clf = None
hidden_prep = None
hidden_reg = None
verification_clf = None
clip_processor = None
clip_model = None
yolo_model = None
_torch = None

MISSION_PROMPTS = {
    'group_cleanup': [
        'a group of people cleaning a neighborhood outdoors',
        'people picking up trash together outside',
    ],
    'recycling': [
        'people sorting recyclables near recycling bins',
        'recyclable items placed for recycling',
    ],
    'jogging_group': [
        'a group of people jogging outdoors',
        'several people running together outside',
    ],
    'kindness_activity': [
        'a person helping a neighbor',
        'people doing a small act of kindness',
    ],
}

class HiddenMissionRequest(BaseModel):
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

class VerificationRequest(BaseModel):
    mission_type: str
    description_text: str
    clip_match_score: float
    predicted_activity_class: str
    activity_class_confidence: float
    person_count_pred: int
    trash_bag_detected: int
    recyclable_item_detected: int
    recycle_bin_detected: int
    litter_picker_detected: int
    image_quality_score: float
    text_length: int
    mission_match_flag: int

@app.on_event('startup')
def startup_event():
    global hidden_approve_clf, hidden_prep, hidden_reg, verification_clf, clip_processor, clip_model, yolo_model, _torch
    hidden_approve_clf = joblib.load(HM_MODEL_DIR / 'hidden_mission_approve_clf.joblib')
    hidden_prep = joblib.load(HM_MODEL_DIR / 'hidden_mission_preprocessor.joblib')
    hidden_reg = joblib.load(HM_MODEL_DIR / 'hidden_mission_score_regressor.joblib')
    verification_clf = joblib.load(VER_MODEL_DIR / 'verification_final_decision_clf.joblib')
    import torch
    from transformers import CLIPProcessor, CLIPModel
    from ultralytics import YOLO
    _torch = torch
    clip_processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32')
    clip_model = CLIPModel.from_pretrained('openai/clip-vit-base-patch32')
    clip_model.eval()
    yolo_model = YOLO('yolov8n.pt')

@app.get('/health')
def health():
    return {'status': 'ok'}

@app.post('/predict/hidden-mission')
def predict_hidden(req: HiddenMissionRequest):
    row = pd.DataFrame([{
        'mission_title': req.title,
        'mission_description': req.description,
        'weather_summary': f"{req.weekly_condition} / rainy_days={req.rainy_days} / outdoor_days={req.outdoor_friendly_days}",
        'text': f"{req.title} {req.description} {req.weekly_condition}",
        'season': req.season,
        'region_type': req.region_type,
        'weekly_condition': req.weekly_condition,
        'avg_temp': req.avg_temp,
        'rainy_days': req.rainy_days,
        'outdoor_friendly_days': req.outdoor_friendly_days,
        'bad_air_days': req.bad_air_days,
        'mission_type': req.mission_type,
        'proof_type': req.proof_type,
        'is_outdoor': req.is_outdoor,
        'is_group': req.is_group,
        'difficulty': req.difficulty,
        'bonus_points': req.bonus_points,
    }])
    X = hidden_prep.transform(row)
    return {
        'predicted_overall_score': float(hidden_reg.predict(X)[0]),
        'approve_probability': float(hidden_approve_clf.predict_proba(X)[0][1])
    }

def _image_quality_score(img: Image.Image) -> float:
    gray = img.convert('L')
    arr = pd.Series(list(gray.getdata()), dtype='float32')
    std = float(arr.std())
    return max(0.0, min(1.0, std / 80.0))

def _clip_score(img: Image.Image, prompts: list[str]):
    inputs = clip_processor(text=prompts, images=img, return_tensors='pt', padding=True)
    with _torch.no_grad():
        outputs = clip_model(**inputs)
        logits_per_image = outputs.logits_per_image
        probs = logits_per_image.softmax(dim=1)[0]
    best_idx = int(probs.argmax())
    return float(probs[best_idx]), prompts[best_idx]

def _yolo_features(img: Image.Image):
    results = yolo_model.predict(img, verbose=False)
    result = results[0]
    names = result.names
    class_names = [names[int(c)] for c in result.boxes.cls.tolist()] if result.boxes is not None else []
    person_count = sum(1 for c in class_names if c == 'person')
    return {
        'person_count_pred': person_count,
        'trash_bag_detected': int(any(c in {'handbag', 'backpack', 'suitcase'} for c in class_names)),
        'recyclable_item_detected': int(any(c in {'bottle', 'cup'} for c in class_names)),
        'recycle_bin_detected': int(any(c in {'trash can'} for c in class_names)),
        'litter_picker_detected': 0,
        'detected_classes': class_names,
    }

def _class_from_mission(mission_type: str, clip_score: float, person_count: int):
    if mission_type == 'group_cleanup' and person_count >= 2 and clip_score >= 0.2:
        return 'group_cleanup', min(0.95, 0.55 + clip_score)
    if mission_type == 'recycling' and clip_score >= 0.18:
        return 'recycling', min(0.95, 0.5 + clip_score)
    if mission_type == 'jogging_group' and person_count >= 2:
        return 'jogging_group', min(0.95, 0.45 + clip_score)
    if mission_type == 'kindness_activity' and clip_score >= 0.16:
        return 'kindness_activity', min(0.95, 0.4 + clip_score)
    return 'invalid', max(0.35, 0.4 - clip_score)

@app.post('/predict/verification')
def predict_verification(req: VerificationRequest):
    row = pd.DataFrame([req.model_dump()])
    proba = verification_clf.predict_proba(row)[0]
    classes = verification_clf.classes_.tolist()
    return {
        'final_label': verification_clf.predict(row)[0],
        'probabilities': {cls: float(p) for cls, p in zip(classes, proba)}
    }

@app.post('/predict/verification-from-images')
async def predict_verification_from_images(
    mission_type: str = Form(...),
    description_text: str = Form(''),
    files: list[UploadFile] = File(...),
):
    prompts = MISSION_PROMPTS.get(mission_type, [f'a photo related to {mission_type}'])
    best_clip_score = 0.0
    best_prompt = prompts[0]
    best_quality = 0.0
    person_count = 0
    object_flags = {
        'trash_bag_detected': 0,
        'recyclable_item_detected': 0,
        'recycle_bin_detected': 0,
        'litter_picker_detected': 0,
    }
    detected_classes_all = []

    for file in files:
        raw = await file.read()
        img = Image.open(BytesIO(raw)).convert('RGB')
        clip_score, prompt = _clip_score(img, prompts)
        if clip_score > best_clip_score:
            best_clip_score = clip_score
            best_prompt = prompt
        best_quality = max(best_quality, _image_quality_score(img))
        yolo = _yolo_features(img)
        person_count = max(person_count, yolo['person_count_pred'])
        detected_classes_all.extend(yolo['detected_classes'])
        for key in object_flags:
            object_flags[key] = max(object_flags[key], yolo[key])

    predicted_activity_class, activity_conf = _class_from_mission(mission_type, best_clip_score, person_count)
    features = {
        'mission_type': mission_type,
        'description_text': description_text,
        'clip_match_score': best_clip_score,
        'predicted_activity_class': predicted_activity_class,
        'activity_class_confidence': activity_conf,
        'person_count_pred': person_count,
        'trash_bag_detected': object_flags['trash_bag_detected'],
        'recyclable_item_detected': object_flags['recyclable_item_detected'],
        'recycle_bin_detected': object_flags['recycle_bin_detected'],
        'litter_picker_detected': object_flags['litter_picker_detected'],
        'image_quality_score': best_quality,
        'text_length': len(description_text.strip()),
        'mission_match_flag': int(predicted_activity_class == mission_type or (mission_type == 'group_cleanup' and predicted_activity_class == 'group_cleanup')),
    }
    row = pd.DataFrame([features])
    proba = verification_clf.predict_proba(row)[0]
    classes = verification_clf.classes_.tolist()
    final_label = verification_clf.predict(row)[0]
    return {
        'final_label': final_label,
        'probabilities': {cls: float(p) for cls, p in zip(classes, proba)},
        'feature_summary': {
            **features,
            'best_matching_prompt': best_prompt,
            'detected_classes': detected_classes_all,
        },
    }
