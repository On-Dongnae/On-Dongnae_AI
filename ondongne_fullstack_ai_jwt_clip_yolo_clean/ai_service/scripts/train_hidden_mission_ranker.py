from pathlib import Path
import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import classification_report, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from scipy import sparse

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / 'data' / 'hidden_mission' / 'hidden_mission_candidates.csv'
MODEL_DIR = BASE / 'models' / 'hidden_mission'
MODEL_DIR.mkdir(parents=True, exist_ok=True)


def build_text(df: pd.DataFrame) -> pd.Series:
    return (
        df['mission_title'].fillna('') + ' ' +
        df['mission_description'].fillna('') + ' ' +
        df['weather_summary'].fillna('')
    )


def main() -> None:
    df = pd.read_csv(DATA)
    df['text'] = build_text(df)

    y_score = df['overall_score']
    y_approve = df['approve_label']

    X_train, X_test, y_score_train, y_score_test, y_app_train, y_app_test = train_test_split(
        df, y_score, y_approve, test_size=0.2, random_state=42, stratify=y_approve
    )

    text_col = 'text'
    cat_cols = ['season', 'region_type', 'weekly_condition', 'mission_type', 'proof_type']
    num_cols = ['avg_temp', 'rainy_days', 'outdoor_friendly_days', 'bad_air_days', 'is_outdoor', 'is_group', 'difficulty', 'bonus_points']

    preprocessor = ColumnTransformer(
        transformers=[
            ('text', TfidfVectorizer(max_features=300, ngram_range=(1, 2)), text_col),
            ('cat', OneHotEncoder(handle_unknown='ignore'), cat_cols),
            ('num', StandardScaler(), num_cols),
        ],
        sparse_threshold=0.3,
    )

    # Approval classifier
    clf = Pipeline([
        ('prep', preprocessor),
        ('model', LogisticRegression(max_iter=2000, class_weight='balanced'))
    ])
    clf.fit(X_train, y_app_train)
    pred_app = clf.predict(X_test)
    print('=== Hidden Mission Approve Classifier ===')
    print(classification_report(y_app_test, pred_app))

    # Score regressor: transform with same feature pipeline, then dense for Ridge if needed
    X_train_trans = preprocessor.fit_transform(X_train)
    X_test_trans = preprocessor.transform(X_test)
    reg = Ridge(alpha=1.0)
    reg.fit(X_train_trans, y_score_train)
    pred_score = reg.predict(X_test_trans)
    print('=== Hidden Mission Score Regressor ===')
    print('MAE:', round(mean_absolute_error(y_score_test, pred_score), 4))
    print('R2 :', round(r2_score(y_score_test, pred_score), 4))

    joblib.dump(clf, MODEL_DIR / 'hidden_mission_approve_clf.joblib')
    joblib.dump(preprocessor, MODEL_DIR / 'hidden_mission_preprocessor.joblib')
    joblib.dump(reg, MODEL_DIR / 'hidden_mission_score_regressor.joblib')
    print(f'Saved models to {MODEL_DIR}')


if __name__ == '__main__':
    main()
