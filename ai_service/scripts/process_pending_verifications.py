from io import BytesIO

from PIL import Image

from app.backend_client import (
    get_pending_verifications,
    patch_ai_result,
    download_image,
)
from app.main import (
    compute_clip_match_score,
    run_yolo_detection,
    image_quality_score,
)


def decide_status_and_reason(
    clip_score: float,
    person_count: int,
    detected_classes: list[str],
    content: str,
    mission_description: str,
):

    confidence = clip_score

    if clip_score >= 0.75:
        return "APPROVED", round(confidence, 4), ""

    reason_parts = []

    if clip_score < 0.75:
        reason_parts.append("이미지와 미션 설명의 일치도가 낮습니다.")

    if person_count == 0:
        reason_parts.append("사진에서 유의미한 활동 인원이 확인되지 않았습니다.")

    if not detected_classes:
        reason_parts.append("이미지에서 관련 객체나 상황을 충분히 확인하지 못했습니다.")

    if not content.strip():
        reason_parts.append("사용자 설명 글이 비어 있습니다.")

    if not mission_description.strip():
        reason_parts.append("미션 원본 설명이 비어 있습니다.")

    reason = " ".join(reason_parts) if reason_parts else "미션 수행 근거가 충분하지 않습니다."
    return "REJECTED", round(confidence, 4), reason


def analyze_single_verification(item: dict):
    verification_id = item["id"]
    content = item.get("content", "")
    image_urls = item.get("imageUrls", [])
    mission_description = item.get("missionDescription", "")

    clip_scores = []
    detected_classes_all = []
    max_person_count = 0
    quality_scores = []

    for image_url in image_urls[:3]:
        image_bytes = download_image(image_url)
        image = Image.open(BytesIO(image_bytes)).convert("RGB")

        quality = image_quality_score(image)
        quality_scores.append(quality)

        clip_result = compute_clip_match_score(image, "group_cleanup")
        clip_scores.append(clip_result["clip_match_score"])

        yolo_result = run_yolo_detection(image)
        detected_classes_all.extend(yolo_result["detected_classes"])
        max_person_count = max(max_person_count, yolo_result["person_count"])

    avg_clip_score = round(sum(clip_scores) / len(clip_scores), 4) if clip_scores else 0.0
    avg_quality_score = round(sum(quality_scores) / len(quality_scores), 4) if quality_scores else 0.0

    status, confidence, reason = decide_status_and_reason(
        clip_score=avg_clip_score,
        person_count=max_person_count,
        detected_classes=detected_classes_all,
        content=content,
        mission_description=mission_description,
    )

    return {
        "verification_id": verification_id,
        "status": status,
        "confidence": confidence,
        "reason": reason,
        "avg_clip_score": avg_clip_score,
        "avg_quality_score": avg_quality_score,
        "person_count": max_person_count,
        "detected_classes": detected_classes_all,
    }


def main():
    pending_items = get_pending_verifications()

    print(f"[INFO] pending verification count = {len(pending_items)}")

    for item in pending_items:
        try:
            result = analyze_single_verification(item)

            patch_ai_result(
                verification_id=result["verification_id"],
                status=result["status"],
                confidence=result["confidence"],
                reason=result["reason"],
            )

            print(
                f"[OK] verification_id={result['verification_id']} "
                f"status={result['status']} confidence={result['confidence']}"
            )

        except Exception as e:
            print(f"[ERROR] verification_id={item.get('id')} detail={e}")


if __name__ == "__main__":
    main()
