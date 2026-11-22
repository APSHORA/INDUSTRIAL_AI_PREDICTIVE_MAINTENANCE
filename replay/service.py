# replay/service.py

import pandas as pd
import requests
import time
from pathlib import Path

# প্রজেক্টের রুট ডিরেক্টরি এবং ডেটার পাথ
BASE_DIR = Path(__file__).parent.parent
DATA_PATH = BASE_DIR / "data" / "processed" / "processed_hydraulic" / "X_test_scaled.csv"
API_URL = "http://127.0.0.1:8000/predict"

def main():
    print(f"📂 Loading data from: {DATA_PATH}")
    
    if not DATA_PATH.exists():
        print(f"❌ Error: Data file not found at {DATA_PATH}")
        return

    df = pd.read_csv(DATA_PATH)
    print(f"✅ Loaded {len(df)} cycles. Starting live replay...\n")

    for index, row in df.iterrows():
        # রো-কে ডিকশনারিতে রূপান্তর করা
        features = row.to_dict()
        
        # API-তে পাঠানোর জন্য পেলোড তৈরি (আমাদের main.py এর ফরম্যাট অনুযায়ী)
        payload = {
            "machine_type": "hydraulic",
            "features": features
        }

        try:
            # FastAPI-তে POST রিকোয়েস্ট পাঠানো
            response = requests.post(API_URL, json=payload)
            response.raise_for_status()
            result = response.json()

            # লাইভ স্ট্যাটাস প্রিন্ট করা
            print(f"🔄 Cycle {index + 1}/{len(df)} | Status: {result['status']} | Details: {result['details']}")
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error sending cycle {index + 1}: {e}")
            print("Make sure the FastAPI backend (webapp/main.py) is running!")
            break

        # ১ সেকেন্ড অপেক্ষা করা (রিয়েল-টাইম সিমুলেশনের জন্য)
        time.sleep(1)

if __name__ == "__main__":
    main()
    