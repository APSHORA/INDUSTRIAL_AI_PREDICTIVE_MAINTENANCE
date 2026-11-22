# src/common/config.py
import json
import importlib
from pathlib import Path

# প্রজেক্টের রুট ডিরেক্টরি (যেখানে machines.json আছে)
BASE_DIR = Path(__file__).parent.parent.parent

def load_machines_config():
    """machines.json ফাইল থেকে মেশিনের লিস্ট লোড করা"""
    config_path = BASE_DIR / "machines.json"
    with open(config_path, "r") as f:
        return json.load(f)

def get_predictor(machine_type: str):
    """মেশিনের টাইপ দেখে অটোমেটিক সঠিক predict ফাংশনটি ইমপোর্ট ও রিটার্ন করা"""
    config = load_machines_config()
    
    for machine in config["machines"]:
        if machine["type"] == machine_type:
            # ডাইনামিক্যালি মডিউল ইমপোর্ট করা (Lego Brick Architecture)
            module = importlib.import_module(machine["predict_module"])
            func = getattr(module, machine["predict_function"])
            return func
            
    raise ValueError(f"Machine type '{machine_type}' not found in machines.json!")