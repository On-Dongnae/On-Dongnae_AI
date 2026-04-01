import os, pandas as pd, joblib
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
BASE_DIR=os.path.dirname(os.path.dirname(__file__))
CSV=os.path.join(BASE_DIR,'data','hidden_mission','hidden_mission_candidates.csv')
MODELS=os.path.join(BASE_DIR,'models'); os.makedirs(MODELS, exist_ok=True)
df=pd.read_csv(CSV)
df['combined_text']=df['mission_title'].fillna('')+' '+df['mission_description'].fillna('')+' '+df['weather_summary'].fillna('')
features=['combined_text','season','region_type','weekly_condition','mission_type','is_outdoor','is_group','avg_temp','rainy_days','outdoor_friendly_days','bad_air_days','difficulty','bonus_points']
X=df[features]; y_cls=df['approve_label']; y_reg=df['overall_score']
pre=ColumnTransformer([
    ('text', TfidfVectorizer(max_features=2000, ngram_range=(1,2)), 'combined_text'),
    ('cat', OneHotEncoder(handle_unknown='ignore'), ['season','region_type','weekly_condition','mission_type']),
    ('num', StandardScaler(), ['is_outdoor','is_group','avg_temp','rainy_days','outdoor_friendly_days','bad_air_days','difficulty','bonus_points'])
])
X_t=pre.fit_transform(X)
clf=LogisticRegression(max_iter=2000).fit(X_t,y_cls)
reg=Ridge(alpha=1.0).fit(X_t,y_reg)
joblib.dump(pre, os.path.join(MODELS,'hidden_mission_preprocessor.joblib'))
joblib.dump(clf, os.path.join(MODELS,'hidden_mission_approve_clf.joblib'))
joblib.dump(reg, os.path.join(MODELS,'hidden_mission_score_regressor.joblib'))
print('hidden mission models saved')
