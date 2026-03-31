import random
from pathlib import Path
import pandas as pd

random.seed(42)
BASE = Path(__file__).resolve().parents[1]

hidden_dir = BASE / 'data' / 'hidden_mission'
ver_dir = BASE / 'data' / 'verification'
hidden_dir.mkdir(parents=True, exist_ok=True)
ver_dir.mkdir(parents=True, exist_ok=True)

seasons = ['spring', 'summer', 'fall', 'winter']
region_types = ['residential', 'park_area', 'school_area', 'mixed_commercial']
weekly_conditions = ['outdoor_good', 'indoor_preferred', 'mixed', 'hot_week', 'cold_week']
mission_types = ['group_cleanup', 'recycling', 'kindness_action', 'energy_saving', 'group_walk']
proof_types = ['photo', 'short_text', 'group_photo']

TEMPLATES = {
    'group_cleanup': [
        ('이번 주 히든 미션: 동네 플로깅 챌린지', '이번 주 안에 팀원과 함께 동네를 걸으며 쓰레기 5개 이상을 줍고 인증하세요.'),
        ('이번 주 히든 미션: 공원 정리 미션', '공원이나 산책로 주변을 정리하고 단체 인증 사진을 올려주세요.')
    ],
    'recycling': [
        ('이번 주 히든 미션: 분리수거 실천', '이번 주 안에 올바른 분리수거를 실천하고 사진과 짧은 설명을 남겨주세요.'),
        ('이번 주 히든 미션: 재활용 점검', '집이나 공동공간에서 재활용 가능한 물품을 구분해 인증하세요.')
    ],
    'kindness_action': [
        ('이번 주 히든 미션: 이웃 배려 행동', '이번 주 안에 이웃을 배려한 작은 행동을 실천하고 후기를 남겨주세요.'),
        ('이번 주 히든 미션: 따뜻한 한마디', '동네 사람이나 팀원에게 응원과 배려를 실천하고 인증하세요.')
    ],
    'energy_saving': [
        ('이번 주 히든 미션: 절전 챌린지', '이번 주 안에 집이나 공동공간에서 전기 절약 행동을 실천하고 인증해보세요.'),
        ('이번 주 히든 미션: 에너지 세이브', '사용하지 않는 전등과 멀티탭을 끄고 절전 인증을 남겨주세요.')
    ],
    'group_walk': [
        ('이번 주 히든 미션: 함께 걷기 챌린지', '이번 주 안에 팀원과 함께 동네를 걸으며 건강과 대화를 챙겨보세요.'),
        ('이번 주 히든 미션: 동네 산책 미션', '가까운 길을 함께 산책하고 짧은 소감을 남겨주세요.')
    ]
}

def score_hidden(mission_type, weekly_condition, region_type, difficulty, is_outdoor, is_group, rainy_days, outdoor_days, bad_air_days):
    novelty = random.randint(2, 5)
    safety = 4
    feasibility = 4
    participation = 3

    if mission_type == 'group_cleanup':
        participation += 1 if region_type in ['park_area', 'school_area'] else 0
        novelty += 1
        if weekly_condition in ['hot_week', 'cold_week']:
            safety -= 1
            feasibility -= 1
        if weekly_condition == 'indoor_preferred' or bad_air_days >= 3:
            safety -= 2
            feasibility -= 2
            participation -= 1
    elif mission_type == 'recycling':
        participation += 1 if weekly_condition in ['indoor_preferred', 'mixed'] else 0
        feasibility += 1
        safety += 1
    elif mission_type == 'kindness_action':
        participation += 1
        feasibility += 1
        safety += 1
    elif mission_type == 'energy_saving':
        participation += 1 if weekly_condition in ['hot_week', 'cold_week', 'indoor_preferred'] else 0
        feasibility += 1
        safety += 1
    elif mission_type == 'group_walk':
        participation += 1 if outdoor_days >= 4 else 0
        if weekly_condition in ['hot_week', 'cold_week', 'indoor_preferred']:
            safety -= 1
            feasibility -= 1

    if difficulty >= 4:
        participation -= 1
        feasibility -= 1
    if is_group:
        novelty += 1
    if is_outdoor and rainy_days >= 4:
        safety -= 1
        feasibility -= 1

    novelty = min(max(novelty, 1), 5)
    safety = min(max(safety, 1), 5)
    feasibility = min(max(feasibility, 1), 5)
    participation = min(max(participation, 1), 5)
    overall = round((novelty + safety + feasibility + participation) / 4)
    approve = int(overall >= 4 and safety >= 3 and feasibility >= 3)
    return novelty, safety, feasibility, participation, overall, approve

hidden_rows = []
for i in range(200):
    season = random.choice(seasons)
    region_type = random.choice(region_types)
    weekly_condition = random.choice(weekly_conditions)
    avg_temp = {'spring': random.uniform(10, 20), 'summer': random.uniform(24, 34), 'fall': random.uniform(8, 22), 'winter': random.uniform(-5, 8)}[season]
    rainy_days = random.randint(0, 5)
    outdoor_days = random.randint(1, 7)
    bad_air_days = random.randint(0, 4)
    mission_type = random.choice(mission_types)
    title, desc = random.choice(TEMPLATES[mission_type])
    is_outdoor = int(mission_type in ['group_cleanup', 'group_walk'])
    is_group = int(mission_type in ['group_cleanup', 'group_walk'])
    difficulty = random.randint(1, 5)
    bonus_points = random.choice([50, 60, 70, 80, 100])
    proof_type = random.choice(proof_types)
    novelty, safety, feasibility, participation, overall, approve = score_hidden(
        mission_type, weekly_condition, region_type, difficulty, is_outdoor, is_group, rainy_days, outdoor_days, bad_air_days
    )
    hidden_rows.append({
        'candidate_id': f'HM_{i+1:04d}',
        'week_id': f'2026-W{(i % 12) + 1:02d}',
        'season': season,
        'region_type': region_type,
        'weather_summary': f'{weekly_condition} / rainy_days={rainy_days} / outdoor_days={outdoor_days}',
        'weekly_condition': weekly_condition,
        'avg_temp': round(avg_temp, 1),
        'rainy_days': rainy_days,
        'outdoor_friendly_days': outdoor_days,
        'bad_air_days': bad_air_days,
        'mission_title': title,
        'mission_description': desc,
        'mission_type': mission_type,
        'is_outdoor': is_outdoor,
        'is_group': is_group,
        'difficulty': difficulty,
        'bonus_points': bonus_points,
        'proof_type': proof_type,
        'novelty_score': novelty,
        'safety_score': safety,
        'feasibility_score': feasibility,
        'participation_score': participation,
        'overall_score': overall,
        'approve_label': approve,
    })

pd.DataFrame(hidden_rows).to_csv(hidden_dir / 'hidden_mission_candidates.csv', index=False, encoding='utf-8-sig')

# Verification decision data
activity_classes = ['group_cleanup', 'recycling', 'jogging_group', 'kindness_activity', 'invalid']
mission_types_v = ['group_cleanup', 'recycling', 'kindness_activity']

ver_rows = []
for i in range(200):
    mission_type = random.choice(mission_types_v)
    # bias predicted class toward mission_type
    if random.random() < 0.7:
        pred_class = mission_type
    else:
        pred_class = random.choice(activity_classes)
    class_conf = round(random.uniform(0.45, 0.98), 3)
    clip = round(random.uniform(0.3, 0.98), 3)
    person_count = random.randint(0, 6)
    trash_bag = int(random.random() < (0.7 if mission_type == 'group_cleanup' else 0.1))
    recyclable_item = int(random.random() < (0.7 if mission_type == 'recycling' else 0.15))
    recycle_bin = int(random.random() < (0.55 if mission_type == 'recycling' else 0.1))
    litter_picker = int(random.random() < (0.45 if mission_type == 'group_cleanup' else 0.05))
    quality = round(random.uniform(0.4, 1.0), 3)
    text_length = random.randint(5, 120)
    mission_match = int(pred_class == mission_type)

    score = 0
    score += 2 if mission_match else -2
    score += 2 if clip >= 0.72 else (1 if clip >= 0.55 else -1)
    score += 1 if class_conf >= 0.75 else 0
    if mission_type == 'group_cleanup':
        score += 1 if person_count >= 2 else -1
        score += trash_bag + litter_picker
    elif mission_type == 'recycling':
        score += recyclable_item + recycle_bin
    elif mission_type == 'kindness_activity':
        score += 1 if text_length >= 20 else 0
        score += 1 if quality >= 0.65 else 0

    score += 1 if quality >= 0.7 else -1

    if pred_class == 'invalid' or clip < 0.4 or quality < 0.45:
        final_label = 'rejected'
    elif score >= 4:
        final_label = 'approved'
    elif score >= 1:
        final_label = 'needs_review'
    else:
        final_label = 'rejected'

    desc = {
        'group_cleanup': '팀원과 함께 동네 쓰레기를 주웠습니다.',
        'recycling': '집에서 분리수거를 실천했습니다.',
        'kindness_activity': '이웃을 도와드리고 따뜻한 말을 전했습니다.'
    }[mission_type]

    ver_rows.append({
        'sample_id': f'VER_{i+1:04d}',
        'mission_type': mission_type,
        'description_text': desc,
        'clip_match_score': clip,
        'predicted_activity_class': pred_class,
        'activity_class_confidence': class_conf,
        'person_count_pred': person_count,
        'trash_bag_detected': trash_bag,
        'recyclable_item_detected': recyclable_item,
        'recycle_bin_detected': recycle_bin,
        'litter_picker_detected': litter_picker,
        'image_quality_score': quality,
        'text_length': text_length,
        'mission_match_flag': mission_match,
        'final_label': final_label,
    })

pd.DataFrame(ver_rows).to_csv(ver_dir / 'verification_final_decision.csv', index=False, encoding='utf-8-sig')
print('Seed data generated.')
