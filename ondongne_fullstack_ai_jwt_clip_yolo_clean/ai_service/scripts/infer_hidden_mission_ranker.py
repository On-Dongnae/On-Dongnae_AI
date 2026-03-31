from pathlib import Path
import argparse
import joblib
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
MODEL_DIR = BASE / 'models' / 'hidden_mission'


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--title', required=True)
    parser.add_argument('--description', required=True)
    parser.add_argument('--season', required=True)
    parser.add_argument('--region_type', required=True)
    parser.add_argument('--weekly_condition', required=True)
    parser.add_argument('--avg_temp', type=float, required=True)
    parser.add_argument('--rainy_days', type=int, required=True)
    parser.add_argument('--outdoor_friendly_days', type=int, required=True)
    parser.add_argument('--bad_air_days', type=int, required=True)
    parser.add_argument('--mission_type', required=True)
    parser.add_argument('--proof_type', required=True)
    parser.add_argument('--is_outdoor', type=int, required=True)
    parser.add_argument('--is_group', type=int, required=True)
    parser.add_argument('--difficulty', type=int, required=True)
    parser.add_argument('--bonus_points', type=int, required=True)
    args = parser.parse_args()

    row = pd.DataFrame([{
        'mission_title': args.title,
        'mission_description': args.description,
        'weather_summary': f"{args.weekly_condition} / rainy_days={args.rainy_days} / outdoor_days={args.outdoor_friendly_days}",
        'text': f"{args.title} {args.description} {args.weekly_condition}",
        'season': args.season,
        'region_type': args.region_type,
        'weekly_condition': args.weekly_condition,
        'avg_temp': args.avg_temp,
        'rainy_days': args.rainy_days,
        'outdoor_friendly_days': args.outdoor_friendly_days,
        'bad_air_days': args.bad_air_days,
        'mission_type': args.mission_type,
        'proof_type': args.proof_type,
        'is_outdoor': args.is_outdoor,
        'is_group': args.is_group,
        'difficulty': args.difficulty,
        'bonus_points': args.bonus_points,
    }])

    clf = joblib.load(MODEL_DIR / 'hidden_mission_approve_clf.joblib')
    prep = joblib.load(MODEL_DIR / 'hidden_mission_preprocessor.joblib')
    reg = joblib.load(MODEL_DIR / 'hidden_mission_score_regressor.joblib')

    approve_prob = clf.predict_proba(row)[0][1]
    score = reg.predict(prep.transform(row))[0]

    print({
        'predicted_overall_score': round(float(score), 3),
        'approve_probability': round(float(approve_prob), 3)
    })


if __name__ == '__main__':
    main()
