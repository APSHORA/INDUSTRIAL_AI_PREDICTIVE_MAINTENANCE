# scripts/train_hydraulic.py
import json
import joblib
import shutil
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import f1_score
from xgboost import XGBClassifier

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data" / "processed" / "processed_hydraulic"
MODEL_DIR = BASE_DIR / "models" / "hydraulic" / "hydraulic_trained_models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

TARGETS = ["cooler_condition", "valve_condition", "pump_leakage", "accumulator_pressure"]

def build_models():
    return {
        "RandomForest": RandomForestClassifier(n_estimators=300, class_weight="balanced", random_state=42, n_jobs=-1),
        "ExtraTrees": ExtraTreesClassifier(n_estimators=300, class_weight="balanced", random_state=42, n_jobs=-1),
        "HistGradientBoosting": HistGradientBoostingClassifier(max_iter=200, random_state=42),
        "XGBoost": XGBClassifier(n_estimators=300, learning_rate=0.08, max_depth=6, eval_metric="mlogloss", random_state=42, n_jobs=-1),
    }

def main():
    print("🔄 Loading local processed data...")
    X_train = pd.read_csv(DATA_DIR / "X_train_scaled.csv")
    X_val = pd.read_csv(DATA_DIR / "X_val_scaled.csv")
    X_test = pd.read_csv(DATA_DIR / "X_test_scaled.csv")
    y_train = pd.read_csv(DATA_DIR / "y_train.csv")
    y_val = pd.read_csv(DATA_DIR / "y_val.csv")
    y_test = pd.read_csv(DATA_DIR / "y_test.csv")

    # লোকাল ভার্সনের সাথে মিলিয়ে Scaler কপি করা
    scaler_path = DATA_DIR / "standard_scaler.joblib"
    if scaler_path.exists():
        shutil.copy(scaler_path, MODEL_DIR / "standard_scaler.joblib")
    shutil.copy(DATA_DIR / "feature_columns.json", MODEL_DIR / "feature_columns.json")

    for target in TARGETS:
        print(f"\n🎯 Training models for: {target}")
        best_score = -1
        best_model_name = ""
        best_model = None
        best_le = None

        for name, model in build_models().items():
            if name == "XGBoost":
                le = LabelEncoder()
                y_train_enc = le.fit_transform(y_train[target])
                model.fit(X_train, y_train_enc)
                val_pred = le.inverse_transform(model.predict(X_val))
            else:
                model.fit(X_train, y_train[target])
                val_pred = model.predict(X_val)
                le = None

            score = f1_score(y_val[target], val_pred, average="macro", zero_division=0)
            print(f"  {name}: F1 = {score:.4f}")
            
            if score > best_score:
                best_score = score
                best_model_name = name
                best_model = model
                best_le = le

        print(f"✅ Best model for {target}: {best_model_name} (F1: {best_score:.4f})")
        joblib.dump(best_model, MODEL_DIR / f"{target}_model.joblib")
        if best_le is not None:
            joblib.dump(best_le, MODEL_DIR / f"{target}_label_encoder.joblib")

    print("\n🎉 All models saved locally! No more 'input stream corrupted' errors.")

if __name__ == "__main__":
    main()