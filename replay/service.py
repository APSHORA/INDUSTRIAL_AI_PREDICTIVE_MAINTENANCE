# replay/service.py
import sys, json, time, random, threading
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import requests

BASE_DIR = Path(__file__).parent.parent
API_URL = "http://127.0.0.1:8000/predict"

def load_machines():
    with open(BASE_DIR / "machines.json") as f:
        return json.load(f)["machines"]

def post_data(machine_type, features, label):
    try:
        payload = {"machine_type": machine_type, "features": features}
        r = requests.post(API_URL, json=payload, timeout=5)
        r.raise_for_status()
        res = r.json()
        print(f"🔄 {label} | Status: {res['status']} | Details: {res['details']}")
    except Exception as e:
        print(f"❌ {label}: {e}")

def replay_hydraulic():
    print("🚀 Starting Hydraulic Replay (Real Data)...")
    csv_path = BASE_DIR / "data" / "processed" / "processed_hydraulic" / "X_test_scaled.csv"
    if not csv_path.exists():
        print(f"⚠️ Hydraulic CSV not found at {csv_path}")
        return
        
    df = pd.read_csv(csv_path)
    for i, row in df.iterrows():
        post_data("hydraulic", row.to_dict(), f"[Hydraulic] Cycle {i+1}/{len(df)}")
        time.sleep(1)

def replay_engine():
    print("🚀 Starting Engine Replay...")
    csv_path = BASE_DIR / "data" / "processed" / "processed_engine" / "X_test_scaled.csv"
    
    # ১. যদি আসল প্রসেসড CSV থাকে, সেটা ব্যবহার করো
    if csv_path.exists():
        print("✅ Found real Engine data. Sending real cycles...")
        df = pd.read_csv(csv_path)
        for i, row in df.iterrows():
            post_data("engine", row.to_dict(), f"[Engine-Real] Cycle {i+1}/{len(df)}")
            time.sleep(1)
            
    # ২. আর যদি CSV না থাকে, তাহলে C-MAPSS সেন্সর অনুযায়ী Mock ডেটা পাঠাও
    else:
        print("⚠️ Real Engine CSV not found. Falling back to Mock Data...")
        machines = load_machines()
        engine = next((m for m in machines if m["type"] == "engine"), None)
        if not engine:
            print("❌ Engine not found in machines.json!")
            return
            
        sensors = engine["sensors"]
        for i in range(1, 50): # ডেমোর জন্য ৫০ সাইকেল
            feats = {s: round(random.uniform(0, 100), 2) for s in sensors}
            post_data("engine", feats, f"[Engine-Mock] Cycle {i}")
            time.sleep(1)

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--machine", default="all", choices=["hydraulic", "engine", "all"])
    a = p.parse_args()

    jobs = []
    if a.machine in ("hydraulic", "all"): jobs.append(replay_hydraulic)
    if a.machine in ("engine", "all"): jobs.append(replay_engine)

    print(f"🚀 Starting replay for: {a.machine}")
    ts = [threading.Thread(target=j) for j in jobs]
    for t in ts: t.start()
    for t in ts: t.join()