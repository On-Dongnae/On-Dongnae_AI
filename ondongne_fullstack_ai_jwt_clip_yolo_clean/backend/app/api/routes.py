from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import settings, UPLOAD_DIR
from app.core.security import get_current_user, create_access_token, verify_password, get_password_hash
from app.db.session import get_db
from app.db.redis_client import get_redis
from app.models.user import User
from app.models.hidden_mission import HiddenMission
from app.models.verification import ActivityVerification, VerificationImage
from app.models.point_log import PointLog
from app.schemas.user import SignupRequest, LoginRequest, TokenResponse, UserRead
from app.schemas.hidden_mission import HiddenMissionCreate, HiddenMissionRead, HiddenMissionPredictRequest
from app.schemas.verification import VerificationRead
from app.services.ranking_service import get_personal_ranking, get_region_ranking
from app.clients.ai_client import predict_hidden_mission, predict_verification_from_images

router = APIRouter()


def _to_verification_read(v: ActivityVerification) -> VerificationRead:
    return VerificationRead(
        id=v.id,
        user_id=v.user_id,
        mission_type=v.mission_type,
        title=v.title,
        description=v.description,
        status=v.status,
        ai_confidence=v.ai_confidence,
        ai_probabilities=v.ai_probabilities,
        ai_raw_result=v.ai_raw_result,
        image_urls=[img.public_url or img.file_path for img in v.images],
        created_at=v.created_at,
    )


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/auth/signup", response_model=UserRead)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=payload.email,
        nickname=payload.nickname,
        region=payload.region,
        password_hash=get_password_hash(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return TokenResponse(access_token=create_access_token(user.email))


@router.get("/auth/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/hidden-missions", response_model=HiddenMissionRead)
def create_hidden_mission_endpoint(payload: HiddenMissionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    mission = HiddenMission(**payload.model_dump())
    db.add(mission)
    db.commit()
    db.refresh(mission)
    get_redis().setex(f"hidden_mission:{mission.week_id}", 3600, mission.model_dump_json() if hasattr(mission, 'model_dump_json') else str(mission.id))
    return mission


@router.get("/hidden-missions/{week_id}", response_model=HiddenMissionRead)
def get_hidden_mission_endpoint(week_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    mission = db.query(HiddenMission).filter(HiddenMission.week_id == week_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Hidden mission not found")
    return mission


@router.post("/hidden-missions/ai-generate-and-save", response_model=HiddenMissionRead)
def ai_generate_and_save_hidden_mission(payload: HiddenMissionPredictRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ai_result = predict_hidden_mission(get_redis(), {
        "title": payload.title,
        "description": payload.description,
        "season": payload.season,
        "region_type": payload.region_type,
        "weekly_condition": payload.weekly_condition,
        "avg_temp": payload.avg_temp,
        "rainy_days": payload.rainy_days,
        "outdoor_friendly_days": payload.outdoor_friendly_days,
        "bad_air_days": payload.bad_air_days,
        "mission_type": payload.mission_type,
        "proof_type": payload.proof_type,
        "is_outdoor": payload.is_outdoor,
        "is_group": payload.is_group,
        "difficulty": payload.difficulty,
        "bonus_points": payload.bonus_points,
    })
    mission = HiddenMission(
        week_id=payload.week_id,
        title=payload.title,
        description=payload.description,
        mission_type=payload.mission_type,
        region=payload.region,
        bonus_points=payload.bonus_points,
        predicted_overall_score=ai_result.get("predicted_overall_score"),
        approve_probability=ai_result.get("approve_probability"),
        ai_model_version="seed-200-v2",
    )
    db.add(mission)
    db.commit()
    db.refresh(mission)
    return mission


@router.post("/verifications/ai-evaluate-and-save", response_model=VerificationRead)
async def ai_evaluate_and_save_verification(
    mission_type: str = Form(...),
    title: str = Form(...),
    description_text: str = Form(""),
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    verification = ActivityVerification(
        user_id=current_user.id,
        mission_type=mission_type,
        title=title,
        description=description_text,
        status="pending",
    )
    db.add(verification)
    db.flush()

    saved_paths = []
    saved_images = []
    verification_dir = UPLOAD_DIR / f"verification_{verification.id}"
    verification_dir.mkdir(parents=True, exist_ok=True)
    for file in files:
        suffix = Path(file.filename).suffix or ".jpg"
        dest = verification_dir / f"{uuid4().hex}{suffix}"
        content = await file.read()
        dest.write_bytes(content)
        public_url = f"{settings.public_base_url}/api/v1/uploads/{dest.relative_to(UPLOAD_DIR).as_posix()}"
        img = VerificationImage(verification_id=verification.id, file_path=str(dest), public_url=public_url)
        db.add(img)
        saved_images.append(img)
        saved_paths.append(str(dest))

    db.flush()
    ai_result = predict_verification_from_images(get_redis(), mission_type, description_text, saved_paths)
    probs = ai_result.get("probabilities", {})
    conf = max(probs.values()) if probs else None
    verification.status = ai_result.get("final_label", "needs_review")
    verification.ai_confidence = conf
    verification.ai_probabilities = probs
    verification.ai_raw_result = ai_result
    db.add(verification)

    if verification.status == "approved":
        points = 10 + (5 if mission_type in {"group_cleanup", "jogging_group"} else 0)
        current_user.total_points += points
        db.add(PointLog(user_id=current_user.id, points=points, reason=f"verification:{verification.id}"))
        r = get_redis()
        r.zincrby("ranking:personal", points, str(current_user.id))
        r.zincrby(f"ranking:region:{current_user.region}", points, str(current_user.id))

    db.commit()
    db.refresh(verification)
    return _to_verification_read(verification)


@router.get("/verifications", response_model=list[VerificationRead])
def list_verifications_endpoint(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = db.query(ActivityVerification).filter(ActivityVerification.user_id == current_user.id).order_by(ActivityVerification.id.desc()).all()
    return [_to_verification_read(v) for v in rows]


@router.get("/verifications/{verification_id}", response_model=VerificationRead)
def get_verification(verification_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    v = db.query(ActivityVerification).filter(ActivityVerification.id == verification_id, ActivityVerification.user_id == current_user.id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Verification not found")
    return _to_verification_read(v)


@router.get("/rankings/personal")
def personal_ranking(current_user: User = Depends(get_current_user)):
    return get_personal_ranking(get_redis())


@router.get("/rankings/regions/{region}")
def region_ranking(region: str, current_user: User = Depends(get_current_user)):
    return get_region_ranking(get_redis(), region)


@router.get('/uploads/{file_path:path}')
def serve_upload(file_path: str):
    path = UPLOAD_DIR / file_path
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail='File not found')
    return FileResponse(path)
