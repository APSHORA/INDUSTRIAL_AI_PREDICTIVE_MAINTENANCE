# src/engine/predict.py
import random

def get_prediction(features: dict) -> dict:
    """
    Mock predictor for Jet Engine. 
    Returns the exact same JSON structure as Hydraulic.
    """
    rul_estimate = random.randint(15, 130) 
    
    if rul_estimate <= 20:
        status = "Critical"
    elif rul_estimate <= 50:
        status = "Warning"
    else:
        status = "OK"

    return {
        "machine": "Jet Engine 1",
        "machine_type": "engine",
        "status": status,
        "details": {
            "rul_cycles": rul_estimate,
            "health_score": round(random.uniform(0.7, 0.99), 2)
        }
    }