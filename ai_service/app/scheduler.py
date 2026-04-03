import logging
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import os
import json
from datetime import datetime, timedelta
from .main import (
    safe_open_image, image_quality_score, compute_clip_match_score,
    run_yolo_detection, infer_predicted_activity_class, build_feature_row, predict_final_status
)
from .weather_client import get_weekly_weather_summary
from .hidden_mission_recommender import recommend_one_hidden_mission

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BACKEND_URL = os.environ.get("BACKEND_URL", "https://api.on-dongnae.site")

def fetch_and_process_verifications():
    try:
        url = f"{BACKEND_URL}/api/admin/verifications?status=PENDING"
        logger.info(f"[Scheduler] Fetching verifications from {url}")
        resp = requests.get(url, timeout=10)
        
        if resp.status_code != 200:
            logger.error(f"[Scheduler] Failed to fetch verifications. Status: {resp.status_code}")
            return
            
        data_json = resp.json()
        if "data" not in data_json or not data_json["data"]:
            logger.info("[Scheduler] No pending verifications at the moment.")
            return
            
        pending_list = data_json["data"]
        logger.info(f"[Scheduler] Found {len(pending_list)} pending verifications.")
        
        for item in pending_list:
            process_single_verification(item)
            
    except Exception as e:
        logger.error(f"[Scheduler] Error in fetch_and_process_verifications: {e}")

def process_single_verification(item: dict):
    verification_id = item.get("id")
    content = item.get("content", "")
    image_urls = item.get("imageUrls", [])
    
    # ODN_BE VerificationDto does not contain missionType/description, use fallbacks
    mission_type = "unknown"
    mission_description = ""
    
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
    
    try:
        if not image_urls:
            send_ai_result(verification_id, "REJECTED", 0.0, "이미지가 없습니다.")
            return

        for img_url in image_urls:
            img_resp = requests.get(img_url, timeout=10)
            if img_resp.status_code != 200:
                continue
                
            image = safe_open_image(img_resp.content)
            
            q_score = image_quality_score(image)
            quality_scores.append(q_score)

            clip_result = compute_clip_match_score(image, mission_description, content)
            clip_scores.append(clip_result["clip_match_score"])

            yolo_result = run_yolo_detection(image)
            all_detected_classes.extend(yolo_result["detected_classes"])
            max_person_count = max(max_person_count, yolo_result["person_count"])

            for k, v in yolo_result["object_presence"].items():
                if v == 1:
                    merged_object_presence[k] = 1

        if not quality_scores:
            send_ai_result(verification_id, "REJECTED", 0.0, "이미지를 분석할 수 없습니다.")
            return
            
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
        
        reason = ""
        if recommended_status == "REJECTED" and confidence_score < 0.5:
             reason = "AI 분석 결과, 인증 목적과 일치하지 않거나 품질이 낮아 검토가 필요합니다."
             
        send_ai_result(verification_id, recommended_status, confidence_score, reason)
        
    except Exception as e:
        logger.error(f"[Scheduler] Failed to process verification {verification_id}: {e}")
        # Optionally send a rejection or just leave it PENDING for manual retry

def send_ai_result(verification_id, status, confidence, reason):
    url = f"{BACKEND_URL}/api/admin/verifications/{verification_id}/ai-result"
    payload = {
        "status": status,
        "confidence": confidence,
        "reason": reason
    }
    logger.info(f"[Scheduler] Sending AI result to {url} payload: {payload}")
    try:
        resp = requests.patch(url, json=payload, timeout=10)
        if resp.status_code != 200:
            logger.error(f"[Scheduler] Failed to send AI result. Status: {resp.status_code}")
    except Exception as e:
        logger.error(f"[Scheduler] Error sending AI result: {e}")

def generate_and_publish_hidden_mission():
    try:
        weather = get_weekly_weather_summary()
        
        mission_info = recommend_one_hidden_mission(
            weather_summary=weather["weather_summary"],
            weekly_condition=weather["weekly_condition"],
            avg_temp=weather["avg_temp"],
            rainy_days=weather["rainy_days"],
            outdoor_friendly_days=weather["outdoor_friendly_days"],
            bad_air_days=weather["bad_air_days"],
        )
        
        # Calculate startDate/endDate (today)
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        payload = {
            "type": "AI_HIDDEN",
            "name": mission_info["hidden_mission_name"],
            "description": mission_info["description"],
            "pointAmount": int(mission_info.get("predicted_reward_score", 300)),
            "startDate": today_str,
            "endDate": today_str
        }
        
        url = f"{BACKEND_URL}/api/admin/missions"
        logger.info(f"[Scheduler] Publishing hidden mission to {url}")
        
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code not in (200, 201):
            logger.error(f"[Scheduler] Failed to publish hidden mission. Status: {resp.status_code}")
        else:
            logger.info("[Scheduler] Successfully published hidden mission.")
            
    except Exception as e:
        logger.error(f"[Scheduler] Error generating/publishing hidden mission: {e}")

# Scheduler Instance Configuration
scheduler = BackgroundScheduler()

def start_scheduler():
    # Job 1: Process verifications every 1 minute
    scheduler.add_job(fetch_and_process_verifications, 'interval', minutes=1, id='check_verifications')
    
    # Job 2: Generate hidden mission daily at midnight (or whatever frequency desired)
    scheduler.add_job(generate_and_publish_hidden_mission, 'cron', hour=0, minute=0, id='hidden_mission_gen')
    
    scheduler.start()
    logger.info("[Scheduler] Started APScheduler for polling and processing verifications/missions.")

def shutdown_scheduler():
    scheduler.shutdown()
    logger.info("[Scheduler] Shutdown APScheduler.")
