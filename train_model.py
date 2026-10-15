"""
SmartHospital - XGBoost Model Training Script
==============================================
Trains 3 XGBoost models from hospital_training_data.csv:

1. MODEL 1 - Occupancy Regressor
   Predicts tomorrow's bed occupancy rate (0.0 - 1.0)

2. MODEL 2 - LOS Regressor
   Predicts patient Length of Stay (days) based on demographics & condition

3. MODEL 3 - Readmission Classifier
   Predicts if a patient will be readmitted (0 = No, 1 = Yes)

Saved Models (joblib):
  models/xgb_occupancy.pkl
  models/xgb_los.pkl
  models/xgb_readmission.pkl
"""

import os
import numpy as np
import pandas as pd
import joblib
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    mean_absolute_error, r2_score,
    classification_report, roc_auc_score
)

# ===========================================================
# 0. Setup
# ===========================================================
MODELS_DIR = os.path.join(os.path.dirname(__file__), 'models')
os.makedirs(MODELS_DIR, exist_ok=True)

DATA_PATH = os.path.join(os.path.dirname(__file__), 'hospital_training_data.csv')

# ===========================================================
# 1. Load Dataset
# ===========================================================
print("=" * 60)
print("SmartHospital XGBoost Training Pipeline")
print("=" * 60)

print("\n[1/6] Loading training data...")
df = pd.read_csv(DATA_PATH)
print(f"  Records loaded: {len(df)}")
print(f"  Features: {list(df.columns)}")

# Shared feature columns (used by all models)
OCCUPANCY_FEATURES = [
    'day_of_week', 'month', 'week_of_year', 'is_weekend',
    'is_winter', 'is_summer',
    'ward_capacity', 'occupied_beds', 'available_beds',
    'daily_admissions', 'daily_discharges',
    'occupancy_rate', 'admission_discharge_ratio'
]

LOS_FEATURES = [
    'age', 'gender_male', 'condition_severity',
    'day_of_week', 'month', 'is_weekend',
    'ward_capacity', 'occupied_beds', 'occupancy_rate'
]

READMIT_FEATURES = [
    'age', 'gender_male', 'condition_severity',
    'day_of_week', 'month',
    'ward_capacity', 'occupancy_rate',
    'occupied_beds', 'available_beds'
]

# ===========================================================
# 2. Train Model 1: Occupancy Rate Regressor
# ===========================================================
print("\n[2/6] Training Model 1: Bed Occupancy Forecast (Regressor)...")

X_occ = df[OCCUPANCY_FEATURES]
y_occ = df['target_next_occupancy']
X_train, X_test, y_train, y_test = train_test_split(X_occ, y_occ, test_size=0.2, random_state=42)

model_occ = xgb.XGBRegressor(
    n_estimators=300,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    reg_alpha=0.1,
    reg_lambda=1.0,
    random_state=42,
    verbosity=0
)
model_occ.fit(X_train, y_train,
              eval_set=[(X_test, y_test)],
              verbose=False)

y_pred_occ = model_occ.predict(X_test)
mae_occ = mean_absolute_error(y_test, y_pred_occ)
r2_occ = r2_score(y_test, y_pred_occ)
print(f"  MAE  : {mae_occ:.4f}")
print(f"  R²   : {r2_occ:.4f}")

joblib.dump(model_occ, os.path.join(MODELS_DIR, 'xgb_occupancy.pkl'))
joblib.dump(OCCUPANCY_FEATURES, os.path.join(MODELS_DIR, 'xgb_occupancy_features.pkl'))
print(f"  Saved: models/xgb_occupancy.pkl")

# ===========================================================
# 3. Train Model 2: Length of Stay Regressor
# ===========================================================
print("\n[3/6] Training Model 2: Patient Length of Stay (Regressor)...")

X_los = df[LOS_FEATURES]
y_los = df['target_los_days']
X_train, X_test, y_train, y_test = train_test_split(X_los, y_los, test_size=0.2, random_state=42)

model_los = xgb.XGBRegressor(
    n_estimators=300,
    max_depth=5,
    learning_rate=0.05,
    subsample=0.85,
    colsample_bytree=0.8,
    reg_alpha=0.05,
    reg_lambda=1.0,
    random_state=42,
    verbosity=0
)
model_los.fit(X_train, y_train,
              eval_set=[(X_test, y_test)],
              verbose=False)

y_pred_los = model_los.predict(X_test)
mae_los = mean_absolute_error(y_test, y_pred_los)
r2_los = r2_score(y_test, y_pred_los)
print(f"  MAE  : {mae_los:.4f} days")
print(f"  R²   : {r2_los:.4f}")

joblib.dump(model_los, os.path.join(MODELS_DIR, 'xgb_los.pkl'))
joblib.dump(LOS_FEATURES, os.path.join(MODELS_DIR, 'xgb_los_features.pkl'))
print(f"  Saved: models/xgb_los.pkl")

# ===========================================================
# 4. Train Model 3: Readmission Classifier
# ===========================================================
print("\n[4/6] Training Model 3: Readmission Risk Classifier...")

X_ra = df[READMIT_FEATURES]
y_ra = df['target_readmission']
X_train, X_test, y_train, y_test = train_test_split(X_ra, y_ra, test_size=0.2, random_state=42)

# Compute class imbalance weight
scale_pos = (y_train == 0).sum() / max(1, (y_train == 1).sum())

model_ra = xgb.XGBClassifier(
    n_estimators=300,
    max_depth=5,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    scale_pos_weight=scale_pos,
    eval_metric='logloss',
    random_state=42,
    verbosity=0
)
model_ra.fit(X_train, y_train,
             eval_set=[(X_test, y_test)],
             verbose=False)

y_pred_ra = model_ra.predict(X_test)
y_prob_ra = model_ra.predict_proba(X_test)[:, 1]
auc = roc_auc_score(y_test, y_prob_ra)
print(f"  AUC-ROC: {auc:.4f}")
print(f"  Report:\n{classification_report(y_test, y_pred_ra, target_names=['No Readmit', 'Readmit'])}")

joblib.dump(model_ra, os.path.join(MODELS_DIR, 'xgb_readmission.pkl'))
joblib.dump(READMIT_FEATURES, os.path.join(MODELS_DIR, 'xgb_readmission_features.pkl'))
print(f"  Saved: models/xgb_readmission.pkl")

# ===========================================================
# 5. Feature Importances Summary
# ===========================================================
print("\n[5/6] Feature Importances:")

def print_importance(model, features, label):
    imp = pd.Series(model.feature_importances_, index=features).sort_values(ascending=False)
    print(f"\n  >>> {label}")
    for feat, score in imp.head(5).items():
        print(f"      {feat:<35} {score:.4f}")

print_importance(model_occ, OCCUPANCY_FEATURES, "Occupancy Forecast")
print_importance(model_los, LOS_FEATURES, "Length of Stay")
print_importance(model_ra, READMIT_FEATURES, "Readmission Risk")

# ===========================================================
# 6. Save training metadata
# ===========================================================
print("\n[6/6] Saving model metadata...")

metadata = {
    'xgb_version': xgb.__version__,
    'training_records': len(df),
    'models': {
        'occupancy': {
            'file': 'xgb_occupancy.pkl',
            'type': 'regressor',
            'target': 'next_day_occupancy_rate',
            'mae': round(mae_occ, 4),
            'r2': round(r2_occ, 4)
        },
        'los': {
            'file': 'xgb_los.pkl',
            'type': 'regressor',
            'target': 'length_of_stay_days',
            'mae': round(mae_los, 4),
            'r2': round(r2_los, 4)
        },
        'readmission': {
            'file': 'xgb_readmission.pkl',
            'type': 'classifier',
            'target': 'will_readmit_binary',
            'auc_roc': round(auc, 4)
        }
    }
}

import json
with open(os.path.join(MODELS_DIR, 'model_metadata.json'), 'w') as f:
    json.dump(metadata, f, indent=2)

print("\n" + "=" * 60)
print("XGBoost Training Complete!")
print(f"  3 models saved to: ./models/")
print("  - xgb_occupancy.pkl      -> Tomorrow's bed occupancy")
print("  - xgb_los.pkl            -> Patient LOS prediction")
print("  - xgb_readmission.pkl    -> Readmission risk score")
print("=" * 60)
