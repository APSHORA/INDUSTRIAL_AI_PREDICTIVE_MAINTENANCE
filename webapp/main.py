# webapp/main.py
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict
import uvicorn

# প্রজেক্টের রুট পাথ সেট করা
BASE_DIR = Path(__file__).parent.parent
sys.path.append(str(BASE_DIR))

# আপনার existing 'common' ফোল্ডার থেকে কনফিগ ইমপোর্ট
from src.common.config import load_machines_config, get_predictor

# নতুন: ডেটাবেস ফাংশন ইমপোর্ট
from database import save_prediction

app = FastAPI(title="Multi-Machine Health Monitoring API")

# সিস্টেম চালু হওয়ার সময় সব মেশিনের কনফিগ লোড করে রাখা
MACHINES_CONFIG = load_machines_config()
PREDICTORS = {}

for machine in MACHINES_CONFIG["machines"]:
    try:
        PREDICTORS[machine["type"]] = get_predictor(machine["type"])
        print(f"✅ Loaded predictor for: {machine['type']}")
    except Exception as e:
        print(f"❌ Failed to load {machine['type']}: {e}")

class SensorReadings(BaseModel):
    machine_type: str
    features: Dict[str, float]

@app.get("/")
def read_root():
    return {
        "message": "Core Platform is running!",
        "active_machines": list(PREDICTORS.keys())
    }

@app.get("/machines")
def list_machines():
    return MACHINES_CONFIG

@app.post("/predict")
def predict_machine_health(readings: SensorReadings):
    machine_type = readings.machine_type
    
    if machine_type not in PREDICTORS:
        raise HTTPException(status_code=404, detail=f"Machine type '{machine_type}' not supported.")
    
    try:
        # ১. প্রেডিকশন নেওয়া
        predictor_func = PREDICTORS[machine_type]
        result = predictor_func(readings.features)
        
        # ২. নতুন: ডেটাবেসে সেভ করা
        save_prediction(
            machine_type=machine_type,
            machine_id=result.get("machine", "unknown"),
            status=result["status"],
            details=result["details"]
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)