import os, pandas as pd, joblib
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
BASE_DIR=os.path.dirname(os.path.dirname(__file__))
CSV=os.path.join(BASE_DIR,'data','verification','verification_final_decision.csv')
MODELS=os.path.join(BASE_DIR,'models'); os.makedirs(MODELS, exist_ok=True)
df=pd.read_csv(CSV)
cat=['mission_type','predicted_activity_class','description_text']
num=['clip_match_score','activity_class_confidence','person_count_pred','trash_bag_detected','recyclable_item_detected','recycle_bin_detected','litter_picker_detected','image_quality_score','text_length','mission_match_flag']
pre=ColumnTransformer([
    ('cat', OneHotEncoder(handle_unknown='ignore'), cat),
    ('num', StandardScaler(), num)
])
clf=Pipeline([('preprocessor',pre),('classifier',LogisticRegression(max_iter=3000))])
clf.fit(df[cat+num], df['final_label'])
joblib.dump(clf, os.path.join(MODELS,'verification_final_decision_clf.joblib'))
print('verification decision model saved')
