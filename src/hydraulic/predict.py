# src/hydraulic/predict.py
import json
import joblib
import pandas as pd
from pathlib import Path

# প্রজেক্টের রুট ডিরেক্টরি খুঁজে বের করা
BASE_DIR = Path(__file__).parent.parent.parent
MODEL_DIR = BASE_DIR / "models" / "hydraulic" / "hydraulic_trained_models"

class HydraulicPredictor:
    def __init__(self):
        print("Loading hydraulic models...")
        
        # ১. ফিচার কলাম লোড করা
        with open(MODEL_DIR / "feature_columns.json", "r") as f:
            self.feature_columns = json.load(f)
            
        # ২. মডেল এবং লেবেল এনকোডার লোড করা
        self.models = {}
        self.encoders = {}
        
        targets = ["cooler_condition", "valve_condition", "pump_leakage", "accumulator_pressure"]
        for target in targets:
            self.models[target] = joblib.load(MODEL_DIR / f"{target}_model.joblib")
            # XGBoost এর জন্য LabelEncoder লোড করা (যদি থাকে)
            enc_path = MODEL_DIR / f"{target}_label_encoder.joblib"
            if enc_path.exists():
                self.encoders[target] = joblib.load(enc_path)
                
        print("✅ Hydraulic models loaded successfully!")

    def predict(self, features_dict: dict) -> dict:
        # ডিকশনারি থেকে DataFrame বানানো
        df = pd.DataFrame([features_dict])
        
        # মিসিং কলাম থাকলে 0.0 দিয়ে পূরণ করা
        for col in self.feature_columns:
            if col not in df.columns:
                df[col] = 0.0
        df = df[self.feature_columns]

        details = {}
        status = "OK"
        
        for target, model in self.models.items():
            pred = model.predict(df)[0]
            
            # যদি LabelEncoder থাকে, তবে প্রেডিকশনকে আসল লেবেলে রূপান্তর করা
            if target in self.encoders:
                pred = self.encoders[target].inverse_transform([int(pred)])[0]
            
            details[target] = int(pred)
            
            # স্ট্যাটাস নির্ধারণ (Project Plan অনুযায়ী)
            if target == "cooler_condition" and details[target] in (3, 20):
                status = "Warning"
            elif target == "valve_condition" and details[target] in (73, 80):
                status = "Warning"
            elif target == "pump_leakage" and details[target] == 2:
                status = "Critical"
            elif target == "accumulator_pressure" and details[target] in (90, 115):
                status = "Warning"

        return {
            "machine": "Hydraulic rig 1",
            "machine_type": "hydraulic",
            "status": status,
            "details": details
        }

# গ্লোবাল ইনস্ট্যান্স তৈরি (যাতে বারবার মডেল লোড না করতে হয়)
predictor = HydraulicPredictor()

def get_prediction(features: dict) -> dict:
    return predictor.predict(features)