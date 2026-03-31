from pathlib import Path
import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / 'data' / 'verification' / 'verification_final_decision.csv'
MODEL_DIR = BASE / 'models' / 'verification'
MODEL_DIR.mkdir(parents=True, exist_ok=True)


def main() -> None:
    df = pd.read_csv(DATA)
    y = df['final_label']
    X = df.drop(columns=['sample_id', 'final_label'])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    cat_cols = ['mission_type', 'predicted_activity_class', 'description_text']
    num_cols = [
        'clip_match_score', 'activity_class_confidence', 'person_count_pred',
        'trash_bag_detected', 'recyclable_item_detected', 'recycle_bin_detected',
        'litter_picker_detected', 'image_quality_score', 'text_length', 'mission_match_flag'
    ]

    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', OneHotEncoder(handle_unknown='ignore'), cat_cols),
            ('num', StandardScaler(), num_cols)
        ]
    )

    clf = Pipeline([
        ('prep', preprocessor),
        ('model', LogisticRegression(max_iter=2000, class_weight='balanced'))
    ])
    clf.fit(X_train, y_train)

    pred = clf.predict(X_test)
    print('=== Verification Final Decision Classifier ===')
    print(classification_report(y_test, pred))

    joblib.dump(clf, MODEL_DIR / 'verification_final_decision_clf.joblib')
    print(f'Saved model to {MODEL_DIR}')


if __name__ == '__main__':
    main()
