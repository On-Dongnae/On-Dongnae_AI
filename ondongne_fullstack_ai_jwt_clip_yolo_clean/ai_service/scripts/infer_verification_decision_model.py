from pathlib import Path
import argparse
import joblib
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
MODEL_DIR = BASE / 'models' / 'verification'


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--mission_type', required=True)
    parser.add_argument('--description_text', required=True)
    parser.add_argument('--clip_match_score', type=float, required=True)
    parser.add_argument('--predicted_activity_class', required=True)
    parser.add_argument('--activity_class_confidence', type=float, required=True)
    parser.add_argument('--person_count_pred', type=int, required=True)
    parser.add_argument('--trash_bag_detected', type=int, required=True)
    parser.add_argument('--recyclable_item_detected', type=int, required=True)
    parser.add_argument('--recycle_bin_detected', type=int, required=True)
    parser.add_argument('--litter_picker_detected', type=int, required=True)
    parser.add_argument('--image_quality_score', type=float, required=True)
    parser.add_argument('--text_length', type=int, required=True)
    parser.add_argument('--mission_match_flag', type=int, required=True)
    args = parser.parse_args()

    row = pd.DataFrame([vars(args)])
    clf = joblib.load(MODEL_DIR / 'verification_final_decision_clf.joblib')
    pred = clf.predict(row)[0]
    proba_dict = dict(zip(clf.classes_.tolist(), clf.predict_proba(row)[0].round(4).tolist()))
    print({'final_label': pred, 'probabilities': proba_dict})


if __name__ == '__main__':
    main()
