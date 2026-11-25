# scripts/prepare_engine_data.py
"""
Phase 3: NASA C-MAPSS (Jet Engine) Data Preprocessing
এই স্ক্রিপ্টটি আপনার লোকাল PC থেকে ডেটা পড়ে প্রসেস করবে।
"""
import os
import json
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

BASE_DIR = Path(__file__).parent.parent
RAW_DIR = RAW_DIR = BASE_DIR / "data" / "raw" / "nasa_cmapps"



DATA_DIR = BASE_DIR / "data" / "processed" / "processed_engine"
DATA_DIR.mkdir(parents=True, exist_ok=True)

def load_and_process():
    print("⚙️ Processing local NASA C-MAPSS data...")
    
    # কলামের নাম (21 sensors + 3 settings + unit_number + time)
    cols = ['unit_number', 'time_in_cycles'] + [f'setting_{i}' for i in range(1, 4)] + [f's_{i}' for i in range(1, 22)]
    
    # ডেটা লোড করা (r"\s+" ব্যবহার করা হয়েছে যাতে Warning না আসে)
    print("📂 Reading files from data/raw/...")
    train_df = pd.read_csv(RAW_DIR / "train_FD001.txt", sep=r"\s+", header=None, names=cols, engine="python")
    test_df = pd.read_csv(RAW_DIR / "test_FD001.txt", sep=r"\s+", header=None, names=cols, engine="python")
    rul_df = pd.read_csv(RAW_DIR / "RUL_FD001.txt", sep=r"\s+", header=None, names=["max_rul"], engine="python")

    # ট্রেন ডেটায় RUL ক্যালকুলেট করা
    max_cycles = train_df.groupby('unit_number')['time_in_cycles'].max().reset_index()
    max_cycles.rename(columns={'time_in_cycles': 'max_cycle'}, inplace=True)
    train_df = train_df.merge(max_cycles, on='unit_number')
    train_df['rul'] = train_df['max_cycle'] - train_df['time_in_cycles']
    train_df.drop('max_cycle', axis=1, inplace=True)

    # টেস্ট ডেটায় RUL ক্যালকুলেট করা
    test_cycles = test_df.groupby('unit_number')['time_in_cycles'].max().reset_index()
    test_cycles.rename(columns={'time_in_cycles': 'last_cycle'}, inplace=True)
    test_df = test_df.merge(test_cycles, on='unit_number')
    test_df = test_df.merge(rul_df, left_on='unit_number', right_index=True)
    test_df['rul'] = (test_df['last_cycle'] - test_df['time_in_cycles']) + test_df['max_rul']
    test_df.drop(['last_cycle', 'max_rul'], axis=1, inplace=True)

    # RUL কে 125 এ Cap করা (স্ট্যান্ডার্ড প্র্যাকটিস)
    train_df['rul'] = train_df['rul'].clip(upper=125)
    test_df['rul'] = test_df['rul'].clip(upper=125)

    # ফিচার এবং টার্গেট আলাদা করা
    feature_cols = [c for c in train_df.columns if c not in ['unit_number', 'time_in_cycles', 'rul']]
    
    X_train_val = train_df[feature_cols]
    y_train_val = train_df['rul']
    X_test = test_df[feature_cols]
    y_test = test_df['rul']

    # Train এবং Validation এ স্প্লিট করা (80% / 20%)
    X_train, X_val, y_train, y_val = train_test_split(X_train_val, y_train_val, test_size=0.2, random_state=42)

    # স্কেলিং
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)

    # DataFrame এ রূপান্তর
    X_train_scaled = pd.DataFrame(X_train_scaled, columns=feature_cols)
    X_val_scaled = pd.DataFrame(X_val_scaled, columns=feature_cols)
    X_test_scaled = pd.DataFrame(X_test_scaled, columns=feature_cols)

    # সেভ করা
    print("💾 Saving processed data...")
    X_train_scaled.to_csv(DATA_DIR / "X_train_scaled.csv", index=False)
    y_train.to_csv(DATA_DIR / "y_train.csv", index=False)
    X_val_scaled.to_csv(DATA_DIR / "X_val_scaled.csv", index=False)
    y_val.to_csv(DATA_DIR / "y_val.csv", index=False)
    X_test_scaled.to_csv(DATA_DIR / "X_test_scaled.csv", index=False)
    y_test.to_csv(DATA_DIR / "y_test.csv", index=False)
    
    joblib.dump(scaler, DATA_DIR / "standard_scaler.joblib")
    with open(DATA_DIR / "feature_columns.json", "w") as f:
        json.dump(feature_cols, f)

    print(f"🎉 Success! Processed Engine data saved to: {DATA_DIR}")
    print(f"   Total Test Cycles: {len(X_test_scaled)}")

if __name__ == "__main__":
    load_and_process()


